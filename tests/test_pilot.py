"""Local pilot-helper tests. Fabricated/double results are never live acceptance."""
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
from scripts.pilot_checks import publish_events, event_module, check_guardrail
from scripts.runtime_admin import invocation_completed


class PilotTests(unittest.TestCase):
    def test_dry_run_retains_exact_cohort_and_its_query(self):
        with tempfile.TemporaryDirectory() as directory, contextlib.redirect_stdout(io.StringIO()):
            root=Path(directory)
            publish_events(root,'dry-run')
            result=json.loads((root/'events.json').read_text())
            self.assertEqual(len(result['events']),10)
            self.assertFalse(result['publisher_completed'])
            self.assertFalse(result['ingestion_verified'])
            ids=[e['EventID'] for e in result['events']]
            self.assertEqual(len(set(ids)),10)
            self.assertTrue(all(i.startswith('SIM-'+result['replay_id']+'-') for i in ids))
            self.assertIn(result['replay_id'],(root/'verify-replay.kql').read_text())

    def test_failed_publish_retains_identity_and_never_retries(self):
        source=event_module()
        source.send_events=Mock(side_effect=TimeoutError('transport-double'))
        with tempfile.TemporaryDirectory() as directory, patch('scripts.pilot_checks.event_module',return_value=source):
            root=Path(directory)
            with self.assertRaises(TimeoutError): publish_events(root,'prime')
            source.send_events.assert_called_once()
            retained=json.loads((root/'events.json').read_text())
            self.assertEqual(len(retained['events']),1)
            self.assertFalse(retained['publisher_completed'])
            self.assertFalse(retained['ingestion_verified'])

    def test_cli_accepts_executed_negative_guardrail_but_not_a_bare_boolean(self):
        self.assertFalse(invocation_completed({'passed':True},'guardrail'))
        self.assertTrue(invocation_completed({'ran':True,'passed':False,'sdk_session_id':'double','tool_call_id':'double'},'guardrail'))
        self.assertTrue(invocation_completed({'status':'Needs review'},'guardrail'))
        self.assertFalse(invocation_completed({'status':'Denied'},'guardrail'))

    def test_guardrail_case_checks_require_sdk_and_evidence(self):
        cfg=SimpleNamespace(expected_source_version='test-source')
        verdict={'ran':True,'passed':False,'profile':'core','source_version':'test-source',
                 'sdk_session_id':'double','tool_call_id':'double','evidence':{'blob':'double'}}
        check_guardrail(verdict,'changed-gap',cfg)
        for field in ('ran','passed','profile','source_version','sdk_session_id','tool_call_id','evidence'):
            changed={**verdict,field:None}
            with self.subTest(field=field), self.assertRaises(ValueError):
                check_guardrail(changed,'changed-gap',cfg)
        with self.assertRaises(ValueError): check_guardrail(verdict,'valid',cfg)
