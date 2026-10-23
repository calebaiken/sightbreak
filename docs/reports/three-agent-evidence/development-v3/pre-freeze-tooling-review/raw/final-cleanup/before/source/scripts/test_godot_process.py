#!/usr/bin/env python3
"""Portable harness controls. Engines/sockets are mocked; containment uses CPython."""
from contextlib import ExitStack
import json
from pathlib import Path, PureWindowsPath
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import MagicMock, Mock, call, patch

import godot_process as helper
import run_network_campaign as campaign
import simulate_network as simulation
import test_connection_lifecycle as lifecycle
import test_network_soak as soak


def frozen_source():
    return {'commit': 'frozen-commit', 'game_tree': 'game-tree', 'dirty': False, 'status': '',
            'content_sha256': 'exact-source-bytes', 'source_paths': list(helper.SOURCE_PATHS),
            'source_files': 4}


def passing_summary():
    return {'passed': True, 'failures': [], 'source_unchanged': True,
            'source_before': frozen_source(), 'source_after': frozen_source()}


class TemporaryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='sightbreak-harness-unit-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / ('checkout with spaces & unicode-' + chr(0x0152))
        self.root.mkdir()


class CommandTests(TemporaryTests):
    def test_windows_native_command_keeps_arguments_and_paths_separate(self):
        binary = self.root / 'engine tools' / 'Godot.EXE'
        binary.parent.mkdir()
        binary.write_bytes(b'not executed')
        arguments = ['--headless', '--script', 'res://tests/network_simulation_probe.gd', '--',
                     '--output=' + str(self.root / 'evidence & reports/client-0.json'),
                     '--reconnect-delay=0.7']
        with patch.object(helper, 'is_windows', return_value=True):
            command = helper.godot_command(arguments, root=self.root, env={'GODOT_BIN': str(binary)})
        self.assertEqual(command, [str(binary), '--path', str(self.root / 'game'), *arguments])
        self.assertEqual(arguments[4], command[7])
        self.assertNotIn('shell', helper.process_group_options())

    def test_windows_drive_and_unc_paths_are_not_shell_split_or_rebased(self):
        root = PureWindowsPath(r'D:\Frozen checkout\SIGHTBREAK')
        for binary in (r'C:\Godot tools & binaries\Godot.exe', r'\\server\engine share\Godot.exe'):
            with self.subTest(binary=binary), patch.object(helper, 'is_windows', return_value=True), \
                    patch.object(Path, 'is_file', return_value=True):
                command = helper.godot_command(['--', r'--output=D:\trial evidence\report.json'],
                                               root=root, env={'GODOT_BIN': binary})
                self.assertEqual(command, [binary, '--path', str(root / 'game'), '--',
                                           r'--output=D:\trial evidence\report.json'])

    def test_windows_relative_binary_is_relative_to_checkout(self):
        binary = self.root / 'tools/Godot.exe'
        binary.parent.mkdir()
        binary.touch()
        with patch.object(helper, 'is_windows', return_value=True):
            command = helper.godot_command([], root=self.root, env={'GODOT_BIN': 'tools/Godot.exe'})
        self.assertEqual(command[0], str(binary))

    def test_windows_default_tools_directory_honored(self):
        tools = self.root / 'existing tools'
        binary = tools / 'godot-4.7.2/Godot_v4.7.2-stable_win64.exe'
        binary.parent.mkdir(parents=True)
        binary.touch()
        with patch.object(helper, 'is_windows', return_value=True):
            command = helper.godot_command([], root=self.root, env={'SIGHTBREAK_TOOLS_DIR': str(tools)})
        self.assertEqual(command[0], str(binary))

    def test_windows_missing_binary_and_shell_wrapper_rejected(self):
        wrapper = self.root / 'godot.sh'
        wrapper.write_text('#!/bin/sh\n', encoding='utf-8')
        for binary in (self.root / 'missing.exe', wrapper):
            with self.subTest(binary=binary), patch.object(helper, 'is_windows', return_value=True):
                with self.assertRaisesRegex(FileNotFoundError, 'GODOT_BIN.*native Godot Windows'):
                    helper.godot_command([], root=self.root, env={'GODOT_BIN': str(binary)})

    def test_posix_keeps_wrapper_and_all_probe_arguments(self):
        arguments = ['--headless', '--script', 'res://tests/probe.gd', '--', '--port=29400']
        with patch.object(helper, 'is_windows', return_value=False):
            self.assertEqual(helper.godot_command(arguments, root=self.root, env={'GODOT_BIN': '/some/engine'}),
                             [str(self.root / 'scripts/godot.sh'), *arguments])

    def test_state_directories_mirror_wrapper_and_windows_appdata(self):
        original = {'SIGHTBREAK_STATE_DIR': 'private state', 'XDG_DATA_HOME': 'do not inherit',
                    'APPDATA': 'personal profile', 'GODOT_BIN': 'Godot.exe'}
        with patch.object(helper, 'is_windows', return_value=True):
            child = helper.godot_environment(root=self.root, env=original)
        for variable, directory in (('XDG_DATA_HOME', 'data'), ('XDG_CONFIG_HOME', 'config'),
                                    ('XDG_CACHE_HOME', 'cache'), ('ANDROID_USER_HOME', 'android')):
            self.assertEqual(child[variable], str(self.root / 'private state' / directory))
            self.assertTrue(Path(child[variable]).is_dir())
        self.assertEqual(child['APPDATA'], child['XDG_DATA_HOME'])
        self.assertEqual(child['LOCALAPPDATA'], child['XDG_CACHE_HOME'])
        self.assertEqual(original['APPDATA'], 'personal profile')
        self.assertEqual(original['XDG_DATA_HOME'], 'do not inherit')

    def test_default_posix_state_and_existing_appdata_preserved(self):
        with patch.object(helper, 'is_windows', return_value=False):
            child = helper.godot_environment(root=self.root, env={'APPDATA': 'unchanged'})
        self.assertEqual(child['XDG_DATA_HOME'], str(self.root / '.local/data'))
        self.assertEqual(child['APPDATA'], 'unchanged')

    def test_platform_specific_group_flags(self):
        with patch.object(helper, 'is_windows', return_value=True):
            self.assertEqual(helper.process_group_options(), {'creationflags': 0x200})
        with patch.object(helper, 'is_windows', return_value=False):
            self.assertEqual(helper.process_group_options(), {'start_new_session': True})


