import unittest
from datetime import date

from capacity_tool import assess, load_scenario
from gxp_checks import check
from policy import qualification_issue as strict_issue
from qualification import qualification_issue


class BaselineTests(unittest.TestCase):
    def test_approved_current_supplier(self):
        record = load_scenario("external-support")["cmos"][0]
        self.assertIsNone(qualification_issue(record, date(2026, 11, 30)))

    def test_unapproved_supplier(self):
        self.assertIsNotNone(qualification_issue({"qualification_status": "Pending"}, date(2026, 11, 30)))

    def test_external_capacity_math(self):
        result = assess(load_scenario("external-support"))
        self.assertEqual((result["internal_units"], result["remaining_units"]), (4500, 2500))

    def test_sufficient_capacity(self):
        data = load_scenario("internal-sufficient")
        result = assess(data)
        self.assertEqual((result["internal_units"], result["remaining_units"]), (7500, 0))
        self.assertEqual(result["candidate_ids"], [])
        self.assertTrue(check(result, data)["passed"])

    def test_conflict_never_invents_capacity(self):
        data = load_scenario("conflicting-evidence")
        result = assess(data)
        self.assertIsNone(result["internal_units"])
        self.assertFalse(check(result, data)["passed"])

    def test_guardrail_rejects_expired_proposal(self):
        data = load_scenario("external-support")
        proposal = assess(data)
        proposal["candidate_ids"] = ["CMO-02"]
        result = check(proposal, data)
        self.assertFalse(result["passed"])
        self.assertTrue(any("CMO-02" in issue for issue in result["issues"]))

    def test_guardrail_rejects_unknown_supplier(self):
        data = load_scenario("external-support")
        proposal = assess(data)
        proposal["candidate_ids"] = ["CMO-99"]
        self.assertFalse(check(proposal, data)["passed"])

    def test_guardrail_rejects_changed_capacity(self):
        data = load_scenario("external-support")
        proposal = assess(data)
        proposal["internal_units"] = 7000
        self.assertFalse(check(proposal, data)["passed"])

    def test_strict_expiry_boundaries(self):
        for expiry, valid in [("2026-11-30", True), ("2026-11-29", False),
                              ("2027-01-01", True), (None, False), ("", False),
                              ("not-a-date", False), ("20261130", False)]:
            with self.subTest(expiry=expiry):
                issue = strict_issue({"qualification_status": "Approved", "qualification_expiry": expiry}, date(2026, 11, 30))
                self.assertEqual(issue is None, valid)


if __name__ == "__main__":
    unittest.main()
