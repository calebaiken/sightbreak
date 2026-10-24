"""Synthetic producer-shaped files for pure shutdown evidence tests only.

No native process, image capture, OCR, API or gameplay runs here. Solid-color PNGs,
OCR text, seeds, process IDs and source identities are deliberately generated data
format fixtures; their agreement cannot establish independent visual/gameplay
quality or an observed shutdown outcome. Production validation must not import
this fixture module as its evidence oracle.
"""
import copy
import hashlib
import json
from pathlib import Path
import struct
import sys
import time
import zlib


CAPTURES = (
    '01-menu', '02-offline-spawn', '03-requisition', '04-move-aim',
    '05-after-fire', '06-after-reload', '06b-scoreboard', '06c-next-round',
    '06d-funded-requisition', '06e-purchased-smg', '06f-switched-sidearm',
    '06g-switched-primary', '07-field-menu', '07b-field-settings',
    '07c-settings-changed', '07d-explicit-resume', '08-return-menu',
    '09-reopened-menu', '10-reopened-loaded-settings',
    '11a-restored-focus-still-paused', '11b-resumed-held-input-neutral',
    '11c-fresh-press-movement',
)
PROFILE_DEFAULTS = {
    'schema': 1, 'scope': 'offline_training', 'display_name': 'Operator',
    'xp': 0, 'level': 1, 'credits': 0, 'matches': 0, 'wins': 0, 'kills': 0,
    'deaths': 0, 'last_daily': '', 'history': [],
    'settings': {
        'sensitivity': 0.0028, 'touch_sensitivity': 0.004, 'fov': 78.0,
        'volume': 0.65, 'difficulty': 1, 'gyro': False, 'gyro_sensitivity': 1.2,
        'window_mode': 0, 'touch_visible': False, 'reduced_motion': False,
        'crosshair_color': 'd9eac6', 'crosshair_size': 5.0, 'fps_limit': 60,
        'graphics_quality': 1, 'render_scale': 1.0, 'ui_text_scale': 1.0,
        'hud_scale': 1.0, 'hud_positions': {},
    },
}


def _hud_specs(name, ammo, reserve):
    return (
        {'label': name + ':(0, 630, 450, 720)', 'psm': 6, 'stdout': b'100 HEALTH\n'},
        {'label': name + ':(980, 648, 1280, 680)', 'psm': 7,
         'stdout': (str(ammo) + ' / ' + str(reserve) + '\n').encode('ascii')},
    )


def _tsv(*lines):
    rows = ['level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext']
    for line_number, words in enumerate(lines, 1):
        for word_number, word in enumerate(words.split(), 1):
            rows.append('\t'.join(map(str, (5, 1, 1, 1, line_number, word_number,
                                            100 + word_number * 100, 100 + line_number * 80,
                                            90, 40, 99, word))))
    return ('\n'.join(rows) + '\n').encode('utf-8')


OCR_SPECS = (
    *_hud_specs('05-after-fire', 13, 60),
    *_hud_specs('06-after-reload', 15, 58),
    {'label': 'current-native-ui', 'psm': 11, 'stdout': _tsv('VECTORLINE')},
    *_hud_specs('06e-purchased-smg', 30, 120),
    *_hud_specs('06f-switched-sidearm', 15, 58),
    *_hud_specs('06g-switched-primary', 30, 120),
    {'label': 'current-native-ui', 'psm': 11, 'stdout': _tsv('SETTINGS')},
    {'label': 'current-native-ui', 'psm': 11, 'stdout': _tsv('MOUSE')},
    *_hud_specs('07d-explicit-resume', 30, 120),
    {'label': 'current-native-ui', 'psm': 11, 'stdout': _tsv('FIELD MENU', 'LEAVE MATCH')},
)