class EvidenceTests(TemporaryTests):
    def test_new_and_empty_output_directories_allowed(self):
        existing = self.root / 'existing empty output'
        existing.mkdir()
        for directory in (self.root / 'new output', existing):
            self.assertEqual(helper.prepare_output(directory), directory.resolve())

    def test_any_previous_evidence_rejected_not_just_json(self):
        for name in ('server.log', '.interrupted', 'summary.json', 'campaign.json'):
            with self.subTest(name=name):
                path = self.root / name
                path.write_bytes(b'original evidence')
                with self.assertRaisesRegex(FileExistsError, 'refusing to overwrite'):
                    helper.prepare_output(self.root)
                self.assertEqual(path.read_bytes(), b'original evidence')
                path.unlink()
        (self.root / 'barrier').mkdir()
        with self.assertRaises(FileExistsError):
            helper.prepare_output(self.root)

    def test_native_leaks_and_existing_error_gates_remain_failures(self):
        process = Mock()
        process.poll.return_value = 0
        path = self.root / 'server.log'
        for message in ('WARNING: 4 ObjectDB instances were leaked at exit',
                        'WARNING: ObjectDB instances leaked at exit', 'Leaked instance: AudioStreamWAV',
                        'SCRIPT ERROR: bad probe', 'ERROR: bad authority', 'Parse Error: broken',
                        '    ERROR: existing substring check'):
            with self.subTest(message=message):
                path.write_text('Godot Engine v4.7.2\n' + message, encoding='utf-8')
                self.assertTrue(helper.native_process_failures([('server', process)], self.root))
        path.write_text('Godot Engine v4.7.2\nWARNING: Could not set V-Sync mode', encoding='utf-8')
        self.assertEqual(helper.native_process_failures([('server', process)], self.root), [])

    def test_nonzero_running_and_missing_native_logs_rejected(self):
        process = Mock()
        for code in (2, None):
            with self.subTest(code=code):
                process.poll.return_value = code
                failures = helper.native_process_failures([('server', process)], self.root)
                self.assertIn('server: exit ' + str(code), failures)
                self.assertIn('server: missing native log', failures)


