#!/usr/bin/env python3
"""Pure synthetic-log falsifiers. These are not engine or native evidence."""
import copy
import json
from pathlib import Path
import subprocess
import unittest

import analyze_audio_lifecycle as diagnostic


def fixture():
    rows = []

    def add(kind, stage='attach', **values):
        rows.append({'schema': 1, 'sequence': len(rows), 'kind': kind, 'stage': stage,
                     'process_frame': 1, 'physics_frame': 1, 'usec': len(rows), **values})

    add('header', driver='CoreAudio', mix_rate=48000, scope='read_only_latest_playback_not_server_drain')
    for identity, name in [('1', 'AudioStreamPlayer3D'), ('2', 'AudioStreamPlayer3D'),
                           ('-9223372036854775805', 'AudioStreamWAV'), ('4', 'AudioStreamWAV'),
                           ('-9223372036854775803', 'AudioStreamPlaybackWAV')]:
        values = {'id': identity, 'class': name}
        if name == 'AudioStreamWAV':
            values['wav'] = {'format': 1, 'mix_rate': 22050, 'stereo': False, 'bytes': 800, 'sha256': 'a' * 64}
        add('object', **values)
    state = {'path': '/root/Match/Operator/Audio', 'owner': {'role': 'actor_shot', 'id': '20',
             'path': '/root/Match/Operator', 'script': 'res://scripts/gameplay/actor.gd'},
             'inside_tree': True, 'queued_for_deletion': False, 'playing': True,
             'stream_paused': False, 'has_stream_playback': True,
             'stream_id': '-9223372036854775805', 'latest_playback_id': '-9223372036854775803', 'latest_playing': True}
    add('player', id='1', event='snapshot', state=state)
    shared = copy.deepcopy(state)
    shared.update(has_stream_playback=False, latest_playback_id='', latest_playing=None)
    shared['owner']['role'] = 'network_shot'
    add('player', id='2', event='snapshot', state=shared)
    for stage in ['before_hud_leave', 'after_hud_leave'] * 6 + ['before_final_leave', 'after_final_leave']:
        add('checkpoint', stage=stage, time_since_last_mix=0.01, time_to_next_mix=0.01)
    for row in rows.copy():
        if row['kind'] == 'object':
            add('weak', stage='final_pre_quit', id=row['id'], alive=False)
    add('checkpoint', stage='final_pre_quit', time_since_last_mix=0.01, time_to_next_mix=0.01)
    return rows



def renumber(rows):
    for sequence, row in enumerate(rows):
        row['sequence'] = sequence
        row['usec'] = sequence
    return rows


def complete_fixture():
    """Complete positive trace; fixture() stays the unchanged R1 falsifier."""
    original = fixture()
    objects = [row for row in original if row['kind'] == 'object']
    rows = []
    for row in original:
        if row['kind'] == 'weak':
            continue
        if row['kind'] == 'checkpoint':
            rows.extend({'schema': 1, 'kind': 'weak', 'stage': row['stage'],
                         'process_frame': 1, 'physics_frame': 1,
                         'id': item['id'], 'alive': False} for item in objects)
        rows.append(row)
    return renumber(rows)


def log(rows, leak=True):
    output = diagnostic.ENGINE + ' - https://godotengine.org\n'
    output += '\n'.join(diagnostic.PREFIX + json.dumps(row) for row in rows)
    output += '\nINPUT_MODE_TEST checks=462 failures=0 graphical_pointer=false scope=simulated_capabilities_and_input_not_physical_hardware baseline=false\n'
    if leak:
        output += ('WARNING: 2 ObjectDB instances were leaked at exit (run with `--verbose` for details).\n'
                   'Leaked instance: AudioStreamPlaybackWAV:9223372036854775813 - Reference count: 1\n'
                   'Leaked instance: AudioStreamWAV:9223372036854775811 - Reference count: 1\n'
                   'Orphan StringName: Master (static: 0, total: 1)\n')
    return output


