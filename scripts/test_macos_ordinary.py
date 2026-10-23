#!/usr/bin/env python3
"""Pure invented counterexamples only; no engine, capture, OCR or native events."""
import copy
import json
import os
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch

import macos_ordinary_input as ordinary
import verify_macos_ordinary as driver
from probe_macos_input import NativePrerequisiteBlocked
from test_macos_menu import capture_fixture


def capture():
    result = capture_fixture()
    result['text'] += [
        {'text': 'DEPLOY · OFFLINE 5V5', 'confidence': .99, 'box_normalized_bottom_left': [.1, .4, .3, .1]},
        {'text': '100 · HEALTH', 'confidence': .99, 'box_normalized_bottom_left': [.05, .05, .15, .05]},
        {'text': 'SIDEARM 14 / 60', 'confidence': .99, 'box_normalized_bottom_left': [.7, .05, .25, .05]}]
    return result


def state():
    return {'schema': 1, 'scope': 'debug_offline_read_only_observation', 'scenario': 'standard',
            'time_scale': 1, 'phase': 'live', 'wall_msec': 100, 'drawn_frames': 20,
            'simulation_tick': 5, 'elapsed': .1, 'round_number': 1, 'objective_state': 'carried',
            'local_actor': {'alive': True, 'health': 100, 'weapon': 'sidearm', 'id': 1,
                            'ammo': 15, 'reserve': 60, 'reload': 0},
            'ui': {'screen': 'game', 'focused': True, 'paused': False}}


def initial():
    result = state()
    result.update(phase='buy', event='initial', initial_conditions='stock_spawns_teams_random_seeds',
                  rules=copy.deepcopy(ordinary.RULES), protocol=6, prediction_enabled=False, difficulty='normal')
    result['ui']['screen'] = 'menu'
    result['initial_profile'] = {'schema': 1, 'scope': 'offline_training', 'xp': 0, 'credits': 0,
        'matches': 0, 'wins': 0, 'kills': 0, 'deaths': 0, 'history': [],
        'settings': {'difficulty': 1, 'graphics_quality': 1, 'render_scale': 1, 'fps_limit': 60}}
    return result


