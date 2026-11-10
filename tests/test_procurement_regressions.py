"""Regression tests against the real GraphLists/FollowUpRequest code; all HTTP is mocked."""
import json
from pathlib import Path
import sys
import unittest
from types import SimpleNamespace

import httpx
from runtime.contracts import FollowUpRequest
from runtime.procurement import GraphLists


class ProcurementReviewTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.rows = []
        self.posts = 0
        self.status = 'Open'
        self.rfp_count = 1
        self.unique = True
        self.post_mode = 'success'
        self.supplier_fields = {
            'Title': 'CMO-01', 'SupplierName': 'Synthetic Partner',
            'Service': 'Sterile fill-finish', 'ProcurementContact': 'contact@example.invalid',
            'DirectoryStatus': 'Listed for sourcing', 'PrivateUnexpectedField': 'not exposed',
        }
        self.cfg = SimpleNamespace(graph_site_id='test-site', rfp_list_id='rfps',
                                   supplier_list_id='suppliers', followup_list_id='followups')
        def transport(request):
            path = request.url.path
            if path.endswith('/columns'):
                return httpx.Response(200, json={'value':[
                    {'name':'ClientRequestId','indexed':True,'enforceUniqueValues':self.unique}]})
            if request.method == 'POST':
                self.posts += 1
                fields = json.loads(request.content)['fields']
                if self.post_mode == 'error-no-write':
                    return httpx.Response(400, json={'error':'simulated unrelated failure'})
                if self.post_mode == 'server-error':
                    return httpx.Response(503, json={'error':'simulated unavailable'})
                row = {'id':'test-receipt-7','fields':fields,'webUrl':'https://example.invalid/item/7'}
                self.rows.append(row)
                if self.post_mode == 'conflict-with-write':
                    return httpx.Response(409, json={'error':'simulated concurrent duplicate'})
                return httpx.Response(201, json=row)
            if '/followups/' in path:
                return httpx.Response(200, json={'value':self.rows})
            if '/suppliers/' in path:
                return httpx.Response(200, json={'value':[{'id':'test-supplier', 'fields':self.supplier_fields}]})
            fields = {'Title':'RFP-01','SupplierId':'CMO-01','Service':'Sterile fill-finish',
                      'LastUpdated':'2026-10-01','FollowUpRequested':False}
            if self.status is not None:
                fields['Status'] = self.status
            return httpx.Response(200, json={'value':[{'id':str(i),'fields':fields} for i in range(self.rfp_count)]})
        credential = SimpleNamespace(get_token=lambda _:SimpleNamespace(token='mock-only'))
        self.graph = GraphLists(self.cfg, credential, transport=httpx.MockTransport(transport))
        self.request = FollowUpRequest(rfp_id='RFP-01', request_text='Confirmed test follow-up.',
            client_request_id='12345678-1234-1234-1234-123456789abc', confirmed=True)

    async def test_open_rfp_creates_once(self):
        result = await self.graph.append(self.request,'test-caller')
        self.assertFalse(result['duplicate'])
        self.assertEqual(self.posts,1)
        self.assertEqual(result['receipt_id'],'test-receipt-7')

    async def test_closed_rfp_rejected_without_write(self):
        self.status='Closed'
        with self.assertRaisesRegex(ValueError,'Open'):
            await self.graph.append(self.request,'test-caller')
        self.assertEqual(self.posts,0)

    async def test_missing_status_rejected_without_write(self):
        self.status=None
        with self.assertRaisesRegex(ValueError,'Open'):
            await self.graph.append(self.request,'test-caller')
        self.assertEqual(self.posts,0)

    async def test_unknown_status_rejected_without_write(self):
        self.status='Pending'
        with self.assertRaisesRegex(ValueError,'Open'):
            await self.graph.append(self.request,'test-caller')
        self.assertEqual(self.posts,0)

    async def test_same_retry_has_same_receipt(self):
        first=await self.graph.append(self.request,'test-caller')
        again=await self.graph.append(self.request,'test-caller')
        self.assertTrue(again['duplicate'])
        self.assertEqual(first['receipt_id'],again['receipt_id'])
        self.assertEqual(self.posts,1)

    async def test_original_receipt_retrievable_after_close(self):
        first=await self.graph.append(self.request,'test-caller')
        self.status='Closed'
        again=await self.graph.append(self.request,'test-caller')
        self.assertTrue(again['duplicate'])
        self.assertEqual(first['receipt_id'],again['receipt_id'])
        self.assertEqual(self.posts,1)

    async def test_different_caller_rejected(self):
        await self.graph.append(self.request,'caller-one')
        with self.assertRaisesRegex(ValueError,'another request'):
            await self.graph.append(self.request,'caller-two')
        self.assertEqual(self.posts,1)

    async def test_different_payload_rejected(self):
        await self.graph.append(self.request,'test-caller')
        changed=self.request.model_copy(update={'request_text':'Different request'})
        with self.assertRaisesRegex(ValueError,'another request'):
            await self.graph.append(changed,'test-caller')
        self.assertEqual(self.posts,1)

    async def test_missing_or_ambiguous_rfp_rejected(self):
        for count in (0,2):
            with self.subTest(count=count):
                self.rfp_count=count
                with self.assertRaisesRegex(ValueError,'exactly once'):
                    await self.graph.append(self.request,'test-caller')
        self.assertEqual(self.posts,0)

    async def test_seeded_supplier_columns_returned(self):
        fields=(await self.graph.catalog('suppliers'))[0]['fields']
        for key in ('Title','SupplierName','Service','ProcurementContact','DirectoryStatus'):
            self.assertEqual(fields[key],self.supplier_fields[key])
        self.assertNotIn('PrivateUnexpectedField',fields)

    async def test_seeded_rfp_columns_returned(self):
        fields=(await self.graph.catalog('rfps'))[0]['fields']
        self.assertEqual(fields['Service'],'Sterile fill-finish')
        self.assertEqual(fields['LastUpdated'],'2026-10-01')
        self.assertIs(fields['FollowUpRequested'],False)

    async def test_nonunique_schema_rejected(self):
        self.unique=False
        with self.assertRaisesRegex(ValueError,'unique'):
            await self.graph.append(self.request,'test-caller')
        self.assertEqual(self.posts,0)

    async def test_concurrent_exact_request_recovers(self):
        self.post_mode='conflict-with-write'
        result=await self.graph.append(self.request,'test-caller')
        self.assertTrue(result['duplicate'])
        self.assertEqual(self.posts,1)

    async def test_unrelated_error_not_reported_as_duplicate(self):
        self.post_mode='error-no-write'
        with self.assertRaises(httpx.HTTPStatusError):
            await self.graph.append(self.request,'test-caller')
        self.assertEqual(self.posts,1)
        self.assertEqual(self.rows,[])

    async def test_server_error_is_not_retried(self):
        self.post_mode='server-error'
        with self.assertRaises(httpx.HTTPStatusError):
            await self.graph.append(self.request,'test-caller')
        self.assertEqual(self.posts,1)

    async def test_write_and_list_boundaries_unchanged(self):
        for method,lst in [('PATCH','followups'),('DELETE','followups'),('POST','rfps'),('GET','manufacturing')]:
            with self.subTest(method=method,lst=lst), self.assertRaises(ValueError):
                await self.graph.request(method,lst,'/items')

    def test_uuid_api_contract_is_not_weakened(self):
        with self.assertRaises(ValueError):
            FollowUpRequest(**{**self.request.model_dump(),'client_request_id':'learner-FOLLOWUP-01'})

    def test_explicit_confirmation_is_not_weakened(self):
        for value in [False,1,'true',None]:
            with self.subTest(value=value),self.assertRaises(ValueError):
                FollowUpRequest(**{**self.request.model_dump(),'confirmed':value})

if __name__=='__main__':
    unittest.main(verbosity=2)
