"""Deterministic compliance tool for a provider-supplied hosted agent.

This script is not the GitHub Copilot SDK harness or regulatory validation.
"""

import argparse
import json
from datetime import date
from pathlib import Path

from capacity_tool import assess, load_scenario, operational_issue
from policy import qualification_issue


def check(proposal: dict, scenario: dict) -> dict:
    issues = []
    expected = assess(scenario)
    for field in ("case_id", "internal_units", "remaining_units"):
        if proposal.get(field) != expected[field]:
            issues.append(f"{field} does not match the source records")
    if scenario["evidence_conflict"]:
        issues.append("Unresolved capacity-definition conflict")
    candidate_ids = proposal.get("candidate_ids")
    if not isinstance(candidate_ids, list) or not all(isinstance(i, str) for i in candidate_ids):
        issues.append("candidate_ids must be an explicit list of supplier IDs")
        candidate_ids = []
    records = {c["id"]: c for c in scenario["cmos"]}
    if len(candidate_ids) != len(set(candidate_ids)):
        issues.append("Duplicate supplier IDs")
    remaining = expected["remaining_units"]
    if remaining is not None and remaining > 0 and not candidate_ids:
        issues.append("No supplier evidence for the remaining gap")
    if remaining == 0 and candidate_ids:
        issues.append("External supply proposed despite sufficient internal capacity")
    for cmo_id in candidate_ids:
        cmo = records.get(cmo_id)
        if cmo is None:
            issues.append(f"Unknown CMO: {cmo_id}")
            continue
        issue = qualification_issue(cmo, date.fromisoformat(scenario["launch_date"]))
        if issue:
            issues.append(f"{cmo_id}: {issue}")
        if remaining is not None:
            issue = operational_issue(cmo, scenario, remaining)
            if issue:
                issues.append(f"{cmo_id}: {issue}")
    return {"case_id": scenario["scenario_id"], "passed": not issues,
            "policy_id": "POL-01", "decision_as_of": scenario["as_of"],
            "checked_candidate_ids": candidate_ids, "issues": issues}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proposal", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    proposal = json.loads(args.proposal.read_text(encoding="utf-8"))
    result = check(proposal, load_scenario(proposal["case_id"]))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
