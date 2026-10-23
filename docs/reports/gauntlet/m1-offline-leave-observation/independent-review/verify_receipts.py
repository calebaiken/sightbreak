#!/usr/bin/env python3
"""Recheck retained evidence without starting OCR, Godot or a native display."""
import ast
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    return json.loads((ROOT / path).read_text())


def main():
    for entry in read_json('sha256.json'):
        data = (ROOT / entry['path']).read_bytes()
        assert len(data) == entry['bytes'], entry['path']
        assert digest(data) == entry['sha256'], entry['path']
    controller = (ROOT / 'source/controller.py').read_bytes()
    probe = (ROOT / 'source/probe.py').read_bytes()
    result = read_json('native/results.json')
    assert result['passed'] is True and result['clean_exit'] is True
    assert result['native_settings_only'] is True
    assert result['full_offline_journey'] == 'UNVERIFIED'
    assert result['settings_restart'] == 'NOT_RUN'
    assert result['source']['source_commit'] == '85d6101bb049d41368cac2921c6479afe420a242'
    assert result['source']['source_dirty'] is False
    assert result['source']['source_content_sha256'] == 'f8a849b90df3ff214037cace7bc32c0c7b5e184911558b424b0a6c0f798db781'
    manifest = read_json('native/source.json')
    assert all(manifest[key] == value for key, value in result['source'].items())
    assert manifest['artifact']['sha256'] == result['executable_sha256']
    assert result['initial_exit'] == 0 and result['cleanup_errors'] == []
    assert 0 < result['elapsed_seconds'] < 300
    assert all(command['exit_code'] == 0 for command in result['commands'])

    receipt = result['settings_only_driver']
    assert receipt['driver_sha256'] == digest(probe)
    assert receipt['production_controller_sha256'] == digest(controller)
    text = controller.decode()
    settings_start = "        capture('07-field-menu')\n"
    settings_end = "        ui.request_close()\n        client.wait(timeout=min(20, remaining()))"
    spawn = "        capture('02-offline-spawn')\n"
    cleanup = '    except (Exception, SystemExit) as error:\n'
    transaction = text[text.index(settings_start):text.index(settings_end)]
    assert receipt['verbatim_settings_block_sha256'] == digest(transaction.encode())
    parsed_probe = ast.parse(probe)
    additions = [node.value.value for node in parsed_probe.body
                 if isinstance(node, ast.AugAssign) and isinstance(node.target, ast.Name)
                 and node.target.id == 'setup']
    finishes = [node.value.value for node in parsed_probe.body
                if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name)
                and target.id == 'finish' for target in node.targets)]
    assert len(additions) == len(finishes) == 1
    transformed = (text[:text.index(spawn) + len(spawn)] + additions[0]
                   + transaction + finishes[0] + text[text.index(cleanup):])
    assert receipt['executed_controller_sha256'] == digest(transformed.encode())

    node = next(node for node in ast.walk(ast.parse(controller))
                if isinstance(node, ast.FunctionDef) and node.name == 'exact_ocr_caption')
    namespace = {}
    exec(compile(ast.Module(body=[node], type_ignores=[]), '<retained caption helper>', 'exec'), namespace)
    caption = namespace['exact_ocr_caption']
    commands = read_json('native/ocr-commands.json')
    assert len(commands) == 7
    for command in commands:
        raw = (ROOT / 'native' / command['stdout_path']).read_bytes()
        assert command['stdout_complete'] is True and command['stdout_truncated'] is False
        assert command['exit_code'] == 0
        assert len(raw) == command['stdout_total_bytes'] == command['stdout_retained_bytes']
        assert digest(raw) == command['stdout_sha256']
        assert 0 < command['finished_seconds'] - command['started_seconds'] < 20
    with (ROOT / 'native' / commands[-1]['stdout_path']).open() as stream:
        rows = [row for row in csv.DictReader(stream, delimiter='\t') if row.get('text', '').strip()]
    for row in rows:
        for field in ('left', 'top', 'width', 'height'):
            row[field] = int(row[field]) // 2
    assert caption(rows, 'FIELD MENU') is not None
    control = caption(rows, 'LEAVE MATCH')
    assert control is not None
    assert (control['left'] + control['width'] // 2, control['top'] + control['height'] // 2) == (639, 384)

    states = result['native_settings_resume']
    original = states['paused_before_settings']
    changed = states['paused_after_settings']
    assert changed['elapsed'] == original['elapsed']
    assert changed['local_actor']['health'] == original['local_actor']['health'] == 100
    for key in ('paused_before_settings', 'paused_after_settings', 'resumed', 'capture_ready', 'after_capture'):
        state = states[key]
        assert state['round_number'] == 1 and state['phase'] == 'live' and state['time_scale'] == 1
        assert state['ui']['screen'] == 'game' and state['ui']['focused'] is True
        for field, value in {'id': 1, 'alive': True, 'weapon': 'sidearm', 'ammo': 15, 'reserve': 60}.items():
            assert state['local_actor'][field] == value
    assert states['resumed']['ui']['paused'] is False
    assert states['capture_ready']['drawn_frames'] >= states['resumed']['drawn_frames'] + 2
    assert original['ui']['paused'] is True and changed['ui']['paused'] is True

    actions = read_json('native/actions.json')
    leave = [item for item in actions if item['event'] == 'click_text' and item.get('text') == 'LEAVE']
    assert len(leave) == 1 and leave[0]['caption'] == 'LEAVE MATCH' and leave[0]['heading'] == 'FIELD MENU'
    assert leave[0]['held_keys'] == []
    assert any(item['event'] == 'wait_completed' and item.get('label') == 'Return from offline match' for item in actions)
    assert digest((ROOT / 'original-windows/ocr-current.png').read_bytes()) == 'e62116a4c42c7b09ca947a7eb1cb3551865c4d6f4ffecff36066f8e7d4bee635'
    assert read_json('original-windows/results.json')['passed'] is False
    assert read_json('baseline-replay/results.json')['exact_LEAVE_row'] is None
    independent = read_json('independent-pixel/results.json')
    assert independent['controller_sha256'] == digest(controller)
    assert len(independent['cases']) == 3
    assert all(case['recognized'] == case['expected_recognized'] for case in independent['cases'])
    print('PASS: retained bytes, source/driver binding, seven native OCR outputs, exact LEAVE and scoped native transaction')


if __name__ == '__main__':
    main()
