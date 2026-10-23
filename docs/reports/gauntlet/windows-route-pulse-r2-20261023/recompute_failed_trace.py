"""Read original native receipts; action brackets are not physical hold times."""
import hashlib
import json
from pathlib import Path
import subprocess


BASE = 'e28c8e90b9ef2d0c766bd9152c194e3197ceba9a'
root = Path('/workspace/reviews/windows-native-e28c8e9/.local/e28-actual/receipts/evidence')
bindings = []
def read(relative):
    payload = (root / relative).read_bytes()
    bindings.append({'path': relative, 'bytes': len(payload), 'sha256': hashlib.sha256(payload).hexdigest()})
    return json.loads(payload)

result = read('offline-input/results.json')
actions = read('offline-input/actions.json')
legacy = read('reload-legacy-delayed/results.json')
pulses = []
for index, row in enumerate(actions):
    if row.get('event') != 'settings_route_movement_control' or row.get('mode') != 'pulse':
        continue
    end = next(i for i in range(index + 1, len(actions))
               if actions[i].get('event') == 'settings_route_movement_pulse_released')
    edges = [value for value in actions[index + 1:end + 1] if value.get('event') in ('key_before', 'key_after')]
    down = next(value for value in edges if value.get('event') == 'key_after' and value.get('down') is True)
    up = next(value for value in edges if value.get('event') == 'key_after' and value.get('key') == down['key']
              and value.get('down') is False and value['seconds'] > down['seconds'])
    pulses.append({'request': row, 'all_driver_edges': edges, 'selected_down_after': down, 'selected_up_after': up,
                   'after_call_driver_bracket_seconds': up['seconds'] - down['seconds']})
assert result['source']['source_commit'] == BASE and result['passed'] is False
assert legacy['passed'] is False
receipt = {'source': BASE, 'run': 39926044462, 'job': 120322557935,
           'original_failed_route': result['settings_cover_route'], 'original_route_error': result['error'],
           'pulses': pulses, 'original_legacy_failure': {'passed': legacy['passed'], 'error': legacy.get('error'),
               'elapsed_seconds': legacy.get('elapsed_seconds')}, 'bindings': bindings,
           'inspected_original_source_sha256': {name: hashlib.sha256(subprocess.check_output(
               ['git', 'show', BASE + ':' + name])).hexdigest() for name in (
               'scripts/verify_integration_export.py', 'scripts/verify_offline_export.py',
               'scripts/native_approach.py', 'scripts/native_settings_route.py')},
           'limits': ['Driver traces bracket controller work, not exact SendInput or physical key edges.',
                      'Original OS diagnostics sample r/d/w and provide no independent A bitmap.',
                      'Source WinUI uses ctypes in process; subprocess startup is not present.',
                      'No causal performance, collision, bot or survival claim follows. Legacy timeout remains failed.']}
Path(__file__).with_name('original-failed-trace.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps({'pulse_requests': [row['request']['pulse_wall_seconds'] for row in pulses],
                  'after_call_brackets': [row['after_call_driver_bracket_seconds'] for row in pulses],
                  'legacy_passed': legacy['passed']}))
