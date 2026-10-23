#!/usr/bin/env python3
"""Pure portability controls for test-owned temporary roots; no native execution."""
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import macos_ordinary_input as ordinary
from probe_macos_input import NativePrerequisiteBlocked
import test_macos_ordinary
import test_macos_ordinary_controller


class TemporaryRootControls(unittest.TestCase):
    def test_runtime_still_rejects_raw_alias_and_accepts_canonical_owned_target(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve(strict=True)
            target = root / 'physical'
            target.mkdir()
            alias = root / 'alias'
            alias.symlink_to(target, target_is_directory=True)
            with self.assertRaisesRegex(NativePrerequisiteBlocked, 'Symlink in native isolation path'):
                ordinary.inventory(alias)
            self.assertEqual(ordinary.inventory(target)['directory_exists'], True)
            self.assertEqual(alias.resolve(strict=True), target)

    def test_both_full_pure_suites_use_canonical_test_roots_under_aliased_tempdir(self):
        # Emulates macOS /var -> /private/var without modifying system paths or
        # the runtime guard. Only freshly owned temporary fixture roots resolve.
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve(strict=True)
            target = root / 'physical'
            target.mkdir()
            alias = root / 'alias'
            alias.symlink_to(target, target_is_directory=True)
            suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromModule(module)
                                       for module in (test_macos_ordinary, test_macos_ordinary_controller))
            transcript = io.StringIO()
            with patch.object(tempfile, 'tempdir', str(alias)), patch('sys.stdout', new_callable=io.StringIO):
                self.assertEqual(tempfile.gettempdir(), str(alias))
                result = unittest.TextTestRunner(stream=transcript, verbosity=2).run(suite)
            self.assertEqual(result.testsRun, 21, transcript.getvalue())
            self.assertTrue(result.wasSuccessful(), transcript.getvalue())
            self.assertEqual(result.skipped, [], transcript.getvalue())
            # Resolving test-owned roots must not resolve aliases supplied to
            # production functions, including descendants of that alias.
            with self.assertRaises(NativePrerequisiteBlocked):
                ordinary.inventory(alias / 'uncreated-userdata')


if __name__ == '__main__':
    unittest.main()
