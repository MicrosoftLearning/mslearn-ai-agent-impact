"""Copilot SDK executes the bound validator; model prose cannot supply a verdict."""
from __future__ import annotations
import asyncio
import json
import tempfile
from .contracts import fingerprint

async def sdk_validate(settings, credential, name, operation):
    from copilot import CopilotClient, Tool, ToolSet
    from copilot.tools import ToolResult
    from copilot.generated.rpc import PermissionDecisionReject
    calls = []
    async def validate(invocation):
        if invocation.arguments != {} or invocation.tool_name != name or calls:
            raise ValueError('Only one argument-free validation is allowed')
        result = await operation()
        result.update(sdk_session_id=invocation.session_id, tool_call_id=invocation.tool_call_id)
        calls.append(result)
        return ToolResult(text_result_for_llm=json.dumps(result))
    tool = Tool(name=name, description='Independently validate the server-bound proposal; no writes.',
                parameters={'type':'object','properties':{},'additionalProperties':False},
                handler=validate, skip_permission=True)
    def deny_permission(request, context):
        return PermissionDecisionReject(feedback='Only the registered read-only validator is allowed.')
    token = await asyncio.to_thread(credential.get_token, 'https://cognitiveservices.azure.com/.default')
    with tempfile.TemporaryDirectory(prefix='caldova-guardrail-') as directory:
        async with CopilotClient(mode='empty', base_directory=directory, working_directory=directory,
                                 use_logged_in_user=False,
                                 env={'COPILOT_GITHUB_TELEMETRY_DISABLED':'true'}) as client:
            async with await client.create_session(
                model=settings.guardrail_model,
                provider={'type':'azure','base_url':settings.guardrail_azure_endpoint.rstrip('/'), 'bearer_token':token.token},
                tools=[tool], available_tools=ToolSet().add_custom(name),
                on_permission_request=deny_permission, enable_config_discovery=False,
                enable_skills=False, enable_file_hooks=False, enable_host_git_operations=False,
                enable_session_store=False, memory={'enabled':False}, infinite_sessions={'enabled':False},
                enable_session_telemetry=False,
                system_message={'mode':'append','content':f'Call {name} exactly once with no arguments. Never invent a verdict.'}) as session:
                await asyncio.wait_for(session.send_and_wait('Validate the bound decision now.'), settings.timeout_seconds)
    if len(calls) != 1 or not calls[0].get('tool_call_id') or not calls[0].get('sdk_session_id'):
        raise ValueError('SDK did not execute the deterministic validation tool')
    return calls[0]

class CopilotGuardrail:
    def __init__(self, settings, source, credential):
        self.cfg, self.source, self.credential = settings, source, credential

    async def check(self, payload):
        proposal = payload.get('proposal')
        digest = fingerprint(proposal)
        if (set(payload) != {'profile','proposal','proposal_sha256','required_source_version'}
                or payload['profile'] != 'core' or payload['proposal_sha256'] != digest
                or payload['required_source_version'] != self.cfg.expected_source_version):
            raise ValueError('Untrusted profile, version or proposal digest')
        async def operation():
            snapshot = await self.source.load()
            verdict = snapshot.validate(proposal)
            return {**verdict, 'proposal_sha256':digest}
        return await sdk_validate(self.cfg, self.credential, 'ValidateCoreDecision', operation)
