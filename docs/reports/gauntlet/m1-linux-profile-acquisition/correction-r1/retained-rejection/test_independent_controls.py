#!/usr/bin/env python3
"""Synthetic source-review controls; Popen is fake and no engine can start."""
from contextlib import ExitStack, redirect_stdout, redirect_stderr
from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
import signal
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'scripts'))
import linux_profile_acquire as acq
import linux_profile_payload as pack
import test_linux_profile_acquire as data
import test_linux_profile_overhead as fixture

RESULTS = []


def make_block(controller, output):
    """Only invented measurements and PNG stand-ins; never rendered or run."""
    expected = fixture.manual_expected(controller.seal['payload_sha256'], str(controller.executable))
    expected.update(source=controller.seal['source'], display=':99127', cpus=[0, 1],
                    seal_sha256=controller.receipt['seal_sha256'])
    block_root = output / 'native-block'
    block_root.mkdir()
    proof = b'synthetic proof bytes, never rendered'
    rows = []
    for index in range(4):
        row = fixture.manual_record(index, controller.seal['payload_sha256'])
        directory = block_root / f'{index + 1:02d}-' / ('on' if row['profile'] else 'off')
        directory.mkdir(parents=True)
        paths = {key: str(directory / 'state' / key) for key in ('data', 'config', 'cache', 'mesa')}
        row.update(output=str(directory),
                   engine_argv=acq.accepted.engine_argv(controller.executable, row['profile'], directory, row['token']),
                   seal_sha256=expected['seal_sha256'], cache_initial={'paths': paths, 'empty': True})
        row['process_argv'] = ['taskset', '-c', '0,1', *row['engine_argv']]
        row['actual_cmdline'] = deepcopy(row['engine_argv'])
        row['selected_environment'].update(DISPLAY=':99127', XDG_DATA_HOME=paths['data'], XDG_CONFIG_HOME=paths['config'],
                                           XDG_CACHE_HOME=paths['cache'], MESA_SHADER_CACHE_DIR=paths['mesa'])
        row['actual_environment'] = deepcopy(row['selected_environment'])
        for name in ('host_begin', 'host_end'):
            row[name]['affinity'] = [0, 1]
        row['fixture']['png_sha256'] = hashlib.sha256(proof).hexdigest()
        acq.write(directory / 'condition.json', row)
        row['publication_sha256'] = acq.digest(directory / 'condition.json')
        (directory / 'client.log').write_text(row['stdout'])
        (directory / 'proof.png').write_bytes(proof)
        acq.write(directory / 'metrics.json', row['fixture'])
        rows.append(row)
    assert acq.accepted.evaluate(rows, expected)['comparable']
    (block_root / 'xvfb.log').write_text('')
    acq.write(block_root / 'block.json', {'passed': True, 'expected': expected, 'records': rows,
                                       'xvfb_cleanup': {'pid_absent': True, 'group_absent': True}})