class SourceTests(TemporaryTests):
    def setUp(self):
        super().setUp()
        for name in ('game/main.gd', 'game/tests/probe.gd', 'scripts/fixture.py', 'backend/app.py'):
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('original\n', encoding='utf-8')
        self.files = ['backend/app.py', 'game/main.gd', 'game/tests/probe.gd', 'scripts/fixture.py']
        self.status = ''
        self.commit = 'commit'
        self.tree = 'game-tree'
        mocked = patch.object(helper.subprocess, 'check_output', side_effect=self.git)
        mocked.start()
        self.addCleanup(mocked.stop)

    def git(self, command, **kwargs):
        self.assertEqual(kwargs['cwd'], self.root)
        arguments = command[1:]
        if arguments[0] == 'status':
            self.assertEqual(arguments[1:], ['--porcelain=v1', '--untracked-files=all'])
            return self.status
        if arguments[0] == 'ls-files':
            self.assertIn('--others', arguments)
            self.assertIn('--exclude-standard', arguments)
            return '\0'.join(self.files) + '\0'
        if arguments == ['rev-parse', 'HEAD']:
            return self.commit + '\n'
        if arguments == ['rev-parse', 'HEAD:game']:
            return self.tree + '\n'
        raise AssertionError(command)

    def test_exact_game_probe_backend_and_harness_bytes_bound(self):
        for name in self.files:
            with self.subTest(name=name):
                before = helper.source_snapshot(root=self.root)
                path = self.root / name
                path.write_text('different\n', encoding='utf-8')
                after = helper.source_snapshot(root=self.root)
                self.assertFalse(before['dirty'])
                self.assertFalse(after['dirty'])
                self.assertEqual(before['commit'], after['commit'])
                self.assertNotEqual(before['content_sha256'], after['content_sha256'])
                self.assertIn('source changed during run', helper.source_failures(before, after))
                path.write_text('original\n', encoding='utf-8')

    def test_two_edits_with_identical_dirty_status_still_change_digest(self):
        self.status = ' M game/main.gd\n'
        before = helper.source_snapshot(root=self.root)
        (self.root / 'game/main.gd').write_text('new dirty contents\n', encoding='utf-8')
        after = helper.source_snapshot(root=self.root)
        self.assertEqual(before['status'], after['status'])
        self.assertTrue(before['dirty'] and after['dirty'])
        self.assertIn('source changed during run', helper.source_failures(before, after))

    def test_deleted_and_new_source_cannot_disappear_from_freeze(self):
        before = helper.source_snapshot(root=self.root)
        (self.root / 'scripts/fixture.py').unlink()
        deleted = helper.source_snapshot(root=self.root)
        self.assertNotEqual(before['content_sha256'], deleted['content_sha256'])
        new = self.root / 'game/tests/untracked.gd'
        new.write_text('new adversarial probe', encoding='utf-8')
        self.files.append('game/tests/untracked.gd')
        self.status = '?? game/tests/untracked.gd\n'
        added = helper.source_snapshot(root=self.root)
        self.assertEqual(added['source_files'], before['source_files'] + 1)
        self.assertNotEqual(deleted['content_sha256'], added['content_sha256'])

    def test_commit_and_tree_changes_rejected_even_when_content_same(self):
        before = helper.source_snapshot(root=self.root)
        self.commit, self.tree = 'new-commit', 'new-tree'
        after = helper.source_snapshot(root=self.root)
        self.assertEqual(before['content_sha256'], after['content_sha256'])
        self.assertIn('source changed during run', helper.source_failures(before, after))

    def test_unchanged_clean_source_passes_but_unchanged_dirty_source_does_not(self):
        before = helper.source_snapshot(root=self.root)
        self.assertEqual(helper.source_failures(before, helper.source_snapshot(root=self.root)), [])
        before['dirty'] = True
        self.assertEqual(len(helper.source_failures(before, dict(before))), 2)


class ProcessTests(unittest.TestCase):
    def test_windows_taskkill_targets_complete_tree_without_posix_calls(self):
        process = Mock(pid=1234)
        process.poll.return_value = None
        with patch.object(helper, 'is_windows', return_value=True), \
                patch.object(helper.subprocess, 'run', return_value=Mock(returncode=0)) as run, \
                patch.object(helper.os, 'killpg', create=True) as killpg:
            helper.terminate_process_tree(process)
        self.assertEqual(run.call_args.args[0], ['taskkill', '/PID', '1234', '/T', '/F'])
        self.assertNotIn('shell', run.call_args.kwargs)
        killpg.assert_not_called()
        process.wait.assert_called_once_with(timeout=5)

    def test_windows_taskkill_failure_reaps_root_but_reports_incomplete_cleanup(self):
        for result in (Mock(returncode=1), FileNotFoundError('taskkill missing'),
                       subprocess.TimeoutExpired('taskkill', 5)):
            with self.subTest(result=result):
                process = Mock(pid=1234)
                process.poll.return_value = None
                with patch.object(helper, 'is_windows', return_value=True), \
                        patch.object(helper.subprocess, 'run') as run:
                    if isinstance(result, Exception):
                        run.side_effect = result
                    else:
                        run.return_value = result
                    with self.assertRaisesRegex(RuntimeError, 'taskkill'):
                        helper.terminate_process_tree(process)
                process.kill.assert_called_once()
                process.wait.assert_called_once_with(timeout=5)

    def test_windows_already_exited_child_is_reaped_without_pid_reuse_kill(self):
        process = Mock(pid=1234)
        process.poll.return_value = 0
        with patch.object(helper, 'is_windows', return_value=True), \
                patch.object(helper.subprocess, 'run') as run:
            helper.terminate_process_tree(process)
        run.assert_not_called()
        process.wait.assert_called_once_with(timeout=5)

    def test_posix_cleanup_includes_nested_sessions_but_not_unrelated_group(self):
        process = Mock(pid=100)
        process.wait.side_effect = [subprocess.TimeoutExpired('simulation', 5), 0]
        with ExitStack() as stack:
            stack.enter_context(patch.object(helper, 'is_windows', return_value=False))
            stack.enter_context(patch.object(helper.subprocess, 'check_output',
                                            return_value='100 10\n101 100\n102 101\n999 1\n'))
            stack.enter_context(patch.object(helper.os, 'getpgrp', return_value=10, create=True))
            stack.enter_context(patch.object(helper.os, 'getpgid',
                                            side_effect=lambda pid: {100: 100, 101: 101, 102: 101}[pid], create=True))
            stack.enter_context(patch.object(helper.signal, 'SIGKILL', 9, create=True))
            killpg = stack.enter_context(patch.object(helper.os, 'killpg', create=True))
            helper.terminate_process_tree(process)
        self.assertCountEqual(killpg.call_args_list,
                              [call(100, 0), call(100, signal.SIGTERM), call(101, signal.SIGTERM),
                               call(100, 9), call(101, 9)])
        self.assertEqual(process.wait.call_count, 2)

    def test_posix_child_of_exited_leader_still_gets_kill_after_term(self):
        process = Mock(pid=100)
        process.wait.return_value = 0
        with patch.object(helper, 'is_windows', return_value=False), \
                patch.object(helper, '_posix_process_groups', return_value={100, 101}), \
                patch.object(helper.os, 'killpg', create=True) as killpg, \
                patch.object(helper.signal, 'SIGKILL', 9, create=True):
            helper.terminate_process_tree(process)
        self.assertIn(call(101, signal.SIGTERM), killpg.call_args_list)
        self.assertIn(call(101, 9), killpg.call_args_list)

    def test_cleanup_attempts_every_child_even_if_one_tree_cleanup_fails(self):
        processes = [('server', Mock()), ('client', Mock())]
        with patch.object(helper, 'terminate_process_tree', side_effect=[RuntimeError('denied'), None]) as stop:
            failures = helper.cleanup_processes(processes)
        self.assertEqual(stop.call_count, 2)
        self.assertIn('client: cleanup failed: denied', failures)


