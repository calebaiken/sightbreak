#!/usr/bin/env python3
"""Additional pure boundary falsifiers; helper Popen is fake throughout."""
from contextlib import ExitStack
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


class BoundaryControls(unittest.TestCase):
    def test_real_finalization_positive_control(self):
        result = maintained.independent.finalized('valid')
        self.assertEqual(result['exit_code'], 0, result)
        self.assertTrue(result['passed'], result)
        RESULTS.append({**result, 'control': 'positive'})

    def test_final_strict_reread_must_match_first_accepted_identity(self):
        state = {'overall': False, 'after_restore': False, 'mutated': False}
        original_write, original_timer, original_read = acq.write, acq.signal.setitimer, Path.read_text
        def write(path, value):
            original_write(path, value)
            if Path(path).name == 'overall.json' and value.get('passed'):
                state['overall'] = True
        def timer(kind, seconds):
            result = original_timer(kind, seconds)
            if seconds == 0 and state['overall']:
                state['after_restore'] = True
            return result
        def read(path, *args, **kwargs):
            if state['after_restore'] and path.name == '01-version.stdout.log' and not state['mutated']:
                state['first_sha256'] = acq.digest(path)
                # This is before the real semantic reread. The reread observes
                # the new clean bytes; it must bind them to the first identity.
                path.write_bytes(b'changed clean log observed by the final semantic reread\n')
                state['changed_sha256'] = acq.digest(path)
                state['mutated'] = True
            value = original_read(path, *args, **kwargs)
            if state['mutated'] and path.name == '01-version.stdout.log':
                state['semantic_reread_observed_changed_bytes'] = value.startswith('changed clean log')
            return value
        with patch.object(acq, 'write', side_effect=write), \
                patch.object(acq.signal, 'setitimer', side_effect=timer), patch.object(Path, 'read_text', read):
            result = maintained.independent.finalized('valid')
        RESULTS.append({**result, **state, 'control': 'final-semantic-log-reread'})
        self.assertTrue(state['mutated'])
        self.assertTrue(state['semantic_reread_observed_changed_bytes'])
        self.assertNotEqual(state['first_sha256'], state['changed_sha256'])
        self.assertEqual(result['exit_code'], 1, result)
        self.assertFalse(result['passed'], result)

    def test_source_drift_during_manifest_publication_must_reject(self):
        state = {'mutated': False, 'sources_checked': 0}
        original_finalize, original_write, original_sources = acq.Acquisition.finalize, acq.write, acq.Acquisition.sources
        def finalize(controller):
            source = acq.ROOT / 'game/frozen.gd'
            source.parent.mkdir(parents=True)
            raw = b'extends Node\n# original source, never executed\n'
            source.write_bytes(raw)
            blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
            def git(*args):
                if args[0] == 'rev-parse':
                    return controller.commit
                if args[0] == 'status':
                    return '' if source.read_bytes() == raw else ' M game/frozen.gd\n'
                if args[0] == 'ls-files':
                    return '100644 ' + blob + ' 0\tgame/frozen.gd\0'
                raise AssertionError(args)
            controller.git = git
            def sources(instance):
                state['sources_checked'] += 1
                return original_sources(instance)
            controller.sources = MethodType(sources, controller)
            controller.original = controller.sources()
            state.update(source=source, controller=controller)
            return original_finalize(controller)
        def write(path, value):
            original_write(path, value)
            if Path(path).name == 'outputs.json' and not state['mutated']:
                state['source'].write_bytes(b'extends Node\n# changed during final manifest publication\n')
                state['mutated'] = True
                before = state['sources_checked']
                try:
                    state['controller'].sources()
                except acq.accepted.Invalid as error:
                    state['real_source_checker_rejects_changed_source'] = str(error)
                # Exclude the critic's own observation from wrapper call count.
                state['sources_checked'] = before
                state['checks_at_mutation'] = before
        with patch.object(acq.Acquisition, 'finalize', finalize), patch.object(acq, 'write', side_effect=write), \
                patch.object(acq, 'ACCEPTED', {}):
            result = maintained.independent.finalized('valid')
        state.pop('source', None)
        state.pop('controller', None)
        RESULTS.append({**result, **state, 'control': 'source-during-manifest-publication'})
        self.assertTrue(state['mutated'])
        self.assertIn('not exact and clean', state['real_source_checker_rejects_changed_source'])
        self.assertEqual(result['exit_code'], 1, result)
        self.assertFalse(result['passed'], result)


if __name__ == '__main__':
    result = unittest.main(exit=False, verbosity=2).result
    (Path(__file__).parent / 'boundary-results.json').write_text(json.dumps({
        'candidate': 'd0d94bec27f539b63e324c5468516ff2f0dd96d7', 'native_runs': 0,
        'methods': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
        'results': RESULTS}, indent=2) + '\n')
    raise SystemExit(0 if result.wasSuccessful() else 1)
