"""Independent pure adversarial controls; synthetic files and an inert owner only."""
import errno
import json
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'scripts'))
from linux_frame_sampler import LinuxFrameSampler, attempt, read_bytes


def proc_stat(pid=491, start=810, name='native ) (client)'):
    fields = ['S'] + ['0'] * 45
    fields[11], fields[12], fields[19] = '101', '23', str(start)
    return f"{pid} ({name}) {' '.join(fields)}\n".encode()


class Owner:
    pid = 491
    returncode = None

    def poll(self):
        return self.returncode


class IndependentControls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.proc = self.root / 'proc'
        self.target = self.proc / '491'
        self.target.mkdir(parents=True)
        (self.target / 'stat').write_bytes(proc_stat())
        (self.target / 'environ').write_bytes(b'DISPLAY=:100\0LP_NUM_THREADS=2\0ACCESS_TOKEN=hidden-marker\0')
        (self.target / 'task' / '491').mkdir(parents=True)
        (self.target / 'task' / '491' / 'stat').write_bytes(proc_stat())
        self.cgroup = self.root / 'cg'
        self.cgroup.mkdir()
        (self.target / 'cgroup').write_text('0::/\n')
        (self.cgroup / 'cpu.max').write_text('max 100000\n')
        (self.cgroup / 'cpu.stat').write_text('usage_usec 500\nuser_usec 400\nsystem_usec 100\n')
        self.observation = self.root / 'status.json'
        self.state = dict(schema=1, scope='debug_offline_read_only_observation', scenario='plant',
                          phase='buy', wall_msec=2345, elapsed=2.0, simulation_tick=120,
                          round_number=1, drawn_frames=15, time_scale=1,
                          actors=[{'access_token': 'hidden-marker'}])
        self.state['frame_diagnostics'] = {key: value for key, value in (
            ('read_begin_usec', 2345000), ('read_end_usec', 2345020),
            ('max_physics_steps_per_frame', 8), ('physics_ticks_per_second', 60),
            ('physics_jitter_fix', .5), ('max_fps', 60), ('process_frames', 15),
            ('physics_frames', 120), ('drawn_frames', 15),
            ('process_max_seconds_last_engine_window', .4),
            ('physics_step_max_seconds_last_engine_window', .002),
            ('draw_calls_last_rendered_frame', 400), ('primitives_last_rendered_frame', 120000),
            ('viewport_3d_scale', 1), ('viewport_visible_size', [1280, 720]),
            ('viewport_texture_size_pixels', [1280, 720]), ('access_token', 'hidden-marker'))}
        self.observation.write_text(json.dumps(self.state))
        self.owner = Owner()
        self.affinity = patch('linux_frame_sampler.os.sched_getaffinity', return_value={3, 5})
        self.affinity.start()
        self.addCleanup(self.affinity.stop)

    def sample(self, duration=.025):
        self.sampler = LinuxFrameSampler(self.owner, self.root / 'samples.jsonl', self.observation,
                                        duration, proc=self.proc, cgroup_root=self.cgroup)
        self.addCleanup(self.sampler.stop)
        self.sampler.thread.join(timeout=2)
        summary = self.sampler.stop()
        self.assertFalse(summary['thread_alive'])
        rows = [json.loads(line) for line in self.sampler.output.read_text().splitlines()]
        return summary, rows

    def test_identity_replaced_during_environment_discards_begin(self):
        original = LinuxFrameSampler._environment
        def replace(sampler):
            result = original(sampler)
            (self.target / 'stat').write_bytes(proc_stat(start=811))
            return result
        with patch.object(LinuxFrameSampler, '_environment', replace):
            summary, rows = self.sample()
        self.assertEqual(summary['reason'], 'target_identity_changed')
        self.assertFalse(summary['complete'])
        self.assertEqual([row['event'] for row in rows], ['end'])

    def test_identity_replaced_mid_sample_discards_entire_row(self):
        original = LinuxFrameSampler._threads
        def replace(sampler):
            result = original(sampler)
            (self.target / 'stat').write_bytes(proc_stat(start=811))
            return result
        with patch.object(LinuxFrameSampler, '_threads', replace):
            summary, rows = self.sample()
        self.assertEqual(summary['reason'], 'target_identity_changed')
        self.assertEqual(summary['samples_written'], 0)
        self.assertEqual([row['event'] for row in rows], ['begin', 'end'])

    def test_unavailable_counters_preserve_process_and_explicit_reasons(self):
        (self.target / 'task' / '491' / 'stat').unlink()
        (self.target / 'cgroup').unlink()
        with patch('linux_frame_sampler.os.sched_getaffinity', side_effect=PermissionError(errno.EPERM, 'hidden-marker')):
            summary, rows = self.sample()
        self.assertTrue(summary['complete'])
        row = next(row for row in rows if row['event'] == 'sample')
        self.assertEqual(row['process_cpu']['value'], dict(user_ticks=101, system_ticks=23, start_time_ticks=810))
        self.assertEqual(row['allowed_cpus']['errno'], errno.EPERM)
        self.assertFalse(row['cgroup_cpu']['available'])
        self.assertFalse(row['thread_cpu']['value']['threads'][0]['available'])
        self.assertNotIn('hidden-marker', json.dumps(rows))

    def test_partial_cgroup_fields_and_privacy_are_retained_honestly(self):
        summary, rows = self.sample()
        row = next(row for row in rows if row['event'] == 'sample')
        self.assertTrue(summary['complete'])
        self.assertEqual(rows[0]['environment']['LIBGL_ALWAYS_SOFTWARE']['reason'], 'not_set')
        fields = row['cgroup_cpu']['value'][0]['cpu_stat']['value']
        self.assertIn('nr_throttled', fields['unavailable_fields'])
        self.assertNotIn('nr_throttled', fields['counters'])
        self.assertNotIn('hidden-marker', json.dumps(rows))
        self.assertNotIn('actors', json.dumps(rows))
        self.assertEqual(row['offline_frame']['value']['frame_diagnostics']['internal_3d_target_size']['available'], False)

    def test_sample_write_failure_does_not_claim_complete(self):
        original = LinuxFrameSampler._write
        def fail_sample(sampler, row):
            if row['event'] == 'sample':
                raise OSError(errno.ENOSPC, 'hidden-marker')
            original(sampler, row)
        with patch.object(LinuxFrameSampler, '_write', fail_sample):
            summary, rows = self.sample()
        self.assertFalse(summary['complete'])
        self.assertEqual(summary['reason'], 'sampling_error')
        self.assertEqual(summary['error']['errno'], errno.ENOSPC)
        self.assertEqual(rows[-1]['event'], 'end')
        self.assertNotIn('hidden-marker', json.dumps(rows))

    def test_nonfinite_observation_is_unavailable_and_does_not_stop_cpu(self):
        self.state['frame_diagnostics']['process_frames'] = float('nan')
        self.observation.write_text(json.dumps(self.state))
        summary, rows = self.sample()
        self.assertTrue(summary['complete'])
        row = next(row for row in rows if row['event'] == 'sample')
        self.assertTrue(row['process_cpu']['available'])
        self.assertFalse(row['offline_frame']['available'])

    def test_read_bound_is_exact_and_excess_is_not_echoed(self):
        path = self.root / 'bounded'
        path.write_bytes(b'a' * 65536)
        self.assertEqual(len(read_bytes(path)), 65536)
        path.write_bytes(b'a' * 65537 + b'hidden-marker')
        result = attempt(lambda: read_bytes(path))
        self.assertEqual(result['reason'], 'read_bound_exceeded')
        self.assertNotIn('hidden-marker', json.dumps(result))

    def test_real_cadence_and_early_stop(self):
        sampler = LinuxFrameSampler(self.owner, self.root / 'samples.jsonl', self.observation,
                                    180, proc=self.proc, cgroup_root=self.cgroup)
        self.addCleanup(sampler.stop)
        time.sleep(1.08)
        started = time.monotonic()
        summary = sampler.stop()
        self.assertLess(time.monotonic() - started, .5)
        self.assertFalse(summary['thread_alive'])
        self.assertEqual(summary['reason'], 'controller_stop')
        samples = [json.loads(line) for line in sampler.output.read_text().splitlines()
                   if json.loads(line)['event'] == 'sample']
        self.assertEqual(len(samples), 2)
        self.assertGreaterEqual(samples[1]['monotonic_begin_ns'] - samples[0]['monotonic_begin_ns'], 1_000_000_000)


if __name__ == '__main__':
    unittest.main(verbosity=2)
