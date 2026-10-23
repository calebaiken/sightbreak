"""Narrow ordinary-gameplay controls layered on the accepted Mac menu adapter."""
import copy
import ctypes as C
import math
import os
from pathlib import Path
import pwd
import re
import shutil
import stat
import time

from macos_native_input import MacMenuUI, same_bounds
from macos_deploy_ocr import BINDING, LABEL as DEPLOY_LABEL, deploy_provenance, derived_deploy_row
from probe_macos_input import (NativePrerequisiteBlocked, Point, digest,
                               require_absent_profile, user_directory)
from verify_macos_menu import require_screen, screen_text, unique_screen_label


RULES = {'buy_seconds': 15, 'round_seconds': 100, 'device_seconds': 35,
         'plant_seconds': 3, 'defuse_seconds': 5, 'win_score': 7}
OVERRIDE_RELATIVE = 'Contents/MacOS/override.cfg'


class OwnedWindowChanged(RuntimeError):
    pass


def owned_visible_windows(rows, pid):
    # MacReadOnly.windows supplies validated layer-zero metadata. Use the same
    # PID/visibility selection for discovery and every later input guard.
    return [row for row in rows if row.get('owner_pid') == pid and row.get('onscreen') is True]


def no_symlinks(path):
    path = Path(path).absolute()
    for entry in (path, *path.parents):
        if entry.is_symlink():
            raise NativePrerequisiteBlocked('Symlink in native isolation path: ' + str(entry))


def account_home():
    home = Path(pwd.getpwuid(os.geteuid()).pw_dir)
    no_symlinks(home)
    if not home.is_absolute() or os.environ.get('HOME') != str(home):
        raise NativePrerequisiteBlocked('HOME must equal the actual OS account home; no replacement home')
    return home


def inventory(directory):
    directory = Path(directory)
    no_symlinks(directory)
    files, directories = {}, []
    if directory.exists():
        if not directory.is_dir():
            raise RuntimeError('Native inventory root is not a directory')
        for path in sorted(directory.rglob('*')):
            if path.is_symlink():
                raise NativePrerequisiteBlocked('Symlink in native inventory: ' + str(path))
            if len(files) + len(directories) >= 8192:
                raise RuntimeError('Native inventory exceeds bounded entry count')
            name = path.relative_to(directory).as_posix()
            if path.is_dir():
                directories.append(name)
            elif path.is_file():
                files[name] = {'bytes': path.stat().st_size, 'sha256': digest(path),
                               'mode': stat.S_IMODE(path.stat().st_mode)}
            else:
                raise RuntimeError('Native inventory contains a non-regular entry')
    return {'directory_exists': directory.exists(), 'directories': directories, 'files': files}


def default_inventory():
    # Check every ancestor before walking. A final non-symlink SIGHTBREAK path
    # can still escape through Library/Godot/app_userdata symlink ancestors.
    return inventory(user_directory())


def override_text(name):
    if not re.fullmatch(r'SIGHTBREAK-mac-ordinary-[0-9a-f]{32}', name):
        raise ValueError('Invalid unique native user-directory name')
    return ('[application]\nconfig/use_custom_user_dir=true\n'
            'config/custom_user_dir_name="' + name + '"\n')


def stage_app(original, destination, name):
    original, destination = Path(original), Path(destination)
    no_symlinks(destination)
    if os.path.lexists(destination):
        raise RuntimeError('Preserve staged native app; select a fresh output')
    before = inventory(original)
    if not before['directory_exists'] or OVERRIDE_RELATIVE in before['files']:
        raise RuntimeError('Expected original app without a sibling settings override')
    text = override_text(name)
    shutil.copytree(original, destination, copy_function=shutil.copy2)
    if inventory(destination) != before or inventory(original) != before:
        raise RuntimeError('Native app copy did not preserve exact payload bytes and modes')
    override = destination / OVERRIDE_RELATIVE
    override.write_text(text, encoding='utf-8')
    after = inventory(destination)
    expected = copy.deepcopy(before)
    expected['files'][OVERRIDE_RELATIVE] = after['files'][OVERRIDE_RELATIVE]
    if after != expected or inventory(original) != before:
        raise RuntimeError('Staging changed more than the two-value settings override')
    return {'original': str(original), 'staged': str(destination), 'original_inventory': before,
            'staged_inventory': after, 'override_text': text, 'override_sha256': digest(override),
            'executable_sha256': digest(destination / 'Contents/MacOS/SIGHTBREAK'),
            'pck_sha256': digest(destination / 'Contents/Resources/SIGHTBREAK.pck')}


