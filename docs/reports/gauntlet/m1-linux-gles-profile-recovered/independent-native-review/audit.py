#!/usr/bin/env python3
"""Independent read-only archive, Git identity, binary and native receipt audit."""
import ast
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import re
import struct
import subprocess
import time
import zipfile

ROOT = Path(__file__).resolve().parents[5]
REPORT = ROOT / 'docs/reports/gauntlet/m1-linux-gles-profile-recovered'
ARCHIVE = REPORT / 'native-r1'
SOURCE = 'b1a131ab4790ac84371b54ee236441a66faf4125'
BUILDER = Path('/workspace/sightbreak-linux-profile-recovered')


def digest(path, kind='sha256'):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, kind).hexdigest()


def load(path):
    return json.loads(Path(path).read_text())


def git(*args, input=None):
    return subprocess.check_output(['git', *args], cwd=ROOT, input=input)


def main():
    index = load(ARCHIVE / 'payload-index.json')
    raw_root = Path(index['original_raw_directory'])
    archived = []
    for item in index['files']:
        path = ARCHIVE / item['archive_path']
        compressed = path.read_bytes()
        raw = gzip.decompress(compressed) if item['gzip'] else compressed
        assert len(compressed) == item['archive_bytes']
        assert hashlib.sha256(compressed).hexdigest() == item['archive_sha256']
        assert len(raw) == item['raw_bytes']
        assert hashlib.sha256(raw).hexdigest() == item['raw_sha256']
        original = (BUILDER if item['archive_path'].startswith('sources/') else raw_root) / item['original_path']
        assert original.read_bytes() == raw, original
        if item['archive_path'].startswith('sources/'):
            assert git('show', SOURCE + ':' + item['original_path']) == raw
        archived.append({'path': item['archive_path'], 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(), 'matches_original': True})
    actual = {p.relative_to(ARCHIVE).as_posix() for p in ARCHIVE.rglob('*') if p.is_file()}
    assert actual == {'payload-index.json', *(item['archive_path'] for item in index['files'])}
    local_only = []
    for item in index['retained_locally_not_duplicated']:
        path = Path(item['path'])
        assert path.stat().st_size == item['bytes'] and digest(path) == item['sha256'], path
        local_only.append({'path': str(path), 'matches_inventory': True})

    tree = git('ls-tree', '-rz', SOURCE).split(b'\0')
    entries = {}
    for record in tree:
        if not record:
            continue
        meta, name = record.split(b'\t', 1)
        mode, kind, oid = meta.split()
        if kind == b'blob':
            entries[name.decode()] = oid
    batch = git('cat-file', '--batch', input=b'\n'.join(entries.values()) + b'\n')
    blobs, cursor = {}, 0
    for path, oid in entries.items():
        end = batch.index(b'\n', cursor)
        header = batch[cursor:end].split()
        assert header[:2] == [oid, b'blob']
        length = int(header[2])
        blobs[path] = batch[end + 1:end + 1 + length]
        cursor = end + 2 + length
    shipping, validation = hashlib.sha256(), hashlib.sha256()
    for path in sorted(p for p in entries if p.startswith('game/')):
        relative = Path(path).relative_to('game')
        if any(part in ('.godot', 'tests') for part in relative.parts):
            continue
        shipping.update(relative.as_posix().encode() + b'\0' + blobs[path] + b'\0')
    for directory in ('scripts', '.github', 'game/tests'):
        for path in sorted(p for p in entries if p.startswith(directory + '/')):
            if any(part in ('__pycache__', '.godot') for part in Path(path).parts) or Path(path).suffix == '.pyc':
                continue
            validation.update(path.encode() + b'\0' + blobs[path] + b'\0')
    identity = {'source_commit': SOURCE, 'source_game_tree': git('rev-parse', SOURCE + ':game').decode().strip(),
                'source_content_sha256': shipping.hexdigest(), 'source_validation_sha256': validation.hexdigest()}
    preflight = load(ARCHIVE / 'preflight.json')
    manifest = load(ARCHIVE / 'export/linux/source.json')
    results = load(ARCHIVE / 'native-plant/results.json')
    post = load(ARCHIVE / 'post-run-cleanup.json')
    for recorded in (preflight['source'], manifest, results['source'], results['artifact_source'], post['source_after']):
        for key, value in identity.items():
            assert recorded[key] == value, (key, recorded[key], value)
        assert recorded['source_dirty'] is False and recorded['source_game_dirty'] is False
    controller = blobs['scripts/verify_offline_match.py']
    controller_sha = hashlib.sha256(controller).hexdigest()
    assert controller_sha == preflight['controller_sha256'] == results['controller_sha256']
    assert git('diff', SOURCE, '--', 'scripts', '.github', 'game') == b''

    pins = {}
    for node in ast.parse(blobs['scripts/toolchain.py']).body:
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name) and node.targets[0].id in ('EDITORS', 'TEMPLATES_SHA512'):
            pins[node.targets[0].id] = ast.literal_eval(node.value)
    archives = []
    for item in preflight['archives']:
        expected = pins['TEMPLATES_SHA512'] if item['archive'].endswith('.tpz') else pins['EDITORS']['linux'][2]
        actual_sha = digest(item['archive'], 'sha512')
        assert actual_sha == expected == item['archive_sha512']
        with zipfile.ZipFile(item['archive']) as z, z.open(item['member']) as stream:
            member_sha = hashlib.file_digest(stream, 'sha256').hexdigest()
            member_bytes = z.getinfo(item['member']).file_size
        assert member_sha == item['member_sha256'] == digest(item['file'])
        assert member_bytes == item['member_bytes'] == Path(item['file']).stat().st_size
        archives.append({'archive': item['archive'], 'archive_bytes': Path(item['archive']).stat().st_size,
                         'sha512': actual_sha, 'member': item['member'], 'member_bytes': member_bytes, 'member_sha256': member_sha})

    executable = Path(results['executable'])
    elf = executable.read_bytes()
    elf_sha = hashlib.sha256(elf).hexdigest()
    assert len(elf) == manifest['artifact']['bytes'] and elf_sha == manifest['artifact']['sha256'] == results['executable_sha256']
    assert elf[:6] == b'\x7fELF\x02\x01' and struct.unpack_from('<H', elf, 18)[0] == 62
    pack_length, trailer_magic = struct.unpack_from('<QI', elf, len(elf) - 12)
    pack_start = len(elf) - 12 - pack_length
    magic, format_version, major, minor, patch, flags, file_base, directory = struct.unpack_from('<6I2Q', elf, pack_start)
    assert magic == trailer_magic == 0x43504447
    assert [format_version, major, minor, patch, flags] == [4, 4, 7, 2, 2]
    pos = pack_start + directory
    count = struct.unpack_from('<I', elf, pos)[0]
    pos += 4
    resources = []
    for _ in range(count):
        length = struct.unpack_from('<I', elf, pos)[0]
        pos += 4
        name = elf[pos:pos + length].rstrip(b'\0').decode()
        pos += length
        offset, size, md5, resource_flags = struct.unpack_from('<QQ16sI', elf, pos)
        pos += 36
        assert resource_flags == 0
        start = pack_start + file_base + offset
        assert pack_start <= start <= start + size <= pack_start + directory
        assert hashlib.md5(elf[start:start + size]).digest() == md5, name
        resources.append({'path': name, 'bytes': size, 'md5_verified': True})
    assert len({item['path'] for item in resources}) == count == 134
    support = load(ARCHIVE / 'export-source-verified.json')
    assert sorted(item['path'] for item in resources) == sorted(support['resources'])
    assert any(item['path'] == 'scripts/offline_diagnostics.gdc' for item in resources)
    assert not any('tests' in Path(item['path']).parts for item in resources)
    for item in manifest['payload']:
        path = raw_root / 'export' / item['path']
        assert digest(path) == item['sha256'] and path.stat().st_size == item['bytes']

    commands = load(ARCHIVE / 'native-plant/commands.json')
    assert commands == results['commands']
    assert [item['name'] for item in commands] == ['xvfb', 'client']
    assert commands[0]['command'][-4:] == ['0', '1280x720x24', '-nolisten', 'tcp']
    client = commands[1]['command']
    assert client[0] == str(executable) and client[1] == '--gpu-profile'
    assert client.index('--gpu-profile') < client.index('--')
    assert '--offline-scenario=plant' in client and '--offline-seed=42' in client
    assert '--linux-frame-diagnostics' not in results['controller_command']
    assert not (raw_root / 'native-plant/linux-frame-samples.jsonl').exists()
    assert results['timeout_seconds'] == 180 and results['target'] == 'linux' and results['scenario'] == 'plant'
    assert results['engine'] == '4.7.2.stable.official.ed1daf0bf'
    assert results['passed'] is False and results['error'] == 'Objective scenario live phase'
    assert results['partial_checks'] == {} and results['initial_exit'] is None and results['reopened_exit'] is None
    assert results['cleanup_errors'] == [] and [item['exit_code'] for item in commands] == [0, -15]
    initial = results['initial']
    event_lines = (ARCHIVE / 'native-plant/trace/events.jsonl').read_text().splitlines()
    assert len(event_lines) == 1 and json.loads(event_lines[0]) == initial
    assert initial['event'] == 'initial' and initial['protocol'] == 6 and initial['prediction_enabled'] is False
    assert initial['initial_conditions'] == 'declared_initial_spawns_side_and_seeds_only'
    assert initial['match_seed'] == '42' and len(initial['actors']) == 10
    assert all(a['alive'] is True and a['health'] == 100 for a in initial['actors'])
    assert initial['rules'] == {'buy_seconds': 15, 'round_seconds': 100, 'device_seconds': 35, 'plant_seconds': 3, 'defuse_seconds': 5, 'win_score': 7}
    settings = initial['initial_profile']['settings']
    assert settings['graphics_quality'] == 1 and settings['render_scale'] == 1 and settings['fps_limit'] == 60
    assert initial['initial_profile']['matches'] == 0 and initial['initial_profile']['xp'] == 0 and initial['initial_profile']['credits'] == 0
    status = load(ARCHIVE / 'native-plant/trace/status.json')
    diagnostic = status['frame_diagnostics']
    assert status['phase'] == 'buy' and status['round_number'] == 1 and status['simulation_tick'] == 844
    assert math.isclose(status['elapsed'], 844 / 60) and math.isclose(status['time_left'], 15 - 844 / 60)
    assert status['time_scale'] == 1 and status['objective_state'] == 'carried'
    assert diagnostic['max_fps'] == diagnostic['physics_ticks_per_second'] == 60
    assert diagnostic['viewport_3d_scale'] == 1 and diagnostic['max_physics_steps_per_frame'] == 8
    assert diagnostic['viewport_visible_size'] == diagnostic['viewport_texture_size_pixels'] == [1280, 720]
    actions = [json.loads(line) for line in (ARCHIVE / 'native-plant/actions.jsonl').read_text().splitlines()]
    assert len(actions) == 9 and actions[-1]['event'] == 'failure'
    assert actions[-1]['observed']['simulation_tick'] == status['simulation_tick']
    assert all(a['held_keys'] == [] and a['native_state']['lmb_down'] is False for a in actions)
    capture_end = next(a for a in actions if a['event'] == 'capture_end' and a['capture'] == '02-offline-initial-conditions')
    wait_bracket = actions[-1]['seconds'] - capture_end['seconds']
    assert 45 <= wait_bracket < 45.5
    assert "wait(lambda item: item.get('phase') == 'live', 45, 'Objective scenario live phase')" in controller.decode()

    log = gzip.decompress((ARCHIVE / 'native-plant/client.log.gz').read_bytes()).decode()
    assert '4.7.2.stable.official.ed1daf0bf' in log and 'llvmpipe' in log and 'Compatibility' in log
    blocks = []
    for line_number, line in enumerate(log.splitlines(), 1):
        if line.startswith('GPU PROFILE'):
            match = re.fullmatch(r'GPU PROFILE \(total ([^ ]+)ms\):\s*', line)
            assert match, line
            value = float(match[1])
            assert math.isfinite(value) and value >= 0
            blocks.append({'line': line_number, 'header_ms': value, 'rows': []})
        elif line.startswith('\t-'):
            match = re.fullmatch(r'\t-(.*): ([^ ]+)ms', line)
            assert match and blocks
            value = float(match[2])
            assert math.isfinite(value) and value > 0.01
            blocks[-1]['rows'].append({'line': line_number, 'name': match[1], 'reported_ms': value})
    row_blocks = [block for block in blocks if block['rows']]
    assert len(blocks) == 35 and len(row_blocks) == 34
    opaque = []
    for block in row_blocks:
        maximum = max(block['rows'], key=lambda row: row['reported_ms'])
        assert maximum['name'] == 'Render Opaque Pass'
        opaque.append(maximum['reported_ms'])

    observed_cleanup = {'unix_ns': time.time_ns(), 'pids': [], 'groups': [], 'display_paths': []}
    for pid in (9725, 9770, 9816):
        absent = not Path('/proc', str(pid)).exists()
        assert absent, pid
        observed_cleanup['pids'].append({'pid': pid, 'absent': absent})
    for group in (9770, 9816):
        try:
            os.killpg(group, 0)
        except ProcessLookupError:
            absent = True
        else:
            absent = False
        assert absent, group
        observed_cleanup['groups'].append({'pgid': group, 'absent': absent})
    for path in ('/tmp/.X11-unix/X123', '/tmp/.X123-lock'):
        absent = not Path(path).exists()
        assert absent
        observed_cleanup['display_paths'].append({'path': path, 'absent': absent})
    output = {'runtime_source': identity, 'controller_sha256': controller_sha,
              'archive_payload_count': len(archived), 'raw_bytes': sum(item['bytes'] for item in archived),
              'archived_bytes': sum(item['archive_bytes'] for item in index['files']),
              'archived_payloads': archived, 'local_only_count': len(local_only), 'local_only': local_only,
              'engine_archive_verification': archives,
              'elf': {'path': str(executable), 'bytes': len(elf), 'sha256': elf_sha, 'machine': 62,
                      'pck_start': pack_start, 'pck_bytes': pack_length, 'version': [major, minor, patch],
                      'format': format_version, 'file_base': file_base, 'directory': directory, 'resources': resources},
              'native': {'controller_elapsed_seconds': results['elapsed_seconds'], 'failure': results['error'],
                         'phase': status['phase'], 'simulation_tick': status['simulation_tick'], 'elapsed_simulation_seconds': status['elapsed'],
                         'time_left': status['time_left'], 'initial_live_wait_driver_bracket_seconds': wait_bracket,
                         'plant_next_buy_restart_reached': False, 'settings': settings, 'terminal_frame_diagnostics': diagnostic},
              'profile': {'headers': len(blocks), 'row_bearing_blocks': len(row_blocks), 'opaque_largest_in_all_row_blocks': True,
                          'opaque_reported_ms_range': [min(opaque), max(opaque)],
                          'header_ms_range': [min(b['header_ms'] for b in blocks), max(b['header_ms'] for b in blocks)], 'blocks': blocks},
              'independent_live_terminal_cleanup': observed_cleanup,
              'no_engine_native_export_ocr_or_profile_run': True}
    print(json.dumps(output, indent=2))


if __name__ == '__main__':
    main()