def finalized(mode):
    """Use real command, artifact, raw block, finalize, phase, and main gates.

    Stage/source/tool/host admission is synthetic. The relevant earlier raw gates
    run before mutation, and finalization/publication run afterward unchanged.
    """
    registry = {}
    class Process:
        pid, returncode = 44001, None
        def poll(self):
            registry.pop(self.pid, None)
            self.returncode = 0
            return self.returncode
    def launch(argv, **kwargs):
        registry[44001] = {'pid': 44001, 'start_ticks': 100, 'ppid': 1,
                           'pgid': 44001, 'sid': 44001, 'state': 'S'}
        kwargs['stdout'].write((acq.toolchain.ENGINE + '\n').encode() if '--version' in argv else b'')
        return Process()
    class Controller(acq.Acquisition):
        def sources(self):
            return self.original
        def verify_tools(self):
            return []
        def host(self):
            return {key: 'synthetic stable host' for key in (
                'uname', 'os_release_sha256', 'affinity', 'nice', 'scheduler', 'python', 'supervisor_libraries', 'quota')}
        def execute(self):
            handbuilt = acq.OUTPUT / 'handbuilt'
            handbuilt.mkdir()
            self.project, self.stage_record, _, template, original_elf = data.manual_stage(handbuilt)
            self.original = [{'path': 'invented source inventory'}]
            self.python_path, self.xvfb, self.display = '/fake-python', '/fake-xvfb', ':99127'
            self.templates = acq.OUTPUT / 'templates'
            private = acq.OUTPUT / 'private-export-state/data/godot/export_templates/4.7.2.stable'
            for folder in (self.templates, private):
                folder.mkdir(parents=True)
                for name in ('version.txt', 'linux_debug.x86_64', 'linux_release.x86_64'):
                    (folder / name).write_bytes(template.read_bytes())
            (acq.OUTPUT / 'export').mkdir()
            (acq.OUTPUT / 'export/linux-profile-diagnostic.x86_64').write_bytes(original_elf.read_bytes())
            self.receipt['host_before'] = self.host()
            self.budget.phase('version', lambda: self.command('version', ['/fake-engine', '--version'], self.project))
            self.budget.phase('artifact', lambda: {'stage': self.inventory_stage('export'), 'payload': self.inspect_artifact()})
            acq.write(acq.OUTPUT / 'diagnostic-stage.json', self.stage_record)
            self.seal = {'source': self.stage_record['source'],
                         'payload_sha256': self.receipt['independent_payload']['ELF_sha256'],
                         'source_ledger_sha256': self.receipt['independent_payload']['ledger_sha256'],
                         'stage_record': str(acq.OUTPUT / 'diagnostic-stage.json'),
                         'stage_sha256': acq.digest(acq.OUTPUT / 'diagnostic-stage.json')}
            acq.write(acq.OUTPUT / 'seal.json', self.seal)
            self.receipt['seal_sha256'] = acq.digest(acq.OUTPUT / 'seal.json')
            make_block(self, acq.OUTPUT)
            self.budget.phase('block', self.run_block)
            directory = acq.OUTPUT / 'native-block/01-/off'
            target = None
            if mode == 'version-warning':
                target = Path(self.receipt['commands'][0]['stdout']['path'])
                target.write_text('WARNING: late retained preparation warning\n')
            elif mode == 'client-warning':
                target = directory / 'client.log'
                target.write_text(target.read_text() + 'WARNING: late retained condition warning\n')
            elif mode == 'proof-change':
                target = directory / 'proof.png'
                target.write_bytes(b'changed after the actual proof hash gate')
            elif mode == 'block-change':
                target = acq.OUTPUT / 'native-block/block.json'
                block = acq.read_json(target)
                block['passed'] = False
                acq.write(target, block)
            elif mode == 'condition-change':
                target = directory / 'condition.json'
                target.write_text('{}\n')
            elif mode == 'phase-change':
                target = acq.OUTPUT / 'version.phase.json'
                target.write_text('{}\n')
            elif mode == 'stage-record-change':
                target = acq.OUTPUT / 'diagnostic-stage.json'
                target.write_text('{}\n')
            self.receipt['review_mutation'] = {'synthetic': True, 'mode': mode,
                                              'path': str(target) if target else None}
            self.budget.phase('finalize', self.finalize)
            self.final_accept_until = self.receipt['phases'][-1]['deadline_monotonic']
            self.budget.check('all phases accepted')
            self.receipt['passed'] = True
    with tempfile.TemporaryDirectory() as temporary, ExitStack() as stack:
        root = Path(temporary)
        output = root / 'builds/attempt'
        for key, value in (('ROOT', root), ('OUTPUT', output), ('LANE_LOCK', root / 'lane'),
                           ('ACQUISITION_LOCK', root / 'acquisition'), ('Acquisition', Controller)):
            stack.enter_context(patch.object(acq, key, value))
        stack.enter_context(patch.object(acq.subprocess, 'Popen', side_effect=launch))
        stack.enter_context(patch.object(acq, 'process_scan', side_effect=lambda: deepcopy(registry)))
        stack.enter_context(patch.object(acq, 'recognized_native', return_value=[]))
        stack.enter_context(patch('sys.argv', ['linux_profile_acquire.py', '--execute-frozen-source', 'c' * 40]))
        old_signals = {number: signal.getsignal(number) for number in (signal.SIGTERM, signal.SIGINT)}
        try:
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                code = acq.main()
        finally:
            for number, handler in old_signals.items():
                signal.signal(number, handler)
        receipt = acq.read_json(output / 'overall.json')
        outputs = acq.read_json(output / 'outputs.json') if (output / 'outputs.json').exists() else {}
        mutation = receipt.get('review_mutation', {})
        target = Path(mutation['path']) if mutation.get('path') else None
        result = {'mode': mode, 'exit_code': code, 'passed': receipt['passed'],
                  'phases': {row['name']: row['passed'] for row in receipt['phases']},
                  'raw_manifest_binds_changed_file': bool(target and outputs.get(target.relative_to(output).as_posix()) == data.descriptor(target.read_bytes())),
                  'error': receipt.get('error')}
        if mode == 'version-warning':
            result['command_log_hash_still_matches'] = acq.digest(target) == receipt['commands'][0]['stdout']['sha256']
        if mode == 'block-change':
            result['block_hash_still_matches'] = acq.digest(target) == receipt['block_sha256']
        RESULTS.append(result)
        return result


class IndependentControls(unittest.TestCase):
    def test_unmodified_real_finalization_path_accepts(self):
        result = finalized('valid')
        self.assertEqual(result['exit_code'], 0, result)
        self.assertTrue(result['passed'])

    def test_final_sealing_rejects_retained_bytes_changed_after_earlier_gates(self):
        for mode in ('version-warning', 'client-warning', 'proof-change', 'block-change',
                     'condition-change', 'phase-change', 'stage-record-change'):
            with self.subTest(mode=mode):
                result = finalized(mode)
                self.assertEqual(result['exit_code'], 1, result)
                self.assertFalse(result['passed'], result)

    def test_checksummed_project_feature_override_rejects_before_seal(self):
        for key, value in (('application/run/main_scene.linux', 'res://main.tscn'),
                           ('debug/settings/stdout/print_gpu_profile.linux', True),
                           ('rendering/driver/threads/thread_model.linux', 2)):
            with self.subTest(key=key), tempfile.TemporaryDirectory() as temporary:
                stage, record, resources, template, executable = data.manual_stage(Path(temporary))
                resources['project.binary'] = data.project_binary({key: value})
                executable.write_bytes(data.make_payload(template.read_bytes(), resources))
                caught = None
                try:
                    pack.inspect(executable, template, stage, record)
                except acq.accepted.Invalid as error:
                    caught = str(error)
                RESULTS.append({'mode': 'feature-override', 'key': key, 'value': value,
                                'payload_gate_rejected': caught is not None, 'error': caught})
                self.assertIsNotNone(caught, 'Payload gate accepted effective critical-setting override: ' + key)


if __name__ == '__main__':
    result = unittest.main(exit=False, verbosity=2).result
    (Path(__file__).parent / 'independent-results.json').write_text(json.dumps({
        'candidate': '04bc153e52341228b2f0d6f4ce72f784528ef1d4', 'synthetic_only': True,
        'native_runs': 0, 'methods': result.testsRun, 'failures': len(result.failures),
        'errors': len(result.errors), 'results': RESULTS}, indent=2) + '\n')
    raise SystemExit(0 if result.wasSuccessful() else 1)