class ResourceTests(unittest.TestCase):
    def test_windows_reports_unavailable_and_never_touches_proc_or_sysconf(self):
        with patch.object(helper.sys, 'platform', 'win32'), \
                patch.object(Path, 'read_text', side_effect=AssertionError('no /proc on Windows')) as read, \
                patch.object(helper.os, 'sysconf', create=True) as sysconf:
            self.assertFalse(helper.resource_measurement()['available'])
            self.assertIn('null, not zero', helper.resource_measurement()['reason'])
            self.assertIsNone(helper.sample_process_resources(1234))
        read.assert_not_called()
        sysconf.assert_not_called()

    def test_linux_preserves_rss_kib_and_process_cpu_seconds(self):
        fields = ['S'] + ['0'] * 20
        fields[11], fields[12] = '120', '50'
        with patch.object(helper.sys, 'platform', 'linux'), \
                patch.object(Path, 'is_dir', return_value=True), \
                patch.object(Path, 'read_text', side_effect=['Name: Godot\nVmRSS:\t45678 kB\n',
                                                           '1234 (Godot (probe)) ' + ' '.join(fields)]), \
                patch.object(helper.os, 'sysconf', return_value=100, create=True):
            self.assertEqual(helper.sample_process_resources(1234),
                             {'rss_current_kib': 45678, 'cpu_seconds': 1.7})

    def test_vanished_process_is_unavailable_not_a_zero_measurement(self):
        with patch.object(helper, 'resource_measurement', return_value={'available': True}), \
                patch.object(Path, 'read_text', side_effect=FileNotFoundError):
            self.assertIsNone(helper.sample_process_resources(1234))


