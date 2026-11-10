"""Production entry points. Hosted ingress must remain private behind Foundry."""
from __future__ import annotations
import asyncio
import json
import os
import uuid
from .contracts import Settings, DecisionRequest, strict_json
from .adapters import BlobEvidence, FabricSnapshotSource, EventhouseSource, FoundryTeam
from .auth import hosted_caller, activity_caller, AccessDenied, EntraAuth


def settings():
    cfg = Settings.model_validate(strict_json(os.environ['CALDOVA_CONFIG']))
    cfg.check_service()
    return cfg


def credential(cfg):
    # No developer CLI credentials or API keys in the hosted container.
    from azure.identity import DefaultAzureCredential
    return DefaultAzureCredential(managed_identity_client_id=cfg.managed_identity_client_id or None,
        exclude_cli_credential=True, exclude_powershell_credential=True,
        exclude_developer_cli_credential=True, exclude_shared_token_cache_credential=True,
        exclude_visual_studio_code_credential=True, exclude_interactive_browser_credential=True,
        exclude_broker_credential=True)


def make_handler(cfg, cred):
    evidence = BlobEvidence(cfg, cred)
    if cfg.service == 'orchestrator':
        from .orchestrator import Orchestrator
        service = Orchestrator(cfg, FabricSnapshotSource(cfg, cred), EventhouseSource(cfg, cred), FoundryTeam(cfg, cred), evidence)
        async def handle(text, caller, headers):
            # Activity uses a natural-language question; Responses accepts the typed JSON contract.
            request = DecisionRequest.model_validate(strict_json(text)) if text.lstrip().startswith('{') else DecisionRequest(question=text)
            return await service.run(request, caller, platform_headers=headers)
    elif cfg.service == 'guardrail':
        from .guardrail import CopilotGuardrail
        service = CopilotGuardrail(cfg, FabricSnapshotSource(cfg, cred), cred)
        async def handle(text, caller, headers):
            result = await service.check(strict_json(text))
            receipt = await evidence.save(str(uuid.uuid4()), {'verdict':result,'caller':caller,'revision':cfg.revision})
            return {**result,'evidence':receipt}
    elif cfg.service == 'fixture':
        from .fixture import FixtureRuntime, FixtureRequest
        service = FixtureRuntime(cfg, FoundryTeam(cfg, cred), evidence, cred)
        async def handle(text, caller, headers):
            return await service.run(FixtureRequest.model_validate(strict_json(text)), caller, platform_headers=headers)
    else:
        raise ValueError('Use the authenticated action API for procurement')
    return handle


def run_hosted(cfg, cred):
    from azure.ai.agentserver.responses import ResponsesAgentServerHost, ResponsesServerOptions, TextResponse
    handler = make_handler(cfg, cred)
    # Cooperative mixins expose both native protocols without bypassing M365 authentication.
    if cfg.service == 'orchestrator':
        from azure.ai.agentserver.activity import ActivityAgentServerHost
        class Host(ResponsesAgentServerHost, ActivityAgentServerHost):
            pass
        host = Host(options=ResponsesServerOptions(default_fetch_history_count=1))
        @host.agent_app.activity('message')
        async def activity(turn, state):
            # Only the authenticated Teams AAD object id is used, never display name/from.id.
            activity = turn.activity
            # The channel SDK authenticates the activity. Foundry's opaque call id is
            # needed for delegated ontology access; absent context must fail closed.
            from azure.ai.agentserver.core import get_request_context
            platform = get_request_context()
            try:
                oid, headers = activity_caller(activity, platform, cfg)
            except AccessDenied:
                await turn.send_activity('Access denied: authenticated delegated caller context is required.')
                return
            result = await handler(activity.text or '', oid, headers)
            await turn.send_activity(json.dumps(result))
    else:
        host = ResponsesAgentServerHost(options=ResponsesServerOptions(default_fetch_history_count=1))
    @host.response_handler
    async def response(request, context, cancel: asyncio.Event):
        try:
            caller, headers = hosted_caller(context, cfg)
            result = await handler(await context.get_input_text() or '', caller, headers)
        except AccessDenied:
            result = {'status':'Denied'}
        except Exception as error:
            result = {'status':'Needs review','error_type':type(error).__name__, 'summary':'Required runtime evidence failed.'}
        # Exactly one final output. No model draft or raw trace streams to the channel.
        return TextResponse(context, request, text=json.dumps(result))
    host.run()


def main():
    if os.environ.get('CALDOVA_BOOTSTRAP') == '1':
        # An inert hosted version creates the platform identity before any grants.
        # It has no source clients, SDK tools, configuration or business operation.
        from azure.ai.agentserver.responses import ResponsesAgentServerHost, TextResponse
        host = ResponsesAgentServerHost()
        @host.response_handler
        async def initialize(request, context, cancel):
            return TextResponse(context, request, text='{"status":"Not configured"}')
        host.run()
        return
    cfg = settings()
    cred = credential(cfg)
    if cfg.service == 'procurement':
        import uvicorn
        from .procurement import GraphLists, create_app
        uvicorn.run(create_app(cfg, GraphLists(cfg, cred), BlobEvidence(cfg, cred), EntraAuth(cfg)), host='0.0.0.0', port=8088)
    else:
        run_hosted(cfg, cred)


if __name__ == '__main__':
    main()
