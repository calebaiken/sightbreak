"""Independent pure adversarial review; no Godot or native execution."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'scripts'))
import linux_profile_acquire as acquisition
import linux_profile_overhead as controller
from test_linux_profile_overhead import manual_expected, manual_record
import test_linux_profile_acquire as outer_controls


def synchronized_settings(row, key, value, delete=False):
    settings = row['fixture']['settings']
    if delete:
        settings.pop(key, None)
    else:
        settings[key] = value
    for name in ('fingerprint_initial', 'fingerprint_terminal'):
        content = json.loads(row['fixture'][name]['serialized'])
        content['settings'] = deepcopy(settings)
        serialized = json.dumps(content, sort_keys=True, separators=(',', ':'))
        row['fixture'][name] = {'serialized': serialized,
                                'sha256': hashlib.sha256(serialized.encode()).hexdigest()}


class IndependentControls(unittest.TestCase):
    def setUp(self):
        self.expected = manual_expected()

    def test_positive_complete_block_and_negative_one_condition_states(self):
        controller.evaluate([manual_record(i) for i in range(4)], self.expected)
        for index in range(4):
            for key in ('caller_is_main_thread', 'caller_is_render_thread'):
                rows = [manual_record(i) for i in range(4)]
                synchronized_settings(rows[index], key, False)
                with self.subTest(index=index, key=key), self.assertRaisesRegex(controller.Invalid, 'thread readback'):
                    controller.evaluate(rows, self.expected)

    def test_self_consistent_forged_thread_types_and_missing_fields_reject(self):
        for key in ('caller_is_main_thread', 'caller_is_render_thread'):
            for value in (False, None, 0, 1, 1.0, 'true', 'True', '1', [], {}, [True]):
                row = manual_record(0)
                synchronized_settings(row, key, value)
                with self.subTest(key=key, value=value), self.assertRaisesRegex(controller.Invalid, 'thread readback'):
                    controller.validate_condition(row, self.expected)
            row = manual_record(0)
            synchronized_settings(row, key, None, delete=True)
            with self.assertRaisesRegex(controller.Invalid, 'thread readback'):
                controller.validate_condition(row, self.expected)

    def test_inconsistent_inner_settings_reject_even_with_rehashed_fingerprint(self):
        for name in ('fingerprint_initial', 'fingerprint_terminal'):
            for key in ('caller_is_main_thread', 'caller_is_render_thread'):
                row = manual_record(0)
                content = json.loads(row['fixture'][name]['serialized'])
                content['settings'][key] = False
                serialized = json.dumps(content, sort_keys=True)
                row['fixture'][name] = {'serialized': serialized,
                    'sha256': hashlib.sha256(serialized.encode()).hexdigest()}
                with self.subTest(name=name, key=key), self.assertRaisesRegex(controller.Invalid, 'fingerprint'):
                    controller.validate_condition(row, self.expected)

    def test_fingerprint_thread_observations_reject_numeric_substitution(self):
        for key in ('caller_is_main_thread', 'caller_is_render_thread'):
            for value in (True, 1, 1.0):
                row = manual_record(0)
                for name in ('fingerprint_initial', 'fingerprint_terminal'):
                    content = json.loads(row['fixture'][name]['serialized'])
                    content['settings'][key] = value
                    serialized = json.dumps(content, sort_keys=True)
                    row['fixture'][name] = {'serialized': serialized,
                        'sha256': hashlib.sha256(serialized.encode()).hexdigest()}
                if value is True:
                    controller.validate_condition(row, self.expected)
                else:
                    with self.subTest(key=key, type=type(value).__name__), self.assertRaises(controller.Invalid):
                        controller.validate_condition(row, self.expected)

    def test_filtered_arguments_are_a_typed_readback_and_not_launch_authority(self):
        for value in ([], ['--arbitrary', '--render-thread', 'unsafe']):
            row = manual_record(0)
            row['fixture']['engine_arguments_filtered'] = value
            controller.validate_condition(row, self.expected)
        for value in (None, (), '', {}, [None], [1.0], [True], [['--render-thread']]):
            row = manual_record(0)
            row['fixture']['engine_arguments_filtered'] = value
            with self.subTest(value=value), self.assertRaisesRegex(controller.Invalid, 'filtered argument'):
                controller.validate_condition(row, self.expected)
        row = manual_record(0)
        del row['fixture']['engine_arguments_filtered']
        with self.assertRaisesRegex(controller.Invalid, 'filtered argument'):
            controller.validate_condition(row, self.expected)

    def test_full_argv_authorities_reject_synchronized_unsafe_and_flag_ambiguity(self):
        baseline = manual_record(0)['engine_argv']
        separator = baseline.index('--')
        mutations = []
        for mode in ('unsafe', 'separate', 'SAFE', ''):
            argv = deepcopy(baseline)
            argv[2] = mode
            mutations.append(argv)
        mutations += [baseline[:1] + baseline[3:],
                      baseline[:separator] + ['--render-thread', 'safe'] + baseline[separator:],
                      baseline[:1] + baseline[3:] + ['--render-thread', 'safe'],
                      baseline[:separator] + ['++'] + baseline[separator + 1:]]
        for argv in mutations:
            row = manual_record(0)
            row['engine_argv'] = deepcopy(argv)
            row['actual_cmdline'] = deepcopy(argv)
            row['process_argv'] = ['taskset', '-c', ','.join(map(str, self.expected['cpus'])), *argv]
            with self.subTest(argv=argv), self.assertRaisesRegex(controller.Invalid, 'Wrong flag'):
                controller.validate_condition(row, self.expected)

    def test_individual_actual_and_affinity_launch_are_independent(self):
        for name in ('actual_cmdline', 'process_argv'):
            row = manual_record(0)
            position = row[name].index('safe')
            row[name][position] = 'unsafe'
            with self.subTest(name=name), self.assertRaises(controller.Invalid):
                controller.validate_condition(row, self.expected)

    def test_project_mode_and_vsync_getter_remain_required(self):
        for mode in (0, 2, None, '1'):
            row = manual_record(0)
            synchronized_settings(row, 'thread_model_project', mode)
            with self.subTest(mode=mode), self.assertRaisesRegex(controller.Invalid, 'thread_model_project'):
                controller.validate_condition(row, self.expected)
        for value in (True, 1.0, None, '1'):
            row = manual_record(0)
            synchronized_settings(row, 'vsync_mode', value)
            with self.subTest(value=value), self.assertRaisesRegex(controller.Invalid, 'V-Sync getter'):
                controller.validate_condition(row, self.expected)

    def test_original_warning_rejects_at_real_outer_block_gate(self):
        outer_controls.BlockBindingTests().execute('valid')
        outer_controls.BlockBindingTests().execute('VSync')
        warning = 'WARNING: Could not set V-Sync mode, as changing V-Sync mode is not supported by the graphics driver.'
        self.assertEqual(acquisition.strict_log(warning), [warning])
        self.assertFalse(controller.native_log_failed(warning))

    def test_both_identity_bits_are_needed_by_pinned_semantics(self):
        # Truth table from independently fetched thread/server source, not runtime.
        states = []
        for caller in (1, 2):
            for server in (1, 2):
                main, render = caller == 1, caller == server
                states.append((caller, server, main and render))
        self.assertEqual(states, [(1, 1, True), (1, 2, False),
                                  (2, 1, False), (2, 2, False)])


if __name__ == '__main__':
    unittest.main()
