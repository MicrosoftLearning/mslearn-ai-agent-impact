"""Code-enforced release gate; raw model drafts never reach the caller."""
from __future__ import annotations

import asyncio
from .contracts import DecisionRequest, fingerprint
from .core import POLICY_ID, SourceError
from .trace import RunTrace


def summary(proposal: dict, signals: dict) -> str:
    suppliers = ', '.join(proposal['eligible_cmo_ids']) or 'none required for the current gap'
    return (f"LP001: target {proposal['target_units']:,} units; qualified {proposal['qualified_units']:,} units; "
            f"authoritative gap {proposal['gap_units']:,} units; binding plant {proposal['binding_plant_id']}; "
            f"{proposal['delayed_batch_count']} delayed batches. Provisional suppliers, in order: {suppliers}. "
            'Qualification-expiry evidence and complete transfer approvals are missing. '
            'Final approval through launch is blocked pending quality evidence. '
            f"Simulation replay {signals['replay_id']}: ten unique events, four strict breaches. "
            'CMO006 has a simulated nine-week lead time versus eight weeks in the core source; investigate separately. '
            'The authoritative gap is unchanged. Sources: launch_program:LP001, plant:'
            f"{proposal['binding_plant_id']}, batch and supplier record keys retained in evidence.")


class Orchestrator:
    def __init__(self, settings, source, events, team, evidence, *, mode='cloud'):
        self.cfg, self.source, self.events, self.team, self.evidence = settings, source, events, team, evidence
        self.mode = mode

    async def run(self, request: DecisionRequest, caller: str, *, platform_headers=None):
        trace = RunTrace(revision=self.cfg.revision, identity=self.cfg.runtime_identity_oid,
                         caller=caller, profile='core', mode=self.mode)
        retained, proposal, signals, verdict = {}, None, None, None
        status, answer = 'Needs review', 'Decision unavailable: required source, specialist or guardrail evidence failed.'
        try:
            async with asyncio.timeout(self.cfg.timeout_seconds * 6):
                snapshot = await trace.call('ReadCoreSnapshot', self.source.load)
                expected = snapshot.assess()
                signals = await trace.call('ReadOperationalReplay', self.events.load)
                payload = {'profile': 'core', 'launch_program_id': 'LP001',
                           'source_version': snapshot.source_version, 'question': request.question,
                           'required_contract': list(expected), 'operational_signals': signals}
                capacity = await trace.call('CurrentCapacity', lambda: self.team.call(
                    'capacity', payload, platform_headers=platform_headers, require_fabric=True))
                retained['capacity'] = capacity
                cap = capacity['value']
                keys = ['target_units','qualified_units','gap_units','binding_plant_id','delayed_batch_count']
                if not isinstance(cap, dict) or any(type(cap.get(k)) is not type(expected[k]) or cap[k] != expected[k] for k in keys):
                    raise SourceError('Current Capacity conflicts with the authoritative snapshot')
                if expected['gap_units'] > 0:
                    cmo = await trace.call('CMOAnalysis', lambda: self.team.call(
                        'cmo', {**payload, 'capacity': cap}, platform_headers=platform_headers, require_fabric=True))
                    retained['cmo'] = cmo
                    if cmo['value'].get('eligible_cmo_ids') != expected['eligible_cmo_ids']:
                        raise SourceError('Supplier analysis differs from core eligibility/order')
                draft = await trace.call('COORecommendation', lambda: self.team.call(
                    'coo', {**payload, 'trusted_contract': expected, 'specialist_findings':
                            {k:v['value'] for k,v in retained.items()}}, platform_headers=platform_headers))
                retained['coo'] = draft
                proposal = draft['value']
                # This is an early rejection, not a substitute for the independent SDK gate.
                if not snapshot.validate(proposal)['passed']:
                    raise SourceError('COO proposal changed the strict core contract')
        except Exception as error:
            retained['pre_guardrail_error_type'] = type(error).__name__
        # Every path attempts the actual independent guardrail, including source errors/internal-only.
        try:
            if self.cfg.fault_mode == 'timeout':
                raise TimeoutError('Isolated guardrail timeout injection')
            guarded = await trace.call('ComplianceGuardrail', lambda: self.team.call(
                'guardrail', {'profile':'core', 'proposal':proposal, 'proposal_sha256': fingerprint(proposal),
                             'required_source_version':self.cfg.expected_source_version},
                platform_headers=platform_headers))
            retained['guardrail'] = guarded
            verdict = guarded['value']
            if self.cfg.fault_mode == 'missing-verdict':
                verdict = None
            elif self.cfg.fault_mode == 'wrong-version':
                verdict = {**verdict, 'source_version': 'injected-stale-version'}
            valid = (isinstance(verdict, dict) and verdict.get('ran') is True and verdict.get('passed') is True
                     and verdict.get('profile') == 'core' and verdict.get('policy_id') == POLICY_ID
                     and verdict.get('source_version') == self.cfg.expected_source_version
                     and verdict.get('proposal_sha256') == fingerprint(proposal)
                     and bool(verdict.get('sdk_session_id')) and bool(verdict.get('tool_call_id')))
            if (valid and proposal is not None and signals is not None
                    and 'pre_guardrail_error_type' not in retained):
                status, answer = 'Ready for review', summary(proposal, signals)
        except Exception as error:
            retained['guardrail_error_type'] = type(error).__name__
        record = {'status':status, 'profile':'core', 'proposal':proposal, 'operational_signals':signals,
                  'guardrail':verdict, 'trace':trace.export(), 'specialist_evidence':retained}
        # Withhold positive output if durable evidence cannot be written.
        try:
            receipt = await self.evidence.save(trace.run_id, record)
        except Exception:
            return {'status':'Needs review', 'run_id':trace.run_id,
                    'summary':'Decision withheld: the evidence store is unavailable.', 'live_verified':False}
        return {'status':status, 'run_id':trace.run_id, 'summary':answer, 'evidence':receipt,
                'live_verified':self.mode == 'cloud' and status == 'Ready for review',
                'provisional':True, 'final_procurement_approval':False}
