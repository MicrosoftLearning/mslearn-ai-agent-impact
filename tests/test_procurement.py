import json
import unittest
from types import SimpleNamespace
import httpx
from swagger_spec_validator.validator20 import validate_spec
from scripts.export_connector import connector_document
from runtime.contracts import FollowUpRequest
from runtime.procurement import GraphLists


class ProcurementTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.rows, self.posts = [], 0
        self.cfg = SimpleNamespace(graph_site_id='site',rfp_list_id='rfps',supplier_list_id='suppliers',followup_list_id='followups')
        def transport(request):
            path = str(request.url)
            if path.endswith('/columns'):
                return httpx.Response(200,json={'value':[{'name':'ClientRequestId','indexed':True,'enforceUniqueValues':True}]})
            if request.method == 'POST':
                self.posts += 1
                fields = json.loads(request.content)['fields']
                self.rows.append({'id':'actual-item-7','fields':fields,'webUrl':'https://example.sharepoint.com/item/7'})
                return httpx.Response(201,json=self.rows[-1])
            return httpx.Response(200,json={'value':self.rows if '/followups/' in path else [{'id':'1','fields':{'Title':'RFP-01','Status':'Open'}}]})
        credential = SimpleNamespace(get_token=lambda _:SimpleNamespace(token='transport-double'))
        self.graph = GraphLists(self.cfg,credential,transport=httpx.MockTransport(transport))
        self.request = FollowUpRequest(rfp_id='RFP-01',request_text='Please follow up.',
            client_request_id='12345678-1234-1234-1234-123456789abc',confirmed=True)

    async def test_retries_return_existing_receipt_without_duplicate_append(self):
        first = await self.graph.append(self.request,'actual-caller')
        second = await self.graph.append(self.request,'actual-caller')
        self.assertEqual(first['receipt_id'],second['receipt_id'])
        self.assertFalse(first['duplicate'])
        self.assertTrue(second['duplicate'])
        self.assertEqual(self.posts,1)

    async def test_reused_key_with_different_caller_or_payload_is_rejected(self):
        await self.graph.append(self.request,'caller-1')
        with self.assertRaises(ValueError):
            await self.graph.append(self.request,'caller-2')
        changed = self.request.model_copy(update={'request_text':'Other request'})
        with self.assertRaises(ValueError):
            await self.graph.append(changed,'caller-1')
        self.assertEqual(self.posts,1)

    async def test_no_patch_delete_or_manufacturing_endpoint(self):
        for method, target in [('PATCH','followups'),('DELETE','followups'),('POST','rfps'),('GET','raw-batches')]:
            with self.assertRaises(ValueError):
                await self.graph.request(method,target,'/items')

    def test_explicit_confirmation_is_required(self):
        for value in (False, 1, 'true', None):
            with self.assertRaises(ValueError):
                FollowUpRequest.model_validate({**self.request.model_dump(),'confirmed':value})

    async def test_schema_without_unique_key_cannot_append(self):
        def bad_schema(request):
            return httpx.Response(200,json={'value':[{'name':'ClientRequestId','indexed':True,'enforceUniqueValues':False}]})
        self.graph.transport = httpx.MockTransport(bad_schema)
        with self.assertRaisesRegex(ValueError,'schema'):
            await self.graph.append(self.request,'caller')
        self.assertEqual(self.posts,0)

    def test_generated_connector_passes_swagger_v2_validation(self):
        cfg = SimpleNamespace(tenant_id='00000000-0000-0000-0000-000000000001',
                              api_audience='00000000-0000-0000-0000-000000000002')
        document = connector_document(cfg,'https://actions.example.test')
        validate_spec(document)
        self.assertEqual(document['swagger'],'2.0')
        self.assertEqual(set(document['paths']),{'/rfps','/suppliers','/follow-ups'})
        confirmation = document['definitions']['FollowUpRequest']['properties']['confirmed']
        self.assertEqual(confirmation['enum'],[True])
        self.assertNotIn('default',confirmation)
        for origin in ('http://actions.example.test','https://evil@actions.example.test','https://actions.example.test/path'):
            with self.assertRaises(ValueError):
                connector_document(cfg,origin)
