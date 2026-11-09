"""Strict service contracts. Model text never selects a profile, identity or endpoint."""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)


class DecisionRequest(StrictModel):
    question: str = Field(min_length=1, max_length=4000)
    launch_program_id: Literal['LP001'] = 'LP001'


class FollowUpRequest(StrictModel):
    rfp_id: str = Field(pattern=r'^RFP-\d{2}$')
    request_text: str = Field(min_length=1, max_length=2000)
    client_request_id: str = Field(pattern=r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')
    confirmed: Literal[True]

    @field_validator('confirmed', mode='before')
    @classmethod
    def explicit_boolean(cls, value):
        if type(value) is not bool or value is not True:
            raise ValueError('Explicit Boolean confirmation is required')
        return value


class AgentRef(StrictModel):
    name: str = Field(pattern=r'^[A-Za-z0-9_-]{1,100}$')
    version: str = Field(pattern=r'^\d+$')


class Settings(StrictModel):
    service: Literal['orchestrator', 'guardrail', 'fixture', 'procurement']
    tenant_id: str
    revision: str = Field(min_length=7)
    runtime_identity_oid: str
    managed_identity_client_id: str = ''
    project_endpoint: str
    agents: dict[str, AgentRef] = Field(default_factory=dict)
    allowed_user_oids: list[str] = Field(min_length=1)
    api_audience: str
    allowed_client_ids: list[str] = Field(min_length=1)
    evidence_account_url: str
    evidence_container: str
    sql_server: str = ''
    sql_database: str = ''
    sql_schema: str = 'dbo'
    expected_source_version: str = ''
    event_cluster: str = ''
    event_database: str = ''
    replay_id: str = ''
    guardrail_azure_endpoint: str = ''
    guardrail_model: str = ''
    graph_site_id: str = ''
    rfp_list_id: str = ''
    followup_list_id: str = ''
    supplier_list_id: str = ''
    timeout_seconds: int = Field(default=90, ge=5, le=180)
    fault_mode: Literal['none', 'timeout', 'missing-verdict', 'wrong-version'] = 'none'
    allow_test_faults: bool = False

    @field_validator('project_endpoint')
    @classmethod
    def project_url(cls, value: str) -> str:
        parsed = urlsplit(value)
        if (parsed.scheme != 'https' or not parsed.hostname or parsed.port or parsed.username
                or not parsed.hostname.endswith('.services.ai.azure.com')
                or not re.fullmatch(r'/api/projects/[A-Za-z0-9_-]+/?', parsed.path)
                or parsed.query or parsed.fragment):
            raise ValueError('Use the actual public-cloud Foundry project endpoint')
        return value.rstrip('/')

    def check_service(self) -> None:
        for name in ('tenant_id', 'runtime_identity_oid'):
            if not re.fullmatch(r'[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}', getattr(self, name)):
                raise ValueError(f'An actual GUID is required: {name}')
        if self.fault_mode != 'none' and not self.allow_test_faults:
            raise ValueError('Fault injection requires an explicitly isolated test deployment')
        if self.service in ('orchestrator', 'guardrail'):
            if not re.fullmatch(r'[A-Za-z0-9.-]+\.datawarehouse\.fabric\.microsoft\.com', self.sql_server):
                raise ValueError('Use the actual Fabric SQL analytics endpoint host')
            if not self.sql_database or not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', self.sql_schema):
                raise ValueError('SQL database and safe schema are required')
            if not re.fullmatch(r'records-sha256:[0-9a-f]{64}', self.expected_source_version):
                raise ValueError('Pin the actual curated-table snapshot version before serving')
        if self.service == 'orchestrator':
            if set(self.agents) != {'capacity', 'cmo', 'coo', 'guardrail'}:
                raise ValueError('Pin the four actual specialist/guardrail agent versions')
            if not re.fullmatch(r'[0-9a-f]{8}', self.replay_id):
                raise ValueError('Pin the actual completed ten-event replay')
            if not self.event_database or not re.fullmatch(r'https://[A-Za-z0-9.-]+\.kusto\.fabric\.microsoft\.com/?', self.event_cluster):
                raise ValueError('Use the actual Eventhouse query URI and database')
        if self.service in ('guardrail', 'fixture'):
            if not re.fullmatch(r'https://[A-Za-z0-9-]+\.openai\.azure\.com/?', self.guardrail_azure_endpoint) or not self.guardrail_model:
                raise ValueError('An actual Azure OpenAI endpoint and deployed guardrail model are required')
        if self.service == 'fixture' and set(self.agents) != {'capacity', 'cmo', 'coo'}:
            raise ValueError('Pin three isolated fixture specialist versions')
        if self.service == 'procurement' and not all((self.graph_site_id, self.rfp_list_id, self.followup_list_id, self.supplier_list_id)):
            raise ValueError('Actual selected-site/list IDs are required')
        if not re.fullmatch(r'https://[a-z0-9]{3,24}\.blob\.core\.windows\.net', self.evidence_account_url):
            raise ValueError('Use the actual private evidence storage account URL')


def fingerprint(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def strict_json(text: str) -> Any:
    def reject(value):
        raise ValueError('Nonfinite JSON number')
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate JSON key')
            result[key] = value
        return result
    return json.loads(text, parse_constant=reject, object_pairs_hook=unique)
