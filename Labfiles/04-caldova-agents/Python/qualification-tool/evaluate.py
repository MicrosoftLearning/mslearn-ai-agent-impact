"""Score exported real agent results against the deterministic lab rubric.

This does not call Foundry, run LLM judges, or fabricate agent traces.
"""

import argparse
import json
from pathlib import Path

from capacity_tool import DATA

AGENT_NAMES = {
    "Caldova Procurement Desk", "Capacity Decision Orchestrator",
    "Current Capacity", "CMO Analysis", "COO Recommendation", "Compliance Guardrail",
}


def text_list(value: object, nonempty: bool = False) -> bool:
    return (isinstance(value, list) and (bool(value) or not nonempty)
            and all(isinstance(item, str) and bool(item.strip()) for item in value))


def score(case: dict, result: dict, registry: list[dict]) -> dict[str, bool]:
    expected = case["expected"]
    claims = result.get("claims")
    evidence = set()
    claims_valid = isinstance(claims, list) and bool(claims)
    if claims_valid:
        for claim in claims:
            valid = (isinstance(claim, dict) and isinstance(claim.get("text"), str)
                     and bool(claim["text"].strip()) and text_list(claim.get("evidence_ids"), True))
            if valid:
                evidence.update(claim["evidence_ids"])
            else:
                claims_valid = False
    trace = result.get("trace", {})
    guardrail = result.get("guardrail", {})
    if not isinstance(trace, dict):
        trace = {}
    if not isinstance(guardrail, dict):
        guardrail = {}
    agents = trace.get("agent_ids")
    valid_registry = all(isinstance(a, dict) for a in registry)
    by_id = {a.get("agent_id"): a for a in registry} if valid_registry else {}
    registry_names = {a.get("name") for a in registry if a.get("agent_id") and a.get("owner")} if valid_registry else set()
    governance = (AGENT_NAMES.issubset(registry_names) and text_list(agents, True)
                  and trace.get("blocked_agent_called") is False
                  and isinstance(trace.get("run_id"), str) and bool(trace["run_id"].strip()))
    if governance:
        governance = all(i in by_id and bool(by_id[i].get("owner"))
                         and by_id[i].get("blocked") is False for i in agents)
    conflict = expected["status"] == "Needs review"
    def exact_units(field: str) -> bool:
        actual = result.get(field)
        target = expected[field]
        return field in result and ((actual is None and target is None)
                                    or (type(actual) is int and actual == target))
    return {
        "capacity_position": exact_units("internal_units") and exact_units("remaining_units"),
        "cmo_qualification": (text_list(result.get("eligible_cmo_ids"))
                              and sorted(result["eligible_cmo_ids"]) == sorted(expected["eligible_cmo_ids"])),
        "conflicting_data": result.get("status") == expected["status"] and text_list(result.get("gaps"), conflict),
        "decision_separation": (text_list(result.get("facts"), True) and text_list(result.get("assumptions"))
                                and "eligible_cmo_ids" in result and "internal_units" in result),
        "evidence": bool(claims_valid) and set(expected["evidence_ids"]).issubset(evidence),
        "compliance": (guardrail.get("ran") is True and guardrail.get("policy_id") == "POL-01"
                       and guardrail.get("passed") is (not conflict)
                       and trace.get("guardrail_before_final") is True),
        "next_action": isinstance(result.get("next_action"), str) and bool(result["next_action"].strip()),
        "governance": bool(governance),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    cases = [json.loads(line) for line in (DATA / "evaluation-cases.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    results = [json.loads(line) for line in args.results.read_text(encoding="utf-8").splitlines() if line.strip()]
    registry = json.loads(args.registry.read_text(encoding="utf-8"))
    if not isinstance(registry, list) or not all(isinstance(row, dict) for row in registry):
        raise ValueError("Registry export must be a JSON array of agent records")
    ids = [result["case_id"] for result in results]
    if len(ids) != len(set(ids)) or set(ids) != {case["case_id"] for case in cases}:
        raise ValueError("Results must contain exactly one real run per evaluation case")
    registry_ids = [row["agent_id"] for row in registry]
    if len(registry_ids) != len(set(registry_ids)):
        raise ValueError("Normalize duplicate registry lifecycle rows to unique runtime identities")
    indexed = {result["case_id"]: result for result in results}
    report = [{"case_id": case["case_id"], "criteria": score(case, indexed[case["case_id"]], registry)} for case in cases]
    passed = all(all(row["criteria"].values()) for row in report)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"passed": passed, "cases": report}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"passed": passed, "cases": report}, indent=2))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
