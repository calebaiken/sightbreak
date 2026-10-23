#!/usr/bin/env python3
"""Independent pure falsifiers. Every derived row/image is synthetic, never OCR."""
import copy
import hashlib
import json
import math
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'scripts'))
import macos_deploy_ocr as analysis
import macos_ordinary_input as ordinary
import verify_macos_ordinary as driver
from test_macos_ordinary_controller import SYNTHETIC_DIGEST, SyntheticController

ORIGINAL = ROOT / 'docs/reports/gauntlet/m2-mac-derived-ocr/original-native-39912086121/macos-ordinary-input'


def synthetic_receipt():
    data = json.loads((ORIGINAL / '01-focused-menu.json').read_text())
    width, height = data['image_dimensions']
    raw = next(row for row in data['text'] if row['text'].startswith('DEPLOY'))
    derived = copy.deepcopy(raw)
    derived['confidence'] = .8
    data['derived_deploy_analysis'] = {
        'schema': 1, 'profile': analysis.PROFILE, 'scope': analysis.SCOPE,
        'source_png_sha256': '1' * 64, 'analysis_png_sha256': '2' * 64,
        'owner_pid': data['owner_pid'], 'window_id': data['window_id'],
        'bounds_points_including_chrome': copy.deepcopy(data['bounds_points_including_chrome']),
        'source_point_pixel_scale': data['point_pixel_scale'],
        'source_image_dimensions': [width, height], 'analysis_image_dimensions': [width * 2, height * 2],
        'source_crop_pixels_top_left': [0, 0, width, height], 'scale': 2,
        'normalized_box_space': 'native-full-window-bottom-left', 'resampling': 'CoreGraphics-high',
        'recognition_level': 'accurate', 'recognition_languages': ['en-US'],
        'uses_language_correction': False, 'custom_words': [], 'text': [derived]}
    return data


def bound(data):
    width, height = data['image_dimensions']
    analysis.bind_analysis(data, '1' * 64, '2' * 64, [width, height], [width * 2, height * 2])
    return data


