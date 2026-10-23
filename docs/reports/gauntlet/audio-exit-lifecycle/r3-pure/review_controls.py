#!/usr/bin/env python3
"""Independent synthetic source controls; never native execution evidence."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'scripts'))
import analyze_audio_lifecycle as diagnostic

OUT = Path(__file__).resolve().parent
FORCED = ['before_hud_leave', 'after_hud_leave'] * 6 + [
    'before_final_leave', 'after_final_leave', 'final_pre_quit']
PLAYER, WAV, PLAYBACK = '11', '-9223372036854775796', '-9223372036854775795'


def number(rows):
    for n, row in enumerate(rows):
        row.update(schema=1, sequence=n, process_frame=n // 8,
                   physics_frame=n // 4, usec=n)
    return rows


def trace(driver='CoreAudio'):
    rows, objects = [], []
    def add(kind, stage, **payload):
        rows.append(dict(kind=kind, stage=stage, **payload))
    def register(identity, cls, stage):
        row = dict(id=identity, **{'class': cls})
        if cls == 'AudioStreamWAV':
            row['wav'] = dict(format=1, mix_rate=22050, stereo=False,
                              bytes=8, sha256='b' * 64)
        add('object', stage, **row)
        objects.append(identity)
    def player(stage, event='snapshot', identity=PLAYER):
        add('player', stage, id=identity, event=event, state={
            'path': '/root/Match/Actor/Audio',
            'owner': {'role': 'actor_shot', 'id': '10',
                      'path': '/root/Match/Actor', 'script': 'res://scripts/gameplay/actor.gd'},
            'inside_tree': event != 'node_removed_after_native_exit', 'queued_for_deletion': False,
            'playing': False, 'stream_paused': False,
            'has_stream_playback': True, 'stream_id': WAV,
            'latest_playback_id': PLAYBACK, 'latest_playing': False})
    add('header', 'attach', driver=driver, mix_rate=44100,
        scope='read_only_latest_playback_not_server_drain')
    register(PLAYER, 'AudioStreamPlayer3D', 'attach')
    register(WAV, 'AudioStreamWAV', 'attach')
    register(PLAYBACK, 'AudioStreamPlaybackWAV', 'attach')
    player('attach', 'node_added')
    for occurrence, stage in enumerate(FORCED):
        # Synchronous structural callbacks retain the previous stage label.
        if occurrence == 2:
            register('22', 'AudioStreamPlayer3D', FORCED[occurrence - 1])
            player(FORCED[occurrence - 1], 'node_added', '22')
        player(stage)
        for identity in objects:
            add('weak', stage, id=identity, alive=(identity != '22' or stage != 'final_pre_quit'))
        add('checkpoint', stage, time_since_last_mix=0.01, time_to_next_mix=0.02)
        if occurrence < len(FORCED) - 1:
            player(stage, 'node_removed_after_native_exit')
            # Valid incremental snapshots may emit zero changed weak values.
            if occurrence % 2:
                add('weak', 'existing_process_frame', id=PLAYER, alive=True)
            add('checkpoint', 'existing_process_frame',
                time_since_last_mix=0.01, time_to_next_mix=0.02)
    return number(rows)


def log(rows, preamble=''):
    return (preamble + diagnostic.ENGINE + ' - https://godotengine.org\n' +
            '\n'.join(diagnostic.PREFIX + json.dumps(row) for row in rows) +
            '\nINPUT_MODE_TEST checks=462 failures=0 graphical_pointer=false '
            'scope=simulated_capabilities_and_input_not_physical_hardware baseline=false\n' +
            'WARNING: 2 ObjectDB instances were leaked at exit\n' +
            'Leaked instance: AudioStreamPlaybackWAV:9223372036854775821 - Reference count: 1\n' +
            'Leaked instance: AudioStreamWAV:9223372036854775820 - Reference count: 1\n')


class ChronologyControls(unittest.TestCase):
    def test_producer_style_dynamic_registry_and_repeated_raw_state(self):
        raw = log(trace())
        report = diagnostic.analyze(raw)
        self.assertEqual(report['final_alive_player_ids'], [PLAYER])
        self.assertEqual([x['stage'] for x in report['forced_weak_snapshots']], FORCED)
        self.assertEqual([x['weak_count'] for x in report['forced_weak_snapshots']], [3, 3] + [4] * 13)
        wav = report['leaks'][1]
        self.assertEqual(wav['descriptor']['id'], WAV)
        self.assertEqual({r['state']['stream_id'] for r in wav['player_observations']},
                         {'9223372036854775820'})
        self.assertGreater(len(wav['player_observations']), 15)
        self.assertTrue(report['strict_raw_log_failed'])
        self.assertIn('unknown', report['server_drain'])
        self.assertIn('unproven', report['cause'])
        self.assertEqual(raw, log(trace()))

    def test_missing_row_from_each_repeated_window_is_rejected(self):
        original = trace()
        indices = [n for n, r in enumerate(original) if r['kind'] == 'checkpoint' and r['stage'] in FORCED]
        for occurrence, end in enumerate(indices):
            start = max([-1] + [n for n in range(end) if original[n]['kind'] == 'checkpoint']) + 1
            rows = copy.deepcopy(original)
            del rows[next(n for n in range(start, end) if rows[n]['kind'] == 'weak')]
            with self.subTest(occurrence=occurrence), self.assertRaises(ValueError):
                diagnostic.analyze(log(number(rows)))

    def test_signed_unsigned_alias_duplicates_are_rejected(self):
        rows = trace()
        index = next(n for n, r in enumerate(rows) if r['kind'] == 'weak' and r['id'] == WAV)
        rows.insert(index + 1, {**rows[index], 'id': '9223372036854775820'})
        with self.assertRaisesRegex(ValueError, 'duplicated'):
            diagnostic.analyze(log(number(rows)))

    def test_backward_frame_or_time_is_rejected(self):
        for key in ['process_frame', 'physics_frame', 'usec']:
            rows = trace()
            rows[-1][key] = 0
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'backward'):
                diagnostic.analyze(log(rows))

    def test_final_boundary_is_sealed_on_otherwise_complete_trace(self):
        for kind in ['header', 'object', 'player', 'weak', 'checkpoint']:
            rows = trace()
            rows.append(copy.deepcopy(next(row for row in rows if row['kind'] == kind)))
            with self.subTest(kind=kind), self.assertRaisesRegex(ValueError, 'sealed final'):
                diagnostic.analyze(log(number(rows)))


class BaselineCompatibilityControls(unittest.TestCase):
    def test_default_headless_dummy_context_should_be_reported(self):
        # Proposed explicit policy amendment, justified by pinned source/ARM argv.
        self.assertEqual(diagnostic.analyze(log(trace('Dummy')))['driver'], 'Dummy')

    def test_original_arm_verbose_preamble_should_preserve_pinned_banner(self):
        # Exact first line of the retained original ARM verbose input-mode log.
        preamble = 'WorkerThreadPool: 3 threads, 1 max low-priority.\n'
        self.assertTrue(diagnostic.analyze(log(trace(), preamble))['strict_raw_log_failed'])


if __name__ == '__main__':
    (OUT / 'complete-producer-style.synthetic.log').write_text(log(trace()))
    (OUT / 'complete-default-headless.synthetic.log').write_text(log(trace('Dummy')))
    (OUT / 'complete-original-verbose-preamble.synthetic.log').write_text(
        log(trace(), 'WorkerThreadPool: 3 threads, 1 max low-priority.\n'))
    unittest.main()
