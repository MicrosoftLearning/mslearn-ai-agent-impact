"""Isolated qualification exercise. The starter defect remains in qualification.py."""
from __future__ import annotations
import asyncio
import importlib
import sys
from pathlib import Path
from typing import Literal
from .contracts import StrictModel, fingerprint
from .guardrail import sdk_validate
from .trace import RunTrace


class FixtureRequest(StrictModel):
    case_id: Literal['external-support','internal-sufficient','conflicting-evidence']


class FixtureRuntime:
    def __init__(self, cfg, team, evidence, credential, *, mode='cloud'):
        directory = Path(__file__).resolve().parents[1] / 'Labfiles/04-caldova-agents/Python/qualification-tool'
        if not directory.is_dir():
            raise ValueError('Fixture assets are absent: use the isolated fixture image')
        sys.path.insert(0, str(directory))
        self.capacity = importlib.import_module('capacity_tool')
        self.gxp = importlib.import_module('gxp_checks')
        self.cfg, self.team, self.evidence, self.credential, self.mode = cfg, team, evidence, credential, mode

    async def run(self, request, caller, *, platform_headers=None):
        trace = RunTrace(revision=self.cfg.revision, identity=self.cfg.runtime_identity_oid,
                         caller=caller, profile='qualification-fixture', mode=self.mode)
        scenario = self.capacity.load_scenario(request.case_id)
        source_version = fingerprint(scenario)
        records, proposal, verdict, error_type = {}, None, None, None
        try:
            assessment = await trace.call('AssessCandidates', lambda: asyncio.to_thread(self.capacity.assess, scenario))
            payload = {'profile':'qualification-fixture','scenario':scenario,'assessment':assessment,
                       'source_version':source_version}
            records['capacity'] = await trace.call('CurrentCapacity', lambda: self.team.call('capacity', payload, platform_headers=platform_headers))
            observed = records['capacity']['value']
            for field in ('case_id','internal_units','remaining_units'):
                if type(observed.get(field)) is not type(assessment[field]) or observed[field] != assessment[field]:
                    raise ValueError('Fixture specialist changed source quantities')
            if assessment['remaining_units'] is not None and assessment['remaining_units'] > 0:
                records['cmo'] = await trace.call('CMOAnalysis', lambda: self.team.call('cmo', payload, platform_headers=platform_headers))
                if records['cmo']['value'] != assessment:
                    raise ValueError('Fixture supplier specialist changed the tool result')
            records['coo'] = await trace.call('COORecommendation', lambda: self.team.call('coo',
                {**payload,'specialist_findings':{k:v['value'] for k,v in records.items()}}, platform_headers=platform_headers))
            proposal = records['coo']['value']
            if proposal != assessment:
                raise ValueError('Fixture recommendation changed the tool result')
        except Exception as error:
            error_type = type(error).__name__
        # Run SDK even for conflicts, internal-only, and pre-gate errors.
        try:
            async def validate():
                result = self.gxp.check(proposal or {}, self.capacity.load_scenario(request.case_id))
                return {**result,'ran':True,'profile':'qualification-fixture',
                        'source_version':source_version,'proposal_sha256':fingerprint(proposal)}
            verdict = await trace.call('ComplianceGuardrail', lambda: sdk_validate(self.cfg, self.credential, 'gxp-checks', validate))
        except Exception as error:
            error_type = type(error).__name__
        safe = (error_type is None and proposal is not None and verdict is not None
                and verdict.get('ran') is True and bool(verdict.get('tool_call_id'))
                and bool(verdict.get('sdk_session_id')))
        passed = safe and verdict['passed'] is True
        ids = (['CAP-01','LEG-01','POL-01'] if scenario['evidence_conflict'] else
               ['BASE-01',*[p['id'] for p in scenario['plants']],
                *((proposal or {}).get('candidate_ids',[])), 'POL-01'])
        result = {'case_id':request.case_id, 'status':'Ready for review' if passed else 'Needs review',
                  'internal_units':proposal['internal_units'] if safe else None,
                  'remaining_units':proposal['remaining_units'] if safe else None,
                  'eligible_cmo_ids':proposal['candidate_ids'] if passed else [],
                  'facts':[f"Fixture evidence as of {scenario['as_of']}; launch {scenario['launch_date']}."],
                  'assumptions':[], 'gaps':[] if passed else ['Resolve qualification/source evidence before approval.'],
                  'next_action':'Quality must review the evidence before procurement takes any action.',
                  'claims':[{'text':'Assessment uses the isolated fixture source and POL-01.', 'evidence_ids':ids}],
                  'guardrail':verdict or {'ran':False,'passed':False,'policy_id':'POL-01'},
                  'trace':{'run_id':trace.run_id,
                           'agent_ids':[r['receipt']['agent_id'] for r in records.values()],
                           'guardrail_before_final':safe, 'blocked_agent_called':False},
                  'profile':'qualification-fixture', 'source_version':source_version,
                  'live_verified':self.mode == 'cloud' and safe, 'final_procurement_approval':False}
        record = {'result':result,'trace':trace.export(),'specialist_evidence':records,'error_type':error_type}
        receipt = await self.evidence.save(trace.run_id, record)
        return {**result,'evidence':receipt}
