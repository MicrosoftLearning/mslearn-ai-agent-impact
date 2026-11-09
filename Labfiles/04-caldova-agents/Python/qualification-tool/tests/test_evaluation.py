import json
import unittest
from copy import deepcopy

from capacity_tool import DATA
from evaluate import AGENT_NAMES, score


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        self.cases = [json.loads(line) for line in (DATA / "evaluation-cases.jsonl").read_text(encoding="utf-8").splitlines()]
        self.registry = [{"agent_id": f"test-{i}", "name": name, "owner": "test-owner", "blocked": False}
                         for i, name in enumerate(sorted(AGENT_NAMES))]

    def fixture(self, case):
        expected = deepcopy(case["expected"])
        return {"case_id": case["case_id"], **expected,
                "facts": ["Synthetic unit-test fact"], "assumptions": [],
                "gaps": ["Synthetic conflict"] if expected["status"] == "Needs review" else [],
                "next_action": "Review source records",
                "claims": [{"text": "Synthetic claim", "evidence_ids": expected["evidence_ids"]}],
                "guardrail": {"ran": True, "passed": expected["status"] != "Needs review", "policy_id": "POL-01"},
                "trace": {"run_id": "unit-test-only", "agent_ids": [a["agent_id"] for a in self.registry],
                          "guardrail_before_final": True, "blocked_agent_called": False}}

    def test_expected_contract_all_cases(self):
        for case in self.cases:
            with self.subTest(case=case["case_id"]):
                self.assertTrue(all(score(case, self.fixture(case), self.registry).values()))

    def test_empty_output_fails_all_criteria(self):
        self.assertFalse(any(score(self.cases[0], {}, self.registry).values()))

    def test_missing_null_fields_fail_capacity_check(self):
        result = self.fixture(self.cases[2])
        del result["internal_units"]
        self.assertFalse(score(self.cases[2], result, self.registry)["capacity_position"])

    def test_bool_is_not_a_unit_count(self):
        result = self.fixture(self.cases[1])
        result["remaining_units"] = False
        self.assertFalse(score(self.cases[1], result, self.registry)["capacity_position"])

    def test_unsupported_cmo_fails(self):
        result = self.fixture(self.cases[0])
        result["eligible_cmo_ids"] = ["CMO-02"]
        self.assertFalse(score(self.cases[0], result, self.registry)["cmo_qualification"])

    def test_no_citations_fail(self):
        result = self.fixture(self.cases[0])
        result["claims"] = []
        self.assertFalse(score(self.cases[0], result, self.registry)["evidence"])

    def test_blocked_or_unknown_agent_fails(self):
        for agent_id in ("unregistered", self.registry[0]["agent_id"]):
            with self.subTest(agent_id=agent_id):
                result = self.fixture(self.cases[0])
                registry = deepcopy(self.registry)
                registry[0]["blocked"] = True
                result["trace"]["agent_ids"] = [agent_id]
                self.assertFalse(score(self.cases[0], result, registry)["governance"])

    def test_missing_guardrail_fails(self):
        result = self.fixture(self.cases[0])
        result["guardrail"] = None
        self.assertFalse(score(self.cases[0], result, self.registry)["compliance"])


if __name__ == "__main__":
    unittest.main()
