#!/usr/bin/env python3
"""Independent pure falsifiers; synthetic inputs are never native evidence."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'scripts'))
import analyze_audio_lifecycle as diagnostic
import test_analyze_audio_lifecycle as maintained

OUT = Path(__file__).resolve().parent


def renumber(rows):
    for sequence, row in enumerate(rows):
        row['sequence'] = sequence
        row['usec'] = sequence
    return rows


def cases():
    original = maintained.fixture()
    late = copy.deepcopy(original)
    late.append({**copy.deepcopy(late[-2]), 'id': '1', 'alive': True,
                 'stage': 'existing_process_frame'})
    early = copy.deepcopy(original)
    final_weak = [row for row in early if row['kind'] == 'weak']
    early = [row for row in early if row['kind'] != 'weak']
    early[8:8] = final_weak
    return {
        'late_weak_after_final_checkpoint': renumber(late),
        'final_weak_before_all_leave_boundaries': renumber(early),
        'missing_all_post_leave_weak_observations': original,
    }


class IndependentChronologyControls(unittest.TestCase):
    def test_late_weak_after_final_checkpoint_is_rejected(self):
        with self.assertRaises(ValueError):
            diagnostic.analyze(maintained.log(cases()['late_weak_after_final_checkpoint']))

    def test_final_weak_before_all_leave_boundaries_is_rejected(self):
        with self.assertRaises(ValueError):
            diagnostic.analyze(maintained.log(cases()['final_weak_before_all_leave_boundaries']))

    def test_missing_post_leave_weak_observations_is_rejected(self):
        with self.assertRaises(ValueError):
            diagnostic.analyze(maintained.log(cases()['missing_all_post_leave_weak_observations']))


if __name__ == '__main__':
    summary = {}
    for name, rows in cases().items():
        text = maintained.log(rows)
        (OUT / (name + '.synthetic.log')).write_text(text)
        try:
            report = diagnostic.analyze(text)
            (OUT / (name + '.accepted-report.json')).write_text(json.dumps(report, indent=2) + '\n')
            final = {row['id']: row['alive'] for row in rows
                     if row['kind'] == 'weak' and row['stage'] == 'final_pre_quit'}
            summary[name] = {
                'accepted': True,
                'explicit_final_weak_player_1': final.get('1'),
                'reported_final_alive_player_ids': report['final_alive_player_ids'],
                'weak_stages': sorted({row['stage'] for row in rows if row['kind'] == 'weak'}),
            }
        except ValueError as error:
            summary[name] = {'accepted': False, 'error': str(error)}
    (OUT / 'counterexample-summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    unittest.main()