class IndependentFalsifiers(unittest.TestCase):
    def test_mixed_separator_and_case_whitespace_keep_original_center(self):
        for raw_separator, derived_separator in (('·', '•'), ('•', '·')):
            data = synthetic_receipt()
            raw = next(row for row in data['text'] if row['text'].startswith('DEPLOY'))
            original = copy.deepcopy(raw['box_normalized_bottom_left'])
            raw['text'] = 'deploy ' + raw_separator + ' offline 5v5'
            data['derived_deploy_analysis']['text'][0]['text'] = ' DEPLOY\t' + derived_separator + '  OFFLINE 5V5\n'
            bx, by, bw, bh = data['bounds_points_including_chrome']
            x, y, w, h = original
            self.assertEqual(ordinary.label_point(bound(data), analysis.LABEL),
                             (bx + (x + w / 2) * bw, by + (1 - y - h / 2) * bh))
            self.assertEqual(raw['confidence'], .5)
            self.assertEqual(raw['box_normalized_bottom_left'], original)

    def test_next_float_below_point_eight_is_rejected(self):
        data = synthetic_receipt()
        data['derived_deploy_analysis']['text'][0]['confidence'] = math.nextafter(.8, 0)
        with self.assertRaises(RuntimeError): ordinary.label_point(bound(data), analysis.LABEL)

    def test_center_agreement_is_reciprocal(self):
        # One center lies in the other box, but the converse fails.
        for raw_box, derived_box in (([.1, .4, .4, .1], [.32, .4, .05, .1]),
                                     ([.32, .4, .05, .1], [.1, .4, .4, .1])):
            data = synthetic_receipt()
            next(row for row in data['text'] if row['text'].startswith('DEPLOY'))['box_normalized_bottom_left'] = raw_box
            data['derived_deploy_analysis']['text'][0]['box_normalized_bottom_left'] = derived_box
            with self.assertRaises(RuntimeError): ordinary.label_point(bound(data), analysis.LABEL)

    def test_corresponding_derived_box_cannot_move_the_click(self):
        data = synthetic_receipt()
        native = next(row for row in data['text'] if row['text'].startswith('DEPLOY'))
        x, y, w, h = native['box_normalized_bottom_left']
        data['derived_deploy_analysis']['text'][0]['box_normalized_bottom_left'] = [x - w / 8, y, w * 1.5, h]
        expected = copy.deepcopy(data)
        expected.pop('derived_deploy_analysis')
        native_expected = next(row for row in expected['text'] if row['text'].startswith('DEPLOY'))
        native_expected.update(text=analysis.LABEL, confidence=.8)
        self.assertEqual(ordinary.label_point(bound(data), analysis.LABEL), ordinary.label_point(expected, analysis.LABEL))

    def test_binding_covers_extra_receipt_fields_and_provenance_returns_copies(self):
        data = bound(synthetic_receipt())
        before = analysis.receipt_digest(data)
        row = analysis.derived_deploy_row(data)
        provenance = analysis.deploy_provenance(data)
        row['box_normalized_bottom_left'][0] = -1
        provenance['derived_caption']['text'] = 'WRONG'
        provenance['source_image_dimensions'][0] = 1
        self.assertEqual(analysis.receipt_digest(data), before)
        data['unexpected_mutation_after_binding'] = True
        with self.assertRaises(RuntimeError): ordinary.label_point(data, analysis.LABEL)

    def test_consistent_false_scale_still_fails_native_geometry(self):
        data = synthetic_receipt()
        data['point_pixel_scale'] = 2
        data['derived_deploy_analysis']['source_point_pixel_scale'] = 2
        with self.assertRaises(RuntimeError): ordinary.label_point(bound(data), analysis.LABEL)

    def test_json_roundtrip_cannot_preserve_typed_authority(self):
        data = bound(synthetic_receipt())
        payload = {key: value for key, value in data.items() if key != analysis.BINDING}
        payload[analysis.BINDING] = {'receipt_sha256': data[analysis.BINDING].receipt_sha256}
        forged = json.loads(json.dumps(payload))
        with self.assertRaises(RuntimeError): ordinary.label_point(forged, analysis.LABEL)

    def test_controller_binds_real_hashes_of_synthetic_files_before_events(self):
        class HashController(SyntheticController):
            def popen(self, arguments, **kwargs):
                process = super().popen(arguments, **kwargs)
                if '--analysis-mode' in arguments:
                    png = Path(arguments[arguments.index('--png') + 1])
                    derived = Path(arguments[arguments.index('--deploy-analysis-png') + 1])
                    receipt = Path(arguments[arguments.index('--report') + 1])
                    data = json.loads(receipt.read_text())
                    data['derived_deploy_analysis']['source_png_sha256'] = hashlib.sha256(png.read_bytes()).hexdigest()
                    data['derived_deploy_analysis']['analysis_png_sha256'] = hashlib.sha256(derived.read_bytes()).hexdigest()
                    receipt.write_text(json.dumps(data))
                    # The maintained harness normally mocks digests. Use real
                    # hashes for existing synthetic files in this control only.
                    driver.digest = lambda path: (hashlib.sha256(Path(path).read_bytes()).hexdigest()
                                                  if Path(path).is_file() else SYNTHETIC_DIGEST)
                    if self.fault in ('raw-file', 'derived-file'):
                        path = png if self.fault == 'raw-file' else derived
                        path.write_bytes(path.read_bytes() + b'CHANGED SYNTHETIC FILE')
                return process

        for fault in (None, 'raw-file', 'derived-file'):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temporary:
                harness = HashController(Path(temporary).resolve(strict=True) / 'synthetic', fault)
                code, report = harness.execute()
                self.assertEqual(code, int(fault is not None), report.get('failure'))
                self.assertEqual(harness.deployed, fault is None)
                if fault:
                    self.assertEqual(report['cg_event_post_attempts'], 0)
                    self.assertIn('provenance mismatch', report['failure']['message'])
                self.assertTrue(all(row['owned_group_gone'] for row in report['cleanup']))


if __name__ == '__main__':
    unittest.main(verbosity=2)
