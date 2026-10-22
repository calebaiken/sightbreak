"""Real native PNG/Tesseract regressions; no settings flag can satisfy these."""
import csv
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import unittest

from PIL import Image
from capture_desktop_layouts import DEFAULT_SIZES, hud_footer_region, ocr_input, ocr_lines, rendered_hud_matches

FIXTURES = Path(__file__).resolve().parents[1] / 'docs/reports/gauntlet/native-layout-ocr'


class RenderedLayoutHUDTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tesseract = os.environ.get('TESSERACT_BIN') or shutil.which('tesseract')
        if not cls.tesseract:
            raise unittest.SkipTest('Actual Tesseract is required; no OCR mock substitutes for rendered evidence')
        cls.temporary = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temporary.cleanup)
        selected = os.environ.get('SIGHTBREAK_OCR_TEST_OUTPUT')
        cls.output = Path(selected) if selected else Path(cls.temporary.name)
        if selected:
            cls.output.mkdir(parents=True, exist_ok=False)
        cls.measurements = []
        cls.groups = {}
        cls.manifest = json.loads((FIXTURES / 'fixtures.json').read_text())
        for fixture in cls.manifest['raw_native_fixtures']:
            path = FIXTURES / fixture['path']
            if hashlib.sha256(path.read_bytes()).hexdigest() != fixture['sha256']:
                raise AssertionError('Native fixture changed: ' + str(path))
            with Image.open(path) as raw:
                cls.groups[path.stem] = (cls.analyze(raw, path.stem, False),
                                         cls.analyze(raw, path.stem, True))

    @classmethod
    def analyze(cls, raw, name, footer):
        factor = 4 if footer else (3 if raw.width < 1100 else 2)
        region = hud_footer_region(raw.size) if footer else None
        data = ocr_input(raw, factor, region=region, threshold=None if footer else 145)
        label = name + ('-footer' if footer else '-full')
        (cls.output / (label + '-analysis.png')).write_bytes(data)
        command = [cls.tesseract, 'stdin', 'stdout', '--psm', '11', 'tsv']
        started = time.monotonic()
        result = subprocess.run(command, input=data, capture_output=True, timeout=5, check=True)
        duration = time.monotonic() - started
        text = result.stdout.decode('utf-8')
        (cls.output / (label + '.tsv')).write_text(text)
        cls.measurements.append({'label': label, 'seconds': duration, 'exit_code': result.returncode,
                                 'analysis_region': region, 'scale': factor,
                                 'analysis_sha256': hashlib.sha256(data).hexdigest(),
                                 'words': [r['text'] for r in csv.DictReader(io.StringIO(text), delimiter='\t') if r['text'].strip()]})
        return ocr_lines(text, factor, origin=region[:2] if region else (0, 0))

    def test_actual_failed_desktop_png_is_recognized_from_full_and_footer_pixels(self):
        full, footer = self.groups['desktop']
        self.assertTrue(rendered_hud_matches(full, False, footer))
        self.assertFalse(rendered_hud_matches(full, True))
        baseline = gzip.decompress((FIXTURES / 'baseline-desktop.tsv.gz').read_bytes()).decode('utf-8')
        baseline_words = {row['text'].upper() for row in csv.DictReader(io.StringIO(baseline), delimiter='\t')}
        self.assertIn('HEALTH', baseline_words)
        self.assertFalse({'TAB', 'ROSTER', 'ESC'}.issubset(baseline_words))

    def test_actual_touch_hud_cannot_be_accepted_as_keyboard_hud(self):
        full, footer = self.groups['touch']
        self.assertTrue(rendered_hud_matches(full, True))
        self.assertFalse(rendered_hud_matches(full, False, footer))
        # Even a keyboard footer from another frame cannot erase rendered FIRE.
        self.assertFalse(rendered_hud_matches(full, False, self.groups['desktop'][1]))

    def test_actual_menu_settings_pause_and_roster_are_rejected(self):
        for name in ['menu', 'field-menu', 'settings', 'roster']:
            with self.subTest(screen=name):
                full, footer = self.groups[name]
                self.assertFalse(rendered_hud_matches(full, False, footer))
                self.assertFalse(rendered_hud_matches(full, True))

    def test_every_declared_native_size_has_positive_and_wrong_screen_controls(self):
        coverage = {}
        for fixture in self.manifest['raw_native_fixtures']:
            size = 'x'.join(map(str, fixture['size']))
            coverage.setdefault(size, set()).add(fixture['screen'])
            with self.subTest(size=size, screen=fixture['screen'], path=fixture['path']):
                full, footer = self.groups[Path(fixture['path']).stem]
                self.assertEqual(rendered_hud_matches(full, False, footer), fixture['expected'] == 'desktop')
                self.assertEqual(rendered_hud_matches(full, True), fixture['expected'] == 'touch')
        self.assertEqual(set(coverage), set(DEFAULT_SIZES))
        for size, screens in coverage.items():
            with self.subTest(size=size):
                self.assertEqual(screens, {'hud', 'menu', 'roster', 'field-menu', 'settings'})

    def test_missing_footer_pixels_cannot_be_replaced_by_health_or_settings(self):
        with Image.open(FIXTURES / 'fixtures/desktop.png') as raw:
            missing = raw.copy()
            missing.paste((0, 0, 0), hud_footer_region(raw.size))
            full = self.analyze(missing, 'erased-footer-counterexample', False)
            footer = self.analyze(missing, 'erased-footer-counterexample', True)
        self.assertFalse(rendered_hud_matches(full, False, footer))
        self.assertFalse(rendered_hud_matches(self.groups['desktop'][0], False))

    def test_cropped_coordinate_parser_retains_native_pixel_origin(self):
        footer = self.groups['desktop'][1]
        words = [r for line in footer for r in line if r['text'].upper().strip('’') in {'TAB', 'ESC'}]
        self.assertEqual(len(words), 2)
        for word in words:
            self.assertGreater(word['top'], 650)
            self.assertLess(word['left'], 800)

    def test_original_native_pngs_remain_byte_identical_after_analysis(self):
        for fixture in self.manifest['raw_native_fixtures']:
            self.assertEqual(hashlib.sha256((FIXTURES / fixture['path']).read_bytes()).hexdigest(), fixture['sha256'])

    @classmethod
    def tearDownClass(cls):
        report = {'scope': 'Saved native image and explicit erased-footer counterexample OCR; not native interaction acceptance',
                  'tesseract': subprocess.check_output([cls.tesseract, '--version'], text=True).splitlines()[0],
                  'measurements': cls.measurements}
        (cls.output / 'results.json').write_text(json.dumps(report, indent=2) + '\n')
        print('RENDERED_LAYOUT_OCR=' + json.dumps(report, sort_keys=True))


if __name__ == '__main__':
    unittest.main()