def fixture_identity():
    """Return a fresh, explicitly synthetic rich runtime-identity-shaped value."""
    source = {
        'source_dirty': False, 'source_game_dirty': False,
        'source_commit': '1' * 40, 'source_game_tree': '2' * 40,
        'source_content_sha256': '3' * 64, 'source_validation_sha256': '4' * 64,
    }
    artifact = {'path': 'windows/SIGHTBREAK.exe', 'bytes': 4096,
                'sha256': '5' * 64, 'mode': 0o644, 'archive_mode': 0o644}
    payload = [artifact,
               {'path': 'windows/GODOT-LICENSE.txt', 'bytes': 100,
                'sha256': '6' * 64, 'mode': 0o644, 'archive_mode': 0o644},
               {'path': 'windows/GODOT-COPYRIGHT.txt', 'bytes': 300,
                'sha256': '7' * 64, 'mode': 0o644, 'archive_mode': 0o644}]
    record = dict(source, target='windows', version='0.3.3-dev', build_number=6,
                  export_completed=True, built_at_utc='2026-10-24T00:00:00+00:00',
                  artifact=copy.deepcopy(artifact), payload=copy.deepcopy(payload))
    return copy.deepcopy({
        'source': source, 'artifact_record': record, 'payload': copy.deepcopy(payload),
        'embedded_pck': {
            'storage': 'embedded exact original pack range', 'offset': 1012,
            'bytes': 3072, 'sha256': '8' * 64, 'pack_version': 4,
            'engine_version': [4, 7, 2],
        },
        'host': {'node': 'SYNTHETIC-NOT-A-NATIVE-HOST',
                 'platform': 'Windows-synthetic-data-format-fixture', 'python': '3.12.0'},
    })


def png_bytes(width=640, height=360, rgb=(32, 48, 64)):
    """Generate a complete stdlib RGB PNG; it is not a game screenshot."""
    if type(width) is not int or type(height) is not int or not 1 <= width <= 4096 or not 1 <= height <= 4096:
        raise ValueError('bounded positive integer fixture dimensions required')
    if len(rgb) != 3 or any(type(value) is not int or not 0 <= value <= 255 for value in rgb):
        raise ValueError('three RGB fixture bytes required')
    def chunk(kind, payload):
        return struct.pack('>I', len(payload)) + kind + payload + struct.pack('>I', zlib.crc32(kind + payload) & 0xffffffff)
    raster = (b'\0' + bytes(rgb) * width) * height
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(raster)) + chunk(b'IEND', b''))


def _json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def _actor(actor_id, *, weapon='sidearm', ammo=15, reserve=60):
    return {
        'id': actor_id, 'team': 0 if actor_id <= 5 else 1, 'alive': True,
        'position': [0.0, 0.05, 0.0], 'velocity': [0.0, 0.0, 0.0],
        'yaw': 0.0, 'pitch': 0.0, 'health': 100.0, 'weapon': weapon,
        'ammo': ammo, 'reserve': reserve, 'reload': 0.0, 'credits': 800,
        'grenades': 1, 'smokes': 1,
        'inventory': ['sidearm'] if weapon == 'sidearm' else ['sidearm', 'smg'],
        'kills': 0, 'deaths': 0, 'assists': 0,
    }