class CampaignTests(TemporaryTests):
    def run_campaign(self, *, summary=None, code=0, child_log='', source=None, only='rtt-0', raw=None,
                     wait_error=None, write_summary=True):
        out = self.root / 'campaign evidence'
        summary = passing_summary() if summary is None else summary
        def launch(command, **kwargs):
            directory = Path(command[command.index('--out') + 1])
            directory.mkdir()
            if write_summary:
                (directory / 'summary.json').write_text(raw if raw is not None else json.dumps(summary), encoding='utf-8')
            (directory / 'nested').mkdir()
            (directory / 'nested/client.log').write_text(child_log, encoding='utf-8')
            kwargs['result_path'].write_text(json.dumps({'complete': True, 'exit': code, 'errors': []}), encoding='utf-8')
            if wait_error is not None:
                raise wait_error
            return code

        arguments = ['run_network_campaign.py', '--out', str(out), '--seconds', '12', '--clients', '2']
        if only:
            arguments.extend(['--only', only])
        with ExitStack() as stack:
            stack.enter_context(patch.object(sys, 'argv', arguments))
            snapshots = stack.enter_context(patch.object(campaign, 'source_snapshot', return_value=frozen_source()))
            if source is not None:
                snapshots.side_effect = source
            runner = stack.enter_context(patch.object(campaign, 'run_process', side_effect=launch))
            stack.enter_context(patch('builtins.print'))
            result = campaign.main()
        return result, json.loads((out / 'campaign.json').read_text(encoding='utf-8')), runner, None, out

    def test_success_uses_current_interpreter_and_keeps_source_binding(self):
        code, rows, runner, _, out = self.run_campaign()
        self.assertEqual(code, 0)
        self.assertTrue(rows[0]['passed'])
        self.assertEqual(rows[0]['command'][0], sys.executable)
        self.assertEqual(rows[0]['source_before'], frozen_source())
        self.assertEqual(rows[0]['source_after'], frozen_source())
        self.assertNotIn('shell', runner.call_args.kwargs)
        self.assertTrue((out / 'rtt-0.process.json').is_file())
        self.assertTrue(json.loads((out / 'source.json').read_text(encoding='utf-8'))['passed'])

    def test_all_twelve_conditions_and_impairment_flags_are_preserved(self):
        code, rows, _, _, _ = self.run_campaign(only=None)
        self.assertEqual(code, 0)
        self.assertEqual([row['name'] for row in rows], ['rtt-0', 'rtt-50', 'rtt-100', 'rtt-150', 'rtt-200',
                                                       'jitter', 'loss', 'reorder', 'impaired', 'blackout',
                                                       'reconnect', 'prediction-disabled'])
        reconnect = rows[10]['command']
        for flag, value in (('--rtt-ms', '100'), ('--jitter-ms', '20'), ('--loss', '0.03'), ('--reorder', '0.05'),
                            ('--blackout-at', '4'), ('--blackout-seconds', '2'), ('--reconnect-at', '8')):
            self.assertEqual(reconnect[reconnect.index(flag) + 1], value)
        self.assertIn('--no-prediction', rows[-1]['command'])
        self.assertEqual(rows[-1]['command'][rows[-1]['command'].index('--port') + 1], str(32200 + 11 * 20))

    def test_nonzero_child_cannot_pass_just_because_summary_exists(self):
        code, rows, _, _, _ = self.run_campaign(code=7)
        self.assertEqual(code, 1)
        self.assertIn('simulation exit 7', rows[0]['failures'])
        self.assertFalse(rows[0]['passed'])

    def test_timeout_cannot_pass_with_summary_and_always_cleans_tree(self):
        code, rows, runner, _, _ = self.run_campaign(wait_error=subprocess.TimeoutExpired('simulation', 72))
        self.assertEqual(code, 1)
        self.assertEqual(rows[0]['exit'], 124)
        self.assertIn('simulation timed out', rows[0]['failures'])
        self.assertTrue(rows[0]['summary']['passed'])
        runner.assert_called_once()

    def test_missing_summary_rejected_even_if_child_exit_zero(self):
        code, rows, _, _, _ = self.run_campaign(write_summary=False)
        self.assertEqual(code, 1)
        self.assertIn('missing or invalid simulation summary', rows[0]['failures'])

    def test_child_failure_list_cannot_be_hidden_by_zero_exit_and_passed_true(self):
        summary = passing_summary()
        summary['failures'] = ['fresh authority assertion failed']
        code, rows, _, _, _ = self.run_campaign(summary=summary)
        self.assertEqual(code, 1)
        self.assertIn('simulation summary contains failures or has no failure gate', rows[0]['failures'])

    def test_explicit_failed_child_summary_rejected_with_empty_failures(self):
        summary = passing_summary()
        summary['passed'] = False
        code, rows, _, _, _ = self.run_campaign(summary=summary)
        self.assertEqual(code, 1)
        self.assertIn('simulation summary did not pass', rows[0]['failures'])

    def test_missing_malformed_and_non_object_summary_gates_rejected(self):
        for summary in ({}, {'passed': True}, [], {'failures': None}, {'failures': ''}):
            with self.subTest(summary=summary):
                self.assertTrue(campaign.trial_failures(0, summary, frozen_source(), frozen_source(), frozen_source()))
        code, rows, _, _, _ = self.run_campaign(raw='{broken JSON')
        self.assertEqual(code, 1)
        self.assertIsNone(rows[0]['summary'])

    def test_nested_native_objectdb_leak_overrides_clean_child_summary(self):
        code, rows, _, _, _ = self.run_campaign(child_log='WARNING: 9 ObjectDB instances were leaked at exit\n')
        self.assertEqual(code, 1)
        self.assertTrue(any('nested' in failure and 'resource leak' in failure for failure in rows[0]['failures']))

    def test_exact_source_change_rejected_and_remaining_trials_not_started(self):
        changed = {**frozen_source(), 'content_sha256': 'changed with same commit and dirty flag'}
        code, rows, popen, _, _ = self.run_campaign(source=[frozen_source(), frozen_source(), changed, changed], only=None)
        self.assertEqual(code, 1)
        self.assertEqual(len(rows), 1)
        popen.assert_called_once()
        self.assertIn('source changed during run', rows[0]['failures'])

    def test_source_change_before_trial_prevents_launch(self):
        changed = {**frozen_source(), 'content_sha256': 'changed'}
        code, rows, popen, _, _ = self.run_campaign(source=[frozen_source(), changed, changed, changed], only=None)
        self.assertEqual(code, 1)
        popen.assert_not_called()
        self.assertIn('source changed before trial; child not launched', rows[0]['failures'])

    def test_final_window_source_change_cannot_leave_pass_only_campaign_record(self):
        changed = {**frozen_source(), 'content_sha256': 'changed after last child'}
        code, rows, _, _, out = self.run_campaign(source=[frozen_source(), frozen_source(), frozen_source(), changed])
        self.assertEqual(code, 1)
        self.assertFalse(rows[0]['passed'])
        self.assertIn('campaign: source changed during run', rows[0]['failures'])
        self.assertFalse(json.loads((out / 'source.json').read_text(encoding='utf-8'))['source_unchanged'])

    def test_child_bound_to_different_source_rejected_even_with_clean_parent(self):
        summary = passing_summary()
        summary['source_before']['content_sha256'] = 'some other checkout'
        code, rows, _, _, _ = self.run_campaign(summary=summary)
        self.assertEqual(code, 1)
        self.assertIn('simulation source does not match frozen campaign source', rows[0]['failures'])

    def test_existing_log_evidence_is_not_truncated(self):
        out = self.root / 'earlier campaign'
        out.mkdir()
        path = out / 'rtt-0.log'
        path.write_bytes(b'failed original trial')
        with patch.object(sys, 'argv', ['campaign', '--out', str(out)]), \
                patch.object(campaign, 'run_process') as popen, patch('sys.stderr'):
            with self.assertRaises(SystemExit):
                campaign.main()
        popen.assert_not_called()
        self.assertEqual(path.read_bytes(), b'failed original trial')

    def test_real_exited_simulation_cannot_leave_descendant_and_passing_summary(self):
        """A synthetic child is not a native campaign or performance result."""
        out = self.root / 'contained campaign'
        scripts = self.root / 'scripts'
        scripts.mkdir()
        marker = self.root / 'late-descendant.txt'
        program = ('import time\nfrom pathlib import Path\ntime.sleep(2)\n'
                   f'Path({str(marker)!r}).write_text("ERROR: escaped descendant")\n'
                   'print("ERROR: late native-shaped output", flush=True)\n')
        simulation_script = scripts / 'simulate_network.py'
        simulation_script.write_text(
            'import json, subprocess, sys\nfrom pathlib import Path\n'
            'out = Path(sys.argv[sys.argv.index("--out") + 1]); out.mkdir()\n'
            f'(out / "summary.json").write_text({json.dumps(passing_summary())!r})\n'
            f'subprocess.Popen([sys.executable, "-c", {program!r}])\n', encoding='utf-8')
        arguments = ['campaign', '--out', str(out), '--seconds', '12', '--clients', '2', '--only', 'rtt-0']
        with patch.object(sys, 'argv', arguments), patch.object(campaign, 'ROOT', self.root), \
                patch.object(campaign, 'source_snapshot', return_value=frozen_source()), patch('builtins.print'):
            code = campaign.main()
        row = json.loads((out / 'campaign.json').read_text(encoding='utf-8'))[0]
        self.assertEqual(code, 1)
        self.assertEqual(row['exit'], 0)
        self.assertTrue(row['summary']['passed'])
        self.assertFalse(row['passed'])
        self.assertIn('HARNESS_ERROR', (out / 'rtt-0.log').read_text(encoding='utf-8'))
        self.assertTrue((out / 'rtt-0.process.json').exists())
        time.sleep(2.1)
        self.assertFalse(marker.exists())


