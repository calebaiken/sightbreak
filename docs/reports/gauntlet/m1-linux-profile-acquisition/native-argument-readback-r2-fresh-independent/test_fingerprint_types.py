"""Fresh adversarial controls; synthetic evidence, zero native invocation."""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'scripts'))
import linux_profile_overhead as controller
from test_linux_profile_overhead import manual_expected, manual_record

SNAPSHOTS = ('fingerprint_initial', 'fingerprint_terminal')
FIELDS = ('caller_is_main_thread', 'caller_is_render_thread')
MISSING = object()
VALUES = (False, None, 0, 0.0, 1, 1.0, -1, 2, 'true', 'True', '1', [], {}, [True], MISSING)
CASES = []


def fingerprint(row, name, mutate, **options):
    content = json.loads(row['fixture'][name]['serialized'])
    mutate(content)
    serialized = json.dumps(content, **options)
    row['fixture'][name] = {'serialized': serialized,
                            'sha256': hashlib.sha256(serialized.encode()).hexdigest()}


class FingerprintTypes(unittest.TestCase):
    def setUp(self):
        self.assertEqual(os.sched_getaffinity(0), {4})
        self.expected = manual_expected()

    def rejected(self, row, label, message='Invalid fingerprint thread readback'):
        with self.subTest(case=label), self.assertRaisesRegex(controller.Invalid, message):
            controller.validate_condition(row, self.expected)
        CASES.append(label)

    def test_literal_true_accepts_rebuilt_hashes_and_serialization_orders(self):
        for index in range(4):
            for options in ({'sort_keys': True}, {'sort_keys': False},
                            {'sort_keys': True, 'separators': (',', ':')}, {'indent': 2}):
                row = manual_record(index)
                for name in SNAPSHOTS:
                    fingerprint(row, name, lambda content: content['settings'].update(
                        {key: True for key in FIELDS}), **options)
                controller.validate_condition(row, self.expected)
                CASES.append(f'literal true index={index} options={options}')

    def test_each_inner_type_and_missing_field_rejects_in_each_snapshot(self):
        for field in FIELDS:
            for names in ((SNAPSHOTS[0],), (SNAPSHOTS[1],), SNAPSHOTS):
                for value in VALUES:
                    row = manual_record(0)
                    def mutate(content):
                        if value is MISSING:
                            del content['settings'][field]
                        else:
                            content['settings'][field] = deepcopy(value)
                    for name in names:
                        fingerprint(row, name, mutate, sort_keys=True)
                    self.rejected(row, f'{field} snapshots={names} value={value!r}')

    def test_simultaneous_field_substitutions_reject(self):
        for index in range(4):
            for names in ((SNAPSHOTS[0],), (SNAPSHOTS[1],), SNAPSHOTS):
                for value in (1, 1.0, False):
                    row = manual_record(index)
                    for name in names:
                        fingerprint(row, name, lambda content: content['settings'].update(
                            {key: value for key in FIELDS}), sort_keys=True)
                    self.rejected(row, f'both fields index={index} snapshots={names} value={value!r}')

    def test_malformed_or_missing_inner_settings_reject(self):
        for name in SNAPSHOTS:
            for value in (None, [], '', 1, True, MISSING):
                row = manual_record(0)
                def mutate(content):
                    if value is MISSING:
                        del content['settings']
                    else:
                        content['settings'] = value
                fingerprint(row, name, mutate)
                self.rejected(row, f'{name} settings={value!r}')

    def test_outer_types_remain_strict_when_all_settings_match(self):
        for field in FIELDS:
            for value in VALUES:
                row = manual_record(0)
                if value is MISSING:
                    del row['fixture']['settings'][field]
                else:
                    row['fixture']['settings'][field] = deepcopy(value)
                for name in SNAPSHOTS:
                    fingerprint(row, name, lambda content: content.update(
                        settings=deepcopy(row['fixture']['settings'])))
                self.rejected(row, f'outer synchronized {field} value={value!r}',
                              'Synchronous safe thread readback failed')

    def test_hash_guard_precedes_type_guard_for_both_snapshots(self):
        for name in SNAPSHOTS:
            row = manual_record(0)
            fingerprint(row, name, lambda content: content['settings'].update(
                caller_is_main_thread=1))
            row['fixture'][name]['sha256'] = '0' * 64
            self.rejected(row, f'{name} hash before type', 'Invalid fingerprint hash')
            row['fixture'][name]['sha256'] = hashlib.sha256(
                row['fixture'][name]['serialized'].encode()).hexdigest()
            self.rejected(row, f'{name} repaired hash reaches type')

    def test_cross_snapshot_equality_still_requires_identical_serialized_bytes(self):
        for name in SNAPSHOTS:
            row = manual_record(0)
            fingerprint(row, name, lambda content: None, separators=(',', ':'))
            self.rejected(row, f'{name} equivalent JSON different serialization',
                          'Scene changed during condition')


if __name__ == '__main__':
    program = unittest.main(exit=False, verbosity=2)
    # Emit case accounting from the completed run without running a second time.
    print(json.dumps({'case_count': len(CASES), 'affinity': sorted(os.sched_getaffinity(0)),
                      'scope': 'Synthetic evidence controls only'}, sort_keys=True))
    sys.exit(not program.result.wasSuccessful())
