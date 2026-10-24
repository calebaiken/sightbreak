@'
import ast
import io
import pathlib
import re
import sys
import types
import unittest
from unittest.mock import Mock

ROOT = pathlib.Path.cwd()
sys.path.insert(0, str(ROOT / 'scripts'))

class LivingHudNegativeControl(unittest.TestCase):
    def test_blank_and_zero_health_status_are_accepted(self):
        tree = ast.parse((ROOT / 'scripts/verify_offline_export.py').read_text())
        main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
        function = next(n for n in main.body if isinstance(n, ast.FunctionDef) and n.name == 'read_hud')
        code = compile(ast.fix_missing_locations(ast.Module(body=[function], type_ignores=[])), str(ROOT / 'scripts/verify_offline_export.py'), 'exec')
        crop = types.SimpleNamespace(width=10, height=10, resize=lambda size: types.SimpleNamespace(save=lambda stream, format: stream.write(b'png')))
        image = types.SimpleNamespace(crop=lambda box: crop)
        for status in (b'', b'000 HEALTH'):
            with self.subTest(status=status):
                scope = dict(Image=types.SimpleNamespace(open=lambda path: image), out=ROOT, args=types.SimpleNamespace(tesseract='never-executed'), io=io, re=re, subprocess=types.SimpleNamespace(check_output=Mock(side_effect=[status, b'12 / 60']), DEVNULL=None))
                exec(code, scope)
                actual = scope['read_hud']('not-a-real-file')
                self.assertEqual(actual['ammo'], 12)
                self.assertEqual(actual['status_ocr'], status.decode())

baseline = unittest.defaultTestLoader.discover('scripts', pattern='test_build_manifest.py')
suite = unittest.TestSuite([baseline, unittest.defaultTestLoader.loadTestsFromTestCase(LivingHudNegativeControl)])
result = unittest.TextTestRunner(verbosity=2, stream=sys.stdout).run(suite)
raise SystemExit(not result.wasSuccessful())
'@ | python -B -