def verify_staged_app(receipt):
    if (inventory(receipt['original']) != receipt['original_inventory']
            or inventory(receipt['staged']) != receipt['staged_inventory']):
        raise RuntimeError('Original or staged native payload changed during execution')


def require_private_userdir(directory, default_before, *, engine_header=True):
    """Only the engine creates this directory/log; the controller never does."""
    if default_inventory() != default_before:
        raise RuntimeError('Default native SIGHTBREAK directory changed during private execution')
    require_absent_profile()
    directory = Path(directory)
    current = inventory(directory)
    logfile = directory / 'mac-ordinary-engine.log'
    if not current['directory_exists'] or not logfile.is_file():
        raise NativePrerequisiteBlocked('Exact native artifact has not established its private user:// log')
    if engine_header and 'Godot Engine v4.7.2.stable' not in logfile.read_text(errors='replace'):
        raise RuntimeError('Private user:// engine log lacks the pinned Godot version header')
    if any(os.path.lexists(directory / name) for name in ('offline_training.json', 'offline_training.json.tmp')):
        raise RuntimeError('Unexpected profile write in narrow stock fire/reload component')
    return current


def capture_geometry(capture):
    """Validate the accepted full-window/chrome/Retina mapping without OCR."""
    if (capture.get('passed') is not True
            or capture.get('scope') != 'OS window screenshot from ScreenCaptureKit; read-only helper'
            or capture.get('permissions', {}).get('CGPreflightScreenCaptureAccess') is not True):
        raise RuntimeError('Accepted native window capture and permission required')
    bounds = capture.get('bounds_points_including_chrome', [])
    content = capture.get('filter_content_rect_points', [])
    scale = capture.get('point_pixel_scale')
    if (not same_bounds(bounds, capture.get('scwindow_frame_points', [])) or min(bounds[2:]) <= 0
            or not same_bounds([0, 0, *bounds[2:]], [0, 0, *content[2:]])
            or not isinstance(scale, (int, float)) or isinstance(scale, bool) or not math.isfinite(scale)
            or not 0 < scale <= 4
            or capture.get('image_dimensions') != [math.ceil(content[2]*scale), math.ceil(content[3]*scale)]):
        raise RuntimeError('Unknown native screenshot chrome/DPI mapping')
    return bounds


def label_point(capture, label):
    bounds = capture_geometry(capture)
    if label == DEPLOY_LABEL and (BINDING in capture or 'derived_deploy_analysis' in capture):
        entry = derived_deploy_row(capture)
    else:
        if not unique_screen_label(capture, label):
            raise RuntimeError('Expected one exact confident in-bounds native label: ' + label)
        entry = screen_text(capture, label)[0]
    x, y, width, height = entry['box_normalized_bottom_left']
    return (bounds[0]+(x+width/2)*bounds[2], bounds[1]+(1-y-height/2)*bounds[3])


def require_field_menu(capture):
    if (capture.get('passed') is not True or not unique_screen_label(capture, 'FIELD MENU')
            or not unique_screen_label(capture, 'LEAVE MATCH')
            or screen_text(capture, 'FIELD SETTINGS') or screen_text(capture, 'OPERATOR RECORD')):
        raise RuntimeError('Original native screenshot did not identify FIELD MENU / LEAVE MATCH')


def number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def integer(value):
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def living_context(state, anchor=None, *, paused=False, phase='live', screen='game'):
    actor, ui = state.get('local_actor', {}), state.get('ui', {})
    if (state.get('schema') != 1 or isinstance(state.get('schema'), bool)
            or state.get('scope') != 'debug_offline_read_only_observation' or state.get('scenario') != 'standard'
            or state.get('time_scale') != 1 or isinstance(state.get('time_scale'), bool)
            or state.get('phase') != phase or not integer(state.get('wall_msec'))
            or not integer(state.get('drawn_frames')) or not integer(state.get('simulation_tick'))
            or not number(state.get('elapsed')) or not integer(state.get('round_number'))
            or actor.get('alive') is not True or not number(actor.get('health')) or not 0 < actor['health'] <= 100
            or actor.get('weapon') != 'sidearm' or not integer(actor.get('id'))
            or not integer(actor.get('ammo')) or not integer(actor.get('reserve'))
            or not number(actor.get('reload')) or actor['reload'] < 0
            or ui.get('screen') != screen or ui.get('focused') is not True or ui.get('paused') is not paused):
        raise RuntimeError('Observation lacks the same ordinary living focused sidearm context')
    if anchor is not None:
        old = anchor['local_actor']
        if state['round_number'] != anchor['round_number'] or actor['id'] != old['id']:
            raise RuntimeError('Player or round changed during ordinary Mac component')
    return actor


