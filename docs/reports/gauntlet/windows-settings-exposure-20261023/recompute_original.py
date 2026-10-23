"""Read original failed journey and inspect one static occluder; no engine/OCR."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil


def intersects(start, end, lower, upper):
    lo, hi = 0., 1.
    for axis in range(3):
        delta = end[axis] - start[axis]
        if abs(delta) < 1e-12:
            if not lower[axis] <= start[axis] <= upper[axis]:
                return False
            continue
        a, b = sorted(((lower[axis] - start[axis]) / delta, (upper[axis] - start[axis]) / delta))
        lo, hi = max(lo, a), min(hi, b)
        if lo > hi:
            return False
    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('original_offline_input', type=Path)
    args = parser.parse_args()
    out = Path(__file__).parent
    bindings = []
    def read(name, lines=False):
        data = (args.original_offline_input / name).read_bytes()
        bindings.append({'path': name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
        return [json.loads(line) for line in data.decode().splitlines() if line] if lines else json.loads(data)
    result, actions = read('results.json'), read('actions.json')
    events = read('initial-offline-trace/events.jsonl', True)
    hud = result['hud_analysis_pauses'][-1]
    before = hud['before']
    selected = [row for row in actions if row['seconds'] >= 100]
    dead = next(row for row in events if row.get('event') == 'alive' and row.get('round_number') == 2
                and row.get('local_actor', {}).get('alive') is False)
    notice = next(row for row in events if row.get('event') == 'notification'
                  and row.get('message') == 'Kestrel  ›  Operator' and row['simulation_tick'] > before['simulation_tick'])
    static = []
    for actor in before['actors']:
        if actor['team'] == 1 and actor['alive'] is True:
            start = [actor['position'][0], actor['position'][1] + 1.62, actor['position'][2]]
            targets = {'original_spawn': [-4.4, 1.62, -21], 'fixed_cover': [-7.8, 1.62, -21]}
            static.append({'actor': actor['id'], 'original_enemy_position': actor['position'],
                           'head_height_segment_intersects_west_container': {
                               name: intersects(start, target, [-8.5, 0, -15.5], [-5.5, 3.1, -6.5])
                               for name, target in targets.items()}})
    for name in ('07d-explicit-resume.png', '06g-switched-primary.png'):
        path = args.original_offline_input / name
        data = path.read_bytes()
        bindings.append({'path': name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
        shutil.copyfile(path, out / ('original-' + name))
    sources = {name: hashlib.sha256(Path(name).read_bytes()).hexdigest() for name in (
        'game/scripts/gameplay/arena.gd', 'game/scripts/gameplay/actor.gd',
        'game/scripts/network/movement_step.gd', 'scripts/verify_offline_export.py', 'scripts/native_approach.py')}
    receipt = {'source': result['source'], 'run': 39916539053, 'job': 120291226421,
               'original_passed': result['passed'], 'original_error': result['error'],
               'original_elapsed_seconds': result['elapsed_seconds'], 'bindings': bindings,
               'original_actions': selected, 'raw_post_capture_before_analysis': before,
               'raw_later_death_notice': notice, 'raw_dead_state': dead,
               'inspected_source_sha256': sources, 'static_container_segments': static,
               'limits': ['Different clock origins and sparse states cannot place the exact death instant inside a capture.',
                          'Capture action spans include controller trace/metadata work, not isolated screenshot cost.',
                          'One static AABB intersection is not native LOS, dynamic obstruction, shot attribution or a survival guarantee.',
                          'The route is a declared test-scenario change and no game/product fix.']}
    assert result['source']['source_commit'] == 'a089473481ced0f2e7b2a7468bbc5d079f92f0ff'
    assert before['local_actor']['alive'] is True and before['simulation_tick'] == 3060
    assert dead['simulation_tick'] == 3071 and before['local_actor']['health'] == 100
    assert all(not row['head_height_segment_intersects_west_container']['original_spawn']
               and row['head_height_segment_intersects_west_container']['fixed_cover'] for row in static)
    (out / 'original-comparison.json').write_text(json.dumps(receipt, indent=2) + '\n')
