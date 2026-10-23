#!/usr/bin/env python3
"""Pure policy guards/forecast tests. No engine or candidate output is produced."""
import copy
from pathlib import Path
import unittest

import audit_candidate as audit

ROOT = Path(__file__).resolve().parents[4]
BASELINE = ROOT / 'docs/reports/gauntlet/m5-exhausted-primary-benchmark/actual-r2/baseline-probe.stdout.log.gz'


class PolicyForecastTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records,_ = audit.parse(BASELINE)
        cls.header = cls.records[0][2]
        cls.row = next(row for _,kind,row in cls.records if kind == 'CASE' and
                       row['label'] == 'core/normal/rifle/exhausted/loaded/far/none')

    def allowed(self,before=None,acquired=True,interacting=False,distance=24,difficulty='normal'):
        return audit.extension_allowed(before or self.row['before'],acquired,interacting,distance,
                                       self.header['profiles'][difficulty],self.header['weapon_definitions'])

    def test_exact_registered_baseline_forecast(self):
        plan = audit.planned_deltas(self.records)
        self.assertEqual((plan['changed_matrix_requests'],plan['preserved_matrix_requests']), (51,516))
        self.assertEqual((plan['changed_first_sequence_requests'],plan['preserved_first_sequence_requests']), (15,57))
        self.assertIn('core/normal/rifle/exhausted/loaded/outside_sidearm/none',plan['changed_matrix_labels'])
        self.assertNotIn('core/hard/rifle/exhausted/loaded/outside_sidearm/none',plan['changed_matrix_labels'])

    def test_extension_positive_and_range_boundaries(self):
        for distance in (6,20,24,44.9,45):
            with self.subTest(distance=distance):
                self.assertTrue(self.allowed(distance=distance))
        for distance in (45.0001,45.1,60):
            with self.subTest(outside=distance):
                self.assertFalse(self.allowed(distance=distance))
        for distance in (24,45.1,60):
            with self.subTest(no_target=distance):
                self.assertTrue(self.allowed(acquired=False,distance=distance))

    def test_difficulty_interaction_loaded_reloadable_unowned_unknown_dry_guards(self):
        self.assertFalse(self.allowed(difficulty='easy'))
        self.assertFalse(self.allowed(interacting=True))
        mutations = [('ammo',1),('reserve',30),('weapon','sidearm'),('weapon','unknown'),
                     ('inventory',['rifle']),('ammo_store',{}),('ammo_store',{'sidearm':[0,0]})]
        for field,value in mutations:
            before = copy.deepcopy(self.row['before']);before[field] = value
            with self.subTest(field=field,value=value):
                self.assertFalse(self.allowed(before))

    def test_known_reserve_positive_and_stale_active_cache(self):
        before = copy.deepcopy(self.row['before'])
        before['ammo_store'].update(sidearm=[0,15],rifle=[30,90])
        self.assertTrue(self.allowed(before))
        before['reserve'] = 30
        before['ammo_store']['rifle'] = [0,0]
        self.assertFalse(self.allowed(before))

    def test_old_near_fallback_preserves_unknown_dry_and_primary_reserve(self):
        for store in ({},{'sidearm':[0,0]}):
            before = copy.deepcopy(self.row['before']);before.update(ammo_store=store,reserve=30)
            self.assertEqual(audit.expected_weapon(before,True,False,6,self.header['profiles']['normal'],self.header['weapon_definitions']),'sidearm')
            self.assertEqual(audit.expected_weapon(before,True,False,20,self.header['profiles']['normal'],self.header['weapon_definitions']),'')

    def test_no_target_return_uses_preserved_primary_priority_and_known_dry_skip(self):
        before = copy.deepcopy(self.row['before']);before.update(weapon='sidearm',inventory=['sidearm','rifle','marksman','smg'])
        before['ammo_store'].update(rifle=[0,0],marksman=[1,0],smg=[30,0])
        self.assertEqual(audit.expected_weapon(before,False,False,6,self.header['profiles']['normal'],self.header['weapon_definitions']),'marksman')
        del before['ammo_store']['rifle']
        self.assertEqual(audit.expected_weapon(before,False,False,6,self.header['profiles']['normal'],self.header['weapon_definitions']),'rifle')

    def test_supplement_registration_is_bounded_and_exact(self):
        rows = audit.expected_records()
        self.assertEqual(len(rows),1268)
        self.assertEqual(len([r for r in rows if r[0]=='POLICY_RANGE']),9)
        reserve = [r for r in rows if r[0]=='POLICY_RESERVE_STEP']
        self.assertEqual([r[2] for r in reserve],list(range(20)))
        self.assertEqual({r[3]['target']['distance'] for r in reserve},{24.0})

    def test_candidate_audit_rejects_original_missing_new_controls(self):
        with self.assertRaisesRegex(AssertionError,'exact row-kind inventory'):
            audit.audit(self.records,ROOT)

    def test_comparator_rejects_unchanged_baseline_as_candidate(self):
        with self.assertRaisesRegex(AssertionError,'exact allowed matrix command delta'):
            audit.compare(self.records,self.records)

    def test_plan_rejects_missing_matrix_identity(self):
        corrupted = [record for record in self.records if not (record[1]=='CASE' and record[2]['label']==self.row['label'])]
        with self.assertRaisesRegex(AssertionError,'baseline matrix registration'):
            audit.planned_deltas(corrupted)


if __name__ == '__main__':
    unittest.main(verbosity=2)
