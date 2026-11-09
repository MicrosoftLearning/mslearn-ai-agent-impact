"""Offline tests of the GENERATED workflow using a bounded WDL/connector double.

This is not the Power Automate engine, a solution-import test, or live authorization.
The interpreter rejects expressions/action types outside the implemented subset.
"""
from __future__ import annotations
import base64
import copy
import importlib.util
import json
from pathlib import Path
import re
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'lifecycle/ex2/build_recordfollowup_solution.py'
spec = importlib.util.spec_from_file_location('recordfollowup_builder_under_test', SOURCE)
flow = importlib.util.module_from_spec(spec)
spec.loader.exec_module(flow)


class WorkflowDouble:
    """Execute this workflow's emitted action tree, with mock SharePoint responses."""
    def __init__(self, definition, request, rows=None, mode='success', rfp_status='Open'):
        self.definition, self.request = definition, copy.deepcopy(request)
        self.rows, self.mode, self.rfp_status = copy.deepcopy(rows or []), mode, rfp_status
        self.outputs, self.statuses, self.response, self.posts = {}, {}, None, 0

    def expression(self, text):
        pos = 0
        def parse():
            nonlocal pos
            while pos < len(text) and text[pos].isspace(): pos += 1
            if pos == len(text): raise ValueError('Missing WDL expression')
            if text[pos] == "'":
                pos += 1; value = ''
                while pos < len(text):
                    ch = text[pos]; pos += 1
                    if ch == "'":
                        if pos < len(text) and text[pos] == "'": value += "'"; pos += 1
                        else: break
                    else: value += ch
                else: raise ValueError('Unterminated WDL string')
            elif text[pos].isdigit():
                m = re.match(r'\d+', text[pos:]); value = int(m[0]); pos += len(m[0])
            else:
                m = re.match(r'[A-Za-z_][A-Za-z0-9_]*', text[pos:])
                if not m: raise ValueError('Unsupported WDL expression: '+text[pos:])
                name=m[0]; pos += len(name)
                if text[pos:pos+1] != '(': raise ValueError('Expected function call')
                pos += 1; args=[]
                while text[pos:pos+1] != ')':
                    args.append(parse())
                    while pos < len(text) and text[pos].isspace(): pos += 1
                    if text[pos:pos+1] == ',': pos += 1
                    elif text[pos:pos+1] != ')': raise ValueError('Expected separator')
                pos += 1
                funcs = {
                    'triggerBody': lambda: self.request,
                    'body': lambda action: self.outputs[action],
                    'length': len,
                    'first': lambda rows: rows[0],
                    'empty': lambda v: v is None or v == '' or v == [] or v == {},
                    'string': lambda v: '' if v is None else str(v),
                    'base64': lambda v: base64.b64encode(v.encode()).decode(),
                    'concat': lambda *v: ''.join(v),
                    'take': lambda v,n: v[:n],
                    'replace': lambda v,a,b: v.replace(a,b),
                }
                if name not in funcs: raise ValueError('Unsupported WDL function: '+name)
                value=funcs[name](*args)
            while text[pos:pos+2] == '?[':
                pos += 2; key=parse()
                if text[pos:pos+1] != ']': raise ValueError('Missing property bracket')
                pos += 1
                value=value.get(key) if isinstance(value,dict) else None
            return value
        result=parse()
        if text[pos:].strip(): raise ValueError('Unparsed WDL suffix: '+text[pos:])
        return result

    def value(self, value):
        if not isinstance(value, str): return value
        if value.startswith('@') and not value.startswith('@{'): return self.expression(value[1:])
        return re.sub(r'@\{([^{}]+)\}', lambda m: str(self.expression(m[1])), value)

    def condition(self, expr):
        op, value = next(iter(expr.items()))
        if len(expr) != 1: raise ValueError('Ambiguous condition')
        if op == 'and': return all(self.condition(e) for e in value)
        if op == 'not': return not self.condition(value)
        if op == 'equals':
            left,right=map(self.value,value)
            return type(left) is type(right) and left == right
        raise ValueError('Unsupported condition: '+op)

    def connect(self, name, action):
        params={k:self.value(v) for k,v in action['inputs']['parameters'].items()}
        op=action['inputs']['host']['operationId']
        if op == 'GetItems':
            if (self.mode == 'initial-read-failure' and name == 'Get_existing_request') or (
                self.mode == 'recovery-read-failure' and name == 'Get_after_failure') or (
                self.mode == 'rfp-read-failure' and name == 'Get_open_RFP'):
                raise RuntimeError('Synthetic read failure')
            if params['table'] == 'followups':
                # Check the emitted escaped filter as well as the lookup result.
                want=self.request['client_request_id'].replace("'", "''")
                if params['$filter'] != "ClientRequestId eq '"+want+"'": raise AssertionError(params)
                rows=[r for r in self.rows if r.get('ClientRequestId') == self.request['client_request_id']]
                return {'value':copy.deepcopy(rows[:params['$top']])}
            if params['table'] == 'rfps':
                rows=[] if self.rfp_status != 'Open' else [{'ID':1,'Title':self.request['rfp_id'],'Status':'Open'}]
                if self.mode == 'ambiguous-rfp': rows=rows*2
                return {'value':rows}
            raise ValueError('Unapproved table')
        if op != 'PostItem' or params['table'] != 'followups': raise ValueError('Unexpected write')
        self.posts += 1
        if self.mode in ('write-failure','recovery-read-failure'): raise RuntimeError('Synthetic write failure')
        if self.mode == 'timeout-no-write': raise TimeoutError('Synthetic timeout')
        row={k[5:]:v for k,v in params.items() if k.startswith('item/')}
        row['ID']=7
        if self.mode == 'conflict-other-caller': row['CallerOid']='other-caller'
        if self.mode == 'conflict-other-text': row['RequestText']='another request'
        self.rows.append(row)
        if self.mode in ('conflict-identical','conflict-other-caller','conflict-other-text'): raise RuntimeError('Synthetic concurrent conflict')
        if self.mode == 'timeout-after-write': raise TimeoutError('Synthetic lost response')
        return {} if self.mode == 'missing-created-id' else {'ID':7}

    def run_actions(self, actions):
        pending=dict(actions)
        while pending:
            progress=False
            for name, action in list(pending.items()):
                prior=action.get('runAfter',{})
                if any(p not in self.statuses for p in prior): continue
                del pending[name];progress=True
                if any(self.statuses[p] not in statuses for p,statuses in prior.items()):
                    self.statuses[name]='Skipped';continue
                try:
                    kind=action['type']
                    if kind == 'OpenApiConnection': self.outputs[name]=self.connect(name,action)
                    elif kind == 'If':
                        branch=action['actions'] if self.condition(action['expression']) else action.get('else',{}).get('actions',{})
                        self.run_actions(branch)
                    elif kind == 'Response':
                        if self.response is not None: raise AssertionError('Multiple responses')
                        self.response={k:self.value(v) for k,v in action['inputs']['body'].items()}
                    else: raise ValueError('Unsupported action: '+kind)
                    self.statuses[name]='Succeeded'
                except (RuntimeError,TimeoutError) as e:
                    self.statuses[name]='TimedOut' if isinstance(e,TimeoutError) else 'Failed'
            if not progress: raise AssertionError('Invalid/unresolved runAfter dependency: '+str(pending))

    def run(self):
        self.run_actions(self.definition['actions'])
        if self.response is None: raise AssertionError('No response emitted')
        return self.response


