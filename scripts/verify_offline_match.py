#!/usr/bin/env python3
"""Exercise exported offline objectives or a complete normal-rules match.

The native OS supplies every gameplay action. Explicit debug/offline observations
are read only. Plant/defuse use declared initial layouts; full-match uses stock
spawns, teams, random seeds and time_scale1. No game API or save is modified here.
The1800-second default is a bounded trial budget, not the maximum duration of
all possible twelve-round matches with late plants. Native hardware/input feel
and screenshot quality require their own independent review.
"""
import argparse
import ctypes as C
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import re
import shutil
import signal
import subprocess
import sys
import time
from urllib.parse import quote

from PIL import Image
from build_manifest import BUILDS, OUTPUTS, source, validate_record
from native_log import failed
from native_observation import read_observation_json
from native_approach import approach_floor
from linux_frame_sampler import LinuxFrameSampler
from verify_integration_export import NativeUI, WinUI, windows_job
import toolchain


# The plant fixture (offline_diagnostics.gd fixture_for) starts the human at (-15, 2). Relay Yard layout revision 2 stands
# a shield (arena.gd "SITE A ENTRY", x -20 to -15, z 3.25 to 5.75) between that start and site A, so the straight line to
# (-15, 8) ends against its east face. These waypoints (x, z) go round the east end and finish at the same point.
PLANT_ROUTE_SITE_A_REVISION_2 = [(-13.4, 2.6), (-13.4, 7.0), (-15, 8)]

RULES = {'buy_seconds': 15, 'round_seconds': 100, 'device_seconds': 35,
         'plant_seconds': 3, 'defuse_seconds': 5, 'win_score': 7}


def require_planted_guidance_context(item, actor_id, round_number):
    """A delayed role observation cannot accept a dead or replacement attacker."""
    current = item.get('local_actor', {})
    context = {name: item.get(name) for name in ('simulation_tick', 'phase', 'round_number', 'objective_state')}
    context.update(actor_id=current.get('id'), alive=current.get('alive'), health=current.get('health'))
    health = current.get('health')
    if (current.get('alive') is False
            or (isinstance(health, (int, float)) and not isinstance(health, bool) and health <= 0)):
        raise RuntimeError('Player died before post-plant role guidance capture: ' + repr(context))
    if (current.get('alive') is not True or isinstance(health, bool)
            or not isinstance(health, (int, float)) or not 0 < health <= 100
            or item.get('phase') != 'live' or item.get('round_number') != round_number
            or item.get('objective_state') != 'planted' or current.get('id') != actor_id
            or current.get('team') != 0):
        raise RuntimeError('Post-plant role guidance lost its actual attacker context: ' + repr(context))


