"""Read original Windows artifacts; no engine, OCR, input or source mutation."""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image


def recompute(root):
    bindings = []

    def read(relative, lines=False):
        data = (root / relative).read_bytes()
        bindings.append({'path': relative, 'bytes': len(data),
                         'sha256': hashlib.sha256(data).hexdigest()})
        return ([json.loads(line) for line in data.decode().splitlines() if line]
                if lines else json.loads(data))

    actions = read('actions.json')
    result = read('results.json')
    events = read('restart-profile-trace/events.jsonl', lines=True)
    status = read('restart-profile-trace/status.json')
    start = next(row['seconds'] for row in actions if row.get('label') ==
                 'Fresh stock match reaches a living active player before native focus loss')
    selected = [row for row in actions if row['seconds'] >= start]
    states = [row for row in selected if isinstance(row.get('state'), dict)]
    captures = []
    for begin in [row for row in selected if row['event'] == 'capture_begin']:
        name = begin['capture']
        end = next(row for row in selected if row['event'] == 'capture_end' and row['capture'] == name)
        path = root / (name + '.png')
        data = path.read_bytes()
        with Image.open(path) as image:
            dimensions = list(image.size)
        bindings.append({'path': path.name, 'bytes': len(data),
                         'sha256': hashlib.sha256(data).hexdigest()})
        captures.append({'name': name, 'begin': begin, 'end': end,
                         'controller_span_seconds': end['seconds'] - begin['seconds'],
                         'dimensions': dimensions,
                         'last_prior_recorded_state': [row for row in states if row['seconds'] < begin['seconds']][-1],
                         'first_subsequent_recorded_state': next(row for row in states if row['seconds'] > end['seconds'])})
    death = next(row for row in events if row.get('event') == 'alive'
                 and row.get('local_actor', {}).get('alive') is False)
    released = next(row for row in states if row.get('label') == 'Released held focus-test controls')
    last_living = [row for row in states if row['seconds'] < released['seconds']
                   and row['state'].get('local_actor', {}).get('alive') is True][-1]
    wait = next(row for row in selected if row['event'] == 'wait_begin'
                and row.get('label') == 'Fresh W press moves actual player after focus recovery')
    key_down = next(row for row in selected if row['event'] == 'key_before'
                    and row.get('key') == 'w' and row.get('down') is True
                    and row['seconds'] > released['seconds'])
    key_up = next(row for row in selected if row['event'] == 'key_before'
                  and row.get('key') == 'w' and row.get('down') is False
                  and row['seconds'] > wait['seconds'])
    assert result['source']['source_commit'] == 'b2e0293a546961230afbd73e5cd2a1a307d69e94'
    assert result['passed'] is False and released['state']['local_actor']['alive'] is False
    return {'run': 39907358390, 'job': 120262263075, 'source': result['source'],
            'original_passed': result['passed'], 'original_error': result['error'],
            'original_elapsed_seconds': result['elapsed_seconds'],
            'original_cleanup_errors': result['cleanup_errors'],
            'original_file_bindings': bindings, 'focus_actions': selected,
            'captures': captures, 'last_living_guard': last_living,
            'native_first_dead_alive_event': death, 'released_ack': released,
            'fresh_key_down': key_down, 'fresh_response_wait_begin': wait,
            'fresh_key_release': key_up, 'last_original_status': status,
            'response_wait_to_key_release_seconds': key_up['seconds'] - wait['seconds'],
            'limits': [
                'Controller capture spans include trace/file work and are not isolated screenshot costs.',
                'Game wall_msec and controller seconds use different origins; no exact cross-clock death instant is inferred.',
                'Recorded states are sparse; the raw 11b PNG shows 005 HEALTH between recorded living and dead states.',
                'No observer-off or source-delta control exists; the failure cause cannot be attributed to bots or capture cost.',
                'Native focus loss/restoration and held-input neutrality do not qualify fresh input response on a living actor.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('original_offline_input', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.write_text(json.dumps(recompute(args.original_offline_input), indent=2) + '\n')
