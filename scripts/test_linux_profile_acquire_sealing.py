#!/usr/bin/env python3
"""Pure late-byte regressions derived from the retained independent falsifiers.

The independent helper runs real acquisition gates with fake Popen and invented
ELF/measurements/proof bytes. Its original bytes remain in the report unchanged.
"""
from contextlib import ExitStack
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import linux_profile_acquire as acq
import linux_profile_payload as pack
import test_linux_profile_acquire as data

RETAINED = acq.ROOT / 'docs/reports/gauntlet/m1-linux-profile-acquisition/correction-r1/retained-rejection/test_independent_controls.py'
spec = importlib.util.spec_from_file_location('retained_acquisition_falsifiers', RETAINED)
independent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(independent)


class SealingTests(unittest.TestCase):
    def test_original_independent_positive_and_all_ten_falsifiers(self):
        result = unittest.TestResult()
        unittest.defaultTestLoader.loadTestsFromTestCase(independent.IndependentControls).run(result)
        self.assertEqual(result.testsRun, 3)
        self.assertEqual(result.errors, [])
        self.assertEqual(result.failures, [])
        self.assertFalse(next(row for row in reversed(independent.RESULTS) if row['mode'] == 'version-warning')['command_log_hash_still_matches'])
        self.assertFalse(next(row for row in reversed(independent.RESULTS) if row['mode'] == 'block-change')['block_hash_still_matches'])

    def test_publication_mutations_cannot_rebaseline_prior_evidence(self):
        # Each hook runs after its relevant I/O returns, so cached readbacks and
        # fresh hashes cannot conceal a mutation of earlier accepted bytes.
        targets = ['01-version.stdout.log', 'native-block/01-/off/client.log',
                   'native-block/01-/off/proof.png', 'native-block/block.json',
                   'native-block/01-/off/condition.json', 'native-block/01-/off/metrics.json',
                   'native-block/xvfb.log', 'version.phase.json', 'finalize.phase.json',
                   'diagnostic-stage.json', 'outputs.json', 'overall.json', 'added-after-close.txt']
        for hook in ('manifest-write', 'overall-write', 'overall-read', 'stdout', 'alarm-restore'):
            for target in targets:
                if target == 'overall.json' and hook == 'manifest-write':
                    continue  # Not published yet; later closed-set control covers it.
                with self.subTest(hook=hook, target=target), ExitStack() as stack:
                    original_write, original_read = acq.write, acq.read_json
                    original_print, original_timer = print, acq.signal.setitimer
                    state = {'mutated': False, 'overall': False}
                    def mutate():
                        if not state['mutated']:
                            state['mutated'] = True
                            # Keep JSON syntactically valid so the independent
                            # helper can inspect the rejected raw package too.
                            (acq.OUTPUT / target).write_bytes(b'{}\n' if target.endswith('.json')
                                                            else b'WARNING: late publication mutation\n')
                    def write(path, value):
                        original_write(path, value)
                        if Path(path).name == 'overall.json' and value.get('passed'):
                            state['overall'] = True
                            if hook == 'overall-write': mutate()
                        if Path(path).name == 'outputs.json' and hook == 'manifest-write': mutate()
                    def read(path):
                        value = original_read(path)
                        if Path(path).name == 'overall.json' and value.get('passed') and hook == 'overall-read': mutate()
                        return value
                    def printed(*args, **kwargs):
                        original_print(*args, **kwargs)
                        if state['overall'] and hook == 'stdout': mutate()
                    def timer(kind, seconds):
                        result = original_timer(kind, seconds)
                        if seconds == 0 and state['overall'] and hook == 'alarm-restore': mutate()
                        return result
                    stack.enter_context(patch.object(acq, 'write', side_effect=write))
                    stack.enter_context(patch.object(acq, 'read_json', side_effect=read))
                    stack.enter_context(patch('builtins.print', side_effect=printed))
                    stack.enter_context(patch.object(acq.signal, 'setitimer', side_effect=timer))
                    result = independent.finalized('valid')
                    self.assertTrue(state['mutated'])
                    self.assertEqual(result['exit_code'], 1, result)
                    self.assertFalse(result['passed'], result)

    def test_first_identity_cannot_be_rebound_and_closed_set_cannot_grow(self):
        with tempfile.TemporaryDirectory() as temporary, patch.object(acq, 'OUTPUT', Path(temporary)):
            path = Path(temporary) / 'evidence.log'
            path.write_bytes(b'original bytes')
            evidence = acq.Evidence({})
            evidence.bind(path)
            path.write_bytes(b'changed bytes')
            with self.assertRaisesRegex(acq.accepted.Invalid, 'identity drift'):
                evidence.bind(path)
            with self.assertRaisesRegex(acq.accepted.Invalid, 'identity drift'):
                evidence.close_outputs()
            path.write_bytes(b'original bytes')
            self.assertEqual(evidence.close_outputs()['evidence.log'], data.descriptor(path.read_bytes()))
            (Path(temporary) / 'unexpected').write_bytes(b'late extra file')
            with self.assertRaisesRegex(acq.accepted.Invalid, 'output set changed'):
                evidence.validate(closed=True)


