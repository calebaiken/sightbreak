#!/usr/bin/env python3
"""Pure synthetic OCR counterexamples; no OCR, Swift, native capture or engine."""
import copy
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest

import macos_deploy_ocr as analysis
import macos_ordinary_input as ordinary
import verify_macos_ordinary as driver
from test_macos_ordinary import capture, hud_capture
from test_macos_ordinary_controller import SYNTHETIC_DIGEST, SyntheticController, synthetic_analysis

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = ROOT/'docs/reports/gauntlet/m2-mac-derived-ocr/original-native-39912086121/macos-ordinary-input'


def candidate():
    image = capture()
    image['text'][3]['text'] = 'DEPLOY • OFFLINE 5V5'
    image['text'][3]['confidence'] = .5
    image['derived_deploy_analysis'] = synthetic_analysis(image)
    image['derived_deploy_analysis']['text'][3]['confidence'] = .8
    return image


def bind(image, **changes):
    arguments = {'source_sha256': SYNTHETIC_DIGEST, 'analysis_sha256': SYNTHETIC_DIGEST,
                 'source_dimensions': image['image_dimensions'],
                 'analysis_dimensions': [value*2 for value in image['image_dimensions']]}
    arguments.update(changes)
    analysis.bind_analysis(image, **arguments)
    return image


