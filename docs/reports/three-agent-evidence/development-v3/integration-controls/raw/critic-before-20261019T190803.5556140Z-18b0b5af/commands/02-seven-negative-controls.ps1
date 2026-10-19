@'
import ast
import contextlib
import io
import json
import pathlib
import re
import stat
import subprocess
import sys
import tempfile
import types
import unittest
import zipfile
from unittest.mock import Mock, patch

ROOT = pathlib.Path.cwd()
sys.path.insert(0, str(ROOT / 'scripts'))
import build_manifest as m
import verify_builds as v

class IsolatedAdversarialReview(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix='sightbreak-readonly-review-', dir=str(ROOT.parent))
        self.addCleanup(tmp.cleanup)
        self.root = pathlib.Path(tmp.name)
        self.builds = self.root / 'builds'
        self.current = dict(source_commit='A', source_game_tree='TREE', source_content_sha256='BYTES', source_game_dirty=False, source_dirty=False)
        for name, value in [('ROOT', self.root), ('BUILDS', self.builds), ('source', lambda: dict(self.current))]:
            p = patch.object(m, name, value)
            p.start()
            self.addCleanup(p.stop)

    def exports(self):
        for target, path in m.OUTPUTS.items():
            m.begin(target)
            out = self.builds / path
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(b'original-export-from-A')
            m.finish(target)

    def test_repro_old_outputs_can_be_reattested_under_another_commit(self):
        self.exports()
        self.current['source_commit'] = 'B'
        for target in m.OUTPUTS:
            m.begin(target)
            m.finish(target)  # No exporter and no output write.
        with contextlib.redirect_stdout(io.StringIO()):
            m.package()
        report = json.loads((self.builds / 'manifest.json').read_text())
        self.assertEqual(report['source_commit'], 'B')
        with zipfile.ZipFile(self.builds / 'sightbreak-linux-debug.zip') as archive:
            self.assertEqual(archive.read('linux/sightbreak.x86_64'), b'original-export-from-A')

    def test_repro_executable_wrapper_is_packaged_without_execute_permissions(self):
        self.exports()
        wrapper = self.builds / 'linux/sightbreak.sh'
        wrapper.write_text('#!/bin/sh\nexec ./sightbreak.x86_64\n')
        wrapper.chmod(0o755)
        m.finish('linux')
        with contextlib.redirect_stdout(io.StringIO()):
            m.package()
        with zipfile.ZipFile(self.builds / 'sightbreak-linux-debug.zip') as archive:
            mode = archive.getinfo('linux/sightbreak.sh').external_attr >> 16
            self.assertEqual(stat.S_IMODE(mode), 0o644)

    def test_repro_failed_reverification_keeps_old_passed_report(self):
        self.exports()
        verification = self.builds / 'verification'
        verification.mkdir()
        result_path = verification / 'results.json'
        result_path.write_text('{"passed": true, "old": true}')
        with patch.object(v, 'ROOT', self.root), patch.object(v, 'BUILDS', self.builds), patch.object(v, 'source', lambda: dict(self.current)), patch.object(v.subprocess, 'run', return_value=types.SimpleNamespace(returncode=1, stdout='current attempt failed')):
            with self.assertRaisesRegex(AssertionError, 'linux-menu failed'):
                v.main()
        self.assertTrue(json.loads(result_path.read_text())['passed'])
        self.assertEqual((verification / 'linux-menu.log').read_text(), 'current attempt failed')

    def test_repro_timeout_discards_captured_stdout_and_keeps_old_log(self):
        self.exports()
        verification = self.builds / 'verification'
        verification.mkdir()
        log = verification / 'linux-menu.log'
        log.write_text('old success output')
        timeout = subprocess.TimeoutExpired(['not-executed'], 120, output='current failure details')
        with patch.object(v, 'ROOT', self.root), patch.object(v, 'BUILDS', self.builds), patch.object(v, 'source', lambda: dict(self.current)), patch.object(v.subprocess, 'run', side_effect=timeout):
            with self.assertRaises(subprocess.TimeoutExpired):
                v.main()
        self.assertEqual(log.read_text(), 'old success output')

    def test_repro_package_accepts_change_after_payload_check(self):
        self.exports()
        note = self.builds / 'linux/NOTICE.txt'
        note.write_bytes(b'original secondary payload')
        m.finish('linux')
        real_zip = zipfile.ZipFile
        class ChangeAtArchiveOpen(real_zip):
            def __enter__(instance):
                if pathlib.Path(instance.filename).name == 'sightbreak-linux-debug.zip':
                    note.write_bytes(b'changed secondary payload')
                return super().__enter__()
        with patch.object(m.zipfile, 'ZipFile', ChangeAtArchiveOpen), contextlib.redirect_stdout(io.StringIO()):
            m.package()
        report = json.loads((self.builds / 'manifest.json').read_text())
        record = report['exports'][0]
        self.assertNotEqual(record['payload'], m.payload('linux'))
        with real_zip(self.builds / 'sightbreak-linux-debug.zip') as archive:
            self.assertEqual(archive.read('linux/NOTICE.txt'), b'changed secondary payload')

    def test_repro_living_hud_check_accepts_blank_and_zero_health_status(self):
        tree = ast.parse((ROOT / 'scripts/verify_offline_export.py').read_text())
        main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
        read_hud = next(n for n in main.body if isinstance(n, ast.FunctionDef) and n.name == 'read_hud')
        code = compile(ast.fix_missing_locations(ast.Module(body=[read_hud], type_ignores=[])), str(ROOT / 'scripts/verify_offline_export.py'), 'exec')
        crop = types.SimpleNamespace(width=10, height=10, resize=lambda size: types.SimpleNamespace(save=lambda stream, format: stream.write(b'png')))
        image = types.SimpleNamespace(crop=lambda box: crop)
        for status in (b'', b'000 HEALTH'):
            with self.subTest(status=status):
                namespace = dict(Image=types.SimpleNamespace(open=lambda path: image), out=self.root, io=io, re=re, subprocess=types.SimpleNamespace(check_output=Mock(side_effect=[status, b'12 / 60'], ), DEVNULL=None))
                exec(code, namespace)
                self.assertEqual(namespace['read_hud']('fixture')['ammo'], 12)

    def test_repro_project_version_disagrees_with_manifest_and_presets(self):
        project = (ROOT / 'game/project.godot').read_text()
        actual = re.search(r'^config/version="([^"]+)"$', project, re.M)[1]
        self.assertEqual(actual, '0.3.1-dev')
        self.assertEqual(m.VERSION, '0.3.2-dev')
        self.assertNotEqual(actual, m.VERSION)

suite = unittest.defaultTestLoader.loadTestsFromTestCase(IsolatedAdversarialReview)
result = unittest.TextTestRunner(verbosity=2, stream=sys.stdout).run(suite)
raise SystemExit(not result.wasSuccessful())
'@ | python -B -