class RecordFollowUpTests(unittest.TestCase):
    def setUp(self):
        self.definition=flow.definition('https://example.invalid/sites/training','rfps','followups')
        self.request={'rfp_id':'RFP-01','request_text':'Please follow up.','client_request_id':'learner-FOLLOWUP-01','caller_oid':'caller-one'}
    def row(self,**changes):
        return {'ID':7,'Title':'RFP-01','RequestText':'Please follow up.','ClientRequestId':'learner-FOLLOWUP-01','CallerOid':'caller-one','Confirmed':True,**changes}
    def simulate(self,**kwargs):
        runner=WorkflowDouble(self.definition,self.request,**kwargs); result=runner.run()
        return result,runner
    def test_open_new_request_creates_once(self):
        r,w=self.simulate();self.assertEqual((r['status'],r['receipt_id'],w.posts),('created','7',1))
    def test_identical_retry_recovers_without_write(self):
        r,w=self.simulate(rows=[self.row()]);self.assertEqual((r['status'],r['receipt_id'],w.posts),('duplicate','7',0))
    def test_identical_retry_after_rfp_closure(self):
        r,w=self.simulate(rows=[self.row()],rfp_status='Closed');self.assertEqual((r['status'],w.posts),('duplicate',0))
    def test_conflicting_caller_does_not_disclose_receipt(self):
        r,w=self.simulate(rows=[self.row(CallerOid='another')]);self.assertEqual((r['status'],r['receipt_id'],w.posts),('rejected','',0))
    def test_conflicting_rfp_rejected(self):
        r,w=self.simulate(rows=[self.row(Title='RFP-02')]);self.assertEqual((r['status'],r['receipt_id']),('rejected',''))
    def test_conflicting_text_rejected(self):
        r,w=self.simulate(rows=[self.row(RequestText='Other')]);self.assertEqual((r['status'],r['receipt_id']),('rejected',''))
    def test_long_requests_not_compared_using_truncated_hash(self):
        self.request['request_text']='x'*400+'A'
        r,w=self.simulate(rows=[self.row(RequestText='x'*400+'B',PayloadHash='same-truncated-legacy-value')]);self.assertEqual(r['status'],'rejected')
    def test_unconfirmed_prior_row_rejected(self):
        r,w=self.simulate(rows=[self.row(Confirmed=False)]);self.assertEqual(r['status'],'rejected')
    def test_missing_prior_receipt_rejected(self):
        r,w=self.simulate(rows=[self.row(ID=None)]);self.assertEqual((r['status'],r['receipt_id']),('rejected',''))
    def test_ambiguous_prior_rows_never_return_a_receipt(self):
        r,w=self.simulate(rows=[self.row(),self.row(ID=8)]);self.assertEqual((r['status'],r['receipt_id'],w.posts),('failed','',0))
    def test_closed_new_request_has_no_write(self):
        r,w=self.simulate(rfp_status='Closed');self.assertEqual((r['status'],w.posts),('rejected',0))
    def test_missing_rfp_status_has_no_write(self):
        r,w=self.simulate(rfp_status=None);self.assertEqual((r['status'],w.posts),('rejected',0))
    def test_ambiguous_rfp_has_no_write(self):
        r,w=self.simulate(mode='ambiguous-rfp');self.assertEqual((r['status'],w.posts),('rejected',0))
    def test_unrelated_failed_write_is_not_duplicate(self):
        r,w=self.simulate(mode='write-failure');self.assertEqual((r['status'],r['receipt_id'],w.posts),('failed','',1))
    def test_timeout_without_row_is_not_duplicate(self):
        r,w=self.simulate(mode='timeout-no-write');self.assertEqual((r['status'],r['receipt_id'],w.posts),('failed','',1))
    def test_timeout_after_write_recovers_actual_receipt(self):
        r,w=self.simulate(mode='timeout-after-write');self.assertEqual((r['status'],r['receipt_id'],w.posts),('duplicate','7',1))
    def test_concurrent_identical_request_recovers(self):
        r,w=self.simulate(mode='conflict-identical');self.assertEqual((r['status'],r['receipt_id'],w.posts),('duplicate','7',1))
    def test_concurrent_other_caller_rejected(self):
        r,w=self.simulate(mode='conflict-other-caller');self.assertEqual((r['status'],r['receipt_id']),('rejected',''))
    def test_concurrent_other_payload_rejected(self):
        r,w=self.simulate(mode='conflict-other-text');self.assertEqual((r['status'],r['receipt_id']),('rejected',''))
    def test_failed_recovery_never_claims_success(self):
        r,w=self.simulate(mode='recovery-read-failure');self.assertEqual((r['status'],r['receipt_id'],w.posts),('failed','',1))
    def test_failed_initial_lookup_prevents_write(self):
        r,w=self.simulate(mode='initial-read-failure');self.assertEqual((r['status'],w.posts),('failed',0))
    def test_failed_rfp_lookup_prevents_write(self):
        r,w=self.simulate(mode='rfp-read-failure');self.assertEqual((r['status'],w.posts),('failed',0))
    def test_missing_create_receipt_is_not_success(self):
        r,w=self.simulate(mode='missing-created-id');self.assertEqual((r['status'],r['receipt_id']),('failed',''))
    def test_quote_in_client_id_is_escaped(self):
        self.request['client_request_id']="learner's-FOLLOWUP-01"
        r,w=self.simulate();self.assertEqual(r['status'],'created')
    def test_required_inputs_and_response_contract_preserved(self):
        schema=self.definition['triggers']['manual']['inputs']['schema']
        self.assertEqual(set(schema['required']),set(self.request))
        r,w=self.simulate();self.assertEqual(set(r),{'status','receipt_id','message'})
    def test_single_append_action_and_no_automatic_post_retry(self):
        def flatten(actions):
            for a in actions.values():
                yield a
                yield from flatten(a.get('actions',{}));yield from flatten(a.get('else',{}).get('actions',{}))
        writes=[a for a in flatten(self.definition['actions']) if a.get('inputs',{}).get('host',{}).get('operationId')=='PostItem']
        self.assertEqual(len(writes),1);self.assertEqual(writes[0]['inputs']['retryPolicy'],{'type':'none'})
    def test_generated_zip_json_and_xml_parse(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'solution.zip'
            flow.build('https://example.invalid/sites/training','rfps','followups',str(path))
            with zipfile.ZipFile(path) as z:
                self.assertIsNone(z.testzip())
                for name in z.namelist():
                    if name.endswith('.xml'): ET.fromstring(z.read(name))
                    elif name.endswith('.json'): json.loads(z.read(name))
                manifest=ET.fromstring(z.read('solution.xml'))
                self.assertEqual(manifest.findtext('./SolutionManifest/Version'),'1.0.0.2')
                definition=json.loads(z.read('Workflows/RecordFollowUp-'+flow.WORKFLOW_ID.upper()+'.json'))
                self.assertEqual(definition['properties']['definition'],self.definition)
    def test_original_workflow_id_and_connection_reference_preserved(self):
        self.assertEqual(flow.WORKFLOW_ID,'8c3f1b2a-6d1e-4f0a-9b7c-2c5a4e7d9f10')
        self.assertEqual(flow.CONN_REF,'cal_sharepoint_caldova')

if __name__=='__main__': unittest.main(verbosity=2)