class DeployAnalysisControls(unittest.TestCase):
    def rejected(self, image):
        with self.assertRaises(RuntimeError):
            bind(image)
            ordinary.label_point(image, analysis.LABEL)

    def test_original_low_confidence_bullet_receipts_still_reject_without_new_observations(self):
        for name in ('00-startup-menu-7', '01-focused-menu'):
            image = json.loads((ORIGINAL/(name+'.json')).read_text())
            before = copy.deepcopy(image)
            row = next(row for row in image['text'] if row['text'].startswith('DEPLOY'))
            self.assertEqual((row['text'], row['confidence']), ('DEPLOY • OFFLINE 5V5', .5))
            with self.assertRaises(RuntimeError): ordinary.label_point(image, analysis.LABEL)
            self.assertEqual(image, before)

    def test_synthetic_high_confidence_analysis_preserves_native_center_and_raw_rows(self):
        for punctuation in ('·', '•'):
            for scale in (1, 2):
                with self.subTest(punctuation=punctuation, scale=scale):
                    image = candidate()
                    image['point_pixel_scale'] = scale
                    image['image_dimensions'] = [960*scale, 568*scale]
                    image['derived_deploy_analysis'] = synthetic_analysis(image)
                    row = image['derived_deploy_analysis']['text'][3]
                    row['text'], row['confidence'] = 'DEPLOY '+punctuation+' OFFLINE 5V5', .8
                    raw = copy.deepcopy(image['text'])
                    self.assertEqual(ordinary.label_point(bind(image), analysis.LABEL), (280, 344.4))
                    self.assertEqual(image['text'], raw)
                    self.assertEqual(image['text'][3]['confidence'], .5)
                    self.assertEqual(analysis.deploy_provenance(image)['scale'], 2)
        # Original native pixels/observations remain untouched. Only the derived
        # candidate below is synthetic, so this is no confidence-improvement claim.
        image = json.loads((ORIGINAL/'01-focused-menu.json').read_text())
        image['derived_deploy_analysis'] = synthetic_analysis(image)
        native = next(row for row in image['text'] if row['text'].startswith('DEPLOY'))
        derived = next(row for row in image['derived_deploy_analysis']['text'] if row['text'].startswith('DEPLOY'))
        derived['confidence'] = .8
        x, y, width, height = native['box_normalized_bottom_left']
        bx, by, bw, bh = image['bounds_points_including_chrome']
        self.assertEqual(ordinary.label_point(bind(image), analysis.LABEL),
                         (bx+(x+width/2)*bw, by+(1-y-height/2)*bh))

    def test_derived_confidence_never_weakens_point_eight(self):
        for value in (.7999999, -.1, float('nan'), float('inf'), True, '0.99', None, 1.01):
            with self.subTest(value=value):
                image = candidate();image['derived_deploy_analysis']['text'][3]['confidence'] = value
                self.rejected(image)

    def test_exact_words_and_only_observed_separator_equivalence(self):
        for text in ('DEPLOY', 'DEPLOY · ONLINE 5V5', 'DEPLOY · OFFLINE 5V4', 'OFFLINE 5V5 · DEPLOY',
                     'DEPLOY : OFFLINE 5V5', 'DEPLOY - OFFLINE 5V5', 'DEPLOY ‧ OFFLINE 5V5',
                     'DEPLOY · OFFLINE 5V5 NOW', 'DEPLOY · OFFLINE', ''):
            for side in ('text', 'derived'):
                with self.subTest(text=text, side=side):
                    image = candidate()
                    rows = image['text'] if side == 'text' else image['derived_deploy_analysis']['text']
                    rows[3]['text'] = text
                    self.rejected(image)

    def test_duplicate_or_invalid_native_corroboration_is_rejected_at_any_confidence(self):
        for side in ('text', 'derived'):
            for value in (.1, .8, .99):
                with self.subTest(side=side, confidence=value):
                    image = candidate()
                    rows = image['text'] if side == 'text' else image['derived_deploy_analysis']['text']
                    rows.append(dict(rows[3], confidence=value))
                    self.rejected(image)
        for value in (True, -.1, float('nan'), 1.01):
            image = candidate();image['text'][3]['confidence'] = value
            self.rejected(image)

    def test_boxes_must_be_in_window_and_agree_at_original_center(self):
        for box in ([-.01, .4, .3, .1], [.9, .4, .3, .1], [.1, .95, .3, .1],
                    [.1, .4, 0, .1], [.1, .4, True, .1], [.1, float('nan'), .3, .1],
                    [.6, .4, .3, .1], [.1, .8, .3, .1], [.1, .4, .02, .01]):
            for side in ('text', 'derived'):
                with self.subTest(box=box, side=side):
                    image = candidate()
                    rows = image['text'] if side == 'text' else image['derived_deploy_analysis']['text']
                    rows[3]['box_normalized_bottom_left'] = box
                    self.rejected(image)

    def test_every_identity_transform_and_recognition_setting_binds_exactly(self):
        changes = {'schema': True, 'profile': 'other', 'scope': 'native OCR',
                   'source_png_sha256': '2'*64, 'analysis_png_sha256': '2'*64,
                   'owner_pid': 999, 'window_id': 35, 'bounds_points_including_chrome': [0, 25, 1004, 664],
                   'source_point_pixel_scale': 1,
                   'source_image_dimensions': [1920, 1135], 'analysis_image_dimensions': [3840, 2271],
                   'source_crop_pixels_top_left': [1, 0, 1920, 1136], 'scale': 3,
                   'normalized_box_space': 'crop-relative', 'resampling': 'nearest',
                   'recognition_level': 'fast', 'recognition_languages': ['en-GB'],
                   'uses_language_correction': True, 'custom_words': [analysis.LABEL]}
        for name, value in changes.items():
            with self.subTest(field=name):
                image = candidate();image['derived_deploy_analysis'][name] = value
                self.rejected(image)
        for name in changes:
            image = candidate();image['derived_deploy_analysis'].pop(name)
            self.rejected(image)

    def test_actual_file_identity_dimensions_and_image_caps_are_required(self):
        for changes in ({'source_sha256': '2'*64}, {'analysis_sha256': '2'*64},
                        {'source_dimensions': [1920, 1135]}, {'analysis_dimensions': [3840, 2271]},
                        {'source_dimensions': [True, 1136]}, {'source_sha256': 'not-a-sha256'}):
            with self.subTest(changes=changes), self.assertRaises(RuntimeError): bind(candidate(), **changes)
        for width, height in ((4097, 1024), (4096, 1025), (1, 9000)):
            image = candidate();image['image_dimensions'] = [width, height]
            image['derived_deploy_analysis'] = synthetic_analysis(image)
            with self.assertRaises(RuntimeError): bind(image)
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary).resolve(strict=True)/'synthetic-header.png'
            path.write_bytes(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR'+struct.pack('>II', 1004, 664))
            self.assertEqual(analysis.png_dimensions(path), [1004, 664])
            path.write_bytes(b'not a PNG')
            with self.assertRaises(RuntimeError): analysis.png_dimensions(path)

    def test_json_cannot_spoof_a_binding_or_mutate_an_already_bound_receipt(self):
        image = candidate();image.pop('derived_deploy_analysis')
        with self.assertRaises(RuntimeError): bind(image)
        image = candidate()
        with self.assertRaises(RuntimeError): ordinary.label_point(image, analysis.LABEL)
        image[analysis.BINDING] = {'receipt_sha256': analysis.receipt_digest(image)}
        with self.assertRaises(RuntimeError): ordinary.label_point(image, analysis.LABEL)
        with self.assertRaises(RuntimeError): bind(image)
        for side in ('text', 'analysis', 'owner', 'bounds'):
            image = bind(candidate())
            if side == 'text': image['text'][3]['confidence'] = .6
            elif side == 'analysis': image['derived_deploy_analysis']['text'][3]['confidence'] = .99
            elif side == 'owner': image['owner_pid'] += 1
            else: image['bounds_points_including_chrome'][0] += 1
            with self.subTest(side=side), self.assertRaises(RuntimeError): ordinary.label_point(image, analysis.LABEL)

    def test_existing_native_selector_and_hud_confidence_remain_strict(self):
        self.assertEqual(ordinary.label_point(capture(), analysis.LABEL), (280, 344.4))
        for text, confidence in (('DEPLOY • OFFLINE 5V5', .99), (analysis.LABEL, .79999)):
            image = capture();image['text'][3].update(text=text, confidence=confidence)
            with self.assertRaises(RuntimeError): ordinary.label_point(image, analysis.LABEL)
        self.assertEqual(ordinary.hud_values(hud_capture()), {'health': 100, 'ammo': 14, 'reserve': 60})
        image = hud_capture();image['text'][0]['confidence'] = .79999
        with self.assertRaises(RuntimeError): ordinary.hud_values(image)

    def test_full_synthetic_controller_requests_derived_analysis_once_and_retains_both_png_headers(self):
        with tempfile.TemporaryDirectory() as temporary:
            harness = SyntheticController(Path(temporary).resolve(strict=True)/'synthetic')
            code, report = harness.execute()
            self.assertEqual(code, 0, report.get('failure'))
            helpers = [row for row in report['actions'] if row['event'] == 'helper_command']
            opted = [row for row in helpers if '--analysis-mode' in row['command']]
            self.assertEqual([row['name'] for row in opted], ['01-focused-menu'])
            self.assertEqual(opted[0]['budget_seconds'], driver.BUDGETS['capture'])
            capture_row = next(row for row in report['capture_attempts'] if row['name'] == '01-focused-menu')
            self.assertEqual(set(capture_row['retained_files']), {'01-focused-menu.png', '01-focused-menu.json',
                                                                  '01-focused-menu-deploy-2x.png'})
            self.assertEqual(harness.focus_calls, 1)

    def test_full_controller_rejects_missing_unopted_spoofed_and_invalid_derived_observations(self):
        class DerivedController(SyntheticController):
            def native_capture(self, name):
                image = super().native_capture(name)
                if name == '01-focused-menu':
                    image['text'][3].update(text='DEPLOY • OFFLINE 5V5', confidence=.5)
                if self.fault == 'unopted' and name.startswith('00-startup'):
                    image['derived_deploy_analysis'] = synthetic_analysis(image)
                return image

            def popen(self, arguments, **kwargs):
                process = super().popen(arguments, **kwargs)
                if '--analysis-mode' in arguments:
                    path = Path(arguments[arguments.index('--report')+1])
                    image = json.loads(path.read_text())
                    row = image['derived_deploy_analysis']['text'][3]
                    row['confidence'] = .8
                    if self.fault == 'missing': image.pop('derived_deploy_analysis')
                    elif self.fault == 'hash': image['derived_deploy_analysis']['analysis_png_sha256'] = '2'*64
                    elif self.fault == 'low': row['confidence'] = .79999
                    elif self.fault == 'words': row['text'] = 'DEPLOY • ONLINE 5V5'
                    elif self.fault == 'duplicate': image['derived_deploy_analysis']['text'].append(copy.deepcopy(row))
                    elif self.fault == 'off_window': row['box_normalized_bottom_left'][0] = -1
                    path.write_text(json.dumps(image))
                return process

            def make_ui(self):
                synthetic_ui = super().make_ui()
                class UI(synthetic_ui):
                    def click_label(self, image, label):
                        ordinary.label_point(image, label)
                        super().click_label(image, label)
                return UI

        for fault in (None, 'unopted', 'missing', 'hash', 'low', 'words', 'duplicate', 'off_window'):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temporary:
                harness = DerivedController(Path(temporary).resolve(strict=True)/'synthetic', fault)
                code, report = harness.execute()
                self.assertEqual(code, int(fault is not None), report.get('failure'))
                self.assertEqual(harness.deployed, fault is None)
                if fault:
                    self.assertEqual(report['cg_event_post_attempts'], 0)
                    self.assertEqual(report['failure']['type'], 'RuntimeError')
                self.assertTrue(all(row['owned_group_gone'] for row in report['cleanup']))

    def test_default_native_helper_ocr_and_gameplay_tail_are_byte_preserved(self):
        # This check runs in the workflow's depth-one checkout. Pin the exact
        # c08889b reference instead of asking CI for an unavailable Git object.
        fixtures = ROOT/'scripts/fixtures/macos_ordinary_source'
        reference_bytes = (fixtures/'reference.json').read_bytes()
        self.assertEqual(hashlib.sha256(reference_bytes).hexdigest(),
                         '47d2484fe191af3a374dbb586474af53d36448d48acf3c8e00ed7a9f6b45d92a')
        reference = json.loads(reference_bytes)
        self.assertEqual(reference['source_commit'], 'c08889b8c1118c89e83c151079df4dc224076760')
        golden = (fixtures/reference['helper_default_fixture']).read_bytes()
        self.assertEqual(hashlib.sha256(golden).hexdigest(), reference['helper_default_sha256'])
        native = (ROOT/reference['helper_source_path']).read_bytes()
        from test_macos_capture_diagnostics import original_capture_helper
        native = original_capture_helper(native)
        start = reference['helper_default_start'].encode()
        self.assertEqual(native[native.index(start):native.index(b'            if let url = analysisURL {')], golden)
        current = native.decode()
        self.assertIn('args.count == 8 || args.count == 12', current)
        self.assertEqual(current.count('"'+analysis.PROFILE+'"'), 2)
        self.assertEqual(current.count('"'+analysis.SCOPE+'"'), 1)
        self.assertEqual(current.count('context.draw(image,'), 1)
        self.assertEqual(current.count('report["derived_deploy_analysis"] = try derivedDeployAnalysis('), 1)
        self.assertNotIn('request.customWords', current)
        current = (ROOT/reference['driver_source_path']).read_bytes()
        boundary = reference['driver_gameplay_boundary'].encode()
        current = current.replace(b"    parser.add_argument('--deploy-target', choices=('ocr', 'owned-ax'), default='ocr')\n", b'')
        current = current.replace(b'return run(arguments.output, arguments.preflight, deploy_target=arguments.deploy_target)',
                                  b'return run(arguments.output, arguments.preflight)')
        self.assertEqual(hashlib.sha256(current[current.index(boundary):]).hexdigest(),
                         reference['driver_gameplay_tail_sha256'])


if __name__ == '__main__':
    unittest.main()
