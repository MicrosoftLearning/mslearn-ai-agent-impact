"""Exercise actual validators via mocked transport, without claiming cloud execution."""
import copy
import inspect
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from copilot import CopilotClient
from copilot.tools import ToolInvocation
from runtime.guardrail import sdk_validate, CopilotGuardrail
from runtime.fixture import FixtureRuntime, FixtureRequest
from runtime.contracts import fingerprint
from test_runtime import snapshot


class GuardrailTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.cfg = SimpleNamespace(guardrail_model='test-model',guardrail_azure_endpoint='https://test.openai.azure.com',timeout_seconds=5)
        self.credential = SimpleNamespace(get_token=lambda _:SimpleNamespace(token='transport-double'))

    async def test_model_cannot_author_a_verdict_without_executing_the_tool(self):
        class Session:
            async def __aenter__(self): return self
            async def __aexit__(self,*_): pass
            async def send_and_wait(self,text): return '{"passed":true}'
        class Client:
            def __init__(self,**kwargs):
                inspect.signature(CopilotClient).bind(**kwargs)
            async def __aenter__(self): return self
            async def __aexit__(self,*_): pass
            async def create_session(self,**kwargs):
                inspect.signature(CopilotClient.create_session).bind(None,**kwargs)
                return Session()
        with patch('copilot.CopilotClient',Client):
            operation = AsyncMock(return_value={'passed':True})
            with self.assertRaisesRegex(ValueError,'did not execute'):
                await sdk_validate(self.cfg,self.credential,'ValidateCoreDecision',operation)
            operation.assert_not_awaited()

    async def test_registered_sdk_handler_recomputes_and_carries_actual_callback_ids(self):
        operation = AsyncMock(return_value={'passed':False,'ran':True})
        class Session:
            async def __aenter__(self): return self
            async def __aexit__(self,*_): pass
            async def send_and_wait(self,text):
                return await self.tool.handler(ToolInvocation(session_id='callback-session',tool_call_id='callback-call',
                    tool_name='ValidateCoreDecision',arguments={}))
        class Client:
            def __init__(self,**kwargs):
                inspect.signature(CopilotClient).bind(**kwargs)
            async def __aenter__(self): return self
            async def __aexit__(self,*_): pass
            async def create_session(self,**kwargs):
                inspect.signature(CopilotClient.create_session).bind(None,**kwargs)
                assert kwargs['enable_skills'] is False and kwargs['enable_host_git_operations'] is False
                rejected = kwargs['on_permission_request'](None,{})
                assert rejected.kind == 'reject'
                session = Session()
                session.tool = kwargs['tools'][0]
                return session
        with patch('copilot.CopilotClient',Client):
            result = await sdk_validate(self.cfg,self.credential,'ValidateCoreDecision',operation)
        operation.assert_awaited_once()
        self.assertFalse(result['passed'])
        self.assertEqual(result['tool_call_id'],'callback-call')

    async def test_core_guardrail_re_reads_its_own_source(self):
        trusted = snapshot()
        self.cfg.expected_source_version = trusted.source_version
        source = SimpleNamespace(load=AsyncMock(return_value=trusted))
        guardrail = CopilotGuardrail(self.cfg,source,self.credential)
        proposal = trusted.assess()
        proposal['gap_units'] = 1
        async def transport(cfg,cred,name,operation):
            return {**await operation(),'sdk_session_id':'double','tool_call_id':'double'}
        with patch('runtime.guardrail.sdk_validate',transport):
            result = await guardrail.check({'profile':'core','proposal':proposal,'proposal_sha256':fingerprint(proposal),
                                            'required_source_version':trusted.source_version})
        source.load.assert_awaited_once()
        self.assertFalse(result['passed'])


class FixtureTests(unittest.IsolatedAsyncioTestCase):
    async def run_fixture(self,case_id,repaired=False):
        cfg = SimpleNamespace(revision='test123',runtime_identity_oid='test-identity')
        store = SimpleNamespace(save=AsyncMock(return_value={'blob':'test','sha256':'test'}))
        team = SimpleNamespace()
        calls = []
        async def call(role,payload,**kwargs):
            calls.append(role)
            assessment = payload['assessment']
            value = ({k:assessment[k] for k in ('case_id','internal_units','remaining_units')}
                     if role == 'capacity' else copy.deepcopy(assessment))
            return {'value':value,'receipt':{'agent_id':'test-'+role}}
        team.call = call
        service = FixtureRuntime(cfg,team,store,None,mode='test')
        async def sdk(cfg,cred,name,operation):
            calls.append('guardrail')
            return {**await operation(),'sdk_session_id':'test','tool_call_id':'test'}
        with patch('runtime.fixture.sdk_validate',sdk):
            if repaired:
                with patch.object(service.capacity,'qualification_issue',service.gxp.qualification_issue):
                    result = await service.run(FixtureRequest(case_id=case_id),'test-caller')
            else:
                result = await service.run(FixtureRequest(case_id=case_id),'test-caller')
        return result,calls

    async def test_starter_is_rejected_by_independent_policy(self):
        result,calls = await self.run_fixture('external-support')
        self.assertEqual(result['status'],'Needs review')
        self.assertFalse(result['guardrail']['passed'])
        self.assertEqual(calls,['capacity','cmo','coo','guardrail'])
        self.assertFalse(result['live_verified'])

    async def test_repaired_and_internal_and_conflict_paths(self):
        external,_ = await self.run_fixture('external-support',True)
        self.assertEqual(external['eligible_cmo_ids'],['CMO-01'])
        self.assertEqual(external['remaining_units'],2500)
        internal,calls = await self.run_fixture('internal-sufficient',True)
        self.assertEqual(internal['remaining_units'],0)
        self.assertNotIn('cmo',calls)
        self.assertEqual(calls[-1],'guardrail')
        conflict,calls = await self.run_fixture('conflicting-evidence',True)
        self.assertEqual(conflict['status'],'Needs review')
        self.assertIsNone(conflict['remaining_units'])
        self.assertFalse(conflict['guardrail']['passed'])
        self.assertEqual(calls[-1],'guardrail')
