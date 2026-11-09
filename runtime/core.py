"""Independent core-profile assessment/validation, not a hosted-agent substitute.

The service owner supplies data_root; a model must never select paths, profiles,
policies, or source versions. Local outputs explicitly do not prove live access.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
from pathlib import Path
from typing import Any

POLICY_ID = "CORE-LP001-v1"
GAPS = ["Qualification-expiry evidence through launch is missing.",
        "Complete transfer-approval evidence is missing."]
NEXT_ACTION = "Quality and procurement must validate the missing evidence before an award."
TABLES = {
    "launch_program": ("launch_program.csv", "LaunchProgramID"),
    "product": ("products.csv", "ProductID"),
    "plant": ("plants.csv", "PlantID"),
    "capacity_plan": ("manufacturing_capacity_plan.csv", "CapacityPlanID"),
    "batch": ("manufacturing_batch_schedule.csv", "BatchID"),
    "supplier": ("procurement_cmo_evaluation.csv", "CMOID"),
}

class SourceError(ValueError):
    """The source is incomplete or inconsistent; do not release a decision."""

def integer(value: str, field: str, minimum: int | None = None) -> int:
    if not isinstance(value, str) or not re.fullmatch(r"-?\d+", value.strip()):
        raise SourceError(f"Invalid integer in {field}")
    result = int(value)
    if minimum is not None and result < minimum:
        raise SourceError(f"Out-of-range integer in {field}")
    return result

class CoreSnapshot:
    """Read one frozen six-file snapshot; never mix it with the repair fixture."""
    def __init__(self, data_root: Path):
        self.tables: dict[str, list[dict[str, str]]] = {}
        digest = hashlib.sha256()
        for name, (filename, primary_key) in TABLES.items():
            path = data_root / filename
            if not path.is_file() or path.is_symlink():
                raise SourceError(f"Missing or unsafe source file: {filename}")
            raw = path.read_bytes()
            digest.update(filename.encode() + b"\0" + len(raw).to_bytes(8, "big") + raw)
            reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
            if not reader.fieldnames or primary_key not in reader.fieldnames:
                raise SourceError(f"Missing primary key in {filename}")
            if len(reader.fieldnames) != len(set(reader.fieldnames)):
                raise SourceError(f"Duplicate columns in {filename}")
            rows = list(reader)
            keys = [row.get(primary_key, "") for row in rows]
            if not rows or any(not key for key in keys) or len(keys) != len(set(keys)):
                raise SourceError(f"Empty or duplicate keys in {filename}")
            if any(None in row or any(value is None for value in row.values()) for row in rows):
                raise SourceError(f"Malformed row in {filename}")
            self.tables[name] = rows
        self.source_version = "sha256:" + digest.hexdigest()
        self._validate_relationships()

    @classmethod
    def from_records(cls, tables: dict[str, list[dict[str, Any]]]) -> 'CoreSnapshot':
        """Freeze adapter-returned records; no file/CSV fallback on the live path."""
        if set(tables) != set(TABLES):
            raise SourceError('A live snapshot must contain exactly the six core tables')
        snapshot = cls.__new__(cls)
        snapshot.tables = {}
        for table, (_, key) in TABLES.items():
            rows = tables[table]
            if not rows or not all(isinstance(row, dict) for row in rows):
                raise SourceError(f'Missing records: {table}')
            converted = []
            for row in rows:
                if any(isinstance(v, (bool, dict, list)) for v in row.values()):
                    raise SourceError(f'Unsupported source value: {table}')
                converted.append({k: '' if v is None else str(v) for k, v in row.items()})
            keys = [row.get(key, '') for row in converted]
            if any(not k for k in keys) or len(keys) != len(set(keys)):
                raise SourceError(f'Empty or duplicate keys: {table}')
            snapshot.tables[table] = sorted(converted, key=lambda row: row[key])
        raw = json.dumps(snapshot.tables, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()
        snapshot.source_version = 'records-sha256:' + hashlib.sha256(raw).hexdigest()
        snapshot._validate_relationships()
        return snapshot

    def _validate_relationships(self) -> None:
        relationships = [
            ("launch_program", "ProductID", "product", "ProductID", False),
            ("launch_program", "BindingConstraintPlantID", "plant", "PlantID", True),
            ("capacity_plan", "LaunchProgramID", "launch_program", "LaunchProgramID", False),
            ("capacity_plan", "PlantID", "plant", "PlantID", False),
            ("batch", "LaunchProgramID", "launch_program", "LaunchProgramID", False),
            ("batch", "PlantID", "plant", "PlantID", False),
            ("batch", "ProductID", "product", "ProductID", False),
            ("supplier", "LaunchProgramID", "launch_program", "LaunchProgramID", False),
            ("supplier", "ProductID", "product", "ProductID", False),
        ]
        for child, field, parent, key, nullable in relationships:
            allowed = {row[key] for row in self.tables[parent]}
            for row in self.tables[child]:
                value = row.get(field)
                if nullable and value is not None and not value.strip():
                    continue
                if value not in allowed:
                    raise SourceError(f"Invalid relationship: {child}.{field}")

    def assess(self, program_id: str = "LP001") -> dict[str, Any]:
        if program_id != "LP001":
            raise SourceError("Only the server-allowlisted LP001 core profile is supported")
        matches = [r for r in self.tables["launch_program"] if r["LaunchProgramID"] == program_id]
        if len(matches) != 1:
            raise SourceError("LP001 must occur exactly once")
        launch = matches[0]
        try:
            target = integer(launch["TargetLaunchVolume"], "TargetLaunchVolume", 0)
            qualified = integer(launch["QualifiedCapacity"], "QualifiedCapacity", 0)
            gap = integer(launch["CapacityGapUnits"], "CapacityGapUnits", 0)
            if target - qualified != gap:
                raise SourceError("Authoritative launch gap conflicts with target minus qualified capacity")
            candidates = []
            for row in self.tables["supplier"]:
                if row["LaunchProgramID"] != program_id:
                    continue
                if row["ProductID"] != launch["ProductID"]:
                    raise SourceError("Supplier product conflicts with its launch program")
                capacity = integer(row["QualifiedAvailableCapacityUnits"], "supplier capacity", 0)
                findings = integer(row["OpenCriticalFindings"], "critical findings", 0)
                score = integer(row["WeightedScore"], "weighted score", 0)
                lead = integer(row["LeadTimeWeeks"], "lead time", 0)
                if (gap > 0 and capacity >= gap and row["GMPCertStatus"] == "Currently valid"
                        and findings == 0 and row["FastTrackEligible"] == "Yes"):
                    candidates.append((row["CMOID"], score, lead))
            candidates.sort(key=lambda r: (-r[1], r[2], r[0]))
            delayed = sum(r["LaunchProgramID"] == program_id and r["BatchStatus"] == "Delayed"
                          for r in self.tables["batch"])
            values = {"target_units": target, "qualified_units": qualified, "gap_units": gap,
                      "binding_plant_id": launch["BindingConstraintPlantID"],
                      "delayed_batch_count": delayed, "eligible_cmo_ids": [r[0] for r in candidates]}
            references = {
                "target_units": [f"launch_program:{program_id}"],
                "qualified_units": [f"launch_program:{program_id}"],
                "gap_units": [f"launch_program:{program_id}"],
                "binding_plant_id": [f"launch_program:{program_id}", f"plant:{values['binding_plant_id']}"],
                "delayed_batch_count": [f"batch:{r['BatchID']}" for r in self.tables["batch"]
                                        if r["LaunchProgramID"] == program_id and r["BatchStatus"] == "Delayed"],
                "eligible_cmo_ids": [f"supplier:{r[0]}" for r in candidates],
            }
        except KeyError as exc:
            raise SourceError(f"Required source column missing: {exc.args[0]}") from exc
        return {
            "profile": "core", "launch_program_id": program_id,
            "source_version": self.source_version, "policy_id": POLICY_ID,
            **values, "provisional": True, "gaps": GAPS.copy(),
            "next_action": NEXT_ACTION,
            "claims": [{"field": field, "value": value, "evidence_refs": references[field]}
                       for field, value in values.items()],
            "operational_signals": [], "operational_signal_status": "Not evaluated",
        }

    def validate(self, proposal: Any) -> dict[str, Any]:
        """Recompute from this trusted snapshot, never from proposal evidence alone."""
        expected = self.assess()
        reasons = []
        if not isinstance(proposal, dict):
            reasons.append("Proposal must be an object")
        else:
            # Strict type equality rejects booleans masquerading as integer quantities.
            for key, value in expected.items():
                actual = proposal.get(key)
                if type(actual) is not type(value) or actual != value:
                    reasons.append(f"Invalid or missing {key}")
            # Only contract fields may reach the deterministic formatter.
            if set(proposal) != set(expected):
                reasons.append("Unexpected proposal fields")
        return {"ran": True, "passed": not reasons, "policy_id": POLICY_ID,
                "profile": "core", "source_version": self.source_version, "reasons": reasons}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["assess", "validate"])
    parser.add_argument("--data-root", type=Path, default=Path(__file__).resolve().parents[1] /
                        "Allfiles/L300-TW-Data/data/core")
    parser.add_argument("--proposal", type=Path)
    args = parser.parse_args()
    try:
        snapshot = CoreSnapshot(args.data_root)
        if args.command == "validate":
            if args.proposal is None:
                parser.error("validate requires --proposal")
            def reject_constant(value: str) -> None:
                raise ValueError(f"Invalid JSON number: {value}")
            proposal = json.loads(args.proposal.read_text(encoding="utf-8"), parse_constant=reject_constant)
            result = snapshot.validate(proposal)
        else:
            result = snapshot.assess()
        print(json.dumps({"execution_mode": "local-offline", "live_verified": False,
                          "result": result}, indent=2))
        return 0 if result.get("passed", True) else 1
    except (SourceError, OSError, ValueError) as exc:
        print(json.dumps({"execution_mode": "local-offline", "live_verified": False,
                          "status": "Needs review", "error": str(exc)}))
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