class AudioLifecycleAnalysisTests(unittest.TestCase):
    def test_complete_positive_has_all_fifteen_forced_weak_windows(self):
        report = diagnostic.analyze(log(complete_fixture()))
        self.assertEqual(len(report['forced_weak_snapshots']), 15)
        self.assertEqual([row['stage'] for row in report['forced_weak_snapshots']],
                         ['before_hud_leave', 'after_hud_leave'] * 6 +
                         ['before_final_leave', 'after_final_leave', 'final_pre_quit'])
        self.assertTrue(all(row['registered_object_count'] == row['weak_count'] == 5
                            for row in report['forced_weak_snapshots']))
        self.assertEqual(report['final_alive_player_ids'], [])
        self.assertEqual(report['final_checkpoint_sequence'], complete_fixture()[-1]['sequence'])

    def test_valid_final_alive_player_is_reported_without_drain_or_cause_claim(self):
        rows = complete_fixture()
        for row in rows:
            if row['kind'] == 'weak' and row['id'] == '1': row['alive'] = True
        report = diagnostic.analyze(log(rows))
        self.assertEqual(report['final_alive_player_ids'], ['1'])
        self.assertIn('unknown', report['server_drain'])
        self.assertIn('unproven', report['cause'])

    def test_incremental_frame_window_may_be_empty_or_partial(self):
        for changed in (False, True):
            rows = complete_fixture()
            additions = []
            if changed:
                additions.append({**copy.deepcopy(rows[8]), 'stage': 'existing_process_frame'})
            additions.append({**copy.deepcopy(rows[13]), 'stage': 'existing_process_frame'})
            rows[8:8] = additions
            with self.subTest(changed=changed):
                self.assertEqual(len(diagnostic.analyze(log(renumber(rows)))['forced_weak_snapshots']), 15)

    def test_every_original_saved_counterexample_is_rejected_unchanged(self):
        root = Path(__file__).resolve().parents[1]
        directory = root / 'docs/reports/gauntlet/audio-exit-lifecycle/independent-source-r1-original'
        paths = sorted(directory.glob('*.synthetic.log'))
        self.assertEqual(len(paths), 3)
        for path in paths:
            with self.subTest(path=path.name), self.assertRaises(ValueError):
                diagnostic.analyze(path.read_text())

    def test_each_post_final_probe_record_kind_is_rejected_on_complete_input(self):
        original = complete_fixture()
        for kind in ('header', 'object', 'player', 'weak', 'checkpoint'):
            rows = copy.deepcopy(original)
            row = copy.deepcopy(next(row for row in rows if row['kind'] == kind))
            row['stage'] = 'existing_process_frame'
            rows.append(row)
            with self.subTest(kind=kind), self.assertRaisesRegex(ValueError, 'after the sealed final'):
                diagnostic.analyze(log(renumber(rows)))

    def test_early_or_falsely_labeled_final_weak_rows_are_rejected_on_complete_input(self):
        rows = complete_fixture()
        final = [row for row in rows if row['kind'] == 'weak' and row['stage'] == 'final_pre_quit']
        early = [row for row in rows if row not in final]
        early[8:8] = final
        with self.assertRaisesRegex(ValueError, 'outside its matching checkpoint window'):
            diagnostic.analyze(log(renumber(early)))
        rows = complete_fixture()
        final = next(row for row in rows if row['kind'] == 'weak' and row['stage'] == 'final_pre_quit')
        final['stage'] = 'after_final_leave'
        with self.assertRaisesRegex(ValueError, 'outside its matching checkpoint window'):
            diagnostic.analyze(log(rows))

    def test_one_missing_weak_row_in_each_forced_window_is_rejected(self):
        original = complete_fixture()
        starts = [0] + [index + 1 for index, row in enumerate(original) if row['kind'] == 'checkpoint']
        ends = [index for index, row in enumerate(original) if row['kind'] == 'checkpoint']
        self.assertEqual(len(ends), 15)
        for occurrence, (start, end) in enumerate(zip(starts, ends)):
            rows = copy.deepcopy(original)
            missing = next(index for index in range(start, end) if rows[index]['kind'] == 'weak')
            del rows[missing]
            with self.subTest(occurrence=occurrence, stage=original[end]['stage']), self.assertRaisesRegex(ValueError, 'lacks complete weak'):
                diagnostic.analyze(log(renumber(rows)))

    def test_duplicate_weak_rows_and_incomplete_trailing_windows_are_rejected(self):
        rows = complete_fixture()
        rows.insert(9, copy.deepcopy(rows[8]))
        with self.assertRaisesRegex(ValueError, 'duplicated within one checkpoint window'):
            diagnostic.analyze(log(renumber(rows)))
        with self.assertRaises(ValueError): diagnostic.analyze(log(complete_fixture()[:-1]))

    def test_exact_unsigned_join_preserves_shared_owner_evidence_and_strict_failure(self):
        report = diagnostic.analyze(log(complete_fixture()))
        playback, wav = report['leaks']
        self.assertTrue(playback['observed'])
        self.assertEqual([row['player_id'] for row in playback['player_observations']], ['1'])
        self.assertEqual({row['player_id'] for row in wav['player_observations']}, {'1', '2'})
        self.assertEqual(wav['descriptor']['wav']['sha256'], 'a' * 64)
        self.assertTrue(report['strict_raw_log_failed'])
        self.assertEqual(report['server_drain'], 'unknown; no public acknowledgment')
        self.assertFalse(report['fixture_owner_coverage_complete'])

    def test_unknown_leak_cannot_borrow_an_observed_owner_or_type(self):
        text = log(complete_fixture()).replace('AudioStreamPlaybackWAV:9223372036854775813', 'AudioStreamPlaybackWAV:99')
        report = diagnostic.analyze(text)
        self.assertEqual(report['unobserved_leaks'], ['99'])
        self.assertEqual(report['leaks'][0]['player_observations'], [])
        self.assertIsNone(report['leaks'][0]['descriptor'])

    def test_different_wav_does_not_borrow_shared_stream_owners(self):
        text = log(complete_fixture()).replace('AudioStreamWAV:9223372036854775811', 'AudioStreamWAV:4')
        wav = diagnostic.analyze(text)['leaks'][1]
        self.assertTrue(wav['observed'])
        self.assertEqual(wav['player_observations'], [])

    def test_stopped_player_and_dead_weakref_cannot_qualify_server_drain(self):
        rows = complete_fixture()
        rows[6]['state']['playing'] = False
        rows[6]['state']['latest_playing'] = False
        report = diagnostic.analyze(log(rows))
        self.assertIn('unknown', report['server_drain'])
        self.assertIn('unproven', report['cause'])
        self.assertTrue(report['strict_raw_log_failed'])

    def test_clean_sample_is_not_a_fix_claim(self):
        report = diagnostic.analyze(log(complete_fixture(), leak=False))
        self.assertFalse(report['strict_raw_log_failed'])
        self.assertEqual(report['sample_status'], 'no_typed_leak_in_this_sample')
        self.assertIn('no fix', report['scope'])

    def test_untyped_strict_failure_cannot_become_a_clean_sample(self):
        report = diagnostic.analyze(log(complete_fixture(), leak=False) + 'WARNING: 2 ObjectDB instances were leaked at exit\n')
        self.assertTrue(report['strict_raw_log_failed'])
        self.assertEqual(report['sample_status'], 'untyped_strict_failure')
        self.assertEqual(report['leaks'], [])

    def test_missing_malformed_or_reordered_probe_is_rejected(self):
        for text in [log([]), log(complete_fixture()).replace('AUDIO_LIFECYCLE {', 'AUDIO_LIFECYCLE bad{', 1),
                     log(complete_fixture()).replace('"sequence": 1,', '"sequence": 3,', 1)]:
            with self.subTest(text=text[:70]), self.assertRaises(ValueError):
                diagnostic.analyze(text)

    def test_missing_final_weak_or_leave_boundary_is_rejected(self):
        for index in [8, 22]:
            rows = complete_fixture()
            rows[index]['stage'] = 'missing'
            with self.subTest(index=index), self.assertRaises(ValueError):
                diagnostic.analyze(log(rows))

    def test_reordered_leave_checkpoints_are_rejected(self):
        rows = complete_fixture()
        first, second = [row for row in rows if row['kind'] == 'checkpoint'][:2]
        first['stage'], second['stage'] = second['stage'], first['stage']
        with self.assertRaises(ValueError): diagnostic.analyze(log(rows))

    def test_dummy_changed_engine_or_changed_assertion_result_is_rejected(self):
        original = log(complete_fixture())
        for text in [original.replace('CoreAudio', 'Dummy'), original.replace('ed1daf0bf', 'unknown'),
                     original.replace('checks=462', 'checks=461'), original.replace('failures=0', 'failures=1')]:
            with self.subTest(text=text[:70]), self.assertRaises(ValueError):
                diagnostic.analyze(text)

    def test_numeric_ids_unregistered_playback_and_class_mismatch_are_rejected(self):
        rows = complete_fixture()
        rows[6]['state']['latest_playback_id'] = 5
        with self.assertRaises(ValueError): diagnostic.analyze(log(rows))
        rows[6]['state']['latest_playback_id'] = '99'
        with self.assertRaises(ValueError): diagnostic.analyze(log(rows))
        with self.assertRaises(ValueError):
            diagnostic.analyze(log(complete_fixture()).replace('Leaked instance: AudioStreamWAV:', 'Leaked instance: Other:'))

    def test_object_id_domain_and_precision(self):
        self.assertEqual(diagnostic.object_id('-1'), '18446744073709551615')
        self.assertEqual(diagnostic.object_id('9223372036854775813'), '9223372036854775813')
        for value in [None, 123, '0', str(1 << 64), str(-(1 << 63) - 1), '1.0']:
            with self.subTest(value=value), self.assertRaises(ValueError): diagnostic.object_id(value)

    def test_maintained_input_mode_changes_are_only_the_optional_hooks(self):
        root = Path(__file__).resolve().parents[1]
        candidate = (root / 'game/tests/input_mode_test.gd').read_text()
        baseline = subprocess.check_output(['git', 'show', 'c08889b8c1118c89e83c151079df4dc224076760:game/tests/input_mode_test.gd'], cwd=root, text=True)
        candidate = candidate.replace('var audio_probe\n\nfunc audio_checkpoint(stage: String) -> void:\n\tif audio_probe != null: audio_probe.snapshot(stage, true)\n', '')
        candidate = candidate.replace('\tfor _i in count:\n\t\tawait process_frame\n\t\tif audio_probe != null: audio_probe.snapshot("existing_process_frame")', '\tfor _i in count: await process_frame')
        candidate = candidate.replace('\tif OS.get_cmdline_user_args().has("--audio-lifecycle-diagnostic"):\n\t\taudio_probe = load("res://tests/audio_lifecycle_probe.gd").new()\n\t\taudio_probe.attach(self)\n', '')
        candidate = re_remove_hooks(candidate)
        self.assertEqual(candidate, baseline)


def re_remove_hooks(text):
    import re
    return re.sub(r'^\s*audio_checkpoint\("(?:before|after)_(?:final|hud)_leave"\)\n|^\tif audio_probe != null: audio_probe.finish\(\)\n', '', text, flags=re.M)


if __name__ == '__main__':
    unittest.main()
