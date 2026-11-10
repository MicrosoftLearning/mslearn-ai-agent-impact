import copy
import csv
import tempfile
import unittest
from pathlib import Path
from runtime.core import CoreSnapshot, SourceError, TABLES

class CoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.rows = {
            'launch_program': [{'LaunchProgramID': 'LP001', 'ProductID': 'P101',
                'BindingConstraintPlantID': 'PL003', 'TargetLaunchVolume': '270000',
                'QualifiedCapacity': '251100', 'CapacityGapUnits': '18900'}],
            'product': [{'ProductID': 'P101'}],
            'plant': [{'PlantID': 'PL003'}],
            'capacity_plan': [{'CapacityPlanID': 'CP01', 'LaunchProgramID': 'LP001', 'PlantID': 'PL003'}],
            'batch': [{'BatchID': f'B{i}', 'LaunchProgramID': 'LP001', 'ProductID': 'P101',
                'PlantID': 'PL003', 'BatchStatus': 'Delayed'} for i in range(8)],
            'supplier': [dict(CMOID=cmo, LaunchProgramID='LP001', ProductID='P101',
                QualifiedAvailableCapacityUnits='20000', GMPCertStatus='Currently valid',
                OpenCriticalFindings='0', FastTrackEligible='Yes', WeightedScore=str(score),
                LeadTimeWeeks=str(lead)) for cmo, score, lead in
                [('CMO006', 80, 8), ('CMO002', 85, 6), ('CMO001', 90, 5)]],
        }
        self.write_rows()

    def write_rows(self):
        for table, rows in self.rows.items():
            with (self.root / TABLES[table][0]).open('w', newline='', encoding='utf-8') as stream:
                writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)

    def snapshot(self):
        return CoreSnapshot(self.root)

    def test_correct_assessment(self):
        snapshot = self.snapshot()
        proposal = snapshot.assess()
        self.assertEqual(proposal['gap_units'], 18900)
        self.assertEqual(proposal['delayed_batch_count'], 8)
        self.assertEqual(proposal['eligible_cmo_ids'], ['CMO001', 'CMO002', 'CMO006'])
        self.assertTrue(snapshot.validate(proposal)['passed'])
        self.assertTrue(proposal['provisional'])
        self.assertEqual(len(proposal['gaps']), 2)

    def test_each_contract_field_is_required(self):
        snapshot = self.snapshot()
        for field in snapshot.assess():
            with self.subTest(field=field):
                proposal = snapshot.assess()
                del proposal[field]
                self.assertFalse(snapshot.validate(proposal)['passed'])

    def test_tampered_quantities_rejected(self):
        snapshot = self.snapshot()
        for field in ['target_units', 'qualified_units', 'gap_units', 'delayed_batch_count']:
            for value in [True, 0, -1, '18900', 18900.0, None]:
                with self.subTest(field=field, value=value):
                    proposal = snapshot.assess()
                    proposal[field] = value
                    self.assertFalse(snapshot.validate(proposal)['passed'])

    def test_wrong_profile_policy_and_version_rejected(self):
        snapshot = self.snapshot()
        for field, value in [('profile', 'qualification-fixture'), ('policy_id', 'POL-01'),
                             ('source_version', 'other'), ('launch_program_id', 'LP002')]:
            proposal = snapshot.assess()
            proposal[field] = value
            self.assertFalse(snapshot.validate(proposal)['passed'])

    def test_order_unknown_and_fixture_ids_rejected(self):
        snapshot = self.snapshot()
        for ids in [['CMO002', 'CMO001', 'CMO006'], ['CMO001'], ['CMO-01'], ['unknown']]:
            proposal = snapshot.assess()
            proposal['eligible_cmo_ids'] = ids
            self.assertFalse(snapshot.validate(proposal)['passed'])

    def test_missing_and_fabricated_evidence_rejected(self):
        snapshot = self.snapshot()
        for refs in [[], ['fake:LP001']]:
            proposal = snapshot.assess()
            proposal['claims'][0]['evidence_refs'] = refs
            self.assertFalse(snapshot.validate(proposal)['passed'])

    def test_no_extra_model_claims_or_approval(self):
        snapshot = self.snapshot()
        proposal = snapshot.assess()
        proposal['approved_for_production'] = True
        self.assertFalse(snapshot.validate(proposal)['passed'])
        proposal = snapshot.assess()
        proposal['provisional'] = False
        self.assertFalse(snapshot.validate(proposal)['passed'])

    def test_changed_source_rejects_old_proposal(self):
        original = self.snapshot().assess()
        self.rows['supplier'][0]['WeightedScore'] = '99'
        self.write_rows()
        current = self.snapshot()
        self.assertNotEqual(current.source_version, original['source_version'])
        self.assertFalse(current.validate(original)['passed'])

    def test_conflicting_gap_fails_closed(self):
        self.rows['launch_program'][0]['CapacityGapUnits'] = '2500'
        self.write_rows()
        with self.assertRaises(SourceError): self.snapshot().assess()

    def test_duplicate_and_orphan_keys_fail(self):
        self.rows['plant'].append(copy.deepcopy(self.rows['plant'][0]))
        self.write_rows()
        with self.assertRaises(SourceError): self.snapshot()
        self.rows['plant'].pop()
        self.rows['batch'][0]['PlantID'] = 'unknown'
        self.write_rows()
        with self.assertRaises(SourceError): self.snapshot()

    def test_supplier_rules_are_all_enforced(self):
        for field, value in [('QualifiedAvailableCapacityUnits', '18000'),
                             ('GMPCertStatus', 'Expired'), ('OpenCriticalFindings', '1'),
                             ('FastTrackEligible', 'No')]:
            with self.subTest(field=field):
                row = self.rows['supplier'][0]
                previous = row[field]
                row[field] = value
                self.write_rows()
                self.assertNotIn('CMO006', self.snapshot().assess()['eligible_cmo_ids'])
                row[field] = previous

    def test_tie_uses_lead_time(self):
        self.rows['supplier'][0]['WeightedScore'] = '90'
        self.rows['supplier'][0]['LeadTimeWeeks'] = '4'
        self.write_rows()
        self.assertEqual(self.snapshot().assess()['eligible_cmo_ids'][0], 'CMO006')

    def test_internal_only_skips_supplier_shortlist(self):
        self.rows['launch_program'][0].update(QualifiedCapacity='270000', CapacityGapUnits='0')
        self.write_rows()
        snapshot = self.snapshot()
        self.assertEqual(snapshot.assess()['eligible_cmo_ids'], [])
        self.assertTrue(snapshot.validate(snapshot.assess())['passed'])

    def test_invalid_source_integer_and_program_fail(self):
        with self.assertRaises(SourceError): self.snapshot().assess('CMO-01')
        self.rows['supplier'][0]['WeightedScore'] = 'NaN'
        self.write_rows()
        with self.assertRaises(SourceError): self.snapshot().assess()

    def test_nonobject_proposal_fails_closed(self):
        for proposal in [None, [], 'passed=true', True]:
            self.assertFalse(self.snapshot().validate(proposal)['passed'])

if __name__ == '__main__':
    unittest.main()
