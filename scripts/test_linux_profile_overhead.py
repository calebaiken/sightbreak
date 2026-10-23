#!/usr/bin/env python3
"""Hand-authored synthetic cadence records and mocked real controller decisions."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from contextlib import ExitStack

import linux_profile_overhead as diagnostic


def manual_report(token, measured_usec=20000, warm_usec=20000):
    """Independent positive data: explicit endpoint sequence, no evaluator result reuse."""
    fingerprint = json.dumps({'source_ledger_sha256': 'ledger', 'nodes': [
        {'path': 'world/0', 'class': 'RelayYard', 'mesh_content': 'mesh', 'shader_parameters': {'roughness': 0.94}},
        {'path': 'world/1', 'class': 'Camera3D', 'transform': [-14, 1.62, -18], 'fov': 82},
    ]}, sort_keys=True)
    fp = {'serialized': fingerprint, 'sha256': hashlib.sha256(fingerprint.encode()).hexdigest()}
    report = {'schema': 1, 'token': token, 'source_ledger_sha256': 'ledger',
              'settings': {'viewport': [1280, 720], 'texture_size': [1280, 720], 'msaa_3d': 1,
                           'render_scale': 1.0, 'scaling_3d_mode': 0, 'max_fps': 60, 'physics_hz': 60, 'physics_limit': 8,
                           'jitter_fix': 0.5, 'time_scale': 1.0, 'thread_model_project': 1,
                           'thread_mode_argument': 'safe', 'print_profile_setting': False, 'vsync_mode': 1},
              'engine': {'major': 4, 'minor': 7, 'patch': 2, 'status': 'stable', 'hash': 'ed1daf0bf001'},
              'adapter': {'name': 'Mesa llvmpipe', 'vendor': 'Mesa', 'api': 'OpenGL 4.5 Mesa'},
              'workload': {'actors': 5, 'view': 'approach', 'static': True, 'authority_ticks': 0, 'visual_ticks': 0},
              'fingerprint_initial': deepcopy(fp), 'fingerprint_terminal': deepcopy(fp), 'png_sha256': 'a' * 64,
              'cold_before': {'clock_usec': 1000, 'counter': 10, 'callback': 1},
              'anchor': {'clock_usec': 2000, 'counter': 10, 'callback': 2}}
    previous = report['anchor']
    for name, count, duration in [('warm', 32, warm_usec), ('measured', 64, measured_usec)]:
        rows = []
        for index in range(count):
            delta = duration[index] if isinstance(duration, list) else duration
            end = {'clock_usec': previous['clock_usec'] + delta, 'counter': previous['counter'] + 1,
                   'callback': previous['callback'] + 1}
            rows.append({'begin': deepcopy(previous), 'end': deepcopy(end), 'draw_calls': 400, 'primitives': 100000})
            previous = end
        report[name] = rows
    report['readback'] = {'clock_usec': previous['clock_usec'] + 20000,
                          'counter': previous['counter'] + 1, 'callback': previous['callback'] + 1}
    report['readback_after'] = {**report['readback'], 'clock_usec': report['readback']['clock_usec'] + 5000}
    content = json.loads(fingerprint)
    content['settings'] = report['settings']
    text = json.dumps(content, sort_keys=True)
    for key in ('fingerprint_initial', 'fingerprint_terminal'):
        report[key] = {'serialized': text, 'sha256': hashlib.sha256(text.encode()).hexdigest()}
    return report


def manual_record(index, payload='payload', duration=20000):
    profile = index in (1, 2)
    output, token = f'/synthetic/{index}', f'token-{index}'
    argv = ['/fixture'] + (['--gpu-profile'] if profile else []) + [
        '--render-thread', 'safe', '--audio-driver', 'Dummy', '--accessibility', 'disabled',
        '--accessibility-driver', 'dummy', '--', '--output=' + output, '--token=' + token]
    host = {'affinity': [2, 3], 'quota': '200000 100000', 'cgroup_path': '/synthetic/cgroup',
            'driver_libraries': {'/synthetic/libgallium.so': 'driver'},
            'throttling': {'nr_throttled': 1, 'throttled_usec': 2}}
    selected = {'DISPLAY': ':99108', 'LIBGL_ALWAYS_SOFTWARE': '1', 'LP_NUM_THREADS': '2',
                'XDG_DATA_HOME': output + '/state/data', 'XDG_CONFIG_HOME': output + '/state/config',
                'XDG_CACHE_HOME': output + '/state/cache', 'MESA_SHADER_CACHE_DIR': output + '/state/mesa'}
    return {'index': index, 'profile': profile, 'output': output, 'token': token, 'engine_argv': argv,
            'process_argv': ['taskset', '-c', '2,3', *argv], 'timeout': False, 'exit_code': 0,
            'actual_cmdline': deepcopy(argv), 'selected_environment': selected,
            'actual_environment': deepcopy(selected),
            'cleanup': {'pid_absent': True, 'group_absent': True, 'forced': False},
            'payload_before': payload, 'payload_after': payload, 'seal_sha256': 'seal',
            'cache_initial': {'paths': {'data': output + '/state/data', 'config': output + '/state/config',
                                       'cache': output + '/state/cache', 'mesa': output + '/state/mesa'}, 'empty': True},
            'host_begin': deepcopy(host), 'host_end': deepcopy(host),
            'rusage': {'user_seconds': 4, 'system_seconds': 1},
            'stdout': 'GPU PROFILE (total 20ms): \n\t-Render Opaque Pass: 18ms\n' if profile else 'Godot fixture\n',
            'fixture': manual_report(token, measured_usec=duration)}


def manual_expected(payload='payload', executable='/fixture'):
    return {'executable': executable, 'payload_sha256': payload, 'seal_sha256': 'seal', 'source_ledger_sha256': 'ledger',
            'cpus': [2, 3], 'display': ':99108', 'quota': '200000 100000', 'cgroup_path': '/synthetic/cgroup',
            'driver_libraries': {'/synthetic/libgallium.so': 'driver'}}


class EvaluatorTests(unittest.TestCase):
    def setUp(self):
        self.rows = [manual_record(index) for index in range(4)]
        self.expected = manual_expected()

    def test_hand_authored_valid_four_record_block_uses_even_median(self):
        result = diagnostic.evaluate(self.rows, self.expected)
        self.assertEqual(result['paired_median_ratios'], [1, 1])
        self.assertEqual(result['outcome'], 'block_did_not_resolve_a_10_percent_median_cadence_increase')
        self.assertEqual(result['conditions'][0]['cadence_total_ms'], 1280)
        self.assertEqual(diagnostic.median([1, 2, 8, 20]), 5)

    def test_ratio_boundaries_and_all_three_outcomes(self):
        for ratios, outcome in [((1.10, 1.10), 'flag_associated'), ((0.90, 0.90), 'block_did_not'),
                                ((1.099, 1.099), 'block_did_not'), ((0.899, 0.899), 'unresolved'),
                                ((1.11, 1.08), 'unresolved')]:
            rows = [manual_record(0), manual_record(1, duration=20000 * ratios[0]),
                    manual_record(2, duration=20000 * ratios[1]), manual_record(3)]
            with self.subTest(ratios=ratios):
                self.assertTrue(diagnostic.evaluate(rows, self.expected)['outcome'].startswith(outcome))

    def test_sparse_stall_survives_in_total_mean_and_tail_when_median_is_small(self):
        for index in (1, 2):
            self.rows[index]['fixture'] = manual_report(self.rows[index]['token'], [20000] * 63 + [260000])
        result = diagnostic.evaluate(self.rows, self.expected)
        self.assertEqual(result['paired_median_ratios'], [1, 1])
        self.assertEqual(result['descriptive_secondary_ratios']['cadence_mean_ms'], [1.1875, 1.1875])
        self.assertEqual(result['conditions'][1]['largest_interval_ms'], 260)
        self.assertEqual(result['conditions'][1]['samples_ms_in_order'][-1], 260)

    def test_declared_drift_and_warm_boundaries(self):
        self.rows[3] = manual_record(3, duration=21000)
        self.rows[0]['fixture'] = manual_report(self.rows[0]['token'], warm_usec=[20000] * 16 + [22000] * 16)
        diagnostic.evaluate(self.rows, self.expected)
        self.rows[3] = manual_record(3, duration=21001)
        with self.assertRaisesRegex(diagnostic.Invalid, 'OFF drift'):
            diagnostic.evaluate(self.rows, self.expected)
        self.rows[3] = manual_record(3)
        self.rows[0]['fixture'] = manual_report(self.rows[0]['token'], warm_usec=[20000] * 16 + [22001] * 16)
        with self.assertRaisesRegex(diagnostic.Invalid, 'Warm-up'):
            diagnostic.evaluate(self.rows, self.expected)

    def reject(self, change):
        rows = deepcopy(self.rows)
        change(rows)
        with self.assertRaises((diagnostic.Invalid, KeyError, TypeError, ValueError)):
            diagnostic.evaluate(rows, self.expected)

    def test_command_treatment_controls_reject(self):
        def late(rows):
            row = rows[1]
            row['engine_argv'].remove('--gpu-profile')
            row['engine_argv'].append('--gpu-profile')
        self.reject(late)
        self.reject(lambda rows: rows[0]['engine_argv'].insert(1, '--gpu-profile'))
        self.reject(lambda rows: rows[1].update(profile=False))
        self.reject(lambda rows: rows[0]['fixture']['settings'].update(print_profile_setting=True))
        self.reject(lambda rows: rows[0].update(stdout='GPU PROFILE (total 0ms): \n'))
        self.reject(lambda rows: rows[0].update(stdout='GPU PROFILE malformed synthetic output\n'))
        self.reject(lambda rows: rows[1].update(stdout='Godot fixture\n'))
        self.reject(lambda rows: rows[1].update(stdout='GPU PROFILE (total 0ms): \n'))
        self.reject(lambda rows: rows[1].update(stdout='ERROR: synthetic error\n' + rows[1]['stdout']))

    def test_same_work_source_payload_driver_cpu_cache_and_pixel_controls_reject(self):
        changes = [lambda rows: rows[1]['fixture']['settings'].update(render_scale=0.75),
                   lambda rows: rows[1].update(payload_before='different'),
                   lambda rows: rows[1].update(payload_after='different'),
                   lambda rows: rows[1].update(seal_sha256='different'),
                   lambda rows: rows[1]['fixture'].update(source_ledger_sha256='different'),
                   lambda rows: rows[1]['host_end']['driver_libraries'].update(other='different'),
                   lambda rows: rows[1]['host_begin'].update(affinity=[0, 1]),
                   lambda rows: rows[1]['host_end'].update(quota='100000 100000'),
                   lambda rows: rows[1]['fixture'].update(png_sha256='b' * 64),
                   lambda rows: rows[1]['fixture']['fingerprint_terminal'].update(sha256='b' * 64),
                   lambda rows: rows[1]['cache_initial'].update(empty=False),
                   lambda rows: rows[1]['cache_initial']['paths'].update(mesa='/reused'),
                   lambda rows: rows[1]['fixture']['workload'].update(visual_ticks=1)]
        for change in changes:
            with self.subTest(change=changes.index(change)):
                self.reject(change)
        changed = deepcopy(self.rows)
        new = json.dumps({'source_ledger_sha256': 'ledger', 'nodes': [{'different': True}], 'settings': changed[1]['fixture']['settings']})
        for key in ('fingerprint_initial', 'fingerprint_terminal'):
            changed[1]['fixture'][key] = {'serialized': new, 'sha256': hashlib.sha256(new.encode()).hexdigest()}
        with self.assertRaisesRegex(diagnostic.Invalid, 'Cross-condition'):
            diagnostic.evaluate(changed, self.expected)

    def test_incomplete_counter_callback_and_numerical_mutations_reject(self):
        self.reject(lambda rows: rows.pop())
        self.reject(lambda rows: rows[0]['fixture']['measured'].pop())
        self.reject(lambda rows: rows[0]['fixture']['warm'].pop())
        self.reject(lambda rows: rows[0]['fixture']['measured'][0]['end'].update(counter=42))
        self.reject(lambda rows: rows[0]['fixture']['measured'][0]['end'].update(counter=44))
        self.reject(lambda rows: rows[0]['fixture']['measured'][0]['end'].update(counter=42.0))
        self.reject(lambda rows: rows[0]['fixture']['measured'][0]['end'].update(callback=42))
        self.reject(lambda rows: rows[0]['fixture']['anchor'].update(counter=11))
        self.reject(lambda rows: rows[0]['fixture']['readback'].update(counter=4000))
        self.reject(lambda rows: rows[0]['fixture']['readback_after'].update(callback=4000))
        self.reject(lambda rows: rows[0]['fixture']['measured'][0].update(draw_calls=500))
        for value in (float('nan'), float('inf'), 0, -100):
            self.reject(lambda rows, value=value: rows[0]['fixture']['measured'][0]['end'].update(clock_usec=value))

    def test_incomplete_timeout_throttling_missing_readback_and_cleanup_reject(self):
        self.reject(lambda rows: rows[1].update(timeout=True))
        self.reject(lambda rows: rows[1].update(exit_code=-15))
        self.reject(lambda rows: rows[1]['host_end']['throttling'].update(throttled_usec=3))
        self.reject(lambda rows: rows[1]['host_end']['throttling'].pop('nr_throttled'))
        self.reject(lambda rows: rows[1]['cleanup'].update(group_absent=False))
        self.reject(lambda rows: rows[1]['cleanup'].update(forced=True))


class SyntheticRunner:
    display = ':99108'

    def __init__(self, fail_index=None):
        self.started = self.stopped = False
        self.commands = []
        self.fail_index = fail_index

    def start(self):
        self.started = True

    def stop(self):
        self.stopped = True
        return {'pid_absent': True, 'group_absent': True, 'forced': True}

    def condition(self, actual, environment):
        self.commands.append(deepcopy(actual))
        index = actual['index']
        require_keys = {'DISPLAY', 'LIBGL_ALWAYS_SOFTWARE', 'LP_NUM_THREADS', 'XDG_DATA_HOME',
                        'XDG_CONFIG_HOME', 'XDG_CACHE_HOME', 'MESA_SHADER_CACHE_DIR'}
        assert require_keys <= environment.keys()
        for path in actual['cache_initial']['paths'].values():
            assert Path(path).is_dir() and not any(Path(path).iterdir())
        fixture = manual_record(index, payload=actual['payload_before'])
        fixture['fixture']['token'] = actual['token']
        fixture.update(actual)
        fixture['actual_cmdline'] = actual['engine_argv']
        fixture['actual_environment'] = actual['selected_environment']
        fixture['payload_after'] = actual['payload_before']
        if index == self.fail_index:
            fixture['timeout'] = True
        return fixture


class ControllerTests(unittest.TestCase):
    def test_staging_is_an_explicit_overlay_and_does_not_edit_base_game(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'game/tests').mkdir(parents=True)
            original = '[application]\nrun/main_scene="res://main.tscn"\n[rendering]\nrenderer/rendering_method="gl_compatibility"\n'
            (root / 'game/project.godot').write_text(original)
            (root / 'game/export_presets.cfg').write_text('include_filter=""\n')
            (root / 'game/keep.txt').write_text('immutable source')
            (root / 'game/tests/no.gd').write_text('excluded test fixture')
            paths = b'game/project.godot\0game/export_presets.cfg\0game/keep.txt\0game/tests/no.gd\0'
            with patch.object(diagnostic, 'ROOT', root), patch.object(diagnostic, 'source_identity', return_value={'fixture_sha256': 'fixture', 'scene_sha256': 'scene'}), \
                    patch.object(diagnostic.subprocess, 'check_output', return_value=paths), \
                    patch.object(diagnostic.subprocess, 'Popen', side_effect=AssertionError('No native process permitted')):
                result = diagnostic.stage(root / 'stage')
            self.assertEqual((root / 'game/project.godot').read_text(), original)
            staged = (root / 'stage/project.godot').read_text()
            self.assertIn('settings/stdout/print_gpu_profile=false', staged)
            self.assertIn('driver/threads/thread_model=1', staged)
            self.assertFalse((root / 'stage/tests').exists())
            self.assertEqual((root / 'stage/keep.txt').read_text(), 'immutable source')
            self.assertIn('diagnostics/source_ledger.json', result['files'])

    def test_real_controller_launches_exact_order_and_isolated_states_using_mock_runner(self):
        with tempfile.TemporaryDirectory() as temporary, patch.object(diagnostic.subprocess, 'Popen', side_effect=AssertionError('No native process permitted')):
            executable = Path(temporary) / 'fixture'
            executable.write_bytes(b'handwritten mock payload, never executed')
            expected = manual_expected(diagnostic.digest(executable), str(executable))
            runner = SyntheticRunner()
            result = diagnostic.run_block(expected, Path(temporary) / 'block', [2, 3], runner)
            self.assertTrue(result['passed'], result.get('error'))
            self.assertTrue(runner.started and runner.stopped)
            self.assertEqual([row['profile'] for row in runner.commands], [False, True, True, False])
            self.assertEqual([row['engine_argv'].count('--gpu-profile') for row in runner.commands], [0, 1, 1, 0])
            for row in runner.commands:
                command = row['engine_argv']
                if row['profile']:
                    self.assertLess(command.index('--gpu-profile'), command.index('--'))
            self.assertEqual(len({row['cache_initial']['paths']['mesa'] for row in runner.commands}), 4)

    def test_real_controller_stops_immediately_after_incomplete_condition_and_still_cleans(self):
        with tempfile.TemporaryDirectory() as temporary, patch.object(diagnostic.subprocess, 'Popen', side_effect=AssertionError('No native process permitted')):
            executable = Path(temporary) / 'fixture'
            executable.write_bytes(b'mock payload')
            runner = SyntheticRunner(fail_index=1)
            result = diagnostic.run_block(manual_expected(diagnostic.digest(executable), str(executable)),
                                          Path(temporary) / 'block', [2, 3], runner)
            self.assertFalse(result['passed'])
            self.assertEqual(len(runner.commands), 2)
            self.assertTrue(runner.stopped)
            self.assertIn('Timeout', result['error'])

    def test_changed_payload_rejects_before_start_or_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            executable = Path(temporary) / 'fixture'
            executable.write_bytes(b'mock payload')
            runner = SyntheticRunner()
            output = Path(temporary) / 'block'
            with self.assertRaisesRegex(diagnostic.Invalid, 'before launch'):
                diagnostic.run_block(manual_expected('wrong', str(executable)), output, [2, 3], runner)
            self.assertFalse(runner.started)
            self.assertFalse(output.exists())


class NativeRunnerMockTests(unittest.TestCase):
    """Exercise NativeRunner's actual Popen/handshake/stop path using fake processes."""
    def execute(self, temporary, timeout=False):
        root = Path(temporary)
        executable = root / 'payload'
        executable.write_bytes(b'fake native payload, never executed')
        expected = manual_expected(diagnostic.digest(executable), str(executable))
        registry = {}

        class Process:
            def __init__(self, args, pid):
                self.args, self.pid, self.returncode = args, pid, None

            def poll(self):
                return self.returncode

            def wait(self, **_kwargs):
                if self.returncode is None:
                    self.returncode = 0
                return self.returncode

        def launch(argv, **kwargs):
            process = Process(argv, 99100 + len(registry))
            registry[process.pid] = (process, kwargs)
            if argv[0] != '/fake-xvfb' and not timeout:
                output = Path(kwargs['cwd'])
                token = next(arg[8:] for arg in argv if arg.startswith('--token='))
                report = manual_report(token)
                proof = b'identical synthetic pixels'
                (output / 'proof.png').write_bytes(proof)
                report['png_sha256'] = hashlib.sha256(proof).hexdigest()
                diagnostic.write(output / 'ready.json', {'token': token})
                diagnostic.write(output / 'metrics.json', report)
                kwargs['stdout'].write(b'GPU PROFILE (total 20ms): \n\t-Render Opaque Pass: 18ms\n'
                                       if '--gpu-profile' in argv else b'Godot synthetic OFF\n')
            return process

        actual_exists = Path.exists

        def socket_ready(path):
            return bool(registry) if str(path) == '/tmp/.X11-unix/X99108' else actual_exists(path)

        def gone(pid, group=False):
            return registry[pid][0].returncode is not None

        def stop_group(pid, signum):
            registry[abs(pid)][0].returncode = -int(signum)

        def observed(pid, keys):
            process, kwargs = registry[pid]
            return process.args[3:], {key: kwargs['env'][key] for key in keys}

        host = manual_record(0)['host_begin']
        with ExitStack() as stack:
            stack.enter_context(patch.object(diagnostic.subprocess, 'Popen', side_effect=launch))
            stack.enter_context(patch.object(diagnostic, 'pid_start', side_effect=lambda pid: pid * 2))
            stack.enter_context(patch.object(diagnostic, 'owned_launch_state', side_effect=observed))
            stack.enter_context(patch.object(diagnostic, 'host_snapshot', side_effect=lambda pid: deepcopy(host)))
            stack.enter_context(patch.object(diagnostic, 'cgroup_snapshot', side_effect=lambda pid: deepcopy(host)))
            stack.enter_context(patch.object(diagnostic, 'absent', side_effect=gone))
            stack.enter_context(patch.object(diagnostic.os, 'killpg', side_effect=stop_group))
            stack.enter_context(patch.object(Path, 'exists', socket_ready))
            if timeout:
                stack.enter_context(patch.object(diagnostic.time, 'monotonic', side_effect=[0, 0, 181]))
            output = root / 'block'
            runner = diagnostic.NativeRunner('/fake-xvfb', ':99108', output)
            result = diagnostic.run_block(expected, output, [2, 3], runner)
        return result, registry

    def test_real_native_runner_uses_popen_arguments_and_handshakes_without_processes(self):
        with tempfile.TemporaryDirectory() as temporary:
            result, registry = self.execute(temporary)
            self.assertTrue(result['passed'], result.get('error'))
            self.assertEqual(len(registry), 5)
            self.assertTrue(all(row[0].returncode is not None for row in registry.values()))
            self.assertEqual([row['actual_cmdline'] for row in result['records']],
                             [row['engine_argv'] for row in result['records']])
            self.assertTrue(all(Path(row['output'], 'begin.ack').is_file() and
                                Path(row['output'], 'finish.ack').is_file() for row in result['records']))

    def test_real_native_runner_times_out_and_stops_block_without_next_launch(self):
        with tempfile.TemporaryDirectory() as temporary:
            result, registry = self.execute(temporary, timeout=True)
            self.assertFalse(result['passed'])
            self.assertEqual(len(registry), 2)
            self.assertEqual(len(result['records']), 1)
            self.assertTrue(result['records'][0]['timeout'])
            self.assertTrue(result['records'][0]['cleanup']['forced'])
            self.assertTrue(result['xvfb_cleanup']['pid_absent'])


if __name__ == '__main__':
    unittest.main()
