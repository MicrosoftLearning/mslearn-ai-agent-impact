"""These two tests deliberately fail until the learner repairs the filter."""

import unittest
from datetime import date

from qualification import qualification_issue


class QualificationRegressionTests(unittest.TestCase):
    def test_expired_qualification_is_rejected(self):
        record = {"qualification_status": "Approved", "qualification_expiry": "2026-09-30"}
        self.assertIsNotNone(qualification_issue(record, date(2026, 11, 30)))

    def test_missing_qualification_expiry_is_rejected(self):
        record = {"qualification_status": "Approved", "qualification_expiry": None}
        self.assertIsNotNone(qualification_issue(record, date(2026, 11, 30)))


if __name__ == "__main__":
    unittest.main()
