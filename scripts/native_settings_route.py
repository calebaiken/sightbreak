"""One fixed ordinary-control route for the living/settings test scenario."""
from copy import deepcopy
import math
import time

from native_approach import approach_floor


SETTINGS_COVER = (-7.8, -21.0)
SETTINGS_SPAWN = (-4.4, -21.0)


def relocate_settings_actor(start, *, actor_id, round_number, observe, key, pause,
                            record, deadline, receipt, clock=time.monotonic):
    """Share the caller's existing second-LIVE cap; never choose another life.

    Only ordinary WASD callbacks reach the native approach helper. The fixed
    destination does not depend on enemy positions, profile, health or seed.
    """
    receipt.update(status='IN_PROGRESS', scope='fixed ordinary-input settings test route; no product fix',
                   requested=list(SETTINGS_COVER), start=deepcopy(start), observations=[],
                   original_second_live_absolute_deadline=deadline)
    last = None

    def reject(reason, raw):
        receipt.update(status='SETTINGS_ROUTE_PRECONDITION_LOST', precondition_loss={
            'reason': reason, 'previous_valid_state': deepcopy(last), 'rejected_state': deepcopy(raw)})
        raise RuntimeError('Living settings route lost precondition: ' + reason)

    def budget():
        value = deadline - clock()
        if value <= 0:
            raise TimeoutError('Original second active round budget expired during fixed settings route')
        return value

    def finite(value):
        return type(value) is int or (type(value) is float and math.isfinite(value))

    def checked(state):
        nonlocal last
        if not isinstance(state, dict):
            reject('observation_not_object', state)
        actor, ui, inputs = (state.get(name) for name in ('local_actor', 'ui', 'local_input'))
        if not all(isinstance(value, dict) for value in (actor, ui, inputs)):
            reject('observation_nested_objects', state)
        if (type(state.get('schema')) is not int or state['schema'] != 1
                or state.get('scope') != 'debug_offline_read_only_observation'
                or state.get('scenario') != 'standard' or state.get('phase') != 'live'
                or type(state.get('round_number')) is not int or state['round_number'] != round_number
                or type(actor.get('id')) is not int or actor['id'] != actor_id
                or not finite(state.get('time_scale')) or state['time_scale'] != 1
                or ui.get('screen') != 'game' or ui.get('focused') is not True
                or ui.get('paused') is not False or ui.get('scoreboard_visible') is not False
                or actor.get('alive') is not True or not finite(actor.get('health')) or not 0 < actor['health'] <= 100):
            reject('living_actor_round_phase_focus_or_health', state)
        for field, size in (('position', 3), ('velocity', 3)):
            value = actor.get(field)
            if not isinstance(value, list) or len(value) != size or not all(finite(item) for item in value):
                reject('invalid_' + field, state)
        if not finite(actor.get('yaw')) or not finite(state.get('elapsed')) or state['elapsed'] < 0:
            reject('invalid_motion_counters', state)
        move = inputs.get('move')
        if (not isinstance(move, list) or len(move) != 2 or not all(finite(value) for value in move)
                or any(inputs.get(field) is not False for field in ('fire', 'interact', 'reload'))
                or ui.get('waiting_for_input_release') is not False):
            reject('unexpected_or_invalid_inputs', state)
        for field in ('simulation_tick', 'wall_msec'):
            if type(state.get(field)) is not int or state[field] < 0 or (last is not None and state[field] < last[field]):
                reject('invalid_or_regressed_' + field, state)
        if (type(actor.get('deaths')) is not int or actor['deaths'] < 0
                or type(actor.get('team')) is not int or actor['team'] != 0
                or actor.get('weapon') != 'smg' or type(actor.get('ammo')) is not int or actor['ammo'] != 30
                or type(actor.get('reserve')) is not int or actor['reserve'] != 120):
            reject('life_weapon_or_ammunition', state)
        if last is not None and any(actor.get(field) != start['local_actor'].get(field)
                                    for field in ('deaths', 'team', 'weapon', 'ammo', 'reserve')):
            reject('changed_life_weapon_or_ammunition', state)
        x, y, z = actor['position']
        if not -8.5 <= x <= -3.9 or not -.1 <= y <= .1 or not -21.75 <= z <= -20.25:
            reject('left_declared_clear_corridor', state)
        if last is None or any(state[field] != last[field] for field in ('wall_msec', 'simulation_tick')):
            receipt['observations'].append(deepcopy(state))
        last = deepcopy(state)
        return state

    try:
        budget()
        checked(start)
        if math.hypot(start['local_actor']['position'][0] - SETTINGS_SPAWN[0],
                      start['local_actor']['position'][2] - SETTINGS_SPAWN[1]) > .25:
            reject('not_original_stock_spawn', start)
        if (start['local_input']['move'] != [0, 0]
                or math.hypot(start['local_actor']['velocity'][0], start['local_actor']['velocity'][2]) > .05):
            reject('not_neutral_stopped_stock_spawn', start)

        def read():
            budget()
            value = observe()
            budget()
            return checked(value)

        endpoint = approach_floor(*SETTINGS_COVER, observe=read, key=key, pause=pause,
                                  record=record, deadline=deadline, clock=clock)
        budget()
        receipt.update(status='FIXED_ROUTE_REACHED', after=deepcopy(last), endpoint=endpoint,
                       remaining_original_second_live_budget=budget())
        return endpoint
    except Exception as error:
        if receipt['status'] == 'IN_PROGRESS':
            receipt.update(status='FIXED_ROUTE_FAILED', error=str(error))
        raise