def _snapshot(wall=1000, *, round_number=1, phase='buy', paused=False,
              weapon='sidearm', ammo=15, reserve=60):
    actor = _actor(1, weapon=weapon, ammo=ammo, reserve=reserve)
    actors = [actor] + [_actor(actor_id) for actor_id in range(2, 11)]
    frames = wall // 16
    return {
        'schema': 1, 'scope': 'debug_offline_read_only_observation', 'scenario': 'standard',
        'wall_msec': wall, 'elapsed': wall / 1000.0, 'drawn_frames': frames,
        'simulation_tick': frames, 'time_scale': 1.0, 'phase': phase,
        'time_left': 15.0 if phase == 'buy' else 90.0,
        'round_number': round_number, 'attack_score': round_number - 1, 'defend_score': 0,
        'objective_state': 'carried', 'objective_timer': 0.0, 'objective_carrier': 1,
        'objective_position': [0.0, 0.05, 0.0], 'interaction_progress': 0.0,
        'local_contribution': 0, 'local_actor': actor, 'actors': actors,
        'completion_calls': 0, 'events_dropped': 0,
        'local_input': {'interact': False, 'fire': False, 'reload': False, 'move': [0.0, 0.0]},
        'frame_diagnostics': {
            'read_begin_usec': wall * 1000, 'read_end_usec': wall * 1000 + 1,
            'max_physics_steps_per_frame': 8, 'physics_ticks_per_second': 60,
            'physics_jitter_fix': 0.5, 'max_fps': 60, 'process_frames': frames,
            'physics_frames': frames, 'drawn_frames': frames,
            'process_max_seconds_last_engine_window': 0.016,
            'physics_step_max_seconds_last_engine_window': 0.001,
            'draw_calls_last_rendered_frame': 100, 'primitives_last_rendered_frame': 1000,
            'viewport_visible_size': [640.0, 360.0], 'viewport_texture_size_pixels': [640.0, 360.0],
            'viewport_3d_scale': 1.0,
            'internal_3d_target_size': {'available': False,
                'reason': 'Inspected Viewport API exposes output texture size, not internal 3D target size.'},
        },
        'ui': {
            'screen': 'game', 'paused': paused, 'status_text': '', 'scoreboard_visible': False,
            'focused': True, 'touch_controls': False, 'waiting_for_input_release': False,
            'capabilities': {'mobile': False, 'touchscreen': False}, 'mouse_mode': 0 if paused else 2,
            'window_mode': 0, 'window_size': [640, 360],
        },
    }


def _initial(profile, seed):
    value = _snapshot()
    value.update(elapsed=0.0, simulation_tick=0)
    value.update(initial_profile=copy.deepcopy(profile),
                 initial_conditions='stock_spawns_teams_random_seeds', match_seed=str(seed),
                 actor_spread_seeds={str(i): str(seed + i * 17) for i in range(1, 11)},
                 difficulty='normal', protocol=6, prediction_enabled=False,
                 rules={'buy_seconds': 15.0, 'round_seconds': 100.0, 'device_seconds': 35.0,
                        'plant_seconds': 3.0, 'defuse_seconds': 5.0, 'win_score': 7})
    return value


def _write_trace(directory, initial, later, status):
    directory.mkdir(parents=True, exist_ok=False)
    rows = [copy.deepcopy(initial), *copy.deepcopy(later)]
    for index, row in enumerate(rows):
        row['event_index'] = index
        row['observer_wall_msec'] = row.get('wall_msec', initial['wall_msec'])
        if index == 0:
            row['event'] = 'initial'
    (directory / 'events.jsonl').write_text(''.join(json.dumps(row, allow_nan=False) + '\n' for row in rows), encoding='utf-8')
    _json(directory / 'status.json', status)
    return rows[0]


def _capture_fence(name, binding, round_number, deadline):
    value = {'capture': name, 'expected_actor_id': 1, 'expected_round': round_number,
             'expected_phase': 'buy', 'expected_binding': copy.deepcopy(binding),
             'absolute_deadline_monotonic': deadline, 'additional_drawn_frames_required': 2,
             'transition_watchdog_seconds': 160 if round_number == 2 else 30,
             'binding_before_capture': copy.deepcopy(binding),
             'binding_after_capture': copy.deepcopy(binding),
             'remaining_original_budget_seconds': 1.0}
    base_wall = 40000 if round_number == 2 else 5000
    for index, field in enumerate(('acknowledged', 'ready', 'before_capture', 'after_capture_barrier', 'after_capture')):
        value[field] = _snapshot(base_wall + index * 100, round_number=round_number)
    return value