class FeatureSettingsTests(unittest.TestCase):
    def test_undeclared_selectors_reject_even_if_their_value_is_safe(self):
        for key, value in (
                ('application/run/main_scene.linux.debug', 'res://diagnostics/linux_profile_overhead.tscn'),
                ('debug/settings/stdout/print_gpu_profile.linux', False),
                ('rendering/driver/threads/thread_model.custom_feature', 1),
                ('rendering/renderer/rendering_method.mobile.linux', 'gl_compatibility')):
            with self.subTest(key=key), tempfile.TemporaryDirectory() as temporary:
                stage, record, resources, template, executable = data.manual_stage(Path(temporary))
                resources['project.binary'] = data.project_binary({key: value})
                executable.write_bytes(data.make_payload(template.read_bytes(), resources))
                with self.assertRaisesRegex(acq.accepted.Invalid, 'Undeclared packed critical'):
                    pack.inspect(executable, template, stage, record)

    def test_declared_safe_variant_and_permitted_default_omissions_pass(self):
        with tempfile.TemporaryDirectory() as temporary:
            stage, record, resources, template, executable = data.manual_stage(Path(temporary))
            source = stage / 'project.godot'
            source.write_text(source.read_text().replace('driver/threads/thread_model=1\n',
                              'driver/threads/thread_model=1\ndriver/threads/thread_model.linux=1\n'))
            record['files']['project.godot'] = data.descriptor(source.read_bytes())
            resources['project.binary'] = data.project_binary({'rendering/driver/threads/thread_model.linux': 1},
                omitted=('rendering/driver/threads/thread_model', 'debug/settings/stdout/print_gpu_profile'))
            executable.write_bytes(data.make_payload(template.read_bytes(), resources))
            result, _ = pack.inspect(executable, template, stage, record)
            self.assertEqual(result['project']['rendering/driver/threads/thread_model.linux'], 1)
            self.assertEqual(result['project']['rendering/renderer/rendering_method.mobile'], 'gl_compatibility')
            self.assertIs(result['project']['debug/settings/stdout/print_gpu_profile'], False)

    def test_unsafe_staged_variant_rejects_and_required_base_cannot_be_omitted(self):
        for mode in ('unsafe-source', 'omitted-main', 'wrong-type'):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as temporary:
                stage, record, resources, template, executable = data.manual_stage(Path(temporary))
                if mode == 'unsafe-source':
                    source = stage / 'project.godot'
                    source.write_text(source.read_text().replace('driver/threads/thread_model=1\n',
                                      'driver/threads/thread_model=1\ndriver/threads/thread_model.linux=2\n'))
                    record['files']['project.godot'] = data.descriptor(source.read_bytes())
                    resources['project.binary'] = data.project_binary({'rendering/driver/threads/thread_model.linux': 2})
                elif mode == 'omitted-main':
                    resources['project.binary'] = data.project_binary(omitted=('application/run/main_scene',))
                else:
                    resources['project.binary'] = data.project_binary({'rendering/driver/threads/thread_model': True})
                executable.write_bytes(data.make_payload(template.read_bytes(), resources))
                with self.assertRaisesRegex(acq.accepted.Invalid, 'staged critical|Wrong packed project'):
                    pack.inspect(executable, template, stage, record)


if __name__ == '__main__':
    unittest.main()
