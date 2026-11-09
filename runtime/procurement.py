"""Selected SharePoint list access and idempotent append-only follow-up requests."""
from __future__ import annotations
import asyncio
import uuid
from urllib.parse import quote
import httpx
from .contracts import FollowUpRequest, fingerprint


class GraphLists:
    def __init__(self, settings, credential, *, transport=None):
        self.cfg, self.credential, self.transport = settings, credential, transport

    async def request(self, method, list_id, suffix='', *, body=None, params=None):
        if list_id not in {self.cfg.rfp_list_id, self.cfg.followup_list_id, self.cfg.supplier_list_id}:
            raise ValueError('List is not allowlisted')
        if method not in ('GET', 'POST') or (method == 'POST' and (list_id != self.cfg.followup_list_id or suffix != '/items')):
            raise ValueError('Only follow-up appends are allowed')
        token = await asyncio.to_thread(self.credential.get_token, 'https://graph.microsoft.com/.default')
        root = f'https://graph.microsoft.com/v1.0/sites/{quote(self.cfg.graph_site_id, safe="")}/lists/{quote(list_id, safe="")}'
        async with httpx.AsyncClient(timeout=30, follow_redirects=False, transport=self.transport) as client:
            return await client.request(method, root+suffix, headers={'Authorization':'Bearer '+token.token},
                                        json=body, params=params)

    async def items(self, list_id, field=None, value=None):
        params = {'$expand':'fields', '$top':'100'}
        if field:
            if field not in {'Title','ClientRequestId'}:
                raise ValueError('Unsafe lookup field')
            params['$filter'] = f"fields/{field} eq '{value.replace(chr(39), chr(39)*2)}'"
        response = await self.request('GET', list_id, '/items', params=params)
        response.raise_for_status()
        data = response.json()
        if '@odata.nextLink' in data:
            raise ValueError('Training list exceeds bounded result size')
        return data['value']

    async def catalog(self, kind):
        list_id = {'rfps':self.cfg.rfp_list_id,'suppliers':self.cfg.supplier_list_id}[kind]
        rows = await self.items(list_id)
        allowed = {'Title','SupplierId','Status','Owner','Contact','DueDate','Description'}
        # Preserve the API's existing fields and expose the actual beta seed columns.
        allowed |= {
            'rfps': {'Service', 'LastUpdated', 'FollowUpRequested'},
            'suppliers': {'SupplierName', 'Service', 'ProcurementContact', 'DirectoryStatus'},
        }[kind]
        return [{'item_id':r['id'], 'web_url':r.get('webUrl'),
                 'fields':{k:v for k,v in r['fields'].items() if k in allowed}} for r in rows]

    async def append(self, request: FollowUpRequest, caller):
        schema = await self.request('GET', self.cfg.followup_list_id, '/columns')
        schema.raise_for_status()
        columns = schema.json()
        keys = [c for c in columns['value'] if c.get('name') == 'ClientRequestId']
        if ('@odata.nextLink' in columns or len(keys) != 1 or keys[0].get('enforceUniqueValues') is not True
                or keys[0].get('indexed') is not True):
            raise ValueError('Actual follow-up schema must enforce a unique indexed ClientRequestId')
        rfps = await self.items(self.cfg.rfp_list_id, 'Title', request.rfp_id)
        if len(rfps) != 1:
            raise ValueError('RFP must exist exactly once in the approved list')
        digest = fingerprint({'rfp_id':request.rfp_id, 'request_text':request.request_text, 'caller':caller})
        async def existing():
            rows = await self.items(self.cfg.followup_list_id, 'ClientRequestId', request.client_request_id)
            if len(rows) > 1:
                raise ValueError('ClientRequestId uniqueness is not enforced')
            if not rows:
                return None
            row = rows[0]
            if row['fields'].get('PayloadHash') != digest or row['fields'].get('CallerOid') != caller:
                raise ValueError('Idempotency key was already used for another request')
            return row
        row = await existing()
        duplicate = row is not None
        if row is None:
            # A matching prior receipt is still retrievable after an RFP closes.
            # Only a new write requires the RFP to be explicitly Open.
            if rfps[0].get('fields', {}).get('Status') != 'Open':
                raise ValueError('A new follow-up requires an Open RFP')
            response = await self.request('POST', self.cfg.followup_list_id, '/items', body={'fields':{
                'Title':request.rfp_id, 'ClientRequestId':request.client_request_id,
                'RequestText':request.request_text, 'CallerOid':caller, 'PayloadHash':digest,
                'Confirmed':True}})
            if response.status_code in (400, 409):
                # A concurrent append may have won the unique-key race. Never blindly retry POST.
                row = await existing()
                if row is None:
                    response.raise_for_status()
                duplicate = True
            else:
                response.raise_for_status()
                row = response.json()
        return {'receipt_id':row['id'], 'list_id':self.cfg.followup_list_id,
                'web_url':row.get('webUrl'), 'client_request_id':request.client_request_id,
                'rfp_id':request.rfp_id, 'payload_sha256':digest, 'duplicate':duplicate,
                'status':'Follow-up recorded', 'award_approved':False}


def create_app(cfg, graph, evidence, auth):
    from fastapi import FastAPI, Header, HTTPException
    from .auth import AccessDenied
    app = FastAPI(title='Caldova Procurement Actions', version='1.0.0')
    async def caller(header, permission):
        try:
            return await auth.caller(header, permission)
        except AccessDenied:
            raise HTTPException(403, 'Access denied') from None
    @app.get('/readiness')
    async def health():
        return {'status':'ready', 'revision':cfg.revision}
    @app.get('/rfps', operation_id='GetRfps')
    async def rfps(authorization: str | None = Header(default=None)):
        await caller(authorization, 'Procurement.Read')
        return await graph.catalog('rfps')
    @app.get('/suppliers', operation_id='GetSuppliers')
    async def suppliers(authorization: str | None = Header(default=None)):
        await caller(authorization, 'Procurement.Read')
        return await graph.catalog('suppliers')
    @app.post('/follow-ups', operation_id='RecordFollowUp')
    async def follow_up(request: FollowUpRequest, authorization: str | None = Header(default=None)):
        oid = await caller(authorization, 'FollowUp.Write')
        try:
            receipt = await graph.append(request, oid)
        except ValueError as error:
            raise HTTPException(409, str(error)) from None
        except Exception:
            raise HTTPException(503, 'Outcome unknown; retry only with the same client_request_id.') from None
        try:
            audit = await evidence.save(str(uuid.uuid4()), {'profile':'procurement','caller':oid,'receipt':receipt,'revision':cfg.revision})
        except Exception:
            raise HTTPException(503, 'Append may have completed; retry with the same client_request_id to recover its receipt.') from None
        return {**receipt,'audit':audit}
    return app
