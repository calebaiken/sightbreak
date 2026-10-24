#!/usr/bin/env python3
"""Pure source/evidence controls; no engine invocation or runtime simulation claim."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import unittest

import linux_profile_acquire as acquire
import linux_profile_overhead as diagnostic
import test_linux_profile_acquire as acquisition_controls
from test_linux_profile_overhead import manual_expected, manual_record


EVIDENCE = diagnostic.ROOT / 'docs/reports/gauntlet/m1-linux-profile-acquisition/native-argument-readback-r1'


def pinned_parser_model(argv):
    """Only the consumed switches used by this actual launch, from pinned main.cpp.

    This is a source-derived model, never a recorded OS.get_cmdline_args() return.
    Unknown arguments remain visible; suffixes after --/++ are user arguments.
    """
    remaining, user = [], []
    separate = None
    index = 1
    while index < len(argv):
        token = argv[index]
        if token in ('--', '++'):
            user = argv[index + 1:]
            break
        if token == '--render-thread':
            mode = argv[index + 1]
            if mode not in ('safe', 'unsafe', 'separate'):
                raise ValueError('Unknown pinned render thread mode')
            separate = mode == 'separate'
            index += 2
        elif token in ('--audio-driver', '--accessibility', '--accessibility-driver'):
            index += 2
        elif token == '--gpu-profile':
            index += 1
        else:
            remaining.append(token)
            index += 1
    return remaining, user, separate


def old_guard(argv):
    if '--render-thread' not in argv:
        return False
    index = argv.index('--render-thread')
    return index + 1 < len(argv) and argv[index + 1] == 'safe'


class ReadbackControls(unittest.TestCase):
    def setUp(self):
        self.expected = manual_expected()

    def test_retained_actual_bytes_and_original_guard_are_pinned(self):
        identities = json.loads((EVIDENCE / 'retained-r3-identities.json').read_text())
        for name, wanted in identities.items():
            data = (EVIDENCE / 'retained-r3' / name).read_bytes()
            self.assertEqual({'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}, wanted)
        old = (EVIDENCE / 'retained-r3/fixture-ec6b34ce.gd').read_text()
        self.assertIn('var argv := OS.get_cmdline_args()', old)
        self.assertIn('argv.find("--render-thread")', old)
        self.assertIn('argv[thread_index + 1] != "safe"', old)
        log = (EVIDENCE / 'retained-r3/native-block/01-/off/client.log').read_text()
        self.assertIn('Pinned synchronous safe render-thread argument required', log)
        self.assertIn('linux_profile_overhead.gd:270', log)
        self.assertTrue(acquire.strict_log(log))
        self.assertTrue(diagnostic.native_log_failed(log))

    def test_pinned_parser_model_rejects_old_guard_for_exact_actual_launch(self):
        launch = json.loads((EVIDENCE / 'retained-r3/native-block/01-/off/launch.json').read_text())
        argv = launch['engine_argv']
        self.assertTrue(old_guard(argv))
        filtered, user, separate = pinned_parser_model(argv)
        self.assertEqual(filtered, [])
        self.assertFalse(old_guard(filtered))
        self.assertFalse(separate)
        self.assertEqual(user, ['--output=' + launch['output'], '--token=' + launch['token']])
        on = deepcopy(argv)
        on.insert(1, '--gpu-profile')
        self.assertEqual(pinned_parser_model(on), (filtered, user, separate))

    def test_pinned_source_consumption_and_effective_thread_api_are_retained(self):
        source = json.loads((EVIDENCE / 'pinned-godot-excerpts.json').read_text())
        self.assertEqual(source['commit'], 'ed1daf0bf001b61586d9930840f2f1394092c079')
        excerpts = {(row['path'], row['first_line']): row['text'] for row in source['excerpts']}
        consumed = excerpts['main/main.cpp', 1570]
        self.assertIn('N->get() == "safe"', consumed)
        self.assertIn('separate_thread_render = 0;', consumed)
        self.assertIn('N->get() == "separate"', consumed)
        self.assertIn('separate_thread_render = 1;', consumed)
        self.assertNotIn('main_args.push_back', consumed)
        self.assertIn('set_cmdline(execpath, main_args, user_args)', excerpts['main/main.cpp', 2250])
        self.assertIn('server_thread = Thread::MAIN_ID;', excerpts['servers/rendering/rendering_server_default.cpp', 276])
        self.assertIn('server_thread = Thread::get_caller_id();', excerpts['servers/rendering/rendering_server_default.cpp', 400])
        self.assertIn('return Thread::get_caller_id() == server_thread;', excerpts['servers/rendering/rendering_server_default.h', 1212])
        self.assertIn('D_METHOD("is_on_render_thread")', excerpts['servers/rendering/rendering_server.cpp', 3577])
        self.assertIn('D_METHOD("get_main_thread_id")', excerpts['core/core_bind.cpp', 849])

    def test_effective_readbacks_require_both_true_booleans(self):
        diagnostic.validate_condition(manual_record(0), self.expected)
        for key in ('caller_is_main_thread', 'caller_is_render_thread'):
            for invalid in (False, None, 0, 1, 'true', [], {}):
                with self.subTest(key=key, invalid=invalid):
                    row = manual_record(0)
                    row['fixture']['settings'][key] = invalid
                    with self.assertRaisesRegex(diagnostic.Invalid, 'thread readback'):
                        diagnostic.validate_condition(row, self.expected)
            row = manual_record(0)
            del row['fixture']['settings'][key]
            with self.assertRaisesRegex(diagnostic.Invalid, 'thread readback'):
                diagnostic.validate_condition(row, self.expected)
        snapshots = ('fingerprint_initial', 'fingerprint_terminal')
        for key in ('caller_is_main_thread', 'caller_is_render_thread'):
            for names in ((snapshots[0],), (snapshots[1],), snapshots):
                for invalid in (False, None, 0, 1, 1.0, 'true', [], {}, '__missing__'):
                    with self.subTest(key=key, snapshots=names, invalid=invalid):
                        row = manual_record(0)
                        for name in names:
                            content = json.loads(row['fixture'][name]['serialized'])
                            if invalid == '__missing__':
                                del content['settings'][key]
                            else:
                                content['settings'][key] = invalid
                            serialized = json.dumps(content, sort_keys=True)
                            row['fixture'][name] = {'serialized': serialized,
                                'sha256': hashlib.sha256(serialized.encode()).hexdigest()}
                        with self.assertRaisesRegex(diagnostic.Invalid, 'fingerprint thread readback'):
                            diagnostic.validate_condition(row, self.expected)
            # Both snapshots can retain real boolean true under rebuilt hashes.
            row = manual_record(0)
            for name in snapshots:
                content = json.loads(row['fixture'][name]['serialized'])
                content['settings'][key] = True
                serialized = json.dumps(content, sort_keys=True)
                row['fixture'][name] = {'serialized': serialized,
                    'sha256': hashlib.sha256(serialized.encode()).hexdigest()}
            diagnostic.validate_condition(row, self.expected)

    def test_full_argv_preserves_explicit_safe_intent_even_when_state_matches(self):
        # unsafe maps to the same engine state; only exact full argv can reject it.
        for mode in ('unsafe', 'separate'):
            row = manual_record(0)
            for key in ('engine_argv', 'actual_cmdline'):
                row[key][2] = mode
            row['process_argv'][5] = mode
            with self.subTest(mode=mode), self.assertRaisesRegex(diagnostic.Invalid, 'Wrong flag'):
                diagnostic.validate_condition(row, self.expected)
        original = manual_record(0)['engine_argv']
        mutations = [original[:1] + original[3:], original[:1] + ['safe', '--render-thread'] + original[3:],
                     original[:3] + ['--render-thread', 'safe'] + original[3:],
                     original[:1] + original[3:] + ['--render-thread', 'safe']]
        for mutated in mutations:
            row = manual_record(0)
            row.update(engine_argv=deepcopy(mutated), actual_cmdline=deepcopy(mutated),
                       process_argv=['taskset', '-c', '2,3', *mutated])
            with self.subTest(argv=mutated), self.assertRaisesRegex(diagnostic.Invalid, 'Wrong flag'):
                diagnostic.validate_condition(row, self.expected)

    def test_actual_cmdline_and_project_mode_still_fail_independently(self):
        row = manual_record(0)
        row['actual_cmdline'][2] = 'unsafe'
        with self.assertRaisesRegex(diagnostic.Invalid, 'Actual owned command'):
            diagnostic.validate_condition(row, self.expected)
        for mode in (0, 2):
            row = manual_record(0)
            row['fixture']['settings']['thread_model_project'] = mode
            with self.subTest(mode=mode), self.assertRaisesRegex(diagnostic.Invalid, 'thread_model_project'):
                diagnostic.validate_condition(row, self.expected)

    def test_filtered_readback_is_observed_and_not_used_as_full_argv(self):
        for observed in ([], ['--unknown']):
            row = manual_record(0)
            row['fixture']['engine_arguments_filtered'] = observed
            diagnostic.validate_condition(row, self.expected)
        for observed in (None, {}, '', [1], [True]):
            row = manual_record(0)
            row['fixture']['engine_arguments_filtered'] = observed
            with self.subTest(observed=observed), self.assertRaisesRegex(diagnostic.Invalid, 'filtered argument'):
                diagnostic.validate_condition(row, self.expected)

    def test_vsync_warning_remains_a_strict_blocker_without_argument_error(self):
        warning = 'WARNING: Could not set V-Sync mode, as changing V-Sync mode is not supported by the graphics driver.\n'
        self.assertEqual(acquire.strict_log(warning), [warning.rstrip()])
        # The existing standalone error/leak gate does not scan warnings. The
        # unchanged outer acquisition gate is the strict warning authority.
        self.assertFalse(diagnostic.native_log_failed(warning))
        row = manual_record(0)
        row['stdout'] = warning
        diagnostic.validate_condition(row, self.expected)
        acquisition_controls.BlockBindingTests().execute('VSync')

    def test_hash_pins_and_fresh_r4_are_explicit(self):
        self.assertEqual(acquire.OUTPUT.name, 'linux-profile-acquisition-r4')
        for name, wanted in acquire.ACCEPTED.items():
            self.assertEqual(diagnostic.digest(diagnostic.ROOT / name), wanted)


if __name__ == '__main__':
    unittest.main()