def require_initial(initial):
    # begin_match emits initial before main.gd changes screen from menu to game.
    # Later readiness is a distinct fresh observation that must show game UI.
    living_context(initial, phase='buy', screen='menu')
    profile = initial.get('initial_profile', {})
    settings = profile.get('settings', {})
    if (initial.get('event') != 'initial' or initial.get('initial_conditions') != 'stock_spawns_teams_random_seeds'
            or initial.get('rules') != RULES or initial.get('protocol') != 6
            or initial.get('prediction_enabled') is not False or initial.get('difficulty') != 'normal'
            or initial.get('round_number') != 1 or initial.get('objective_state') != 'carried'
            or initial['local_actor']['ammo'] != 15 or initial['local_actor']['reserve'] != 60
            or profile.get('schema') != 1 or profile.get('scope') != 'offline_training'
            or any(profile.get(key) != 0 for key in ('xp', 'credits', 'matches', 'wins', 'kills', 'deaths'))
            or profile.get('history') != [] or settings.get('difficulty') != 1
            or settings.get('graphics_quality') != 1 or settings.get('render_scale') != 1
            or settings.get('fps_limit') != 60):
        raise RuntimeError('Initial event does not prove fresh stock defaults and normal rules')


def hud_values(capture):
    """Require native Vision health and sidearm values in separate HUD regions."""
    capture_geometry(capture)
    if any(screen_text(capture, label) for label in ('OPERATOR RECORD', 'FIELD MENU', 'FIELD SETTINGS')):
        raise RuntimeError('Native HUD capture shows a menu or settings overlay')
    health, ammo = [], []
    for entry in capture.get('text', []):
        text = ' '.join(entry.get('text', '').upper().split())
        confidence, box = entry.get('confidence'), entry.get('box_normalized_bottom_left', [])
        if not number(confidence) or confidence < .8 or len(box) != 4 or not all(number(x) for x in box):
            continue
        x, y, w, h = box
        if min(w, h) <= 0 or min(x, y) < 0 or w > 1-x or h > 1-y:
            continue
        if any(term in text for term in ('ELIMINATED', 'SPECTATING', 'RELOADING')):
            raise RuntimeError('Native pixels show eliminated/spectating/reloading instead of settled living HUD')
        found = re.fullmatch(r'(\d{1,3})\s*[^A-Z0-9]*HEALTH', text)
        if found and x+w <= .5 and y+h <= .3:
            health.append(int(found[1]))
        found = re.fullmatch(r'SIDEARM\s+(\d{1,2})\s*/\s*(\d{1,3})', text)
        if found and x >= .5 and y+h <= .3:
            ammo.append((int(found[1]), int(found[2])))
    if len(health) != 1 or not 0 < health[0] <= 100 or len(ammo) != 1:
        raise RuntimeError('Exact confident positive-health/sidearm native HUD values unavailable')
    return {'health': health[0], 'ammo': ammo[0][0], 'reserve': ammo[0][1]}