class SimulationTests(TemporaryTests):
    def run_simulation(self, *, leak=False, child_exit=0, source=None, binding=None, extra=(), corrupt=False,
                       empty_report=False):
        out = self.root / 'native evidence'
        commands, children = [], []
        bindings = binding if binding is not None else [{'actor': i + 1, 'idle_msec': 0, 'input_ack': 10} for i in range(2)]
        server_report = {'occupancy': [{'enet': [1, 2], 'bindings': bindings}],
                         'poses': [{'id': i, 't': t, 'x': t, 'y': 0, 'z': 0} for i in (1, 2) for t in (0, 1)],
                         'tick_usec': [100, 200], 'tick_intervals_usec': [16666, 16667], 'skipped_commands': 3}
        client_report = {'accepted_tick_gaps': [3, 3], 'poses': [{'id': 1, 't': t, 'x': t, 'y': 0, 'z': 0} for t in (.25, .75)],
                         'state': 'connected', 'accepted_snapshots': 10, 'last_snapshot_age_seconds': .1,
                         'last_accepted_age_seconds': .1, 'last_accepted_tick': 99, 'first_movement_seconds': .02,
                         'prediction_errors_m': [.01, .02], 'corrections': 1, 'hard_corrections': 0}
        if empty_report:
            client_report = {}

        def launch(command, **kwargs):
            commands.append((command, kwargs))
            output = Path(next(argument.split('=', 1)[1] for argument in command if argument.startswith('--output=')))
            process = Mock(pid=500 + len(commands))
            process.name = output.stem
            process.log = kwargs['stdout']
            process.poll.side_effect = lambda: child_exit if (out / 'barrier/stop').exists() else None
            children.append((output.stem, process))
            kwargs['stdout'].write('SIGHTBREAK_SERVER_READY\n' if output.stem == 'server' else 'Godot Engine v4.7.2\n')
            kwargs['stdout'].flush()
            output.with_suffix('.json.ready').write_text('ready', encoding='utf-8')
            output.write_text('{broken' if corrupt and output.stem == 'client-0' else
                              json.dumps(server_report if output.stem == 'server' else client_report), encoding='utf-8')
            return process

        def cleanup(processes):
            if leak:
                processes[0][1].log.write('WARNING: 4 ObjectDB instances were leaked at exit\n')
                processes[0][1].log.flush()
            return []

        selector = MagicMock()
        selector.select.return_value = []
        with ExitStack() as stack:
            stack.enter_context(patch.object(sys, 'argv', ['simulate_network.py', '--out', str(out), '--seconds', '5', *extra]))
            snapshots = stack.enter_context(patch.object(simulation, 'source_snapshot', return_value=frozen_source()))
            if source is not None:
                snapshots.side_effect = source
            stack.enter_context(patch.object(simulation, 'godot_command', side_effect=lambda args, **kwargs: ['native Godot.exe', *args]))
            stack.enter_context(patch.object(simulation, 'godot_environment', side_effect=lambda **kwargs: kwargs['env']))
            stack.enter_context(patch.object(simulation.subprocess, 'Popen', side_effect=launch))
            stack.enter_context(patch.object(simulation.platform, 'platform', return_value='mock native platform'))
            stack.enter_context(patch.object(simulation, 'cleanup_processes', side_effect=cleanup))
            stack.enter_context(patch.object(simulation.socket, 'socket'))
            stack.enter_context(patch.object(simulation.selectors, 'DefaultSelector', return_value=selector))
            stack.enter_context(patch.object(simulation, 'resource_measurement', return_value={'available': False, 'method': None}))
            sampler = stack.enter_context(patch.object(simulation, 'sample_process_resources'))
            stack.enter_context(patch('builtins.print'))
            code = simulation.main()
        sampler.assert_not_called()
        return code, json.loads((out / 'summary.json').read_text(encoding='utf-8')), commands, out

    def test_success_keeps_all_metrics_and_marks_windows_resources_null(self):
        code, summary, commands, _ = self.run_simulation()
        self.assertEqual(code, 0)
        self.assertEqual(len(commands), 3)
        self.assertTrue(summary['passed'] and summary['shared_stop_reached'] and summary['source_unchanged'])
        self.assertEqual(summary['failures'], [])
        self.assertFalse(summary['resource_measurement']['available'])
        for sample in summary['processes'].values():
            self.assertIsNone(sample['rss_peak_kib'])
            self.assertIsNone(sample['rss_current_kib'])
            self.assertIsNone(sample['cpu_seconds'])
        self.assertEqual(summary['received_tick_gap_median'], 3)
        self.assertEqual(summary['render_position_error_p95_m'], 0)
        self.assertEqual(summary['render_samples_compared'], 4)
        self.assertEqual(summary['skipped_commands'], 3)
        self.assertEqual(summary['tick_usec_max'], 200)
        self.assertEqual(summary['measurement_duration_seconds'], 5)
        self.assertEqual(summary['source_before'], summary['source_after'])

    def test_leak_emitted_during_cleanup_is_caught_before_summary(self):
        code, summary, _, _ = self.run_simulation(leak=True)
        self.assertEqual(code, 1)
        self.assertIn('server: logged error or resource leak', summary['failures'])

    def test_nonzero_native_child_rejected_despite_complete_reports(self):
        code, summary, _, _ = self.run_simulation(child_exit=2)
        self.assertEqual(code, 1)
        self.assertIn('client-0: exit 2', summary['failures'])

    def test_source_changed_with_same_commit_and_clean_flag_is_rejected(self):
        changed = {**frozen_source(), 'content_sha256': 'changed'}
        code, summary, _, _ = self.run_simulation(source=[frozen_source(), changed])
        self.assertEqual(code, 1)
        self.assertFalse(summary['source_unchanged'])
        self.assertIn('source changed during run', summary['failures'])

    def test_dirty_source_prevents_any_native_launch_and_retains_failure_record(self):
        dirty = {**frozen_source(), 'dirty': True, 'status': ' M game/main.gd'}
        code, summary, commands, _ = self.run_simulation(source=[dirty, dirty])
        self.assertEqual(code, 1)
        self.assertEqual(commands, [])
        self.assertIn('source was not clean before run', summary['failures'])
        self.assertIn('conditions', summary)

    def test_failed_final_source_verification_is_not_a_pass(self):
        code, summary, _, _ = self.run_simulation(source=[frozen_source(), FileNotFoundError('git missing')])
        self.assertEqual(code, 1)
        self.assertIsNone(summary['source_after'])
        self.assertTrue(any('source verification failed' in failure for failure in summary['failures']))

    def test_existing_authority_freshness_tolerances_are_not_weakened(self):
        for binding in ({'actor': 1, 'idle_msec': 750, 'input_ack': 10},
                        {'actor': 1, 'idle_msec': 0, 'input_ack': 9}):
            with self.subTest(binding=binding):
                bindings = [binding, {'actor': 2, 'idle_msec': 0, 'input_ack': 10}]
                code, summary, _, out = self.run_simulation(binding=bindings)
                self.assertEqual(code, 1)
                self.assertIn('server: restored input authority is not fresh', summary['failures'])
                # Each mock trial needs a distinct empty directory, just like a real run.
                self.root = self.root / 'next test'
                self.root.mkdir()

    def test_duplicate_actor_authority_rejected(self):
        bindings = [{'actor': 1, 'idle_msec': 0, 'input_ack': 10}] * 2
        code, summary, _, _ = self.run_simulation(binding=bindings)
        self.assertEqual(code, 1)
        self.assertIn('server: capacity or duplicate actor authority', summary['failures'])

    def test_corrupt_report_preserves_failed_trial_evidence(self):
        code, summary, _, _ = self.run_simulation(corrupt=True)
        self.assertEqual(code, 1)
        self.assertTrue(any('client-0: missing or invalid report' in failure for failure in summary['failures']))
        self.assertIn('traffic', summary)
        self.assertIn('conditions', summary)

    def test_empty_client_reports_cannot_be_silently_skipped_as_success(self):
        code, summary, _, _ = self.run_simulation(empty_report=True)
        self.assertEqual(code, 1)
        self.assertTrue(any('client-0: missing or invalid report' in failure for failure in summary['failures']))

    def test_prediction_reconnect_and_render_arguments_unchanged(self):
        code, _, commands, _ = self.run_simulation(extra=('--no-prediction', '--reconnect-at', '2',
                                                         '--reconnect-delay', '0.7', '--render-client', '0'))
        self.assertEqual(code, 0)
        for command, _ in commands:
            self.assertIn('--no-prediction', command)
            self.assertEqual(command[command.index('--max-fps') + 1], '60')
        self.assertIn('--audio-driver', commands[1][0])
        self.assertNotIn('--headless', commands[1][0])
        self.assertIn('--headless', commands[0][0])
        self.assertIn('--headless', commands[2][0])
        for command, _ in commands[1:]:
            self.assertIn('--reconnect-delay=0.7', command)
            self.assertIn('--reconnect-at=2.0', command)

    def test_client_environment_never_inherits_server_credentials(self):
        tickets = self.root / 'private tickets.json'
        tickets.write_text(json.dumps(['ticket-0', 'ticket-1']), encoding='utf-8')
        with patch.dict(simulation.os.environ, {'SIGHTBREAK_SERVER_KEY': 'server secret',
                                               'SIGHTBREAK_RESULT_SPOOL': 'private spool'}, clear=True):
            code, summary, commands, _ = self.run_simulation(extra=('--account-tickets', str(tickets)))
        self.assertEqual(code, 0)
        self.assertEqual(commands[0][1]['env']['SIGHTBREAK_SERVER_KEY'], 'server secret')
        for index, (_, options) in enumerate(commands[1:]):
            self.assertNotIn('SIGHTBREAK_SERVER_KEY', options['env'])
            self.assertNotIn('SIGHTBREAK_RESULT_SPOOL', options['env'])
            self.assertEqual(options['env']['SIGHTBREAK_JOIN_TICKET'], 'ticket-' + str(index))
        self.assertIs(summary['conditions']['account_tickets'], True)
        self.assertNotIn('ticket-0', json.dumps(summary))
        self.assertNotIn(str(tickets), json.dumps(summary))


