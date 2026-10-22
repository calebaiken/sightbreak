"""Pure Python controls with synthetic proc/cgroup trees; no native client."""
from copy import deepcopy
import errno
import io
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from linux_frame_sampler import LinuxFrameSampler, MAX_THREADS, attempt, cpu_max, cpu_stat, process_stat


def stat(pid=123, name='client (native)', user=12, system=34, start=50):
    fields = ['S'] + ['0'] * 49
    for index, value in ((11, user), (12, system), (19, start)):
        fields[index] = str(value)
    return f"{pid} ({name}) {' '.join(fields)}\n".encode()


class Process:
    pid = 123
    returncode = None

    def poll(self):
        return self.returncode


class SamplingTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.proc, self.cgroup = self.root / 'proc', self.root / 'cgroup'
        self.target = self.proc / '123'
        self.target.mkdir(parents=True)
        (self.target / 'stat').write_bytes(stat())
        (self.target / 'environ').write_bytes(b'DISPLAY=:123\0LIBGL_ALWAYS_SOFTWARE=1\0LP_NUM_THREADS=2\0PASSWORD=never-export-this\0BEARER=never-export-this\0')
        (self.target / 'cgroup').write_text('0::/game\n')
        for tid, name in ((123, 'client'), (124, 'llvmpipe-0'), (125, 'never-export-this')):
            directory = self.target / f'task/{tid}'
            directory.mkdir(parents=True)
            (directory / 'stat').write_bytes(stat(tid, name))
        (self.cgroup / 'game').mkdir(parents=True)
        for directory in (self.cgroup, self.cgroup / 'game'):
            (directory / 'cpu.max').write_text('200000 100000\n')
            (directory / 'cpu.stat').write_text('usage_usec 123\nuser_usec 100\nsystem_usec 23\nnr_periods 10\nnr_throttled 2\nthrottled_usec 22\n')
        self.observation = self.root / 'status.json'
        self.frame = {key: 1 for key in ('read_begin_usec', 'read_end_usec', 'max_physics_steps_per_frame',
                     'physics_ticks_per_second', 'physics_jitter_fix', 'max_fps', 'process_frames', 'physics_frames',
                     'drawn_frames', 'process_max_seconds_last_engine_window', 'physics_step_max_seconds_last_engine_window',
                     'draw_calls_last_rendered_frame', 'primitives_last_rendered_frame', 'viewport_3d_scale')}
        self.frame.update(viewport_visible_size=[1280, 720], viewport_texture_size_pixels=[1280, 720],
                          private_extra='never-export-this')
        self.state = dict(schema=1, scope='debug_offline_read_only_observation', scenario='plant', phase='post',
                          wall_msec=1200, elapsed=1.25, simulation_tick=75, round_number=1, drawn_frames=5,
                          time_scale=1, frame_diagnostics=self.frame,
                          actors=[{'account': 'never-export-this'}], initial_profile={'bearer': 'never-export-this'})
        self.observation.write_text(json.dumps(self.state))
        self.process = Process()
        affinity = patch('linux_frame_sampler.os.sched_getaffinity', return_value={0, 1})
        affinity.start()
        self.addCleanup(affinity.stop)

    def inert(self):
        sampler = LinuxFrameSampler.__new__(LinuxFrameSampler)
        sampler.proc, sampler.cgroup_root = self.proc, self.cgroup
        sampler.pid, sampler.observation = 123, self.observation
        return sampler

    def run_sampler(self, duration=.015, **changes):
        sampler = LinuxFrameSampler(self.process, self.root / 'samples.jsonl', self.observation, duration,
                                    proc=self.proc, cgroup_root=self.cgroup, **changes)
        self.addCleanup(sampler.stop)
        sampler.thread.join(timeout=2)
        self.assertFalse(sampler.thread.is_alive())
        summary = sampler.stop()
        rows = [json.loads(line) for line in sampler.output.read_text().splitlines()]
        return summary, rows

    def test_owned_sample_units_identity_privacy_and_shutdown(self):
        summary, rows = self.run_sampler()
        self.assertTrue(summary['sampling_completed'])
        self.assertEqual(summary['reason'], 'duration_reached')
        self.assertEqual(rows[0]['start_time_ticks'], 50)
        self.assertGreater(rows[0]['cpu_ticks_per_second'], 0)
        sample = rows[1]
        self.assertEqual(sample['process_cpu']['value'], {'user_ticks': 12, 'system_ticks': 34, 'start_time_ticks': 50})
        self.assertEqual(sample['allowed_cpus']['value'], [0, 1])
        roles = [item['value']['role'] for item in sample['thread_cpu']['value']['threads']]
        self.assertEqual(roles, ['client_main', 'mesa_llvmpipe', 'other'])
        self.assertEqual(sample['offline_frame']['value']['frame_diagnostics']['viewport_texture_size_pixels'], [1280, 720])
        self.assertNotIn('never-export-this', json.dumps(rows))
        self.assertNotIn('PASSWORD', json.dumps(rows))
        self.assertNotIn('BEARER', json.dumps(rows))
        self.assertEqual(rows[-1]['event'], 'end')

    def test_real_one_second_cadence_has_no_catchup_burst(self):
        summary, rows = self.run_sampler(1.04)
        samples = [row for row in rows if row['event'] == 'sample']
        self.assertEqual(summary['samples_written'], 2)
        self.assertGreaterEqual(samples[1]['monotonic_begin_ns'] - samples[0]['monotonic_begin_ns'], 1_000_000_000)

    def test_stop_is_bounded_and_idempotent(self):
        sampler = LinuxFrameSampler(self.process, self.root / 'samples.jsonl', self.observation, 180,
                                    proc=self.proc, cgroup_root=self.cgroup)
        started = time.monotonic()
        summary = sampler.stop()
        self.assertLess(time.monotonic() - started, 1)
        self.assertFalse(summary['thread_alive'])
        self.assertEqual(sampler.stop(), summary)

    def test_missing_counter_fields_are_not_zero(self):
        (self.cgroup / 'game/cpu.max').unlink()
        (self.cgroup / 'game/cpu.stat').write_text('usage_usec 123\n')
        group = self.inert()._cgroup()[0]
        self.assertEqual(group['cpu_max']['errno'], errno.ENOENT)
        self.assertFalse(group['cpu_max']['available'])
        counters = group['cpu_stat']['value']
        self.assertNotIn('nr_throttled', counters['counters'])
        self.assertIn('nr_throttled', counters['unavailable_fields'])

    def test_cgroup_target_and_ancestors_keep_scopes(self):
        groups = self.inert()._cgroup()
        self.assertEqual([(group['path'], group['scope']) for group in groups], [('/game', 'target'), ('/', 'ancestor')])
        self.assertEqual(groups[0]['cpu_max']['value']['quota_usec'], 200000)
        self.assertEqual(cpu_max(b'max 100000')['quota_usec'], None)

    def test_unsupported_traversing_or_symlinked_cgroup_is_unavailable(self):
        for value in ('2:cpu:/group', '0::/../outside', '0::relative', '0::/' + '/'.join(['deep'] * 33)):
            with self.subTest(value=value):
                (self.target / 'cgroup').write_text(value + '\n')
                self.assertFalse(attempt(self.inert()._cgroup)['available'])
        (self.cgroup / 'escape').symlink_to(self.root)
        (self.target / 'cgroup').write_text('0::/escape\n')
        self.assertEqual(attempt(self.inert()._cgroup)['reason'], 'cgroup_path_escapes_mount')

    def test_thread_enumeration_is_bounded_and_missing_thread_is_explicit(self):
        for number in range(200, 200 + MAX_THREADS):
            (self.target / f'task/{number}').mkdir()
        result = self.inert()._threads()
        self.assertTrue(result['enumeration_truncated'])
        self.assertEqual(len(result['threads']), MAX_THREADS)
        self.assertTrue(any(not item['available'] for item in result['threads']))

    def test_invalid_counter_payload_is_unavailable_without_echo(self):
        for read in (lambda: process_stat(b'never-export-this'), lambda: cpu_max(b'never-export-this'),
                     lambda: cpu_stat(b'usage_usec never-export-this')):
            result = attempt(read)
            self.assertFalse(result['available'])
            self.assertNotIn('never-export-this', json.dumps(result))

    def test_malformed_or_nonoffline_observation_is_not_serialized(self):
        for value in ([], {'schema': 1, 'scope': 'account'}, {**self.state, 'scenario': 'defuse'},
                      {**self.state, 'schema': True}, {**self.state, 'frame_diagnostics': {}},
                      {**self.state, 'simulation_tick': True}):
            self.observation.write_text(json.dumps(value))
            self.assertFalse(attempt(self.inert()._observation)['available'])
        invalid = deepcopy(self.state)
        invalid['frame_diagnostics']['viewport_texture_size_pixels'] = ['never-export-this', 720]
        self.observation.write_text(json.dumps(invalid))
        self.assertFalse(attempt(self.inert()._observation)['available'])

    def test_disappeared_or_reused_identity_stops_before_other_reads(self):
        for replacement in (None, stat(start=51)):
            def identity_then_change(sampler):
                identity = original(sampler)
                if replacement is None:
                    (self.target / 'stat').unlink()
                else:
                    (self.target / 'stat').write_bytes(replacement)
                return identity
            original = LinuxFrameSampler._identity
            with patch.object(LinuxFrameSampler, '_identity', identity_then_change), patch.object(LinuxFrameSampler, '_environment') as environment:
                summary, rows = self.run_sampler()
                self.assertEqual(summary['samples_written'], 0)
                self.assertFalse(summary['sampling_completed'])
                self.assertIn(summary['reason'], ('target_identity_changed', 'target_identity_unavailable'))
                environment.assert_not_called()
            (self.root / 'samples.jsonl').unlink()
            (self.target / 'stat').write_bytes(stat())

    def test_exit_after_collection_discards_uncertain_sample(self):
        original = LinuxFrameSampler._observation
        def read_then_exit(sampler):
            value = original(sampler)
            self.process.returncode = 0
            return value
        with patch.object(LinuxFrameSampler, '_observation', read_then_exit):
            summary, rows = self.run_sampler()
        self.assertEqual(summary['reason'], 'owned_client_exited')
        self.assertFalse(any(row['event'] == 'sample' for row in rows))

    def test_reuse_after_collection_discards_uncertain_sample(self):
        original = LinuxFrameSampler._observation
        def read_then_reuse(sampler):
            value = original(sampler)
            (self.target / 'stat').write_bytes(stat(start=51))
            return value
        with patch.object(LinuxFrameSampler, '_observation', read_then_reuse):
            summary, rows = self.run_sampler()
        self.assertEqual(summary['reason'], 'target_identity_changed')
        self.assertFalse(any(row['event'] == 'sample' for row in rows))

    def test_unreadable_affinity_and_unset_environment_are_explicit(self):
        (self.target / 'environ').write_bytes(b'DISPLAY=:123\0')
        with patch('linux_frame_sampler.os.sched_getaffinity', side_effect=PermissionError(errno.EACCES, 'denied')):
            summary, rows = self.run_sampler()
        self.assertTrue(summary['sampling_completed'])
        self.assertEqual(rows[0]['environment']['value']['LP_NUM_THREADS'], {'available': False, 'reason': 'not_set'})
        self.assertEqual(rows[1]['allowed_cpus']['errno'], errno.EACCES)
        self.assertFalse(rows[1]['allowed_cpus']['available'])

    def test_fresh_output_and_live_owned_identity_are_required(self):
        output = self.root / 'samples.jsonl'
        output.write_text('original failure')
        with self.assertRaises(FileExistsError):
            LinuxFrameSampler(self.process, output, self.observation, 1, proc=self.proc, cgroup_root=self.cgroup)
        self.assertEqual(output.read_text(), 'original failure')
        self.process.returncode = 0
        with self.assertRaises(ValueError):
            LinuxFrameSampler(self.process, self.root / 'other.jsonl', self.observation, 1, proc=self.proc, cgroup_root=self.cgroup)

    def test_nonfinite_or_extended_duration_is_rejected(self):
        for duration in (0, -1, 181, float('inf'), float('nan')):
            with self.subTest(duration=duration), self.assertRaises(ValueError):
                LinuxFrameSampler(self.process, self.root / 'samples.jsonl', self.observation, duration,
                                  proc=self.proc, cgroup_root=self.cgroup)

    def test_output_error_is_retained_and_worker_is_gone(self):
        with patch.object(LinuxFrameSampler, '_write', side_effect=OSError(errno.ENOSPC, 'disk full')):
            summary, rows = self.run_sampler()
        self.assertEqual(summary['reason'], 'output_error')
        self.assertFalse(summary['thread_alive'])
        self.assertEqual(summary['error']['errno'], errno.ENOSPC)
        self.assertEqual(rows, [])


