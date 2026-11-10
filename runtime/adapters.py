"""Authenticated live adapters. None falls back to repository CSVs or model memory."""
from __future__ import annotations

import asyncio
import json
import math
import re
import struct
from datetime import timedelta
from typing import Any

from .contracts import Settings, fingerprint, strict_json
from .core import CoreSnapshot, SourceError, TABLES


class FabricSnapshotSource:
    def __init__(self, settings: Settings, credential):
        self.settings, self.credential = settings, credential

    async def load(self, *, enforce_pin: bool = True) -> CoreSnapshot:
        def read():
            import pyodbc
            cfg = self.settings
            token = self.credential.get_token('https://database.windows.net/.default').token.encode('utf-16-le')
            auth = struct.pack('<I', len(token)) + token
            database = '{' + cfg.sql_database.replace('}', '}}') + '}'
            connection = pyodbc.connect(
                f'Driver={{ODBC Driver 18 for SQL Server}};Server={cfg.sql_server};Database={database};'
                'Encrypt=yes;TrustServerCertificate=no;ApplicationIntent=ReadOnly;',
                attrs_before={1256: auth}, timeout=30, autocommit=True)
            try:
                records = {}
                cursor = connection.cursor()
                cursor.timeout = 30
                for table in TABLES:
                    cursor.execute(f'SELECT * FROM [{cfg.sql_schema}].[{table}]')
                    columns = [column[0] for column in cursor.description]
                    rows = cursor.fetchmany(10001)
                    if len(rows) > 10000:
                        raise SourceError('Source exceeds this bounded training adapter')
                    records[table] = [dict(zip(columns, row)) for row in rows]
                snapshot = CoreSnapshot.from_records(records)
                if enforce_pin and snapshot.source_version != cfg.expected_source_version:
                    raise SourceError('Curated source changed; checkpoint review required')
                return snapshot
            finally:
                connection.close()
        return await asyncio.to_thread(read)


def verify_events(events: list[dict[str, Any]], replay: str) -> dict[str, Any]:
    if not re.fullmatch(r'[0-9a-f]{8}', replay):
        raise SourceError('Invalid trusted replay ID')
    by_id = {}
    for event in events:
        event_id = event.get('EventID', '')
        if not re.fullmatch(fr'SIM-{replay}-\d{{3}}', event_id) or event.get('SourceSystem') != 'CaldovaLabSimulator':
            raise SourceError('Cross-cohort or nonsimulation event')
        if event.get('LaunchProgramID') != 'LP001' or event.get('ProductID') != 'P101':
            raise SourceError('Wrong event business keys')
        if not event.get('EventTime'):
            raise SourceError('Missing event timestamp')
        previous = by_id.get(event_id)
        if previous and fingerprint(previous) != fingerprint(event):
            raise SourceError('Conflicting duplicate event identity')
        by_id[event_id] = event
    if set(by_id) != {f'SIM-{replay}-{i:03d}' for i in range(1, 11)}:
        raise SourceError('One complete ten-event cohort is required')
    breaches = []
    for event in by_id.values():
        metric, threshold = event.get('MetricValue'), event.get('Threshold')
        if (type(metric) not in (int, float) or type(threshold) not in (int, float)
                or not math.isfinite(metric) or not math.isfinite(threshold)):
            raise SourceError('Event metric/threshold must be numeric')
        if metric > threshold:
            breaches.append(event)
    expected = {('UtilizationPercent', 'PL003', '', 112), ('UtilizationPercent', 'PL003', '', 118),
                ('OpenDeviationCount', 'PL003', '', 3), ('ProjectedLeadTimeWeeks', '', 'CMO006', 9)}
    actual = {(e['MetricName'], e.get('PlantID', ''), e.get('CMOID', ''), e['MetricValue']) for e in breaches}
    if len(breaches) != 4 or actual != expected:
        raise SourceError('The selected cohort does not match the four expected strict breaches')
    return {'replay_id': replay, 'unique_events': 10, 'source_system': 'CaldovaLabSimulator',
            'simulation': True, 'events': sorted(by_id.values(), key=lambda e: e['EventID']),
            'breaches': sorted(breaches, key=lambda e: e['EventID']),
            'conflicts': ['CMO006 simulated lead time is nine weeks; the core source remains eight weeks. Source-owner review required.']}