class SmallerHarnessTests(TemporaryTests):
    def run_harness(self, module, *, leak=False):
        out = self.root / module.__name__
        commands = []

        def launch(command, **kwargs):
            commands.append((command, kwargs))
            kwargs['stdout'].write('SIGHTBREAK_SERVER_READY\n{"ok":true}\n')
            if leak:
                kwargs['stdout'].write('WARNING: ObjectDB instances leaked at exit\n')
            kwargs['stdout'].flush()
            for argument in command:
                if argument.startswith('--output='):
                    Path(argument.split('=', 1)[1]).write_text('{"passed":true}', encoding='utf-8')
            process = Mock()
            process.wait.return_value = 0
            return process

        with ExitStack() as stack:
            stack.enter_context(patch.object(sys, 'argv', [module.__name__, '--out', str(out)]))
            stack.enter_context(patch.object(module, 'source_snapshot', return_value=frozen_source()))
            stack.enter_context(patch.object(module, 'godot_command', side_effect=lambda args, **kwargs: ['native Godot.exe', *args]))
            stack.enter_context(patch.object(module, 'godot_environment', return_value={'test': 'environment'}))
            stack.enter_context(patch.object(module.subprocess, 'Popen', side_effect=launch))
            cleanup = stack.enter_context(patch.object(module, 'cleanup_processes', return_value=[]))
            stack.enter_context(patch('builtins.print'))
            module.main()
        cleanup.assert_called_once()
        self.assertTrue(all(options['env'] == {'test': 'environment'} for _, options in commands))
        self.assertTrue(all(command[0] == 'native Godot.exe' for command, _ in commands))
        return commands

    def test_soak_uses_portable_launch_for_server_and_two_clients(self):
        self.assertEqual(len(self.run_harness(soak)), 3)

    def test_lifecycle_uses_portable_launch_for_all_six_peers(self):
        self.assertEqual(len(self.run_harness(lifecycle)), 6)

    def test_soak_resource_leak_rejected(self):
        with self.assertRaisesRegex(AssertionError, 'server failed'):
            self.run_harness(soak, leak=True)

    def test_lifecycle_resource_leak_rejected_despite_ok_marker(self):
        with self.assertRaisesRegex(RuntimeError, 'Failed:'):
            self.run_harness(lifecycle, leak=True)


if __name__ == '__main__':
    unittest.main()