class OrdinaryControls(unittest.TestCase):
    def test_native_bounds_and_retina_mapping_match_accepted_menu_mapping(self):
        candidate = capture()
        expected = ordinary.label_point(candidate, 'DEPLOY · OFFLINE 5V5')
        self.assertEqual(expected, (280, 344.4))
        candidate['point_pixel_scale'], candidate['image_dimensions'] = 1, [960, 568]
        self.assertEqual(ordinary.label_point(candidate, 'DEPLOY · OFFLINE 5V5'), expected)
        for field, value in (('scwindow_frame_points', [40, 60, 960, 540]),
                             ('filter_content_rect_points', [0, 0, 960, 540]),
                             ('image_dimensions', [960, 568]), ('point_pixel_scale', float('nan')),
                             ('point_pixel_scale', True), ('point_pixel_scale', 0), ('scope', 'internal game screenshot')):
            bad = capture()
            bad[field] = value
            with self.subTest(field=field, value=value), self.assertRaises(RuntimeError):
                ordinary.label_point(bad, 'DEPLOY · OFFLINE 5V5')

    def test_pointer_target_is_exact_unique_confident_and_inside_original_image(self):
        for change in ('partial', 'missing', 'duplicate', 'low', 'nan', 'bool', 'outside'):
            bad = capture()
            row = bad['text'][3]
            if change == 'partial': row['text'] = 'DEPLOY'
            elif change == 'missing': bad['text'].remove(row)
            elif change == 'duplicate': bad['text'].append(copy.deepcopy(row))
            elif change == 'outside': row['box_normalized_bottom_left'] = [.9, .1, .2, .1]
            else: row['confidence'] = {'low': .79999, 'nan': float('nan'), 'bool': True}[change]
            with self.subTest(change=change), self.assertRaises(RuntimeError):
                ordinary.label_point(bad, 'DEPLOY · OFFLINE 5V5')

    def test_native_hud_rejects_missing_ambiguous_foreign_or_dead_values(self):
        self.assertEqual(ordinary.hud_values(capture()), {'health': 100, 'ammo': 14, 'reserve': 60})
        for change in ('dead', 'zero', 'weapon', 'reload', 'partial', 'duplicate', 'low', 'region', 'outside'):
            bad = capture()
            health, ammo = bad['text'][-2:]
            if change == 'dead': health['text'] = 'ELIMINATED · SPECTATING'
            elif change == 'zero': health['text'] = '000 · HEALTH'
            elif change == 'weapon': ammo['text'] = 'RIFLE 14 / 60'
            elif change == 'reload': ammo['text'] = 'RELOADING 0.1s'
            elif change == 'partial': ammo['text'] = '14 / 60'
            elif change == 'duplicate': bad['text'].append(copy.deepcopy(ammo))
            elif change == 'low': ammo['confidence'] = .7999
            elif change == 'region': ammo['box_normalized_bottom_left'][0] = .05
            else: health['box_normalized_bottom_left'][0] = -.01
            with self.subTest(change=change), self.assertRaises(RuntimeError):
                ordinary.hud_values(bad)

    def test_field_menu_requires_unique_exact_heading_and_leave(self):
        field = capture()
        field['text'] = [dict(field['text'][0], text='FIELD MENU'), dict(field['text'][1], text='LEAVE MATCH')]
        ordinary.require_field_menu(field)
        ordinary.label_point(field, 'LEAVE MATCH')
        for change in ('heading', 'leave', 'settings', 'home', 'duplicate'):
            bad = copy.deepcopy(field)
            if change == 'heading': bad['text'][0]['text'] = 'FIELD SETTINGS'
            elif change == 'leave': bad['text'][1]['text'] = 'LEAVE'
            elif change == 'duplicate': bad['text'].append(copy.deepcopy(bad['text'][0]))
            else: bad['text'].append(dict(bad['text'][0], text='FIELD SETTINGS' if change == 'settings' else 'OPERATOR RECORD'))
            with self.subTest(change=change), self.assertRaises(RuntimeError):
                ordinary.require_field_menu(bad)

    def test_living_context_rejects_changed_life_round_scope_focus_and_nonfinite_fields(self):
        ordinary.living_context(state())
        changes = [('schema', True), ('scenario', 'plant'), ('scope', 'other'), ('time_scale', 2),
                   ('time_scale', True), ('phase', 'buy'), ('wall_msec', True), ('drawn_frames', -1),
                   ('elapsed', float('nan')), ('simulation_tick', False), ('round_number', 2),
                   ('local_actor.alive', False), ('local_actor.health', 0), ('local_actor.health', True),
                   ('local_actor.weapon', 'rifle'), ('local_actor.id', 2), ('local_actor.ammo', True),
                   ('local_actor.reserve', -1), ('local_actor.reload', float('inf')),
                   ('ui.focused', False), ('ui.paused', True), ('ui.screen', 'menu')]
        for key, value in changes:
            bad = state()
            path = key.split('.')
            target = bad if len(path) == 1 else bad[path[0]]
            target[path[-1]] = value
            with self.subTest(key=key, value=value), self.assertRaises(RuntimeError):
                ordinary.living_context(bad, state())

    def test_initial_requires_stock_rules_defaults_and_pretransition_menu_state(self):
        ordinary.require_initial(initial())
        for key, value in [('initial_conditions', 'declared_initial_spawns_side_and_seeds_only'),
                           ('rules', {}), ('protocol', 5), ('prediction_enabled', True),
                           ('difficulty', 'easy'), ('round_number', 2), ('objective_state', 'planted')]:
            bad = initial()
            bad[key] = value
            with self.subTest(key=key), self.assertRaises(RuntimeError):
                ordinary.require_initial(bad)
        for key in ('xp', 'credits', 'matches', 'wins', 'kills', 'deaths'):
            bad = initial()
            bad['initial_profile'][key] = 1
            with self.subTest(profile=key), self.assertRaises(RuntimeError):
                ordinary.require_initial(bad)
        for key in ('difficulty', 'graphics_quality', 'render_scale', 'fps_limit'):
            bad = initial()
            bad['initial_profile']['settings'][key] = -1
            with self.subTest(settings=key), self.assertRaises(RuntimeError):
                ordinary.require_initial(bad)

    def test_staged_native_bytes_modes_and_only_two_setting_overrides(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            original = root / 'export/SIGHTBREAK.app'
            executable = original / 'Contents/MacOS/SIGHTBREAK'
            executable.parent.mkdir(parents=True)
            executable.write_bytes(b'invented executable bytes, never executed')
            executable.chmod(0o755)
            pck = original / 'Contents/Resources/SIGHTBREAK.pck'
            pck.parent.mkdir()
            pck.write_bytes(b'invented pck bytes, never loaded')
            receipt = ordinary.stage_app(original, root / 'output/SIGHTBREAK.app', 'SIGHTBREAK-mac-ordinary-'+'a'*32)
            ordinary.verify_staged_app(receipt)
            self.assertEqual(receipt['override_text'].splitlines(), ['[application]', 'config/use_custom_user_dir=true',
                'config/custom_user_dir_name="SIGHTBREAK-mac-ordinary-'+'a'*32+'"'])
            self.assertEqual(set(receipt['staged_inventory']['files'])-set(receipt['original_inventory']['files']), {ordinary.OVERRIDE_RELATIVE})
            (Path(receipt['staged']) / 'Contents/Resources/SIGHTBREAK.pck').write_bytes(b'changed')
            with self.assertRaisesRegex(RuntimeError, 'payload changed'):
                ordinary.verify_staged_app(receipt)
            with self.assertRaisesRegex(RuntimeError, 'fresh output'):
                ordinary.stage_app(original, Path(receipt['staged']), 'SIGHTBREAK-mac-ordinary-'+'b'*32)

    def test_symlinked_app_or_native_userdata_is_refused_without_following(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / 'target'
            target.mkdir()
            link = root / 'link'
            link.symlink_to(target, target_is_directory=True)
            for path in (link, link / 'child'):
                with self.subTest(path=path), self.assertRaises(NativePrerequisiteBlocked):
                    ordinary.inventory(path)
            (target / 'dangling').symlink_to(root / 'missing')
            with self.assertRaises(NativePrerequisiteBlocked):
                ordinary.inventory(target)

    def test_fake_home_and_settings_injection_never_establish_isolation(self):
        with patch.object(ordinary.pwd, 'getpwuid', return_value=types.SimpleNamespace(pw_dir='/actual/account')), patch.dict(os.environ, {'HOME': '/fake/home'}):
            with self.assertRaisesRegex(NativePrerequisiteBlocked, 'actual OS account home'):
                ordinary.account_home()
        for name in ('../elsewhere', 'SIGHTBREAK-mac-ordinary-'+('a'*32)+'\nrendering/quality=0', '', 'SIGHTBREAK'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                ordinary.override_text(name)

    def test_private_userdir_requires_native_log_and_unchanged_default_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            default = {'files': {}, 'directories': [], 'directory_exists': False}
            with patch.object(ordinary, 'require_absent_profile'), patch.object(ordinary, 'default_inventory', return_value=default):
                with self.assertRaises(NativePrerequisiteBlocked):
                    ordinary.require_private_userdir(root, default)
                logfile = root / 'mac-ordinary-engine.log'
                logfile.write_text('Godot Engine v4.7.2.stable.official\n')
                ordinary.require_private_userdir(root, default)
                logfile.write_text('Godot Engine v4.6.0.stable\n')
                with self.assertRaises(RuntimeError):
                    ordinary.require_private_userdir(root, default)
                logfile.write_text('Godot Engine v4.7.2.stable.official\n')
                (root / 'offline_training.json.tmp').write_text('{}')
                with self.assertRaisesRegex(RuntimeError, 'Unexpected profile write'):
                    ordinary.require_private_userdir(root, default)
            with patch.object(ordinary, 'require_absent_profile'), patch.object(ordinary, 'default_inventory', return_value={'files': {'changed': {}}}):
                with self.assertRaisesRegex(RuntimeError, 'Default native'):
                    ordinary.require_private_userdir(root, default)

    def test_default_userdata_rejects_symlinked_ancestors_and_tracks_file_modes(self):
        for ancestor in ('Godot', 'app_userdata'):
            with self.subTest(ancestor=ancestor), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                base = root / 'Library/Application Support/Godot/app_userdata/SIGHTBREAK'
                selected = next(path for path in base.parents if path.name == ancestor)
                selected.parent.mkdir(parents=True)
                target = root / 'elsewhere'
                target.mkdir()
                selected.symlink_to(target, target_is_directory=True)
                with patch.object(ordinary, 'user_directory', return_value=base), self.assertRaises(NativePrerequisiteBlocked):
                    ordinary.default_inventory()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            file = root / 'existing.cache'
            file.write_bytes(b'invented cache')
            before = ordinary.inventory(root)
            file.chmod(0o400)
            after = ordinary.inventory(root)
            self.assertNotEqual(before, after)
            self.assertEqual(before['files'][file.name]['sha256'], after['files'][file.name]['sha256'])

    def test_r_cleanup_releases_only_owned_reload_and_confirms_os_state(self):
        ui = object.__new__(ordinary.MacOrdinaryUI)
        ui.held, ui.last_pointer_point = {'reload'}, None
        ui.cg = types.SimpleNamespace(CGEventCreateKeyboardEvent=lambda *args: 1,
                                      CGEventSourceKeyState=lambda *args: False)
        posted = []
        ui.post = lambda event, kind: posted.append(kind)
        ui.diagnostics = lambda: {'reload_down': False, 'lmb_down': False, 'escape_down': False}
        report = ui.release_owned()
        self.assertEqual(posted, ['reload_up'])
        self.assertEqual(report['held_after_release'], [])
        self.assertEqual(report['errors'], [])
        ui.release_owned()
        self.assertEqual(posted, ['reload_up'])

    def test_foreign_focus_or_dirty_r_prevents_down_and_preserves_external_input(self):
        ui = object.__new__(ordinary.MacOrdinaryUI)
        ui.held = set()
        ui.require_target = lambda: (_ for _ in ()).throw(RuntimeError('foreign focus'))
        with patch.object(ui, 'post') as post:
            with self.assertRaises(RuntimeError):
                ui.reload_key(True)
            post.assert_not_called()
            self.assertEqual(ui.held, set())
        ui.require_target = lambda: None
        ui.cg = types.SimpleNamespace(CGEventSourceKeyState=lambda source, code: code == 15)
        ui.pid = 1
        ui.diagnostics = lambda: {'foreground_pid': 1, 'lmb_down': False, 'escape_down': False}
        with patch.object(ui, 'post') as post:
            with self.assertRaisesRegex(RuntimeError, 'R key is held'):
                ui.reload_key(True)
            post.assert_not_called()
            self.assertEqual(ui.held, set())

    def test_non_native_host_never_compiles_or_launches(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / 'evidence'
            with patch.object(driver, 'MacReadOnly', side_effect=RuntimeError('requires native ARM Mac')), patch.object(driver.subprocess, 'Popen') as launch:
                self.assertEqual(driver.run(output, Path(temporary) / 'unused.json'), 1)
                launch.assert_not_called()
            report = json.loads((output / 'results.json').read_text())
            self.assertFalse(report['passed'])
            self.assertEqual(report['captures'], [])
            self.assertEqual(report['actions'], [])


if __name__ == '__main__':
    unittest.main()