def _hud_pause(name, *, wall, weapon, ammo, reserve, round_number, phase, resume):
    before = _snapshot(wall, round_number=round_number, phase=phase,
                       weapon=weapon, ammo=ammo, reserve=reserve)
    paused = _snapshot(wall + 100, round_number=round_number, phase=phase, paused=True,
                       weapon=weapon, ammo=ammo, reserve=reserve)
    after = copy.deepcopy(paused)
    after.update(wall_msec=wall + 200, drawn_frames=paused['drawn_frames'] + 2)
    receipt = {'capture': name, 'before': before, 'paused': paused,
               'after_analysis': after, 'scope': 'ordinary native pause for saved-pixel OCR',
               'resume_after_analysis': resume}
    if resume:
        receipt['resumed'] = _snapshot(wall + 300, round_number=round_number, phase=phase,
                                       weapon=weapon, ammo=ammo, reserve=reserve)
    return receipt


def write_complete_trial(directory, identity, *, verbose=False, client_pid=101,
                         reopened_pid=201, observer=None):
    """Write53 required synthetic files and return the generated results object.

    Observer, when provided, is a fake/test callback. It supplies its own owned
    birth/job context externally. This function never invents native birth data.
    Runtime clocks surround synchronous construction; no sleeps or input occur.
    """
    if type(verbose) is not bool:
        raise ValueError('fixture verbose flag must be bool')
    if any(type(pid) is not int or pid <= 0 for pid in (client_pid, reopened_pid)) or client_pid == reopened_pid:
        raise ValueError('distinct positive fixture process IDs required')
    directory = Path(directory).absolute()
    if directory.is_symlink() or (directory.exists() and not directory.is_dir()):
        raise ValueError('fixture needs a real directory')
    owned = [name + '.png' for name in CAPTURES] + ['ocr-current.png']
    owned += ['ocr-stdout/%03d.log' % index for index in range(1, 17)]
    owned += ['commands.json', 'actions.json', 'ocr-commands.json', 'results.json',
              'client.log', 'reopened.log', 'ocr-stderr.log',
              'controller-stdout.log', 'controller-stderr.log',
              'initial-offline-trace/events.jsonl', 'initial-offline-trace/status.json',
              'restart-profile-trace/events.jsonl', 'restart-profile-trace/status.json',
              'state/roaming/Godot/app_userdata/SIGHTBREAK/offline_training.json']
    for name in owned:
        target = directory / name
        if target.exists() or target.is_symlink():
            raise ValueError('fixture refuses existing producer output: ' + name)
        for parent in target.parents:
            if parent == directory.parent:
                break
            if parent.is_symlink() or (parent.exists() and not parent.is_dir()):
                raise ValueError('fixture output parent is not a real directory')
    directory.mkdir(parents=True, exist_ok=True)
    directory = directory.resolve()
    identity = copy.deepcopy(identity)
    source = copy.deepcopy(identity['source'])
    started = time.monotonic()
    actions, commands, ocr_commands, close_receipts = [], [], [], []
    def seconds():
        return time.monotonic() - started
    def action(event, **details):
        value = {'event': event, 'seconds': seconds(),
                 'wall_unix_msec': time.time_ns() // 1_000_000, 'held_keys': [],
                 'native_state': {'target_window': 1001, 'foreground_window': 1001,
                                  'target_focused': True, 'lmb_down': False,
                                  'keys_down': {'r': False, 'd': False, 'w': False},
                                  'state_source': 'GetForegroundWindow/GetAsyncKeyState; zero is not delivery proof'}}
        value.update(details)
        actions.append(value)
    executable = 'C:/synthetic-export/windows/SIGHTBREAK.exe'
    flags = ['--audio-driver', 'Dummy', '--position', '0,0', '--resolution', '640x360']
    def launch(name, pid, trace, use_verbose=False):
        command = [executable, *flags, *(['--verbose'] if use_verbose else []), '--',
                   '--offline-validation', '--offline-trace-dir=' + str(trace)]
        commands.append({'name': name, 'command': command, 'pid': pid, 'started_seconds': seconds(), 'exit_code': 0})
        if observer is not None:
            observer('native_launch', name=name, pid=pid)
    def close(name, pid):
        receipt = {'process': name, 'pid': pid, 'close_limit_seconds': 20,
                   'request_before_monotonic': time.monotonic(),
                   'request_before_wall_unix_ns': time.time_ns()}
        receipt.update(request_returned_monotonic=time.monotonic(), request_returned_wall_unix_ns=time.time_ns())
        receipt.update(wait_finished_monotonic=time.monotonic(), wait_finished_wall_unix_ns=time.time_ns(), exit_code=0)
        close_receipts.append(receipt)
        if observer is not None:
            observer('close_wait_finished', **copy.deepcopy(receipt))
    initial_trace = directory / 'initial-offline-trace'
    restart_trace = directory / 'restart-profile-trace'
    profile_path = directory / 'state/roaming/Godot/app_userdata/SIGHTBREAK/offline_training.json'
    final_profile = copy.deepcopy(PROFILE_DEFAULTS)
    final_profile['settings']['sensitivity'] = 0.004
    launch('client', client_pid, initial_trace)
    client_initial = _initial(PROFILE_DEFAULTS, 314159265)
    client_later = [_snapshot(20000, phase='live', ammo=13),
                    _snapshot(22000, phase='live', ammo=15, reserve=58),
                    _snapshot(40000, round_number=2),
                    _snapshot(60000, round_number=2, phase='live', paused=True, weapon='smg', ammo=30, reserve=120)]
    for row, kind in zip(client_later, ('local_shot', 'reload', 'round_number', 'weapon')):
        row['event'] = kind
    client_status = _snapshot(100000, round_number=2, phase='live', paused=True, weapon='smg', ammo=30, reserve=120)
    client_initial = _write_trace(initial_trace, client_initial, client_later, client_status)
    _json(profile_path, final_profile)
    capture_records = []
    stderr = bytearray()
    def write_ocr(number):
        spec = OCR_SPECS[number - 1]
        if spec['psm'] == 11:
            (directory / 'ocr-current.png').write_bytes(png_bytes(rgb=(80 + number, 48, 64)))
        receipt = {'command': ['C:/synthetic-tesseract/tesseract.exe', 'stdin', 'stdout', '--psm', str(spec['psm'])],
                   'label': spec['label'], 'started_seconds': seconds()}
        if spec['psm'] == 11:
            receipt['command'].append('tsv')
        payload = spec['stdout']
        path = directory / 'ocr-stdout' / (str(number).zfill(3) + '.log')
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(payload)
        receipt.update(stdout_path=path.relative_to(directory).as_posix(), stdout_total_bytes=len(payload),
                       stdout_retained_bytes=len(payload), stdout_sha256=hashlib.sha256(payload).hexdigest(),
                       stdout_complete=True, stdout_truncated=False, exit_code=0, finished_seconds=seconds())
        ocr_commands.append(receipt)
        stderr.extend(('\nOCR ' + spec['label'] + '\n').encode('utf-8'))
    after_capture_ocr = {
        '05-after-fire': (1, 2), '06-after-reload': (3, 4),
        '06d-funded-requisition': (5,), '06e-purchased-smg': (6, 7),
        '06f-switched-sidearm': (8, 9), '06g-switched-primary': (10, 11),
        '07-field-menu': (12,), '07b-field-settings': (13,),
        '07d-explicit-resume': (14, 15, 16),
    }
    for index, name in enumerate(CAPTURES[:17]):
        action('capture_begin', capture=name)
        (directory / (name + '.png')).write_bytes(png_bytes(rgb=(32 + index, 48, 64)))
        capture_records.append({'name': name, 'dimensions': [640, 360]})
        action('capture_end', capture=name, dimensions=[640, 360])
        for number in after_capture_ocr.get(name, ()):
            write_ocr(number)
            if number == 5:
                action('click_text', text='VECTORLINE', caption=None, heading=None)
            elif number == 12:
                action('click_text', text='SETTINGS', caption=None, heading=None)
            elif number == 13:
                action('settings_slider_click')
            elif number == 16:
                action('click_text', text='LEAVE', caption='LEAVE MATCH', heading='FIELD MENU')
    (directory / 'ocr-stderr.log').write_bytes(bytes(stderr))
    (directory / 'client.log').write_text('Godot Engine v4.7.2.stable.official.ed1daf0bf\nMATCH: Round 1\nMATCH: Round live. Secure Relay Yard.\nMATCH: Round 2\nMATCH: Round live. Secure Relay Yard.\n', encoding='utf-8')
    close('client', client_pid)
    launch('reopened', reopened_pid, restart_trace, verbose)
    restart_initial = _initial(final_profile, 271828182)
    restart_live = _snapshot(16000, phase='live')
    restart_live['event'] = 'phase'
    restart_status = _snapshot(20000, phase='live')
    restart_status['local_actor']['position'] = [0.0, 0.05, -1.0]
    restart_status['actors'][0] = copy.deepcopy(restart_status['local_actor'])
    restart_initial = _write_trace(restart_trace, restart_initial, [restart_live], restart_status)
    for index, name in enumerate(CAPTURES[17:], 17):
        action('capture_begin', capture=name)
        (directory / (name + '.png')).write_bytes(png_bytes(rgb=(32 + index, 48, 64)))
        capture_records.append({'name': name, 'dimensions': [640, 360]})
        action('capture_end', capture=name, dimensions=[640, 360])
    (directory / 'reopened.log').write_text('Godot Engine v4.7.2.stable.official.ed1daf0bf\nMATCH: Round 1\nMATCH: Round live. Secure Relay Yard.\n', encoding='utf-8')
    close('reopened', reopened_pid)
    initial_binding = {'source': source, 'process_pid': client_pid, 'process_running': True,
                       'trace_directory': str(initial_trace)}
    loaded_binding = {'source': source, 'process_pid': reopened_pid, 'process_running': True,
                      'trace_directory': str(restart_trace), 'loaded_initial_event': restart_initial,
                      'stored_profile': final_profile}
    driver_args = ['scripts/verify_offline_export.py', '--target', 'windows', '--hosted-render-priority', 'below-normal',
                   '--display', ':102', '--timeout', '300', '--output', str(directory),
                   *(['--reopened-verbose'] if verbose else [])]
    pauses = [
        _hud_pause('05-after-fire', wall=20100, weapon='sidearm', ammo=13, reserve=60,
                   round_number=1, phase='live', resume=True),
        _hud_pause('06-after-reload', wall=22300, weapon='sidearm', ammo=15, reserve=58,
                   round_number=1, phase='live', resume=True),
        _hud_pause('06e-purchased-smg', wall=41000, weapon='smg', ammo=30, reserve=120,
                   round_number=2, phase='buy', resume=True),
        _hud_pause('06f-switched-sidearm', wall=60000, weapon='sidearm', ammo=15, reserve=58,
                   round_number=2, phase='live', resume=True),
        _hud_pause('06g-switched-primary', wall=61000, weapon='smg', ammo=30, reserve=120,
                   round_number=2, phase='live', resume=False),
        _hud_pause('07d-explicit-resume', wall=61800, weapon='smg', ammo=30, reserve=120,
                   round_number=2, phase='live', resume=False),
    ]
    reload_before = _snapshot(20500, phase='live', ammo=13)
    reload_started = _snapshot(20600, phase='live', ammo=13)
    reload_started['local_actor']['reload'] = 1.3
    reload_started['actors'][0] = copy.deepcopy(reload_started['local_actor'])
    reload_completed = _snapshot(22000, phase='live', ammo=15, reserve=58)
    reload_ready = _snapshot(22100, phase='live', ammo=15, reserve=58)
    reload_after = _snapshot(22200, phase='live', ammo=15, reserve=58)
    settings_paused = copy.deepcopy(pauses[4]['after_analysis'])
    settings_ready = copy.deepcopy(settings_paused)
    settings_ready.update(wall_msec=61400, drawn_frames=settings_paused['drawn_frames'] + 2)
    settings_resumed = _snapshot(61500, round_number=2, phase='live', weapon='smg', ammo=30, reserve=120)
    settings_capture = _snapshot(61600, round_number=2, phase='live', weapon='smg', ammo=30, reserve=120)
    settings_after = _snapshot(61700, round_number=2, phase='live', weapon='smg', ammo=30, reserve=120)
    focus_start = _snapshot(16000, phase='live')
    held_input = _snapshot(16100, phase='live')
    held_input['local_input'].update(move=[0.0, -1.0], fire=True)
    focus_lost = _snapshot(16200, phase='live', paused=True)
    focus_lost['ui']['focused'] = False
    focus_restored = _snapshot(16300, phase='live', paused=True)
    neutral_samples = [_snapshot(wall, phase='live') for wall in (16400, 16500, 16600)]
    for state in neutral_samples:
        state['ui']['waiting_for_input_release'] = True
    controls_released = _snapshot(16700, phase='live')
    before_fresh_key = _snapshot(16800, phase='live')
    moved = _snapshot(16900, phase='live')
    moved['local_input']['move'] = [0.0, -1.0]
    moved['local_actor']['position'] = [0.0, 0.05, -1.0]
    moved['actors'][0] = copy.deepcopy(moved['local_actor'])
    focus_after = _snapshot(17000, phase='live')
    focus_after['local_actor']['position'] = [0.0, 0.05, -1.0]
    focus_after['actors'][0] = copy.deepcopy(focus_after['local_actor'])
    route_start = _snapshot(56000, round_number=2, phase='live', weapon='smg', ammo=30, reserve=120)
    route_start['local_actor']['position'] = [-4.4, 0.05, -21.0]
    route_start['actors'][0] = copy.deepcopy(route_start['local_actor'])
    route_after = _snapshot(59000, round_number=2, phase='live', weapon='smg', ammo=30, reserve=120)
    route_after['local_actor']['position'] = [-7.8, 0.05, -21.0]
    route_after['actors'][0] = copy.deepcopy(route_after['local_actor'])
    result = {
        'passed': True, 'target': 'windows', 'host': identity['host']['platform'],
        'controller_command': [sys.executable, *driver_args], 'captures': capture_records,
        'source': source, 'artifact_source': identity['artifact_record'],
        'executable_sha256': identity['artifact_record']['artifact']['sha256'],
        'engine': '4.7.2.stable.official.ed1daf0bf', 'profile_observation_path': str(profile_path),
        'shutdown_study_observations': close_receipts, 'commands': commands,
        'ocr_commands': ocr_commands, 'events': list(CAPTURES), 'cleanup_errors': [],
        'initial_exit': 0, 'reopened_exit': 0, 'exit': 0, 'clean_exit': True,
        'exit_method': 'completion-driven WM_CLOSE', 'settings_restart_equal': True,
        'natural_round_completed': True, 'purchase_and_weapon_switch': True,
        'settings_loaded_into_reopened_process': True, 'explicit_resume': True,
        'incomplete_training_unchanged_after_reopened_exit': True,
        'exported_plant_defuse': 'UNVERIFIED',
        'training_progress': 'Stored record preserved; full exported match completion remains UNVERIFIED',
        'capture_method': 'raw Windows client-area desktop capture',
        'movement_aim': 'Real native input delivered during live phase; authoritative displacement is not measured by this controller',
        'limits': 'Screenshots require visual review; no physical-device/performance acceptance. Linux isolated automation disables accessibility and D-Bus portals; their coverage remains UNVERIFIED.',
        'controller_sha256': hashlib.sha256(Path(__file__).with_name('verify_offline_export.py').read_bytes()).hexdigest(),
        'fired_hud': {'health': 100, 'ammo': 13, 'reserve': 60, 'status_ocr': '100 HEALTH\n', 'ammo_ocr': '13 / 60\n'},
        'reloaded_hud': {'health': 100, 'ammo': 15, 'reserve': 58, 'status_ocr': '100 HEALTH\n', 'ammo_ocr': '15 / 58\n'},
        'resumed_hud': {'health': 100, 'ammo': 30, 'reserve': 120, 'status_ocr': '100 HEALTH\n', 'ammo_ocr': '30 / 120\n'},
        'hud_analysis_pauses': pauses,
        'native_reload': {
            'before': reload_before, 'started': reload_started, 'completed': reload_completed,
            'capture_ready': reload_ready, 'after_capture': reload_after,
            'input_seconds': commands[0]['started_seconds'],
            'wall_seconds_after_input': max(0.0, close_receipts[0]['request_before_monotonic'] - started
                                            - commands[0]['started_seconds']),
            'observed_simulation_seconds': reload_completed['elapsed'] - reload_started['elapsed'],
            'completion_watchdog_seconds': 15, 'whole_flow_deadline_unchanged': True,
        },
        'native_settings_resume': {
            'paused_before_settings': settings_paused, 'paused_after_settings': settings_ready,
            'resumed': settings_resumed, 'capture_ready': settings_capture, 'after_capture': settings_after,
            'transition_watchdog_seconds': 10, 'same_living_player_required': True,
        },
        'hosted_render_priority': [
            {'pid': pid, 'window_pid': pid, 'before_priority_class': 0x20,
             'current_priority_class': 0x4000,
             'scope': 'Opt-in Windows hosted offline QA only; owned child below-normal, no affinity/rules/time-scale changes'}
            for pid in (client_pid, reopened_pid)
        ],
        'settings_cover_route': {
            'status': 'FIXED_ROUTE_REACHED',
            'scope': 'fixed ordinary-input settings test route; no product fix',
            'requested': [-7.8, -21.0], 'start': route_start,
            'observations': [copy.deepcopy(route_start), copy.deepcopy(route_after)],
            'original_second_live_absolute_deadline': started + 35,
            'after': route_after, 'endpoint': [-7.8, 0.05, -21.0],
            'remaining_original_second_live_budget': 1.0,
        },
        'phase_capture_fences': {
            '06c-next-round': _capture_fence('06c-next-round', initial_binding, 2, started + 160),
            '10-reopened-loaded-settings': _capture_fence('10-reopened-loaded-settings', loaded_binding, 1, started + 30),
        },
        'native_focus_recovery': {
            'scope': 'fresh stock match after settings restart', 'passed': True,
            'context_fence': {'status': 'LIVING_CONTEXT_PRESERVED_THROUGH_CAPTURE',
                              'baseline': focus_start, 'last_valid_state': focus_after},
            'held_input_acknowledged': held_input, 'lost': focus_lost,
            'restored_paused': focus_restored, 'held_neutral_samples': neutral_samples,
            'released': controls_released,
            'fresh_press': {'status': 'LIVING_MOVEMENT_OBSERVED', 'released': copy.deepcopy(controls_released),
                            'key_down_dispatched': True, 'before_key': before_fresh_key,
                            'last_after_key': copy.deepcopy(moved), 'moved': copy.deepcopy(moved)},
            'capture_context': {
                '11a-restored-focus-still-paused': {'before': copy.deepcopy(focus_restored),
                                                  'after': copy.deepcopy(focus_restored)},
                '11b-resumed-held-input-neutral': {'before': copy.deepcopy(neutral_samples[-1]),
                                                  'after': copy.deepcopy(neutral_samples[-1])},
                '11c-fresh-press-movement': {'before': copy.deepcopy(moved), 'after': copy.deepcopy(focus_after)},
            },
            'fresh_press_movement': copy.deepcopy(moved),
        },
        'last_offline_observation': restart_status,
        'elapsed_seconds': seconds(),
    }
    _json(directory / 'commands.json', commands)
    _json(directory / 'actions.json', actions)
    _json(directory / 'ocr-commands.json', ocr_commands)
    _json(directory / 'results.json', result)
    (directory / 'controller-stdout.log').write_text('\n'.join(CAPTURES) + '\n' + json.dumps(result, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    (directory / 'controller-stderr.log').write_bytes(b'')
    return result