class EventhouseSource:
    def __init__(self, settings: Settings, credential):
        self.settings, self.credential = settings, credential

    async def load(self):
        def read():
            from azure.kusto.data import KustoClient, KustoConnectionStringBuilder, ClientRequestProperties
            cfg = self.settings
            cluster = cfg.event_cluster.rstrip('/')
            connection = KustoConnectionStringBuilder.with_azure_token_provider(
                cluster, lambda: self.credential.get_token(cluster+'/.default').token)
            properties = ClientRequestProperties()
            properties.set_option('servertimeout', timedelta(seconds=30))
            # ReplayId comes from validated, server-owned configuration, never user/model text.
            query = ("operational_events | where SourceSystem == 'CaldovaLabSimulator' "
                     f"| where EventID startswith 'SIM-{cfg.replay_id}-' | take 1001")
            with KustoClient(connection) as client:
                result = client.execute_query(cfg.event_database, query, properties)
                table = result.primary_results[0]
                columns = [c.column_name for c in table.columns]
                events = [dict(zip(columns, row)) for row in table]
            if len(events) > 1000:
                raise SourceError('Too many replay rows; investigate retries before continuing')
            for event in events:
                if event.get('EventTime') is None:
                    raise SourceError('Missing event timestamp')
                event['EventTime'] = str(event['EventTime'])
            return verify_events(events, cfg.replay_id)
        return await asyncio.to_thread(read)


class FoundryTeam:
    def __init__(self, settings: Settings, credential):
        from azure.ai.projects import AIProjectClient
        self.settings = settings
        self.project = AIProjectClient(settings.project_endpoint, credential=credential,
                                       retry_total=0, connection_timeout=15, read_timeout=settings.timeout_seconds)

    async def call(self, role: str, payload: dict, *, platform_headers=None, require_fabric=False):
        def invoke():
            ref = self.settings.agents[role]
            agent = self.project.agents.get_version(ref.name, ref.version)
            if agent.name != ref.name or str(agent.version) != ref.version:
                raise SourceError('Agent identity/version mismatch')
            if role == 'guardrail' and (agent.definition.kind != 'hosted' or agent.metadata.get('profile') != 'guardrail'):
                raise SourceError('The guardrail must be the pinned executable hosted service')
            client = self.project.get_openai_client()
            try:
                response = client.responses.create(
                    input=json.dumps(payload, allow_nan=False),
                    extra_body={'agent_reference': {'type': 'agent_reference', 'name': ref.name, 'version': ref.version}},
                    extra_headers=platform_headers or {}, timeout=self.settings.timeout_seconds)
                raw = response.model_dump(mode='json')
                if raw.get('status') != 'completed' or not raw.get('id'):
                    raise SourceError('Specialist did not complete')
                calls = [o for o in raw.get('output', []) if o.get('type') == 'mcp_call'
                         and o.get('server_label') == 'caldova-core'
                         and o.get('status') == 'completed' and not o.get('error') and o.get('output')]
                if require_fabric and not calls:
                    raise SourceError('Required Fabric IQ tool execution is absent')
                policy_calls = [o for o in raw.get('output', []) if o.get('type') == 'azure_ai_search_call'
                                and o.get('status') == 'completed' and o.get('results') and not o.get('error')]
                if self.settings.service == 'orchestrator' and role == 'cmo' and not policy_calls:
                    raise SourceError('Required approved-policy retrieval is absent')
                value = strict_json(response.output_text)
                receipt = {'agent_id': agent.id, 'agent_name': agent.name, 'agent_version': str(agent.version),
                           'response_id': response.id, 'usage': raw.get('usage'),
                           'fabric_tool_calls': len(calls), 'policy_tool_calls': len(policy_calls)}
                return {'value': value, 'receipt': receipt, 'raw': raw}
            finally:
                client.close()
        return await asyncio.to_thread(invoke)


class BlobEvidence:
    def __init__(self, settings: Settings, credential):
        from azure.storage.blob import BlobServiceClient
        self.container = BlobServiceClient(settings.evidence_account_url, credential=credential,
                                           retry_total=0).get_container_client(settings.evidence_container)

    async def save(self, run_id: str, value: dict):
        def write():
            from azure.storage.blob import ContentSettings
            if not re.fullmatch(r'[0-9a-f-]{36}', run_id):
                raise ValueError('Invalid runtime-owned run ID')
            raw = json.dumps(value, sort_keys=True, allow_nan=False, default=str).encode()
            blob = self.container.get_blob_client(f'runs/{run_id}.json')
            blob.upload_blob(raw, overwrite=False, content_settings=ContentSettings(content_type='application/json'))
            return {'blob': f'runs/{run_id}.json', 'sha256': fingerprint(value)}
        return await asyncio.to_thread(write)
