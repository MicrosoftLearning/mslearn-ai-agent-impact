"""Local deterministic tool fixture, not an agent or a hosted runtime."""

import argparse
import json
from copy import deepcopy
from datetime import date, timedelta
from pathlib import Path

from qualification import qualification_issue

DATA = Path(__file__).resolve().parents[2] / "data"
CASES = ("external-support", "internal-sufficient", "conflicting-evidence")


def load_scenario(case_id: str) -> dict:
    if case_id not in CASES:
        raise ValueError(f"Unknown scenario: {case_id}")
    data = json.loads((DATA / "scenario.json").read_text(encoding="utf-8"))
    data = deepcopy(data)
    data["scenario_id"] = case_id
    if case_id == "internal-sufficient":
        for plant in data["plants"]:
            plant["available_units"] = 2500
    elif case_id == "conflicting-evidence":
        data["evidence_conflict"] = True
    return data


def operational_issue(cmo: dict, scenario: dict, remaining: int) -> str | None:
    if cmo["region"] != scenario["required_region"]:
        return "Manufacturing region is not UK"
    if not cmo.get("audit_id"):
        return "Audit reference is missing"
    if cmo["capacity_units"] < remaining:
        return "Capacity does not cover the remaining gap"
    ready = date.fromisoformat(scenario["as_of"]) + timedelta(days=cmo["transfer_days"])
    if ready > date.fromisoformat(scenario["launch_date"]):
        return "Transfer finishes after launch"
    return None


def assess(scenario: dict) -> dict:
    if scenario["evidence_conflict"]:
        return {"case_id": scenario["scenario_id"], "internal_units": None,
                "remaining_units": None, "candidate_ids": [],
                "issues": ["CAP-01 conflicts with LEG-01; obtain an authoritative definition"]}
    gap_numerator = scenario["baseline_units"] * scenario["gap_percent"]
    if gap_numerator % 100:
        raise ValueError("Fixture requires a whole-unit gap")
    required = gap_numerator // 100
    for plant in scenario["plants"]:
        if plant["region"] != scenario["required_region"] or not plant.get("audit_id"):
            raise ValueError(f"Plant evidence failed policy: {plant['id']}")
    internal = sum(p["available_units"] for p in scenario["plants"]
                   if p["batch_status"] == "Released")
    remaining = max(0, required - internal)
    candidates = []
    issues = []
    if remaining:
        launch = date.fromisoformat(scenario["launch_date"])
        for cmo in scenario["cmos"]:
            issue = qualification_issue(cmo, launch) or operational_issue(cmo, scenario, remaining)
            if issue:
                issues.append(f"{cmo['id']}: {issue}")
            else:
                candidates.append(cmo)
    candidates.sort(key=lambda c: (c["cost_per_unit_gbp"], c["id"]))
    return {"case_id": scenario["scenario_id"], "internal_units": internal,
            "remaining_units": remaining, "candidate_ids": [c["id"] for c in candidates],
            "issues": issues}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=CASES, default=CASES[0])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = assess(load_scenario(args.case))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