class ControllerOptionTests(unittest.TestCase):
    def test_opt_in_rejects_other_scenarios_and_changed_budgets_before_launch(self):
        import verify_offline_match as controller
        for extra in ([], ['--timeout', '181'], ['--timeout', '180', '--scenario', 'defuse'],
                      ['--timeout', '180', '--seed', '43']):
            command = ['verify_offline_match.py', '--output', '/unused', '--scenario', 'plant', '--target', 'linux',
                       '--linux-frame-diagnostics', *extra]
            with self.subTest(extra=extra), patch('sys.argv', command), patch.object(controller.platform, 'system', return_value='Linux'), \
                    patch.object(controller.subprocess, 'Popen') as launch, self.assertRaises(SystemExit) as result:
                controller.main()
            self.assertEqual(result.exception.code, 2)
            launch.assert_not_called()

    def test_original_default_path_and_valid_opt_in_reach_existing_display_check(self):
        import verify_offline_match as controller
        for extra in (['--timeout', '181'], ['--linux-frame-diagnostics', '--timeout', '180']):
            command = ['verify_offline_match.py', '--output', '/unused', '--scenario', 'plant', '--target', 'linux',
                       '--xvfb', '', *extra]
            stderr = io.StringIO()
            with self.subTest(extra=extra), patch('sys.argv', command), patch('sys.stderr', stderr), \
                    patch.object(controller.platform, 'system', return_value='Linux'), \
                    patch.object(controller.subprocess, 'Popen') as launch, self.assertRaises(SystemExit):
                controller.main()
            self.assertIn('Supply Xvfb', stderr.getvalue())
            launch.assert_not_called()


if __name__ == '__main__':
    unittest.main()
