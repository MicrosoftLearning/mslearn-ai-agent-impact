"""Runtime-owned evidence; model-provided traces are never accepted."""
from __future__ import annotations

from datetime import datetime, timezone
import time
from typing import Any
from uuid import uuid4


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class RunTrace:
    def __init__(self, *, revision: str, identity: str, caller: str, profile: str, mode: str = 'cloud'):
        self.run_id = str(uuid4())
        self.started = utc_now()
        self.revision, self.identity, self.caller, self.profile = revision, identity, caller, profile
        self.mode = mode
        self.steps: list[dict[str, Any]] = []

    async def call(self, name, operation):
        step = {'order': len(self.steps)+1, 'name': name, 'started_utc': utc_now(), 'status': 'running'}
        self.steps.append(step)
        start = time.monotonic()
        try:
            result = await operation()
            step['status'] = 'succeeded'
            return result
        except Exception as error:
            # Error bodies can contain source data, URLs or credentials. Export only the class.
            step.update(status='failed', error_type=type(error).__name__)
            raise
        finally:
            step.update(duration_ms=round((time.monotonic()-start)*1000), finished_utc=utc_now())

    def export(self):
        return {'run_id': self.run_id, 'execution_mode': self.mode, 'started_utc': self.started,
                'revision': self.revision, 'runtime_identity_oid': self.identity, 'caller_oid': self.caller,
                'profile': self.profile, 'steps': self.steps}
