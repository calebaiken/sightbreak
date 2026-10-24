#!/usr/bin/env python3
"""Frozen Git/source arithmetic only. Does not import or execute GDScript."""
import hashlib
import itertools
import json
import math
from pathlib import Path
import re
import subprocess

FROZEN = 'b87afb717bf09a78c6d36b164d48906902734bdb'
BASE = 'b2e0293a546961230afbd73e5cd2a1a307d69e94'
R1 = '114150a06c4ae00f38c84e796e5b05054e25ac37'
REPORT = 'docs/reports/gauntlet/m5-exhausted-primary-benchmark/'


def git(*args):
    return subprocess.check_output(['git', *args])


def source(path):
    return git('show', FROZEN + ':' + path).decode()


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def hit_segment(a, b, center, size):
    low, high = 0., 1.
    for axis in range(3):
        lo, hi = center[axis] - size[axis] / 2, center[axis] + size[axis] / 2
        delta = b[axis] - a[axis]
        if abs(delta) < 1e-12:
            if not lo <= a[axis] <= hi:
                return False
        else:
            first, second = sorted(((lo - a[axis]) / delta, (hi - a[axis]) / delta))
            low, high = max(low, first), min(high, second)
            if low > high:
                return False
    return True


def main():
    manifest = json.loads(source(REPORT + 'SOURCE_FREEZE_R2.json'))
    hashes = {}
    for path, expected in manifest['sha256'].items():
        actual = hashlib.sha256(git('show', FROZEN + ':' + path)).hexdigest()
        require(actual == expected, 'manifest hash: ' + path)
        require(hashlib.sha256(Path(path).read_bytes()).hexdigest() == actual, 'checkout differs: ' + path)
        hashes[path] = actual
    product_paths = ['game/scripts', 'scripts', 'backend', 'docs/engineering', 'docs/roadmap']
    unchanged = git('diff', '--name-only', BASE, FROZEN, '--', *product_paths).decode()
    require(not unchanged, 'product or canonical source changed')
    changed = git('diff', '--name-only', BASE, FROZEN).decode().splitlines()
    require(len(changed) == 9 and all(p.startswith(REPORT) or p == 'game/tests/bot_exhausted_primary_probe.gd' for p in changed), 'unexpected diff scope')
    require(not git('ls-tree', FROZEN, 'game/tests/bot_exhausted_primary_probe.gd.uid'), 'unexpected generated UID')
    subprocess.run(['git', 'merge-base', '--is-ancestor', R1, FROZEN], check=True)

    probe = source('game/tests/bot_exhausted_primary_probe.gd')
    match = source('game/scripts/gameplay/match.gd')
    spawn = match.split('func _spawn_actor(', 1)[1].split('\nfunc ', 1)[0]
    stock_callbacks = re.findall(r'actor\.(\w+)\.connect\((\w+)\)', spawn)
    probe_callbacks = re.findall(r'bot\.(\w+)\.connect\(m\.(\w+)\)', probe)
    require(stock_callbacks == probe_callbacks and len(stock_callbacks) == 5, 'stock callback wiring')
    require('bot.tick_authority_actions(DT)' in probe and 'm._bot_input(bot, DT)' in probe, 'real decision/action calls')
    require(not re.search(r'\.(apply_damage|resolve_shot_hit|_eliminated|_fire)\(', probe), 'injected authority outcome')
    require('await physics_frame\n\tawait physics_frame' in probe and 'm.set_physics_process(false)' in probe, 'settlement fence')

    profiles, primaries = ('easy', 'normal', 'hard'), ('smg', 'rifle', 'marksman')
    targets = ('near', 'fallback_boundary', 'far', 'outside_sidearm', 'outside_vision', 'no_target')
    subset = ('near', 'far', 'no_target')
    cells = []
    for difficulty, primary in itertools.product(profiles, primaries):
        for target in targets:
            cells += [('core', difficulty, primary, active, sidearm, target, 'none')
                      for active, sidearm in itertools.product(('exhausted', 'reloadable'), ('loaded', 'dry', 'unknown'))]
            cells.append(('loaded_primary', difficulty, primary, 'loaded', 'loaded', target, 'none'))
        for target in subset:
            cells += [('reserve_only_sidearm', difficulty, primary, 'exhausted', 'reserve_only', target, 'none'),
                      ('unowned_sidearm', difficulty, primary, 'exhausted', 'unowned', target, 'none')]
            cells += [('stale_active_cache', difficulty, primary, active, 'loaded', target, 'none') for active in ('exhausted', 'reloadable', 'loaded')]
            cells += [('objective_guard', difficulty, primary, 'exhausted', 'loaded', target, objective) for objective in ('carrier', 'defuser')]
    counts = {group: sum(row[0] == group for row in cells) for group in sorted({row[0] for row in cells})}
    require(len(cells) == len(set(cells)) == 567, 'matrix enumeration')
    sequences = 3 * 3 * 8
    control_steps = {'kill_rifle': 8, **{'reload_' + w: math.ceil(t / .12) + 3 for w, t in [('smg', 1.85), ('rifle', 2.25), ('marksman', 2.8)]}, 'reload_sidearm': math.ceil(.3 / .12) + math.ceil(1.45 / .12) + 4}
    require(sequences == 72 and sum(control_steps.values()) == 96, 'step budgets')

    # All solid stock boxes from arena._build. Later presentation helpers pass
    # solid=false; _pipe and _beam_between add no collision. Arithmetic is not
    # evidence of Godot's settled physics registration.
    solids = [((0, -.3, 0), (48, .6, 48)), ((-24, 3, 0), (1, 6, 49)),
              ((24, 3, 0), (1, 6, 49)), ((0, 3, 24), (48, 6, 1)), ((0, 3, -24), (48, 6, 1))]
    solids += [((x, 1.55, z), (3, 3.1, length)) for x, z, length in [(-7, -11, 9), (7, -11, 9), (-7, 4, 8), (7, 4, 8), (-20, 0, 5), (20, 0, 5)]]
    solids += [((x, .65, z), (2.5, 1.3, 2.5)) for x, z in [(-14, -5), (14, -5), (-18, 13), (18, 13), (0, 8), (-3, -1), (3, -1)]]
    solids += [((x, .45, 12.4), (1, .9, 1)) for x in (-15, 15)]
    solids += [((x, 4, z), (.18, 8, .18)) for x, z in itertools.product((-22, 22), (-18, 16))]
    solids += [((x, 3.4, 16), (.5, 6.8, .5)) for x in (-21, 21)]
    poses = []
    for distance in (2., 6., 20., 24., 45.5, 60.):
        unit = (1., 0.) if distance <= 45.5 else (math.sqrt(.5), math.sqrt(.5))
        shooter = (-unit[0] * distance / 2, 0., -20. if distance <= 45.5 else -unit[1] * distance / 2)
        target = (shooter[0] + unit[0] * distance, 0., shooter[2] + unit[1] * distance)
        pitch = math.atan2(-.35, distance)
        ray_from = (shooter[0], 1.62, shooter[2])
        ray_to = (ray_from[0] + unit[0] * math.cos(pitch) * (distance + .5), ray_from[1] + math.sin(pitch) * (distance + .5), ray_from[2] + unit[1] * math.cos(pitch) * (distance + .5))
        blocked = [i for i, (center, size) in enumerate(solids) if hit_segment(ray_from, ray_to, center, size)]
        inside = all(abs(point[axis]) + .31 < 23.5 for point in (shooter, target) for axis in (0, 2))
        require(inside, 'capsule footprint bounds')
        if distance <= 45.5:
            require(not blocked, 'ordinary/control source center ray obstruction')
        poses.append({'distance': distance, 'shooter': shooter, 'target': target, 'capsule_radius': .31, 'in_bounds': inside, 'solid_indices_crossed': blocked, 'ray_from': ray_from, 'ray_to': ray_to})
    objective_poses = [{'shooter': [-15, 0, 10], 'target': [-15 + d, 0, 10]} for d in (6, 24)]
    require(all(abs(p[axis]) + .31 < 23.5 for row in objective_poses for p in row.values() for axis in (0, 2)), 'objective footprint bounds')
    print(json.dumps({'scope': 'pure frozen Git/source arithmetic; no engine/import/UID/native/services', 'frozen': FROZEN, 'base': BASE,
                      'sha256': hashes, 'changed_files': changed, 'product_and_canonical_diff': unchanged, 'stock_callback_connections': stock_callbacks,
                      'matrix_counts': counts, 'matrix_unique': len(set(cells)), 'sequences': sequences, 'sequence_steps': sequences * 8,
                      'controls': control_steps, 'total_rows': len(cells) + sequences * 8 + sum(control_steps.values()),
                      'stock_solid_box_count': len(solids), 'source_geometry': poses, 'objective_poses': objective_poses,
                      'geometry_limit': 'Source AABB arithmetic, not observed physics or fired-shot success'}, indent=2))


if __name__ == '__main__':
    main()
