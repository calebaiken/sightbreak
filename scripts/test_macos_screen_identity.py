#!/usr/bin/env python3
"""Replay retained Vision JSON and invented counterexamples; no native/OCR work."""
import copy
import hashlib
import json
from pathlib import Path
import unittest

import verify_macos_menu as driver


FIXTURES = Path(__file__).resolve().parents[1] / 'docs/reports/gauntlet/m2-macos-screen-identity/fixtures'


def original(name):
    return json.loads((FIXTURES / name).read_text())


class ScreenIdentity(unittest.TestCase):
    def test_originals_are_byte_exact_and_all_three_screens_are_distinguished(self):
        provenance = json.loads((FIXTURES / 'provenance.json').read_text())
        for name, info in provenance['files'].items():
            data = (FIXTURES / name).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), info['sha256'])
            self.assertEqual(len(data), info['bytes'])
            capture = json.loads(data)
            expected = 'settings' if any(row['text'] == 'FIELD SETTINGS' for row in capture['text']) else 'menu'
            driver.require_screen(capture, expected)
            with self.assertRaises(RuntimeError):
                driver.require_screen(capture, 'menu' if expected == 'settings' else 'settings')

    def test_original_returned_masthead_remains_below_threshold(self):
        capture = original('03-returned-menu.json')
        self.assertEqual(driver.screen_text(capture, 'TACTICAL OPERATIONS'), [])
        driver.require_screen(capture, 'menu')
        # The title bar alone is exact text for neither hero nor screen identity.
        capture['text'] = [row for row in capture['text'] if row['text'] == 'SIGHTBREAK (DEBUG)']
        with self.assertRaises(RuntimeError):
            driver.require_screen(capture, 'menu')

    def test_each_required_label_rejects_missing_foreign_partial_low_confidence_or_ambiguity(self):
        for label in driver.HOME_LABELS:
            for change in ('missing', 'foreign', 'partial', 'low', 'duplicate', 'title', 'nan', 'inf', 'bool'):
                capture = original('03-returned-menu.json')
                entry = next(row for row in capture['text'] if row['text'] == label)
                if change == 'missing': capture['text'].remove(entry)
                elif change == 'foreign': entry['text'] = 'FOREIGN APPLICATION'
                elif change == 'partial': entry['text'] += ' EXTRA'
                elif change == 'title': entry['text'] += ' (DEBUG)'
                elif change == 'duplicate': capture['text'].append(copy.deepcopy(entry))
                else: entry['confidence'] = {'low': .799999, 'nan': float('nan'), 'inf': float('inf'), 'bool': True}[change]
                with self.subTest(label=label, change=change), self.assertRaises(RuntimeError):
                    driver.require_screen(capture, 'menu')

    def test_every_required_box_must_be_positive_finite_and_inside_original_image(self):
        for label in (*driver.HOME_LABELS, 'FIELD SETTINGS'):
            source = '02-field-settings.json' if label == 'FIELD SETTINGS' else '03-returned-menu.json'
            for box in ([], [0, 0, 0, .1], [-.01, .2, .1, .1], [.9, .1, .2, .1],
                        [.1, .95, .1, .1], [.1, float('nan'), .1, .1], [False, .1, .1, .1],
                        [1, .1, 1e-20, .1], [.1, 1, .1, 1e-20]):
                capture = original(source)
                next(row for row in capture['text'] if row['text'] == label)['box_normalized_bottom_left'] = box
                with self.subTest(label=label, box=box), self.assertRaises(RuntimeError):
                    driver.require_screen(capture, 'settings' if label == 'FIELD SETTINGS' else 'menu')

    def test_mixed_screen_labels_do_not_qualify_either_screen(self):
        home, settings = original('03-returned-menu.json'), original('02-field-settings.json')
        mixed = copy.deepcopy(home)
        mixed['text'] += copy.deepcopy(settings['text'])
        for name in ('menu', 'settings'):
            with self.subTest(name=name), self.assertRaises(RuntimeError):
                driver.require_screen(mixed, name)

    def test_settings_requires_exact_unique_heading_at_same_threshold(self):
        for change in ('duplicate', 'partial', 'low'):
            capture = original('02-field-settings.json')
            entry = next(row for row in capture['text'] if row['text'] == 'FIELD SETTINGS')
            if change == 'duplicate': capture['text'].append(copy.deepcopy(entry))
            elif change == 'partial': entry['text'] = 'SAVED FIELD SETTINGS'
            else: entry['confidence'] = .79
            with self.subTest(change=change), self.assertRaises(RuntimeError):
                driver.require_screen(capture, 'settings')

    def test_threshold_boundary_and_normalization_are_exact(self):
        capture = original('03-returned-menu.json')
        for row in capture['text']:
            if row['text'] in driver.HOME_LABELS:
                row['confidence'] = .8
                row['text'] = '  ' + row['text'].lower().replace(' ', '   ') + '  '
        driver.require_screen(capture, 'menu')
        capture['passed'] = False
        with self.assertRaises(RuntimeError):
            driver.require_screen(capture, 'menu')
        with self.assertRaises(ValueError):
            driver.require_screen(original('03-returned-menu.json'), 'invented')


if __name__ == '__main__':
    unittest.main()
