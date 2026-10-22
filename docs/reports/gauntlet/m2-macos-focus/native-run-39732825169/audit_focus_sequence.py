"""Read original focus/capture artifacts without invoking native implementation."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image

read = lambda path: json.loads(path.read_text())
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()


def audit(root):
    menu_root = root / 'macos-menu-input'
    menu = read(menu_root / 'results.json')
    actions = read(menu_root / 'actions.json')
    target, controller = menu.get('client_pid'), menu.get('controller_pid')
    selected = menu.get('selected_client_window')
    samples = [item for item in actions if item['event'] == 'focus_sample']
    requests = [item for item in actions if item['event'] == 'focus_request_returned']
    observations = [item for item in actions if item['event'] == 'focus_observed']
    attempts = [item for item in actions if item['event'] == 'cg_event_post_attempt']
    snapshots = [item.get('native_state') for item in actions
                 if item['event'] in ('observer_before_background_capture', 'focus_before_request',
                                      'focus_request_returned', 'background_capture_observed')]
    for sample in samples:
        snapshots += [sample.get('before_run_loop'), sample.get('after_run_loop')]
    snapshots = [s for s in snapshots if s is not None]
    captures = []
    for path in sorted(menu_root.glob('*.json')):
        if path.name in ('results.json', 'actions.json'):
            continue
        data = read(path)
        if data.get('scope') != 'OS window screenshot from ScreenCaptureKit; read-only helper':
            continue
        png = path.with_suffix('.png')
        pixels = None
        if png.is_file():
            image = Image.open(png)
            image.verify()
            pixels = {'sha256': sha(png), 'dimensions': Image.open(png).size}
        captures.append({'name': path.stem, 'receipt_sha256': sha(path),
                         'receipt': data, 'original_PNG': pixels,
                         'owner_is_current_client': data.get('owner_pid') == target,
                         'window_is_selected': selected is not None and data.get('window_id') == selected.get('window_id')})
    captured_hashes = {c['name']: c for c in captures}
    bindings = []
    for item in menu.get('captures', []):
        actual = captured_hashes.get(item['name'])
        bindings.append({'name': item['name'], 'listed_capture_exists': actual is not None,
                         'PNG_hash_matches': actual is not None and actual['original_PNG'] is not None
                         and actual['original_PNG']['sha256'] == item['png_sha256'],
                         'receipt_hash_matches': actual is not None and actual['receipt_sha256'] == item['receipt_sha256']})
    return {'status': menu['status'], 'failure': menu.get('failure'), 'blocker': menu.get('blocker'),
            'client_pid': target, 'controller_pid': controller, 'selected_client_window': selected,
            'selected_window_owner_matches_client': selected is not None and selected.get('owner_pid') == target,
            'actions_match_embedded_results': actions == menu.get('actions'),
            'background_capture_status': menu.get('background_capture_status'),
            'background_capture_failure': menu.get('background_capture_failure'),
            'request_count': len(requests), 'requests': requests,
            'raw_controller_and_target_identities_consistent': all(
                s.get('controller_pid') == controller and s.get('target_pid') == target for s in snapshots),
            'sample_count': len(samples),
            'samples': samples, 'focus_observations': observations,
            'timeouts': [item for item in actions if item['event'] == 'focus_timeout'],
            'post_attempt_count_from_actions': len(attempts),
            'post_attempts_recorded_before_cleanup': menu.get('cg_event_post_attempts'),
            'post_attempts_recorded_after_cleanup': menu.get('cg_event_post_attempts_after_cleanup'),
            'post_attempts': attempts,
            'observed_control_states': [item for item in actions if item['event'] == 'native_control_observed'],
            'screen_confirmations': [item for item in actions if item['event'] == 'screen_confirmed'],
            'capture_receipts': captures, 'capture_list_hash_bindings': bindings,
            'final_input_release': menu.get('final_input_release'),
            'failure_ordinary_close': menu.get('failure_ordinary_close'), 'cleanup': menu.get('cleanup')}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('full_qa', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.full_qa)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ('status', 'background_capture_status', 'request_count',
                                            'sample_count', 'post_attempt_count_from_actions')}))
