#!/usr/bin/env python3
"""Pure admission and initial-command checks; never start native processes."""
from contextlib import ExitStack, redirect_stderr, redirect_stdout
import hashlib
import io
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import verify_offline_match as controller


class LinuxGpuProfileTests(unittest.TestCase):
    def test_rejects_other_scenarios_seeds_budgets_and_sampler_before_side_effects(self):
        for extra in ([], ['--timeout', '179'], ['--timeout', '181'],
                      ['--timeout', '180', '--scenario', 'defuse'],
                      ['--timeout', '180', '--scenario', 'full-match'],
                      ['--timeout', '180', '--seed', '43'],
                      ['--timeout', '180', '--linux-frame-diagnostics'],
                      ['--timeout', '180', '--target', 'windows']):
            with self.subTest(extra=extra), tempfile.TemporaryDirectory() as temporary:
                out = Path(temporary) / 'must-not-exist'
                argv = ['verify_offline_match.py', '--output', str(out), '--scenario', 'plant',
                        '--target', 'linux', '--linux-gpu-profile', *extra]
                with patch('sys.argv', argv), patch.object(controller.platform, 'system', return_value='Linux'), \
                        patch.object(controller.subprocess, 'Popen') as launch, \
                        patch.object(controller, 'source') as source, redirect_stderr(io.StringIO()), \
                        self.assertRaises(SystemExit) as rejected:
                    controller.main()
                self.assertEqual(rejected.exception.code, 2)
                launch.assert_not_called()
                source.assert_not_called()
                self.assertFalse(out.exists())

    def test_non_native_host_rejects_before_side_effects(self):
        argv = ['verify_offline_match.py', '--output', '/unused', '--scenario', 'plant',
                '--target', 'linux', '--timeout', '180', '--linux-gpu-profile']
        with patch('sys.argv', argv), patch.object(controller.platform, 'system', return_value='Darwin'), \
                patch.object(controller.subprocess, 'Popen') as launch, redirect_stderr(io.StringIO()), \
                self.assertRaises(SystemExit) as rejected:
            controller.main()
        self.assertEqual(rejected.exception.code, 2)
        launch.assert_not_called()

    def test_initial_engine_option_and_default_command_with_no_sampler(self):
        for extra in ([], ['--linux-gpu-profile'], ['--linux-gpu-profile', '--seed', '42']):
            with self.subTest(extra=extra), tempfile.TemporaryDirectory() as temporary, ExitStack() as stack:
                root = Path(temporary)
                out, executable = root / 'output', root / 'fixture-executable'
                executable.write_bytes(b'pure controller fixture, never executed')
                digest = hashlib.sha256(executable.read_bytes()).hexdigest()
                commands = []

                def intercept(command, **_kwargs):
                    commands.append(command)
                    return SimpleNamespace(pid=987000 + len(commands), returncode=0,
                                           poll=lambda: None, wait=lambda **_kwargs: 0)

                exists = Path.exists

                def display_ready(path):
                    if str(path) == '/tmp/.X11-unix/X99107':
                        return bool(commands)
                    return exists(path)

                ui = Mock()
                ui.focus_game.side_effect = RuntimeError('pure interception at initial menu')
                ui.diagnostics.return_value = {}
                argv = ['verify_offline_match.py', '--output', str(out), '--scenario', 'plant',
                        '--target', 'linux', '--timeout', '180', '--display', ':99107',
                        '--xvfb', '/pure-xvfb', '--executable', str(executable), *extra]
                stack.enter_context(patch('sys.argv', argv))
                stack.enter_context(patch.object(controller.platform, 'system', return_value='Linux'))
                stack.enter_context(patch.object(controller.platform, 'platform', return_value='pure-Linux-fixture'))
                stack.enter_context(patch.object(controller, 'source', return_value={'fixture': True}))
                stack.enter_context(patch.object(controller, 'validate_record', return_value={'artifact': {'sha256': digest}}))
                engine = stack.enter_context(patch.object(controller.toolchain, 'verify_engine', return_value='pure-engine-fixture'))
                stack.enter_context(patch.object(controller, 'NativeUI', return_value=ui))
                stack.enter_context(patch.object(controller.subprocess, 'Popen', side_effect=intercept))
                sampler = stack.enter_context(patch.object(controller, 'LinuxFrameSampler'))
                stack.enter_context(patch.object(controller.signal, 'signal'))
                stack.enter_context(patch.object(controller.os, 'killpg', side_effect=ProcessLookupError))
                stack.enter_context(patch.object(Path, 'exists', display_ready))
                stack.enter_context(redirect_stdout(io.StringIO()))
                with self.assertRaisesRegex(RuntimeError, 'pure interception at initial menu'):
                    controller.main()
                engine.assert_called_once_with()
                sampler.assert_not_called()
                self.assertEqual(commands[0], ['/pure-xvfb', ':99107', '-screen', '0', '1280x720x24', '-nolisten', 'tcp'])
                expected = [str(executable), '--audio-driver', 'Dummy', '--accessibility', 'disabled',
                            '--accessibility-driver', 'dummy', '--', '--offline-validation',
                            '--offline-trace-dir=' + str(out / 'trace'), '--offline-scenario=plant', '--offline-seed=42']
                if extra:
                    expected.insert(1, '--gpu-profile')
                self.assertEqual(commands[1], expected)
                self.assertEqual(len(commands), 2)
                self.assertFalse((out / 'linux-frame-samples.jsonl').exists())


if __name__ == '__main__':
    unittest.main()