def verify_hold_edges(observations, prior, required, message):
    """Measure exact consumed-input/notification edges, independently of progress."""
    completions = [item for item in observations if item.get('event') == 'notification'
                   and message in item.get('message', '') and item['simulation_tick'] > prior['simulation_tick']]
    if len(completions) != 1:
        raise RuntimeError('Exact authoritative objective completion notification is missing or duplicated')
    completed = completions[0]
    inputs = [item for item in observations if item.get('event') == 'local_interact_input'
              and prior['simulation_tick'] < item['simulation_tick'] <= completed['simulation_tick']]
    if len(inputs) != 1 or inputs[0].get('held') is not True:
        raise RuntimeError('Final objective hold lacks one uninterrupted authoritative consumed-E edge')
    started = inputs[0]
    seconds = completed['elapsed'] - started['elapsed']
    ticks = completed['simulation_tick'] - started['simulation_tick']
    # The input observer sees the first consumed tick, rather than the instant
    # just before its delta. Allow that single60-Hz tick, not a status-sample gap.
    if seconds + 1 / 60 + 1e-6 < required or ticks + 1 + 1e-6 < required * 60:
        raise RuntimeError('Objective completed before its full authoritative consumed-input hold duration')
    if completed['elapsed'] - prior['elapsed'] + 1 / 60 + 1e-6 < required:
        raise RuntimeError('Objective completed too early after the known-zero authority observation')
    return {'input_started': started, 'completion_notification': completed,
            'simulation_seconds': seconds, 'simulation_ticks': ticks,
            'one_tick_tolerance_seconds': 1 / 60}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--scenario', choices=('plant', 'defuse', 'full-match'), required=True)
    parser.add_argument('--target', choices=('linux', 'windows'), default='windows' if os.name == 'nt' else 'linux')
    parser.add_argument('--executable', type=Path, help='Extracted executable; hash must match the selected manifest')
    parser.add_argument('--seed', type=int, help='Declared plant/defuse initial-condition seed, default42; forbidden for full-match')
    parser.add_argument('--timeout', type=float, default=1800, help='Whole native flow wall budget plus bounded failure cleanup')
    parser.add_argument('--display', default=':106', help='Free isolated X11 display (Linux only)')
    parser.add_argument('--xvfb', default=os.environ.get('XVFB_BIN') or shutil.which('Xvfb'))
    parser.add_argument('--hosted-render-priority', choices=('inherited', 'below-normal'), default='inherited')
    parser.add_argument('--linux-frame-diagnostics', action='store_true',
                        help='Sample the owned Linux plant client CPU once per second; requires --timeout 180')
    parser.add_argument('--linux-gpu-profile', action='store_true',
                        help='Print initial Linux plant renderer query timings; requires --timeout 180 and sampler off')
    args = parser.parse_args()
    if platform.system() not in ('Linux', 'Windows') or args.target != ('windows' if os.name == 'nt' else 'linux'):
        parser.error('Execute the selected package on native Linux/Windows; macOS gameplay remains UNVERIFIED')
    if args.timeout <= 0 or args.seed is not None and not 0 <= args.seed <= 2147483647:
        parser.error('Timeout must be positive; scenario seed must be a nonnegative signed32-bit integer')
    if args.scenario == 'full-match' and args.seed is not None:
        parser.error('Full-match must retain stock random seeds; omit --seed')
    if args.hosted_render_priority != 'inherited' and args.target != 'windows':
        parser.error('Hosted render priority requires native Windows; other targets retain inherited priority')
    if args.linux_frame_diagnostics and (args.target != 'linux' or args.scenario != 'plant'
                                        or args.timeout != 180 or args.seed not in (None, 42)):
        parser.error('Linux frame diagnostics requires Linux plant, seed 42 and original --timeout 180')
    if args.linux_gpu_profile and (args.target != 'linux' or args.scenario != 'plant'
                                  or args.timeout != 180 or args.seed not in (None, 42)
                                  or args.linux_frame_diagnostics):
        parser.error('Linux GPU profile requires Linux plant, seed 42, original --timeout 180 and frame sampler off')
    socket = None
    if args.target == 'linux':
        if not args.xvfb or not re.fullmatch(r':[0-9]+', args.display):
            parser.error('Supply Xvfb and a free isolated numbered display')
        socket = Path('/tmp/.X11-unix/X' + args.display[1:])
        if socket.exists():
            parser.error('Display already in use: ' + args.display)
    out = args.output.resolve()
    if out.exists() and any(out.iterdir()):
        parser.error('Use a fresh output directory; prior failures and evidence are retained')
    out.mkdir(parents=True, exist_ok=True)
    trace_dir = out / 'trace'
    executable = (args.executable or BUILDS / OUTPUTS[args.target]).resolve()
    started, deadline = time.monotonic(), time.monotonic() + args.timeout
    logs, processes, commands, captures = [], [], [], []
    held = set()
    before = manifest = ui = job = client = None
    frame_sampler = None
    last_state, last_update = {}, started
    initial_exit = reopened_exit = None
    result = {'passed': False, 'scenario': args.scenario, 'target': args.target,
              'host': platform.platform(), 'controller_command': [sys.executable, *sys.argv],
              'timeout_seconds': args.timeout, 'partial_checks': {}, 'captures': captures}

    def interrupted(signum, _frame):
        raise SystemExit('Native validation interrupted by ' + signal.Signals(signum).name)

    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)

    def write_result():
        (out / 'results.json').write_text(json.dumps(result, indent=2) + '\n')

    def remaining():
        value = deadline - time.monotonic()
        if value <= 0:
            raise TimeoutError('Whole exported offline scenario deadline exceeded')
        return value

    def pause(seconds):
        if seconds >= remaining():
            raise TimeoutError('Whole exported offline scenario deadline exceeded')
        time.sleep(seconds)

    def record(event, **data):
        entry = {'event': event, 'seconds': time.monotonic() - started,
                 'wall_unix_msec': time.time_ns() // 1_000_000, 'held_keys': sorted(held), **data}
        if last_state:
            entry['observed'] = {name: last_state.get(name) for name in
                                 ('wall_msec', 'drawn_frames', 'phase', 'round_number', 'elapsed', 'simulation_tick', 'objective_state',
                                  'interaction_progress', 'local_contribution', 'local_actor')}
        if ui is not None:
            try:
                entry['native_state'] = ui.diagnostics()
            except Exception as error:
                entry['native_state_error'] = str(error)
        with (out / 'actions.jsonl').open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(entry) + '\n')

    def launch(name, command, env):
        remaining()
        log = (out / (name + '.log')).open('w', encoding='utf-8')
        logs.append(log)
        process = subprocess.Popen(command, env=env, cwd=out, stdout=log, stderr=subprocess.STDOUT,
                                   start_new_session=os.name != 'nt')
        processes.append((name, process))
        commands.append({'name': name, 'command': command, 'pid': process.pid,
                         'started_seconds': time.monotonic() - started})
        (out / 'commands.json').write_text(json.dumps(commands, indent=2) + '\n')
        return process

    def observe():
        nonlocal last_state, last_update
        if client is not None and client.poll() is not None:
            raise RuntimeError('Export exited before scenario completion')
        remaining()
        try:
            state = read_observation_json(trace_dir / 'status.json')
        except (OSError, ValueError):
            if last_state and time.monotonic() - last_update > 5:
                raise RuntimeError('Offline observation stalled or became unreadable')
            return last_state
        if state.get('schema') != 1 or state.get('scenario') != ('standard' if args.scenario == 'full-match' else args.scenario):
            raise RuntimeError('Read-only offline observation schema/scenario mismatch')
        if state.get('time_scale') != 1:
            raise RuntimeError('Scenario changed normal simulation speed')
        if not last_state or state['wall_msec'] != last_state['wall_msec']:
            if last_state and state['wall_msec'] < last_state['wall_msec']:
                raise RuntimeError('Observation process clock moved backward')
            last_update = time.monotonic()
        elif state.get('phase') != 'match_over' and time.monotonic() - last_update > 5:
            raise RuntimeError('Offline observation stopped advancing')
        last_state = state
        return state

    def wait(condition, seconds, label):
        until = min(deadline, time.monotonic() + seconds)
        while time.monotonic() < until:
            state = observe()
            if condition(state):
                record('observed', label=label)
                return state
            time.sleep(.1)
        raise TimeoutError(label)

    def wait_ui(condition, seconds, label, process):
        until = min(deadline, time.monotonic() + seconds)
        while time.monotonic() < until:
            if process.poll() is not None:
                raise RuntimeError(label + ': native process exited early')
            if condition():
                return
            time.sleep(.1)
        raise TimeoutError(label)

    def local(state=None):
        actor = (state or observe()).get('local_actor', {})
        if not actor.get('alive') or not 0 < actor.get('health', 0) <= 100:
            raise RuntimeError('Player is not alive for the required native action')
        return actor

    def native_menu_ready():
        if not ui.focus_game():
            return False
        if (args.hosted_render_priority == 'below-normal'
                and not any(item['pid'] == client.pid for item in result.get('hosted_render_priority', []))):
            result.setdefault('hosted_render_priority', []).append(ui.lower_owned_render_priority(client))
        return ui.menu_visible()

    def key(name, down):
        # A reached deadline must never prevent a held native key being released.
        if down:
            remaining()
        if down == (name in held):
            return
        ui.key(name, down)
        (held.add if down else held.discard)(name)
        record('key', key=name, down=down)

    def stop():
        for name in list(held):
            key(name, False)
        ui.button(False)
        record('buttons_released')

    def tap(name, duration=.25):
        key(name, True)
        pause(duration)
        key(name, False)
        pause(.3)

    def fire(duration=.4):
        ui.button(True)
        record('lmb', down=True)
        pause(duration)
        ui.button(False)
        record('lmb', down=False)
        pause(.3)

    def capture(name):
        remaining()
        freshness = None
        # Authority transitions can precede the next HUD draw. Observe two
        # subsequent rendered frames before naming a capture for that state.
        # Menus already use the native rendered-menu readiness check and may
        # have no trace (or retain the previous process's final observation).
        in_game = name not in ('01-main-menu', '09-reopened-menu') and last_state.get('ui', {}).get('screen') == 'game'
        if in_game:
            phase, round_number = last_state.get('phase'), last_state.get('round_number')
            before_frames = last_state.get('drawn_frames')
            if not isinstance(before_frames, int) or before_frames < 0:
                raise RuntimeError('Rendered capture requires a valid drawn-frame observation: ' + name)
            freshness = {'expected_phase': phase, 'expected_round': round_number,
                         'before_drawn_frames': before_frames}
            record('capture_render_wait_begin', capture=name, **freshness)
            until = min(deadline, time.monotonic() + 5)
            while True:
                state = observe()
                if state.get('phase') != phase or state.get('round_number') != round_number:
                    record('capture_render_phase_changed', capture=name, **freshness)
                    raise RuntimeError('Expected capture phase/round changed before rendering: ' + name)
                drawn = state.get('drawn_frames')
                if not isinstance(drawn, int) or drawn < before_frames:
                    raise RuntimeError('Rendered frame counter is missing or moved backward: ' + name)
                if drawn >= before_frames + 2:
                    freshness['ready_drawn_frames'] = drawn
                    break
                if time.monotonic() >= until:
                    raise TimeoutError('Two rendered frames did not advance within the capture budget: ' + name)
                time.sleep(.05)
        record('capture_begin', capture=name, render_freshness=freshness)
        ui.capture(out / (name + '.png'))
        with Image.open(out / (name + '.png')) as image:
            dimensions = list(image.size)
        remaining()
        receipt = {'name': name, 'dimensions': dimensions, 'seconds': time.monotonic() - started,
                   'render_freshness': freshness}
        captures.append(receipt)
        if freshness is not None:
            state = observe()
            freshness['after_capture_drawn_frames'] = state.get('drawn_frames')
            if state.get('phase') != freshness['expected_phase'] or state.get('round_number') != freshness['expected_round']:
                receipt['render_phase_changed'] = True
                record('capture_render_phase_changed', capture=name, render_freshness=freshness)
                raise RuntimeError('Expected capture phase/round changed during native capture: ' + name)
        record('capture_end', capture=name, dimensions=dimensions, render_freshness=freshness)
        print(name, flush=True)

    def events():
        path = trace_dir / 'events.jsonl'
        if path.stat().st_size > 64 * 1024 * 1024:
            raise RuntimeError('Offline event evidence exceeded its bounded read budget')
        return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]

    def aim(yaw, pitch, sensitivity):
        until = min(deadline, time.monotonic() + 4)
        while time.monotonic() < until:
            actor = local()
            horizontal = (yaw - actor['yaw'] + math.pi) % (2 * math.pi) - math.pi
            vertical = pitch - actor['pitch']
            if abs(horizontal) < .025 and abs(vertical) < .025:
                return
            dx = max(-650, min(650, round(-horizontal / sensitivity)))
            dy = max(-450, min(450, round(-vertical / sensitivity)))
            ui.relative_motion(dx, dy)
            record('aim_motion', dx=dx, dy=dy)
            pause(.25)
        raise TimeoutError('Native mouse aiming did not reach the observed orientation')

    def move_to(x, z, seconds=15):
        until = min(deadline, time.monotonic() + seconds)
        return approach_floor(x, z, observe=observe, key=key, pause=pause,
                              record=record, deadline=until)

    def invalid_interaction():
        before_count = observe()['local_contribution']
        key('e', True)
        pause(.6)
        state = observe()
        key('e', False)
        if state['interaction_progress'] != 0 or state['local_contribution'] != before_count:
            raise RuntimeError('Out-of-range interaction unexpectedly progressed')
        record('invalid_interaction_rejected')
        pause(.3)

    def interrupted_interaction(expected_state):
        prior = observe()
        key('e', True)
        wait(lambda state: 0.1 <= state.get('interaction_progress', 0) < .8, 3, 'Real E interaction progress')
        key('e', False)
        reset = wait(lambda state: state.get('interaction_progress') == 0 and not state.get('local_input', {}).get('interact'),
                     2, 'Released E clears interaction progress')
        if reset['objective_state'] != expected_state or reset['local_contribution'] != prior['local_contribution']:
            raise RuntimeError('Interrupted hold completed an objective')
        result['partial_checks']['interrupted_E_reset'] = True
        capture('04-interrupted-hold-reset')

    def move_via(points, seconds=15):
        for x, z in points:
            move_to(x, z, seconds)

    def smoke(sensitivity, yaw, pitch=-1.2):
        before_smokes = local()['smokes']
        if before_smokes < 1:
            raise RuntimeError('Stock smoke inventory is unavailable')
        aim(yaw, pitch, sensitivity)
        key('q', True)
        try:
            consumed = wait(lambda state: state.get('local_actor', {}).get('smokes') == before_smokes - 1,
                            3, 'Real Q consumes ordinary smoke inventory')
        finally:
            key('q', False)
        result['partial_checks']['native_smoke_deployed'] = True
        return consumed

    def objectives(initial, sensitivity):
        state = wait(lambda item: item.get('phase') == 'live', 45, 'Objective scenario live phase')
        origin = local(state)['position'][:]
        if args.scenario == 'plant':
            if state['objective_carrier'] != local(state)['id'] or local(state)['team'] != 0:
                raise RuntimeError('Plant fixture did not start the ordinary living attacker carrier')
            invalid_interaction()
            consumed = smoke(sensitivity, math.pi, pitch=-0.8)
            # Ordinary projectile fuse is1.6s. Establish cover before entering
            # the exposed site; waiting never changes the utility or bot rules.
            wait(lambda item: item.get('elapsed', 0) >= consumed['elapsed'] + 1.7,
                 5, 'Ordinary smoke fuse advances in authoritative simulation time')
            move_via(PLANT_ROUTE_SITE_A_REVISION_2)
            expected_state, goal, required, minimum_distance = 'carried', 'planted', 3, 4.2
        else:
            if local(state)['team'] != 1:
                raise RuntimeError('Defuse fixture did not start the human on defense')
            carrier = next(actor for actor in state['actors'] if actor['id'] == state['objective_carrier'])
            if carrier['team'] != 0 or carrier['id'] == local(state)['id']:
                raise RuntimeError('Defuse fixture carrier is not an independent attacker')
            result['bot_planter_id'] = carrier['id']
            smoke(sensitivity, -math.pi / 2)
            wait(lambda item: item.get('objective_state') == 'planted', 15, 'Ordinary bot completes a legitimate plant')
            result['partial_checks']['ordinary_bot_plant_observed'] = True
            invalid_interaction()
            capture('03-bot-planted-device')
            move_to(-17, 9)
            expected_state, goal, required, minimum_distance = 'planted', 'defused', 5, 2
        entered = observe()
        actor = local(entered)
        distance = math.hypot(actor['position'][0] - origin[0], actor['position'][2] - origin[2])
        if distance <= minimum_distance:
            raise RuntimeError('Objective approach did not establish sufficient real authoritative displacement')
        if args.scenario == 'plant' and math.hypot(actor['position'][0] + 15, actor['position'][2] - 10) >= 3.8:
            raise RuntimeError('Human did not reach the legitimate site radius')
        if args.scenario == 'defuse' and math.dist(actor['position'], entered['objective_position']) > 2.8:
            raise RuntimeError('Human did not reach the legitimate device interaction radius')
        result.update(approach_origin=origin, approach_end=actor['position'], approach_distance=distance)
        capture('03b-legitimate-objective-approach')
        interrupted_interaction(expected_state)
        prior = observe()
        credits, count, round_number = local(prior)['credits'], prior['local_contribution'], prior['round_number']
        if prior['phase'] != 'live' or prior['objective_state'] != expected_state or prior['interaction_progress'] != 0:
            raise RuntimeError('Final objective hold did not start from a reset eligible live state')
        command_wall_msec = time.time_ns() // 1_000_000
        command_monotonic = time.monotonic()
        record('objective_hold_command', elapsed=prior['elapsed'], simulation_tick=prior['simulation_tick'],
               command_wall_unix_msec=command_wall_msec, required_simulation_seconds=required)
        samples = []

        def hold_observation(item):
            if item.get('round_number') != round_number:
                raise RuntimeError('Round changed during the final native E hold')
            if item.get('objective_state') == goal and item.get('local_contribution') == count + 1:
                return True
            if item.get('phase') != 'live' or item.get('objective_state') != expected_state or item.get('local_contribution') != count:
                raise RuntimeError('Objective state changed before the final native hold completed')
            progress = item.get('interaction_progress', 0)
            if samples and (progress <= 0 or progress + 1e-6 < samples[-1]['progress']):
                raise RuntimeError('Final native E hold lost uninterrupted authoritative progress')
            if progress > 0:
                if not item.get('local_input', {}).get('interact'):
                    raise RuntimeError('Progress was observed without authoritative held interaction input')
                if not samples or item['simulation_tick'] != samples[-1]['simulation_tick']:
                    samples.append({'elapsed': item['elapsed'], 'simulation_tick': item['simulation_tick'], 'progress': progress})
            return False

        key('e', True)
        try:
            def started_hold(item):
                if hold_observation(item):
                    raise RuntimeError('Objective completed before a full-duration native hold was observed')
                return bool(samples)
            wait(started_hold, 3, 'Final native E hold starts')
            capture('05-objective-hold')
            # Linux llvmpipe trial linux-defuse-r1 advanced only4.216 of the
            # required5 simulation seconds during the former8-second watchdog.
            # Bound software-renderer wall overhead separately; acceptance still
            # requires the exact3/5 authority seconds from consumed-input edges.
            wall_budget = required * 3
            result['objective_hold_wall_budget_seconds'] = wall_budget
            completed = wait(hold_observation, wall_budget, 'Player-driven ' + args.scenario + ' completes')
        finally:
            key('e', False)
        completion_observed_monotonic = time.monotonic()
        # Per-physics consumed-input edges and transition notifications avoid
        # five-Hz status sampling and normalized-progress inference as a gate.
        message = 'Relay device armed' if args.scenario == 'plant' else 'Relay device defused'
        timing = verify_hold_edges(events(), prior, required, message)
        start_elapsed = samples[0]['elapsed'] - samples[0]['progress'] * required
        result['objective_hold'] = {'command_wall_unix_msec': command_wall_msec, 'command_elapsed': prior['elapsed'],
                                    'command_simulation_tick': prior['simulation_tick'], 'samples': samples,
                                    'diagnostic_start_inferred_from_normalized_progress': start_elapsed,
                                    'diagnostic_native_command_to_observed_completion_wall_seconds': completion_observed_monotonic - command_monotonic,
                                    **timing}
        actor = local(completed)
        if completed['phase'] == 'post':
            round_won = completed['attack_score'] > prior['attack_score'] if actor['team'] == 0 else completed['defend_score'] > prior['defend_score']
            expected_credits = min(9000, min(9000, credits + 300) + (2700 if round_won else 1900))
            funds_note = 'Objective300 plus ordinary round award in the same observed transition'
        else:
            expected_credits, funds_note = min(9000, credits + 300), 'Ordinary objective300 award'
        if actor['credits'] != expected_credits:
            raise RuntimeError('Objective contribution/funds transition does not match ordinary authority rules')
        result.update(objective_transition=goal, local_contribution_before=count,
                      local_contribution_after=completed['local_contribution'], credits_before=credits,
                      credits_after=actor['credits'], funds_explanation=funds_note)
        result['partial_checks']['player_' + args.scenario] = True
        capture('06-player-objective-completed')
        if args.scenario == 'plant':
            guidance_actor_id = actor['id']
            def planted_role_guidance(item):
                require_planted_guidance_context(item, guidance_actor_id, round_number)
                return item.get('ui', {}).get('status_text') == 'DEFEND THE DEVICE'
            wait(planted_role_guidance, 15, 'Actual attacker HUD restores post-plant role guidance')
            capture('06b-postplant-role-guidance')
            require_planted_guidance_context(observe(), guidance_actor_id, round_number)
            result['partial_checks']['postplant_attacker_role_guidance'] = True
        resolved = wait(lambda item: item.get('phase') in ('post', 'match_over'), 50, 'Natural objective round resolution')
        notices = [item.get('message', '') for item in events() if item.get('event') == 'notification']
        if not any('Relay device defused' in item or 'Relay device detonated' in item for item in notices):
            raise RuntimeError('Round ended by elimination without proving device resolution')
        result['objective_resolution'] = 'defused' if resolved['objective_state'] == 'defused' else 'detonated'
        capture('07-objective-round-resolved')
        wait(lambda item: item.get('round_number', 0) == round_number + 1 and item.get('phase') == 'buy',
             12, 'Natural next round after objective resolution')
        capture('08-natural-next-round')
        result['partial_checks']['objective_resolution_and_next_round'] = True

    def first_round_combat():
        state = wait(lambda item: item.get('phase') == 'live', 45, 'Standard first live round')
        actor = local(state)
        if actor['weapon'] != 'sidearm' or actor['ammo'] != 15 or actor['reserve'] != 60:
            raise RuntimeError('Full-match did not retain the stock pistol-round loadout')
        origin, look = actor['position'][:], [actor['yaw'], actor['pitch']]
        key('d', True)
        pause(.3)
        key('d', False)
        ui.relative_motion(35, -8)
        record('initial_native_aim', dx=35, dy=-8)
        moved = wait(lambda item: item.get('local_actor', {}).get('position') != origin and
                     (item['local_actor']['yaw'] != look[0] or item['local_actor']['pitch'] != look[1]),
                     3, 'Real authoritative movement and aim')
        result['initial_displacement'] = math.dist(origin, local(moved)['position'])
        if result['initial_displacement'] < .3:
            raise RuntimeError('Native movement did not establish meaningful authoritative displacement')
        capture('03-real-move-aim')
        for _ in range(2):
            fire()
        fired = wait(lambda item: 0 < item.get('local_actor', {}).get('ammo', 15) < 15,
                     3, 'Actual stock sidearm ammunition depletion')
        actor = local(fired)
        if actor['reserve'] != 60:
            raise RuntimeError('Firing unexpectedly changed reserve ammunition')
        fired_ammo = [actor['ammo'], actor['reserve']]
        capture('04-real-fire')
        key('r', True)
        wait(lambda item: item.get('local_actor', {}).get('reload', 0) > 0, 3, 'Native R starts authoritative reload')
        key('r', False)
        capture('05-real-reload-start')
        reloaded = wait(lambda item: item.get('local_actor', {}).get('reload') == 0 and item['local_actor']['ammo'] == 15,
                        5, 'Authoritative reload completes')
        actor = local(reloaded)
        if actor['reserve'] >= fired_ammo[1] or actor['ammo'] + actor['reserve'] != sum(fired_ammo):
            raise RuntimeError('Full-match reload failed ammunition conservation')
        result.update(fired_ammunition=fired_ammo, reloaded_ammunition=[actor['ammo'], actor['reserve']])
        result['partial_checks']['standard_live_move_aim_fire_reload'] = True
        capture('06-real-reload-completed')

    def full_match(initial):
        first_round_combat()
        seen, entered_rounds = set(), set()
        while True:
            state = observe()
            marker = (state.get('round_number'), state.get('phase'))
            if marker not in seen:
                seen.add(marker)
                stop()
                capture('round-%02d-%s' % marker)
            if state.get('phase') == 'match_over':
                break
            actor = state.get('local_actor', {})
            if state.get('phase') == 'live' and actor.get('alive') and marker[0] not in entered_rounds:
                # Ordinary input enters combat; deaths and team bots may settle
                # rounds naturally. No winner, timer, actor or save is changed.
                entered_rounds.add(marker[0])
                key('w', True)
                pause(2)
                key('w', False)
                record('normal_round_combat_entry')
            pause(.2)
        stop()
        pause(.5)
        capture('07-operation-complete')
        summary, training = state.get('summary', {}), state.get('training_after', {})
        if not summary or state.get('completion_calls') != 1 or state.get('events_dropped') != 0:
            raise RuntimeError('Complete single-emission summary evidence is missing')
        rounds, attack, defend = summary.get('rounds', 0), summary.get('attack_score', -1), summary.get('defend_score', -1)
        if not summary.get('offline') or not 7 <= rounds <= 12 or attack + defend != rounds or not (max(attack, defend) == 7 or rounds == 12):
            raise RuntimeError('Final score/rounds do not satisfy normal offline match rules')
        roster = summary.get('scoreboard', [])
        humans = [entry for entry in roster if entry.get('local')]
        if len(roster) != 10 or len({entry['id'] for entry in roster}) != 10 or len(humans) != 1 or any(sum(entry['team'] == team for entry in roster) != 5 for team in (0, 1)):
            raise RuntimeError('Final scoreboard is not a complete5v5 human/bot roster')
        human = humans[0]
        if any(summary[name] != human[name] for name in ('kills', 'assists', 'deaths', 'objectives')):
            raise RuntimeError('Summary does not match the final human scoreboard row')
        if summary['won'] != ((attack > defend) if human['team'] == 0 else (defend > attack)) or summary['draw'] != (attack == defend):
            raise RuntimeError('Final squad outcome is inconsistent after halftime')
        all_events = events()
        observed_rounds = {item['round_number'] for item in all_events if item.get('event') in ('initial', 'round_number')}
        if observed_rounds != set(range(1, rounds + 1)):
            raise RuntimeError('Evidence does not cover every natural round transition')
        seventh = next((item for item in all_events if item.get('event') == 'round_number' and item['round_number'] == 7), None)
        if seventh is None or seventh['local_actor']['team'] == initial['local_actor']['team']:
            raise RuntimeError('Full match did not record the natural halftime team switch')
        if sum(item.get('event') == 'completed' for item in all_events) != 1 or any(item.get('event') == 'duplicate_completion' for item in all_events):
            raise RuntimeError('Offline completion was emitted more than once')
        old = initial['initial_profile']
        xp = old['xp'] + 120 + 15 * summary['kills'] + 50 * summary['objectives']
        level = 1 + int(math.sqrt(xp / 150))
        earned = 100 + (75 if summary['won'] else 0) + (150 if old['last_daily'] != training.get('last_daily') else 0) + (level - old['level']) * 250
        if training.get('scope') != 'offline_training' or training.get('matches') != 1 or len(training.get('history', [])) != 1:
            raise RuntimeError('New offline training match was not recorded exactly once')
        for name, expected in {'xp': xp, 'level': level, 'credits': old['credits'] + earned,
                               'wins': old['wins'] + int(summary['won']), 'kills': old['kills'] + summary['kills'],
                               'deaths': old['deaths'] + summary['deaths']}.items():
            if training.get(name) != expected:
                raise RuntimeError('Offline training formula mismatch: ' + name)
        if any(training['history'][0].get(name) != value for name, value in summary.items()) or training['history'][0].get('credits_earned') != earned:
            raise RuntimeError('Stored history does not match the actual earned match summary')
        result.update(summary=summary, training_before=old, training_after=training,
                      expected_xp=xp, expected_credits_earned=earned, natural_rounds=sorted(observed_rounds))
        result['partial_checks']['normal_full_match_and_single_training_record'] = True
        tap('Escape')
        wait(lambda s: s.get('phase') == 'match_over' and s.get('ui', {}).get('paused') is False,
             8, 'Real Escape dismisses final summary before Tab roster')
        key('Tab', True)
        try:
            roster_state = wait(lambda s: s.get('phase') == 'match_over'
                               and s.get('ui', {}).get('paused') is False
                               and s.get('ui', {}).get('scoreboard_visible') is True,
                               8, 'Actual held Tab displays final roster')
            capture('08-final-scoreboard')
            if observe().get('ui', {}).get('scoreboard_visible') is not True:
                raise RuntimeError('Final roster disappeared during native capture')
            result['final_roster_visibility'] = roster_state
        finally:
            key('Tab', False)
        wait(lambda s: s.get('ui', {}).get('scoreboard_visible') is False,
             5, 'Actual Tab release dismisses final roster')
        pause(3)
        if observe().get('completion_calls') != 1:
            raise RuntimeError('Completed-match dwell repeated training completion')

    write_result()
    try:
        before = source()
        manifest = validate_record(args.target, before)
        with executable.open('rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        if digest != manifest['artifact']['sha256']:
            raise RuntimeError('Extracted executable bytes do not match the selected exact-source artifact')
        result.update(source=before, artifact_source=manifest, executable=str(executable), executable_sha256=digest,
                      engine=toolchain.verify_engine())
        env = dict(os.environ)
        if args.target == 'linux':
            display = launch('xvfb', [args.xvfb, args.display, '-screen', '0', '1280x720x24', '-nolisten', 'tcp'], env)
            wait_ui(socket.exists, 5, 'Xvfb readiness', display)
            env.update(DISPLAY=args.display, LIBGL_ALWAYS_SOFTWARE='1', LP_NUM_THREADS='2',
                       DBUS_SESSION_BUS_ADDRESS='unix:path=' + quote(str(out / 'unavailable-bus'), safe='/._-'))
            for variable, part in [('XDG_DATA_HOME', 'data'), ('XDG_CONFIG_HOME', 'config'), ('XDG_CACHE_HOME', 'cache')]:
                env[variable] = str(out / 'state' / part)
                Path(env[variable]).mkdir(parents=True, exist_ok=True)
            profile_path = Path(env['XDG_DATA_HOME']) / 'godot/app_userdata/SIGHTBREAK/offline_training.json'
            ui, flags = NativeUI(args.display), ['--accessibility', 'disabled', '--accessibility-driver', 'dummy']
        else:
            job = windows_job()
            for variable, part in [('APPDATA', 'roaming'), ('LOCALAPPDATA', 'local')]:
                env[variable] = str(out / 'state' / part)
                Path(env[variable]).mkdir(parents=True, exist_ok=True)
            profile_path = Path(env['APPDATA']) / 'Godot/app_userdata/SIGHTBREAK/offline_training.json'
            ui = WinUI()
            flags = ['--position', '0,0', '--resolution', f'{ui.width}x{ui.height}']
        command = [str(executable), '--audio-driver', 'Dummy', *flags, '--', '--offline-validation', '--offline-trace-dir=' + str(trace_dir)]
        if args.scenario != 'full-match':
            command += ['--offline-scenario=' + args.scenario, '--offline-seed=' + str(42 if args.seed is None else args.seed)]
        if args.linux_gpu_profile:
            command.insert(1, '--gpu-profile')
        client = launch('client', command, env)
        if args.linux_frame_diagnostics:
            frame_sampler = LinuxFrameSampler(client, out / 'linux-frame-samples.jsonl', trace_dir / 'status.json', min(180.0, remaining()))
        if args.target == 'windows': ui.pid = client.pid
        wait_ui(native_menu_ready, 60, 'Real exported main menu', client)
        capture('01-main-menu')
        # A rendered menu can remain visible while the native match is loading.
        # Replaying its absolute pointer click after capture would become aim.
        record('deploy_click_before', x=248, y=319)
        ui.click(248, 319)
        record('deploy_click_after', x=248, y=319)
        wait(lambda state: bool(state.get('local_actor')) and state.get('ui', {}).get('screen') == 'game',
             30, 'Read-only actual offline state')
        with (trace_dir / 'events.jsonl').open(encoding='utf-8') as stream:
            initial = json.loads(stream.readline())
        expected_initial = 'stock_spawns_teams_random_seeds' if args.scenario == 'full-match' else 'declared_initial_spawns_side_and_seeds_only'
        if initial.get('event') != 'initial' or initial.get('initial_conditions') != expected_initial or initial.get('rules') != RULES:
            raise RuntimeError('Initial conditions or normal game rules do not match the declared scenario')
        if initial.get('protocol') != 6 or initial.get('prediction_enabled') is not False:
            raise RuntimeError('Protocol/default-off prediction contract changed')
        old = initial['initial_profile']
        if old.get('scope') != 'offline_training' or old.get('matches') != 0 or old.get('history') or old.get('xp') != 0 or old.get('credits') != 0:
            raise RuntimeError('Scenario did not start with genuine empty isolated offline training')
        if len(initial['actors']) != 10 or not all(actor['alive'] and actor['health'] == 100 for actor in initial['actors']):
            raise RuntimeError('Initial conditions did not preserve ten living stock-health actors')
        result.update(initial=initial, profile_observation_path=str(profile_path))
        capture('02-offline-initial-conditions')
        if args.scenario == 'full-match': full_match(initial)
        else: objectives(initial, float(old['settings']['sensitivity']))
        stop()
        saved = json.loads(profile_path.read_text(encoding='utf-8')) if profile_path.exists() else old
        if args.scenario == 'full-match' and saved != result['training_after']:
            raise RuntimeError('Actual saved progression does not match the completed authority/profile observation')
        pause(2)
        if profile_path.exists() and json.loads(profile_path.read_text(encoding='utf-8')) != saved:
            raise RuntimeError('Progression changed again during completed/round dwell')
        ui.request_close()
        client.wait(timeout=min(20, remaining()))
        initial_exit = client.returncode
        if initial_exit != 0 or failed((out / 'client.log').read_text(encoding='utf-8', errors='replace')):
            raise RuntimeError('Scenario export did not exit normally with a clean engine log')
        reopened_command = [str(executable), '--audio-driver', 'Dummy', *flags]
        if args.scenario == 'full-match':
            trace_dir = out / 'trace-reopened'
            last_state, last_update = {}, time.monotonic()
            reopened_command += ['--', '--offline-validation', '--offline-trace-dir=' + str(trace_dir)]
        client = launch('reopened', reopened_command, env)
        if args.target == 'windows': ui.pid = client.pid
        wait_ui(native_menu_ready, 60, 'Normal reopened native main menu', client)
        capture('09-reopened-menu')
        reopened_profile = json.loads(profile_path.read_text(encoding='utf-8')) if profile_path.exists() else old
        if reopened_profile != saved:
            raise RuntimeError('Local progression/settings changed across normal restart')
        if args.scenario == 'full-match':
            record('reopened_deploy_click_before', x=248, y=319)
            ui.click(248, 319)
            record('reopened_deploy_click_after', x=248, y=319)
            wait(lambda item: bool(item.get('local_actor')) and item.get('ui', {}).get('screen') == 'game',
                 30, 'Reopened stock match observes the loaded profile')
            with (trace_dir / 'events.jsonl').open(encoding='utf-8') as stream:
                reopened_initial = json.loads(stream.readline())
            if reopened_initial.get('event') != 'initial' or reopened_initial.get('initial_conditions') != 'stock_spawns_teams_random_seeds' or reopened_initial.get('initial_profile') != saved:
                raise RuntimeError('Restart did not load the earned training/settings into the actual runtime profile')
            if observe().get('completion_calls') != 0 or observe().get('phase') != 'buy':
                raise RuntimeError('Restart profile verification unexpectedly completed or advanced beyond the new buy phase')
            result['reopened_initial_profile'] = reopened_initial['initial_profile']
            result['partial_checks']['earned_profile_loaded_after_restart'] = True
            capture('10-reopened-earned-profile-stock-match')
            if json.loads(profile_path.read_text(encoding='utf-8')) != saved:
                raise RuntimeError('Starting the next uncompleted stock match changed earned training/settings')
        ui.request_close()
        client.wait(timeout=min(20, remaining()))
        reopened_exit = client.returncode
        if reopened_exit != 0 or failed((out / 'reopened.log').read_text(encoding='utf-8', errors='replace')):
            raise RuntimeError('Reopened export did not exit normally with a clean engine log')
        validate_record(args.target, before)
        if source() != before: raise RuntimeError('Source changed during exported offline scenario')
        if os.name == 'nt':
            accounting = C.create_string_buffer(48)
            if not job[0].QueryInformationJobObject(job[1], 1, accounting, len(accounting), None): raise C.WinError(C.get_last_error())
            if C.c_uint32.from_buffer(accounting, 40).value != 1: raise RuntimeError('Windows job retains a native descendant')
        else:
            for name, process in processes:
                if name == 'xvfb': continue
                try: os.killpg(process.pid, 0)
                except ProcessLookupError: continue
                raise RuntimeError(name + ': native descendant remains alive after normal root exit')
        remaining()
        result.update(passed=True, progression_settings_restart_equal=True,
                      exit_method='WM_DELETE_WINDOW' if args.target == 'linux' else 'WM_CLOSE',
                      capture_method='raw X11 desktop' if args.target == 'linux' else 'raw Windows client-area capture',
                      scope='Actual exported native OS input and explicit read-only debug/offline observation; no physical-device/input-feel acceptance')
    except (Exception, SystemExit) as error:
        result.update(passed=False, error=str(error), source=before, artifact_source=manifest)
        record('failure', error=str(error))
    finally:
        cleanup_errors = []
        if ui:
            for name in list(held):
                try: ui.key(name, False)
                except Exception as error: cleanup_errors.append('release ' + name + ': ' + str(error))
            try: ui.button(False); ui.close()
            except Exception as error: cleanup_errors.append('native input teardown: ' + str(error))
        for name, process in reversed(processes):
            try:
                if os.name != 'nt': os.killpg(process.pid, signal.SIGTERM)
                elif process.poll() is None: process.terminate()
            except ProcessLookupError: pass
            except Exception as error: cleanup_errors.append(name + ' termination: ' + str(error))
        for name, process in reversed(processes):
            try: process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                try:
                    if os.name != 'nt': os.killpg(process.pid, signal.SIGKILL)
                    else: process.kill()
                    process.wait(timeout=5)
                except Exception as error: cleanup_errors.append(name + ' forced cleanup: ' + str(error))
            if os.name != 'nt':
                try: os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError: pass
                except Exception as error: cleanup_errors.append(name + ' descendant cleanup: ' + str(error))
        for entry, (_, process) in zip(commands, processes): entry['exit_code'] = process.returncode
        if frame_sampler is not None:
            result['linux_frame_diagnostics'] = frame_sampler.stop()
            if result['linux_frame_diagnostics']['thread_alive']:
                cleanup_errors.append('Owned Linux frame sampler did not stop')
        for log in logs: log.close()
        result.update(initial_exit=initial_exit, reopened_exit=reopened_exit, commands=commands,
                      cleanup_errors=cleanup_errors, elapsed_seconds=time.monotonic() - started,
                      controller_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
        if cleanup_errors: result.update(passed=False, error=result.get('error', 'Native process cleanup failed'))
        (out / 'commands.json').write_text(json.dumps(commands, indent=2) + '\n')
        write_result()
    if not result['passed']:
        print(json.dumps(result, indent=2))
        for name in ('client', 'reopened'):
            path = out / (name + '.log')
            if path.is_file(): print(name + ' log tail:\n' + path.read_text(encoding='utf-8', errors='replace')[-12000:])
        raise RuntimeError(result.get('error', 'Exported offline scenario failed'))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