class MacOrdinaryUI(MacMenuUI):
    def post(self, event, kind):
        if not getattr(self, 'input_geometry_pinned', False):
            if event:
                self.cf.CFRelease(event)
            raise RuntimeError('No CGEvent attempt is allowed before permanent input geometry pinning')
        target = getattr(self, 'semantic_deploy_target', None)
        if target is not None and kind in ('pointer_move', 'lmb_down'):
            try:
                from macos_semantic_deploy import SemanticDeployTarget
                if type(target) is not SemanticDeployTarget:
                    raise RuntimeError('Semantic Deploy target is not controller-bound')
                target.point(target.capture, self)
            except BaseException:
                # button() records ownership immediately before post(). This
                # semantic rejection happens before any OS down attempt.
                if kind == 'lmb_down':
                    self.held.discard('lmb')
                if event:
                    self.cf.CFRelease(event)
                raise
        super().post(event, kind)

    def pin_for_input(self, capture):
        if getattr(self, 'input_geometry_pinned', False) or self.event_post_attempts or self.held:
            raise RuntimeError('Input geometry may be pinned only once before any owned event')
        require_screen(capture, 'menu')
        capture_geometry(capture)
        if (capture.get('owner_pid') != self.pid or capture.get('window_id') != self.window
                or not same_bounds(capture.get('bounds_points_including_chrome', []), self.bounds)):
            raise RuntimeError('Fresh post-focus menu does not match the candidate owned window')
        self.require_target()
        self.neutral()
        self.input_geometry_pinned = True
        self.trace('input_geometry_pinned', target_pid=self.pid, window_id=self.window,
                   bounds_points_including_chrome=self.bounds, native_state=self.diagnostics())

    def diagnostics(self):
        result = super().diagnostics()
        result['reload_down'] = bool(self.cg.CGEventSourceKeyState(0, 15))
        return result

    def require_window(self):
        # Preserve permission/isolation guards and retain every decision row.
        # The selected ID must remain the only owned visible layer-zero window.
        require_private_userdir(self.private_directory, self.default_before)
        permissions = self.preflight()
        denied = [name for name in ('CGPreflightPostEventAccess', 'CGPreflightScreenCaptureAccess')
                  if permissions[name] is not True]
        if denied:
            raise NativePrerequisiteBlocked('Current controller permission denied: ' + ', '.join(denied))
        current = self.windows(self.pid)
        self.trace('owned_window_guard', target_pid=self.pid, expected_window=self.window,
                   expected_bounds_points=self.bounds, observed_owned_layer_zero_windows=current,
                   input_geometry_pinned=bool(getattr(self, 'input_geometry_pinned', False)),
                   cg_event_post_attempts=self.event_post_attempts)
        matched = owned_visible_windows(current, self.pid)
        if (len(matched) != 1 or matched[0].get('window_id') != self.window
                or not same_bounds(matched[0]['bounds_points_including_chrome'], self.bounds)):
            raise OwnedWindowChanged('Unique owned visible window or its geometry changed before input')

    def neutral(self):
        super().neutral()
        if self.cg.CGEventSourceKeyState(0, 15):
            raise RuntimeError('Native R key is held before input transaction')

    def reload_key(self, down):
        if down:
            self.require_target()
            self.neutral()
            self.held.add('reload')
        self.post(self.cg.CGEventCreateKeyboardEvent(None, 15, down), 'reload_down' if down else 'reload_up')
        if not down:
            until = time.monotonic() + 1
            while time.monotonic() < until:
                if not self.cg.CGEventSourceKeyState(0, 15):
                    self.held.discard('reload')
                    return
                time.sleep(.02)
            raise RuntimeError('Native OS state did not acknowledge owned R release')

    def click_label(self, capture, label):
        target = getattr(self, 'semantic_deploy_target', None)
        if target is None:
            return self._click_label(capture, label)
        from macos_semantic_deploy import SemanticDeployTarget
        if type(target) is not SemanticDeployTarget or label != DEPLOY_LABEL:
            raise RuntimeError('Semantic target is restricted to one explicit Deploy transaction')
        try:
            return self._click_label(capture, label, target)
        finally:
            target.consume()
            self.semantic_deploy_target = None

    def _click_label(self, capture, label, semantic_target=None):
        self.require_target()
        self.neutral()
        if (capture.get('owner_pid') != self.pid or capture.get('window_id') != self.window
                or not same_bounds(capture.get('bounds_points_including_chrome', []), self.bounds)):
            raise RuntimeError('Label screenshot belongs to a different native window')
        point = (label_point(capture, label) if semantic_target is None
                 else semantic_target.point(capture, self))
        if semantic_target is not None:
            self.trace('semantic_deploy_target', label=label, target_points=list(point),
                       expires_monotonic=semantic_target.expires)
        if label == DEPLOY_LABEL and BINDING in capture:
            self.trace('derived_deploy_target', label=label, target_points=list(point),
                       original_native_row=derived_deploy_row(capture), analysis=deploy_provenance(capture))
        self.post(self.cg.CGEventCreateMouseEvent(None, 5, Point(*point), 0), 'pointer_move')
        time.sleep(.2)
        self.require_target()
        actual = self.diagnostics()['pointer_points']
        if max(abs(a-b) for a, b in zip(point, actual)) > 2:
            raise RuntimeError('Native pointer did not reach the exact screenshot label')
        self.trace('label_pointer_observed', label=label, target_points=list(point), actual_pointer_points=actual)
        self.button(True, point)
        try:
            self.observed_state('lmb', True)
            time.sleep(.15)
        finally:
            self.button(False, point)
        self.observed_state('lmb', False)

    def fire_button(self, down):
        if down:
            point = self.diagnostics()['pointer_points']
            x, y, width, height = self.bounds
            if not x < point[0] < x+width or not y+32 < point[1] < y+height:
                raise RuntimeError('Captured gameplay pointer lies outside the owned client area')
        else:
            point = self.last_pointer_point
        self.button(down, point)

    def release_owned(self):
        errors = []
        if 'reload' in self.held:
            try:
                self.reload_key(False)
            except BaseException as error:
                errors.append('reload: ' + str(error))
        result = super().release_owned()
        result['errors'].extend(errors)
        return result
