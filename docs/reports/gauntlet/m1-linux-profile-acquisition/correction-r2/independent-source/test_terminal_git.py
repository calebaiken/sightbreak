#!/usr/bin/env python3
"""Real source/git/command gates with fake processes and temporary source only."""
import hashlib
import json
from pathlib import Path
import sys
from types import MethodType
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(ROOT / 'scripts'))
import linux_profile_acquire as acq
import test_linux_profile_acquire_sealing as maintained

RESULTS = []


def run(mode):
    state = {'manifest_read': False, 'observed': False, 'mutated': False}
    original_finalize, original_sources = acq.Acquisition.finalize, acq.Acquisition.sources
    original_command, original_observe, original_read = acq.Acquisition.command, acq.Acquisition.observe_publication_source, acq.read_json
    def command(controller, label, argv, cwd, environment=None):
        if label != 'git':
            return original_command(controller, label, argv, cwd, environment)
        fake_launch = acq.subprocess.Popen
        def launch(arguments, **kwargs):
            process = fake_launch(arguments, **kwargs)
            subcommand = arguments[1]
            if subcommand == 'rev-parse':
                raw = (controller.commit + '\n').encode()
            elif subcommand == 'status':
                raw = b'' if state['source'].read_bytes() == state['original'] else b' M game/frozen.gd\n'
            elif subcommand == 'ls-files':
                raw = state['index'].encode()
            else:
                raise AssertionError(arguments)
            kwargs['stdout'].write(raw)
            return process
        with patch.object(acq.subprocess, 'Popen', side_effect=launch):
            return original_command(controller, label, argv, cwd, environment)
    def finalize(controller):
        source = acq.ROOT / 'game/frozen.gd'
        source.parent.mkdir(parents=True)
        raw = b'extends Node\n# pure temporary source, never executed\n'
        source.write_bytes(raw)
        blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
        state.update(source=source, original=raw, index='100644 ' + blob + ' 0\tgame/frozen.gd\0')
        controller.git_path = '/fake-git'
        controller.sources = MethodType(original_sources, controller)
        controller.original = controller.sources()
        return original_finalize(controller)
    def read(path):
        value = original_read(path)
        if Path(path).name == 'outputs.json' and not state['observed']:
            state['manifest_read'] = True
        if Path(path).name == 'overall.json' and state['observed']:
            manifest = original_read(acq.OUTPUT / 'outputs.json')
            names = state['terminal_names']
            state['terminal_logs_excluded_from_earlier_manifest'] = all(name not in manifest for name in names)
            state['terminal_logs_bound_by_overall'] = all(name in value['validated_evidence'] for name in names)
            state['source_observation'] = value['publication_source_observation']
        return value
    def observe(controller):
        assert state['manifest_read'], 'Source observation must follow actual manifest readback'
        before = len(controller.receipt['commands'])
        original_observe(controller)
        terminal = controller.receipt['commands'][before:]
        assert len(terminal) == 3 and all(row['label'] == 'git' for row in terminal)
        state['terminal_names'] = [Path(row[stream]['path']).relative_to(acq.OUTPUT).as_posix()
                                   for row in terminal for stream in ('stdout', 'stderr')]
        state['observed'] = True
        if mode == 'changed-terminal-log':
            Path(terminal[-1]['stdout']['path']).write_bytes(b'clean drift after the source observation\n')
            state['mutated'] = True
    with patch.object(acq.Acquisition, 'finalize', finalize), patch.object(acq.Acquisition, 'command', command), \
            patch.object(acq.Acquisition, 'observe_publication_source', observe), patch.object(acq, 'read_json', side_effect=read), \
            patch.object(acq, 'ACCEPTED', {}):
        result = maintained.independent.finalized('valid')
    state.pop('source', None)
    state.pop('original', None)
    state.pop('index', None)
    row = {**result, **state, 'control': mode}
    RESULTS.append(row)
    return row


class TerminalGitTests(unittest.TestCase):
    def test_real_source_git_command_chain_binds_post_manifest_logs(self):
        row = run('positive')
        self.assertEqual(row['exit_code'], 0, row)
        self.assertTrue(row['passed'])
        self.assertTrue(row['observed'])
        self.assertEqual(len(row['terminal_names']), 6)
        self.assertTrue(row['terminal_logs_excluded_from_earlier_manifest'])
        self.assertTrue(row['terminal_logs_bound_by_overall'])
        self.assertTrue(row['source_observation']['passed'])
        self.assertLess(row['source_observation']['ended_monotonic'], row['source_observation']['deadline_monotonic'])

    def test_new_terminal_git_log_cannot_escape_final_sealing(self):
        row = run('changed-terminal-log')
        self.assertTrue(row['observed'] and row['mutated'])
        self.assertEqual(row['exit_code'], 1, row)
        self.assertFalse(row['passed'])
        self.assertTrue(row['terminal_logs_bound_by_overall'])


if __name__ == '__main__':
    result = unittest.main(exit=False, verbosity=2).result
    (Path(__file__).parent / 'terminal-git-results.json').write_text(json.dumps({
        'candidate': 'f242a2f20adb3ba1d9c49feb1c6caca1bdbf52b9', 'native_runs': 0,
        'methods': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
        'results': RESULTS}, indent=2) + '\n')
    raise SystemExit(0 if result.wasSuccessful() else 1)
