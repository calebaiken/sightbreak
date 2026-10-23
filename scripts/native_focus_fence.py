"""Fail-closed observation fences for the exported focus-recovery controller."""
from copy import deepcopy
import math


class FocusPreconditionLost(RuntimeError):
    def __init__(self, reason, stage):
        super().__init__('FOCUS_PRECONDITION_LOST: ' + reason + ' at ' + stage)


class FocusContextFence:
    def __init__(self, baseline, receipt):
        self.baseline, self.receipt = deepcopy(baseline), receipt
        self.last_valid = None
        receipt.update(status='IN_PROGRESS', baseline=deepcopy(baseline))
        self.require(baseline, 'focus_start', focused=True, paused=False)

    def require(self, state, stage, *, focused=None, paused=None, released=False):
        current = state if isinstance(state, dict) else {}
        actor = current.get('local_actor') if isinstance(current.get('local_actor'), dict) else {}
        ui = current.get('ui') if isinstance(current.get('ui'), dict) else {}
        state = current
        expected_actor = self.baseline.get('local_actor', {}).get('id')
        expected_round = self.baseline.get('round_number')
        reason = None
        if (type(state.get('schema')) is not int or state['schema'] != 1
                or state.get('scope') != 'debug_offline_read_only_observation'
                or state.get('scenario') != 'standard'):
            reason = 'observation_contract_changed'
        elif state.get('phase') != 'live':
            reason = 'live_phase_lost'
        elif (type(expected_round) is not int or expected_round < 1
              or type(state.get('round_number')) is not int
              or state['round_number'] != expected_round):
            reason = 'round_identity_changed'
        elif (type(expected_actor) is not int or expected_actor < 1
              or type(actor.get('id')) is not int or actor['id'] != expected_actor):
            reason = 'actor_identity_changed'
        elif (type(actor.get('deaths')) is not int or actor['deaths'] < 0
              or actor['deaths'] != self.baseline['local_actor'].get('deaths')):
            reason = 'actor_life_changed'
        elif actor.get('alive') is not True:
            reason = 'actor_not_alive'
        elif (type(actor.get('health')) not in (int, float)
              or not math.isfinite(actor['health']) or not 0 < actor['health'] <= 100):
            reason = 'actor_health_invalid'
        elif type(state.get('time_scale')) not in (int, float) or state['time_scale'] != 1:
            reason = 'simulation_speed_changed'
        elif ui.get('screen') != 'game' or ui.get('scoreboard_visible') is not False:
            reason = 'game_ui_context_lost'
        elif type(ui.get('focused')) is not bool or type(ui.get('paused')) is not bool:
            reason = 'unknown_focus_or_pause_context'
        elif focused is not None and ui.get('focused') is not focused:
            reason = 'required_focus_lost'
        elif paused is not None and ui.get('paused') is not paused:
            reason = 'required_pause_context_lost'
        elif released and (ui.get('waiting_for_input_release') is not False
                           or state.get('local_input', {}).get('move') != [0, 0]
                           or state.get('local_input', {}).get('fire') is not False):
            reason = 'controls_not_released'
        elif (not isinstance(actor.get('position'), list) or len(actor['position']) != 3
              or any(type(value) not in (int, float) or not math.isfinite(value) for value in actor['position'])):
            reason = 'invalid_actor_position'
        else:
            for field in ('wall_msec', 'simulation_tick', 'drawn_frames'):
                value = state.get(field)
                if type(value) is not int or value < 0:
                    reason = 'invalid_' + field
                    break
                if self.last_valid is not None and value < self.last_valid[field]:
                    reason = 'regressed_' + field
                    break
        if reason:
            self.receipt.update(status='FOCUS_PRECONDITION_LOST', precondition_loss={
                'kind': 'FOCUS_PRECONDITION_LOST', 'reason': reason, 'stage': stage,
                'previous_valid_state': deepcopy(self.last_valid), 'rejected_state': deepcopy(state)})
            raise FocusPreconditionLost(reason, stage)
        self.last_valid = deepcopy(state)
        self.receipt['last_valid_state'] = deepcopy(state)
        return state


def fresh_focus_movement(*, fence, released, snapshot, observed, key, receipt):
    """Retain the before/after states and original ten-second movement wait.

    No life/round retry is permitted. A timeout only reports an unobserved
    response within the deadline; it does not assert an input defect.
    """
    receipt.update(status='IN_PROGRESS', released=deepcopy(released), key_down_dispatched=False)
    key_attempted = False
    try:
        fence.require(released, 'released_controls', focused=True, paused=False, released=True)
        before = snapshot()
        receipt['before_key'] = deepcopy(before)
        fence.require(before, 'before_fresh_w_down', focused=True, paused=False, released=True)

        def moved(state):
            receipt['last_after_key'] = deepcopy(state)
            fence.require(state, 'fresh_w_response_wait', focused=True, paused=False)
            move = state.get('local_input', {}).get('move')
            return (isinstance(move, list) and len(move) == 2
                    and all(type(value) in (int, float) and math.isfinite(value) for value in move)
                    and move != [0, 0] and state['simulation_tick'] > before['simulation_tick']
                    and state['local_actor']['position'] != before['local_actor']['position'])

        key_attempted = True
        key('w', True)
        receipt['key_down_dispatched'] = True
        result = observed(moved, 10, 'Fresh W press moves actual player after focus recovery', before['wall_msec'])
        receipt.update(status='LIVING_MOVEMENT_OBSERVED', moved=deepcopy(result))
        return result
    except FocusPreconditionLost:
        receipt['status'] = 'FOCUS_PRECONDITION_LOST'
        raise
    except TimeoutError:
        receipt['status'] = 'RESPONSE_NOT_OBSERVED_BEFORE_ORIGINAL_DEADLINE'
        raise
    finally:
        if key_attempted:
            key('w', False)
