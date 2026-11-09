"""Check exported runtime receipts. Transport doubles and missing gates cannot pass.

First download each record with runtime_admin export, which checks its returned hash.
This check supplements source/tenant audit review; it does not certify regulatory readiness.
"""
import argparse
import json
import re
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from runtime.contracts import Settings, fingerprint
from runtime.core import POLICY_ID


def require(value, message):
    if not value:
        raise ValueError(message)


def verify(record, cfg):
    trace = record['trace']
    require(trace.get('execution_mode') == 'cloud', 'Offline/double evidence is not live acceptance')
    require(trace.get('revision') == cfg.revision, 'Wrong deployed revision')
    require(trace.get('runtime_identity_oid') == cfg.runtime_identity_oid, 'Wrong runtime identity')
    require(re.fullmatch(r'[0-9a-f-]{36}',trace.get('run_id','')), 'Missing runtime run ID')
    steps = trace['steps']
    names = [s['name'] for s in steps]
    require(all(s.get('finished_utc') and s.get('duration_ms') is not None for s in steps), 'Incomplete runtime span')
    result = record.get('result', record)
    guard = result['guardrail']
    require(guard.get('ran') is True and guard.get('tool_call_id') and guard.get('sdk_session_id'), 'Missing SDK callback evidence')
    if cfg.service == 'orchestrator':
        require(names == ['ReadCoreSnapshot','ReadOperationalReplay','CurrentCapacity','CMOAnalysis','COORecommendation','ComplianceGuardrail'], 'Wrong real LP001 handoffs')
        require(all(s['status']=='succeeded' for s in steps), 'A real core step failed')
        require(result['status']=='Ready for review' and guard.get('passed') is True, 'Core gate did not pass')
        proposal = result['proposal']
        require(guard.get('profile')=='core' and guard.get('policy_id')==POLICY_ID, 'Wrong policy/profile')
        require(guard.get('source_version')==cfg.expected_source_version==proposal.get('source_version'), 'Source pin mismatch')
        require(guard.get('proposal_sha256')==fingerprint(proposal), 'Unbound verdict')
        require(result['operational_signals']['replay_id']==cfg.replay_id, 'Wrong replay')
        for role in ('capacity','cmo'):
            receipt = record['specialist_evidence'][role]['receipt']
            require(receipt['fabric_tool_calls']>0,'Missing actual Fabric tool execution')
        require(record['specialist_evidence']['cmo']['receipt']['policy_tool_calls']>0,'Missing approved-policy retrieval')
        for role, entry in record['specialist_evidence'].items():
            require(entry['receipt']['agent_name']==cfg.agents[role].name and entry['receipt']['agent_version']==cfg.agents[role].version,'Unpinned specialist')
    elif cfg.service == 'fixture':
        require(trace.get('profile')=='qualification-fixture' and names[-1]=='ComplianceGuardrail', 'Wrong fixture gate')
        require(result['trace']['guardrail_before_final'] is True and result['trace']['blocked_agent_called'] is False,'Invalid fixture order')
        require(result.get('live_verified') is True,'Fixture execution incomplete')
    else:
        raise ValueError('Use an orchestrator or fixture configuration')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,required=True)
    parser.add_argument('--records',type=Path,nargs='+',required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    cfg = Settings.model_validate_json(args.config.read_text(encoding='utf-8-sig'))
    results = [verify(json.loads(p.read_text(encoding='utf-8')),cfg) for p in args.records]
    if cfg.service == 'fixture':
        ids = [r['case_id'] for r in results]
        require(len(ids)==3 and set(ids)=={'external-support','internal-sufficient','conflicting-evidence'},'Exactly three distinct live fixture cases required')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(''.join(json.dumps(r,allow_nan=False)+'\n' for r in results),encoding='utf-8')
    print('Runtime receipt checks passed. Review source audit, actual channel activation/denial and governance evidence separately.')


if __name__ == '__main__':
    main()
