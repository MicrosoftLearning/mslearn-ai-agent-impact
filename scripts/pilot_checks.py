"""Helpers for actual pilot requests/results. Never creates successful traces or inventory."""
from __future__ import annotations
import argparse
import asyncio
import copy
import importlib.util
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from runtime.contracts import Settings, fingerprint, strict_json
from scripts.verify_live import verify


def read(path):
    return strict_json(Path(path).read_text(encoding='utf-8-sig'))


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def check_guardrail(result, case, cfg):
    if case == 'wrong-source':
        if result.get('status') != 'Needs review' or result.get('passed') is True:
            raise ValueError('Wrong-version request was not rejected')
        return
    expected = case == 'valid'
    if (result.get('ran') is not True or result.get('passed') is not expected
            or result.get('profile') != 'core' or result.get('source_version') != cfg.expected_source_version
            or not result.get('sdk_session_id') or not result.get('tool_call_id') or not result.get('evidence')):
        raise ValueError(f'{case}: actual SDK gate/verdict/evidence did not match the expected result')


def check_fixture(record, cfg, state):
    result = verify(record,cfg)
    case = result['case_id']
    expected = {
        'external-support':('Ready for review' if state=='repaired' else 'Needs review',4500,2500,['CMO-01'] if state=='repaired' else []),
        'internal-sufficient':('Ready for review',7500,0,[]),
        'conflicting-evidence':('Needs review',None,None,[])}[case]
    for field, value in zip(('status','internal_units','remaining_units','eligible_cmo_ids'),expected):
        if type(result.get(field)) is not type(value) or result[field] != value:
            raise ValueError(f'{case}: wrong {field} for {state} fixture')
    expected_guard = case == 'internal-sufficient' or (case == 'external-support' and state == 'repaired')
    if result['guardrail'].get('passed') is not expected_guard:
        raise ValueError('Unexpected independent fixture guardrail verdict')
    names = [s['name'] for s in record['trace']['steps']]
    if ('CMOAnalysis' in names) is not (case=='external-support'):
        raise ValueError('Conditional fixture sourcing path differs from the expected case')


def event_module():
    path = ROOT/'Allfiles/L300-TW-Data/event-simulator/replay_events.py'
    spec = importlib.util.spec_from_file_location('pilot_replay_source',path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def publish_events(output, mode):
    module = event_module()
    rows = module.build_events(ROOT/'Allfiles/L300-TW-Data/event-simulator/event_templates.json')
    if mode == 'prime': rows = rows[:1]
    replay_id = rows[0]['EventID'].split('-')[1]
    # Preserve the exact cohort BEFORE attempting any side effect. No automatic resend.
    record = {'mode':mode,'replay_id':replay_id,'publisher_completed':False,
              'ingestion_verified':False,'events':rows}
    write(output/'events.json',record)
    template = (ROOT/'Allfiles/L300-TW-Data/event-simulator/verify_operational_replay.kql').read_text()
    (output/'verify-replay.kql').write_text(template.replace('REPLACE_WITH_ACTUAL_REPLAY_ID',replay_id),encoding='utf-8')
    if mode != 'dry-run':
        module.send_events(rows,0.5)
        record['publisher_completed'] = True
        write(output/'events.json',record)
    print(json.dumps({'mode':mode,'replay_id':replay_id,'event_count':len(rows),
                      'publisher_completed':record['publisher_completed'],'ingestion_verified':False}))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['guardrail-inputs','guardrail-result','core-result','fixture-result','events','fault-result'])
    parser.add_argument('--config',type=Path)
    parser.add_argument('--input',type=Path)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--case',choices=['valid','changed-gap','unknown-supplier','wrong-source'])
    parser.add_argument('--fixture-state',choices=['starter','repaired'],default='starter')
    parser.add_argument('--mode',choices=['prime','replay','dry-run','timeout','missing-verdict','wrong-version'])
    args=parser.parse_args()
    if args.command=='events':
        if args.mode not in ('prime','replay','dry-run') or args.output is None:
            parser.error('events requires --mode prime/replay/dry-run and --output directory')
        args.output.mkdir(parents=True,exist_ok=True)
        publish_events(args.output,args.mode)
        return
    cfg=Settings.model_validate(read(args.config))
    cfg.check_service()
    if args.command=='guardrail-inputs':
        from azure.identity import AzureCliCredential
        from runtime.adapters import FabricSnapshotSource
        source=asyncio.run(FabricSnapshotSource(cfg,AzureCliCredential(tenant_id=cfg.tenant_id)).load())
        proposal=source.assess()
        for case in ('valid','changed-gap','unknown-supplier','wrong-source'):
            value=copy.deepcopy(proposal)
            if case=='changed-gap': value['gap_units']+=1
            if case=='unknown-supplier': value['eligible_cmo_ids']=['UNKNOWN-SUPPLIER']
            required=cfg.expected_source_version if case!='wrong-source' else 'records-sha256:'+'0'*64
            write(args.output/(case+'.json'),{'profile':'core','proposal':value,'proposal_sha256':fingerprint(value),
                                             'required_source_version':required})
        print('Wrote four requests from the actual pinned curated tables; no cloud verdict was fabricated.')
    elif args.command=='guardrail-result':
        check_guardrail(read(args.input)['result'],args.case,cfg)
        print('Expected live guardrail result verified:',args.case)
    elif args.command=='core-result':
        verify(read(args.input),cfg)
        print('Actual core evidence checks passed; channel/source-denial tests remain separate.')
    elif args.command=='fixture-result':
        check_fixture(read(args.input),cfg,args.fixture_state)
        print('Expected live fixture result verified:',args.fixture_state)
    elif args.command=='fault-result':
        record=read(args.input)
        if (record.get('status')!='Needs review' or record['specialist_evidence'].get('pre_guardrail_error_type')
                or record['trace'].get('execution_mode')!='cloud' or record['trace'].get('revision')!=cfg.revision
                or record['trace'].get('runtime_identity_oid')!=cfg.runtime_identity_oid
                or record.get('proposal',{}).get('source_version')!=cfg.expected_source_version):
            raise ValueError('Expected isolated gate rejection without an earlier specialist failure')
        names=[s['name'] for s in record['trace']['steps']]
        if names[:5] != ['ReadCoreSnapshot','ReadOperationalReplay','CurrentCapacity','CMOAnalysis','COORecommendation']:
            raise ValueError('Fault run did not complete the required pre-gate path')
        if args.mode=='timeout':
            if record['specialist_evidence'].get('guardrail_error_type')!='TimeoutError':
                raise ValueError('Timeout hook was not demonstrated')
        elif args.mode=='missing-verdict' and record.get('guardrail') is not None:
            raise ValueError('Missing verdict hook was not demonstrated')
        elif args.mode=='wrong-version' and record.get('guardrail',{}).get('source_version')!='injected-stale-version':
            raise ValueError('Wrong-version hook was not demonstrated')
        print('Expected isolated fault rejection verified:',args.mode)


if __name__=='__main__':
    main()
