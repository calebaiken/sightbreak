#!/usr/bin/env python3
"""Independent synthetic observer controls. Never posts input or executes native tools.

Run from any directory. --source selects an exact-source snapshot containing
scripts and the three retained fixture receipts. The snapshot default is ebb5cf9.
"""
import argparse
import copy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
parser = argparse.ArgumentParser()
parser.add_argument('--source', type=Path, default=Path(__file__).resolve().parent / 'exact-source')
parser.add_argument('--results', type=Path, default=Path(__file__).resolve().parent / 'independent-controls-results.json')
args, remaining = parser.parse_known_args()
sys.path.insert(0, str(args.source / 'scripts'))
import verify_macos_menu as driver
import macos_native_input as adapter

fixtures = args.source / 'docs/reports/gauntlet/m2-macos-screen-identity/fixtures'
observations = []

def original(name):
    return json.loads((fixtures / name).read_text())

def target(capture, label):
    return next(row for row in capture['text'] if row['text'] == label)

class IndependentControls(unittest.TestCase):
    def check(self, case, capture, screen, expected):
        error = None
        try:
            driver.require_screen(capture, screen)
            accepted = True
        except Exception as caught:
            accepted = False
            error = {'type': type(caught).__name__, 'message': str(caught)}
        observations.append({'case': case, 'synthetic': True, 'screen': screen,
                             'expected_accept': expected, 'accepted': accepted, 'error': error})
        self.assertEqual(accepted, expected, case)

    def test_each_single_home_label_blocks_settings(self):
        # All-three mixed-screen testing can miss a full-trio-only opposition bug.
        home = original('03-returned-menu.json')
        for label in ('SIGHTBREAK', 'OPERATOR RECORD', 'SETTINGS'):
            for box in ([.1,.2,.3,.1], [], [-1,.1,.3,.1]):
                capture = original('02-field-settings.json')
                entry = copy.deepcopy(target(home, label))
                entry['box_normalized_bottom_left'] = box
                capture['text'].append(entry)
                with self.subTest(label=label, box=box):
                    self.check('single opposite label '+label+' box '+repr(box), capture, 'settings', False)

    def test_opposite_heading_blocks_home_even_with_bad_geometry(self):
        settings = original('02-field-settings.json')
        for box in ([.1,.2,.3,.1], [], [2,.1,.3,.1]):
            capture = original('03-returned-menu.json')
            entry = copy.deepcopy(target(settings, 'FIELD SETTINGS'))
            entry['box_normalized_bottom_left'] = box
            capture['text'].append(entry)
            with self.subTest(box=box):
                self.check('opposite heading box '+repr(box), capture, 'menu', False)

    def test_normalized_duplicates_are_ambiguous_for_every_role(self):
        for label in ('SIGHTBREAK','OPERATOR RECORD','SETTINGS','FIELD SETTINGS'):
            settings = label == 'FIELD SETTINGS'
            capture = original('02-field-settings.json' if settings else '03-returned-menu.json')
            duplicate = copy.deepcopy(target(capture, label))
            duplicate['text'] = '\t' + label.lower().replace(' ', ' \n\t ') + '\n'
            capture['text'].append(duplicate)
            with self.subTest(label=label):
                self.check('normalized duplicate '+label, capture, 'settings' if settings else 'menu', False)

    def test_confusable_decorated_and_merged_labels_cannot_substitute(self):
        for label in ('SIGHTBREAK','OPERATOR RECORD','SETTINGS','FIELD SETTINGS'):
            settings = label == 'FIELD SETTINGS'
            for replacement in (label+'!', '('+label+')', 'PREFIX '+label, label+' EXTRA',
                                label.replace('I','\u0406'), label+'\u200b', label.replace(' ','')):
                # SIGHTBREAK has no spaces; do not call an unchanged label hostile.
                if replacement == label:
                    continue
                capture = original('02-field-settings.json' if settings else '03-returned-menu.json')
                target(capture,label)['text'] = replacement
                with self.subTest(label=label,replacement=replacement):
                    self.check('nonexact '+repr(replacement),capture,'settings' if settings else 'menu',False)

    def test_required_confidence_values_fail_closed(self):
        for label in ('SIGHTBREAK','OPERATOR RECORD','SETTINGS','FIELD SETTINGS'):
            settings = label == 'FIELD SETTINGS'
            for value in (None,'1',{},[],False,True,float('-inf'),float('nan'),-1,.7999999999999999):
                capture = original('02-field-settings.json' if settings else '03-returned-menu.json')
                target(capture,label)['confidence'] = value
                with self.subTest(label=label,value=repr(value)):
                    self.check('bad confidence '+label+' '+repr(value),capture,'settings' if settings else 'menu',False)

    def test_positive_boxes_starting_on_outside_edge_fail_despite_float_rounding(self):
        # A positive extent starting at1 cannot be wholly inside the image.
        for label in ('SIGHTBREAK','OPERATOR RECORD','SETTINGS','FIELD SETTINGS'):
            settings = label == 'FIELD SETTINGS'
            for box in ([1.0,.1,1e-20,.1],[.1,1.0,.1,1e-20]):
                capture = original('02-field-settings.json' if settings else '03-returned-menu.json')
                target(capture,label)['box_normalized_bottom_left'] = box
                with self.subTest(label=label,box=box):
                    self.check('float rounded outside '+label+' '+repr(box),capture,'settings' if settings else 'menu',False)

    def test_additional_malformed_boxes_fail_closed(self):
        for label in ('SIGHTBREAK','OPERATOR RECORD','SETTINGS','FIELD SETTINGS'):
            settings = label == 'FIELD SETTINGS'
            for box in (None,{},'0,0,1,1',[.1,.1,-.1,.1],[.1,.1,.1,-.1],
                        [0,-1e-20,.1,.1],[0,0,1.0000000000000002,1],
                        [0,0,1,1.0000000000000002],[.1,.1,float('inf'),.1],
                        [.1,.1,.1,float('-inf')],[.1,.1,'0.1',.1]):
                capture = original('02-field-settings.json' if settings else '03-returned-menu.json')
                target(capture,label)['box_normalized_bottom_left'] = box
                with self.subTest(label=label,box=repr(box)):
                    self.check('malformed box '+label+' '+repr(box),capture,'settings' if settings else 'menu',False)

    def test_exact_edge_boxes_normalization_and_row_order_remain_valid(self):
        for name,screen in (('03-returned-menu.json','menu'),('02-field-settings.json','settings')):
            capture = original(name)
            labels = ('FIELD SETTINGS',) if screen == 'settings' else ('SIGHTBREAK','OPERATOR RECORD','SETTINGS')
            for label in labels:
                entry = target(capture,label)
                entry['box_normalized_bottom_left'] = [0,0,1,1]
                entry['text'] = '\t'+label.lower().replace(' ','\n')+'\n'
                entry['confidence'] = .8
            capture['text'].reverse()
            self.check('valid exact edges '+screen,capture,screen,True)

    def test_malformed_text_rows_fail_closed(self):
        for bad in (None,{},'FIELD SETTINGS',[None],[7],[{'text':None,'confidence':1}],
                    [{'text':7,'confidence':1}],[{'text':'SIGHTBREAK','confidence':1,'box_normalized_bottom_left':None}]):
            capture = original('03-returned-menu.json')
            capture['text'] = bad
            with self.subTest(bad=repr(bad)):
                self.check('malformed text '+repr(bad),capture,'menu',False)

    def test_screen_check_does_not_replace_exact_owner_window_pointer_guard(self):
        # Exact identity is intentionally separate from the adapter owner guard.
        for field,value in (('owner_pid',999),('window_id',999),('bounds_points_including_chrome',[0,0,1,1])):
            capture = original('03-returned-menu.json')
            capture[field] = value
            driver.require_screen(capture,'menu')
            ui = object.__new__(adapter.MacMenuUI)
            ui.pid,ui.window,ui.bounds = 4062,45,[40,60,960,568]
            ui.require_target = lambda: None
            ui.neutral = lambda: None
            with self.subTest(field=field),patch.object(ui,'post') as post:
                with self.assertRaisesRegex(RuntimeError,'current exact owned window'):
                    ui.click_settings(capture)
                post.assert_not_called()
                observations.append({'case':'pointer rejects changed '+field,'synthetic':True,'accepted':False,'expected_accept':False})

if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(IndependentControls)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    args.results.write_text(json.dumps({'source':str(args.source.resolve()),'tests':result.testsRun,
                                      'cases':len(observations),'failed':len(result.failures)+len(result.errors),
                                      'observations':observations},indent=2)+'\n')
    raise SystemExit(0 if result.wasSuccessful() else 1)
