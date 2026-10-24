"""Independent pure probes of frozen helper and actual controller wait AST.

No engine, OCR executable, input process, export, CI, or services are started.
Snapshots and monotonic time are declared test inputs, never native evidence.
"""
import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'scripts'))
from native_focus_fence import FocusContextFence, FocusPreconditionLost, fresh_focus_movement

RAW = json.loads((ROOT / 'scripts/fixtures/offline_focus_observations.json').read_text())
CONTROLLER = ast.parse((ROOT / 'scripts/verify_offline_export.py').read_text())
MISSING = object()


def living(offset=0, moving=False):
    value = deepcopy(RAW['last_living_guard'])
    value['wall_msec'] += offset * 100
    value['simulation_tick'] += offset
    value['drawn_frames'] += offset
    value['ui']['waiting_for_input_release'] = False
    if moving:
        value['local_input']['move'] = [0, 1]
        value['local_actor']['position'][2] += 1
    return value


def extracted(name, namespace):
    node = next(node for node in ast.walk(CONTROLLER)
                if isinstance(node, ast.FunctionDef) and node.name == name)
    module = ast.Module(body=[node], type_ignores=[])
    exec(compile(module, 'actual-controller:' + name, 'exec'), namespace)
    return namespace[name]


class Clock:
    def __init__(self):
        self.value = 0
    def monotonic(self):
        return self.value
    def sleep(self, seconds):
        self.value += seconds


class Trial:
    def __init__(self, *, baseline=MISSING, released=MISSING, before=MISSING, states=(), deadline=300,
                 scope_read_check=False, key_error=False, poll_advance=0):
        self.baseline = deepcopy(RAW['focus_start'] if baseline is MISSING else baseline)
        self.released = deepcopy(living() if released is MISSING else released)
        self.before = deepcopy(living(1) if before is MISSING else before)
        self.states = list(deepcopy(states))
        self.keys, self.waits, self.polls = [], [], []
        self.receipt, self.context = {}, {}
        self.clock, self.deadline = Clock(), deadline
        self.scope_read_check, self.key_error, self.poll_advance = scope_read_check, key_error, poll_advance

    def read(self):
        state = self.states.pop(0) if self.states else {}
        self.polls.append(deepcopy(state))
        self.clock.value += self.poll_advance
        return state

    def key(self, name, down):
        self.keys.append([name, down])
        if down and self.key_error:
            raise RuntimeError('declared down dispatch failure')

    def run(self):
        namespace = {'time': self.clock, 'deadline': self.deadline,
                     'trace': lambda event, **kw: self.waits.append({'event': event, **kw}),
                     'client': None, 'offline_observation': self.read}
        if self.scope_read_check:
            namespace.update(read_observation_json=lambda path: self.read(),
                             initial_trace=Path('/declared/trace'), result={})
            namespace['offline_observation'] = extracted('offline_observation', namespace)
        namespace['wait_for'] = extracted('wait_for', namespace)
        observed = extracted('observed', namespace)
        error = None
        result = None
        try:
            fence = FocusContextFence(self.baseline, self.context)
            result = fresh_focus_movement(fence=fence, released=self.released,
                snapshot=lambda: self.before, observed=observed, key=self.key, receipt=self.receipt)
        except Exception as caught:
            error = {'type': type(caught).__name__, 'message': str(caught)}
        return {'exception': error, 'result': result, 'fresh_press': self.receipt,
                'context_fence': self.context, 'keys': self.keys, 'waits': self.waits,
                'polls': self.polls, 'final_clock': self.clock.value}


def mutate(state, section, field, value=MISSING):
    target = state[section] if section else state
    if value is MISSING:
        target.pop(field, None)
    else:
        target[field] = deepcopy(value)
    return state


def main():
    rows = []
    def case(name, expectation, **kwargs):
        row = {'name': name, 'expectation': expectation, **Trial(**kwargs).run()}
        rows.append(row)
        return row

    case('valid_living_movement', 'LIVING_MOVEMENT_OBSERVED', states=[living(2, True)])
    case('original_dead_release', 'FOCUS_PRECONDITION_LOST and zero key calls', released=RAW['dead_release_ack'])
    for section, field, value in [('local_actor', 'alive', False), ('local_actor', 'health', 0),
        ('local_actor', 'id', 2), ('local_actor', 'deaths', 1), ('', 'phase', 'post'), ('', 'round_number', 2)]:
        for boundary in ('before', 'during'):
            changed = mutate(living(2, True), section, field, value)
            case(f'{section}.{field}_{boundary}', 'FOCUS_PRECONDITION_LOST; rejected movement must not pass',
                 before=changed if boundary == 'before' else living(1),
                 states=[changed, living(3, True)])
    for section, field, values in [
        ('local_actor', 'health', [MISSING, None, True, '100', -1, 101]),
        ('local_actor', 'id', [MISSING, None, True, 1.0]),
        ('local_actor', 'deaths', [MISSING, None, True, 0.0]),
        ('', 'round_number', [MISSING, None, True, 1.0]),
        ('', 'time_scale', [MISSING, None, True, 1.0]),
        ('', 'schema', [MISSING, None, True, 1.0]),
        ('ui', 'focused', [MISSING, None, 1]),
        ('ui', 'paused', [MISSING, None, 0]),
        ('local_actor', 'position', [MISSING, None, [1, 2], [1, 2, True]]),
    ]:
        for index, value in enumerate(values):
            case(f'bad_{section}.{field}_{index}', 'Strict invalid values must reject (time_scale float 1.0 is valid)',
                 before=mutate(living(1), section, field, value), states=[living(2, True)])

    for value in [None, [], 'raw-string', 3]:
        case(f'non_dict_before_{type(value).__name__}', 'FOCUS_PRECONDITION_LOST with exact raw rejected value', before=value)
    for boundary in ('before', 'during'):
        for value in [None, [], True, 'raw-string', 3]:
            changed = mutate(living(2, True), '', 'local_input', value)
            case(f'wrong_local_input_{type(value).__name__}_{boundary}', 'FOCUS_PRECONDITION_LOST with rejected raw snapshot',
                 before=changed if boundary == 'before' else living(1), states=[changed, living(3, True)])
    case('wrong_baseline_actor', 'FOCUS_PRECONDITION_LOST with rejected raw baseline', baseline=mutate(deepcopy(RAW['focus_start']), '', 'local_actor', None))
    case('boolean_neutral_move', 'FOCUS_PRECONDITION_LOST for wrong-type control vector',
         before=mutate(living(1), 'local_input', 'move', [False, False]), states=[living(2, True)])
    for field, value in [('wall_msec', MISSING), ('wall_msec', -1), ('wall_msec', 'later'),
                         ('simulation_tick', MISSING), ('drawn_frames', MISSING)]:
        bad = mutate(living(2, True), '', field, value)
        bad['local_actor'].update(alive=False, health=0)
        suffix = 'MISSING' if value is MISSING else str(value)
        case(f'dead_bad_counter_{field}_{suffix}', 'FOCUS_PRECONDITION_LOST; do not skip dead state and accept later movement',
             states=[bad, living(3, True)])
    case('changed_scope_through_actual_reader_guard', 'FOCUS_PRECONDITION_LOST with rejected raw snapshot',
         states=[mutate(living(2, True), '', 'scope', 'other')], scope_read_check=True)
    case('stale_movement_then_timeout', 'Original 10-second timeout and key release', states=[living(1, True)])
    case('missing_publication_then_timeout', 'Original 10-second timeout and key release', states=[{}])
    case('whole_deadline_limits_wait', 'Original whole deadline at 0.25s limits 10-second wait', states=[], deadline=.25)
    case('dispatch_failure_still_releases', 'Down dispatch failure still attempts W up', key_error=True)
    case('predicate_returns_after_original_deadline', 'Existing wait_for limitation: condition can complete beyond prechecked deadline',
         states=[living(2, True)], poll_advance=11)
    for row in rows:
        row['observation'] = row['exception']['type'] if row['exception'] else row['fresh_press'].get('status')
    by_name = {row['name']: row for row in rows}
    checks = []
    def verify(name, condition):
        assert condition, name
        checks.append(name)
    verify('positive living control passes', by_name['valid_living_movement']['observation'] == 'LIVING_MOVEMENT_OBSERVED')
    verify('original dead release dispatches no key', by_name['original_dead_release']['keys'] == [])
    for row in rows:
        if row['name'].startswith(('local_actor.', '.phase_', '.round_number_')):
            verify(row['name'] + ' rejects', row['observation'] == 'FocusPreconditionLost')
            verify(row['name'] + ' never records moved', 'moved' not in row['fresh_press'])
    for name in ('dead_bad_counter_wall_msec_MISSING', 'dead_bad_counter_wall_msec_-1', 'boolean_neutral_move'):
        verify(name + ' reproduces false acceptance', by_name[name]['observation'] == 'LIVING_MOVEMENT_OBSERVED')
    for row in rows:
        if row['name'].startswith('wrong_local_input_') or row['name'] == 'wrong_baseline_actor':
            verify(row['name'] + ' lacks structured rejection', row['observation'] == 'AttributeError'
                   and row['context_fence']['status'] == 'IN_PROGRESS'
                   and 'precondition_loss' not in row['context_fence'])
        if row['name'].startswith('non_dict_before_'):
            verify(row['name'] + ' loses raw rejected type', row['context_fence']['precondition_loss']['rejected_state'] == {})
    for name in ('stale_movement_then_timeout', 'missing_publication_then_timeout', 'whole_deadline_limits_wait'):
        verify(name + ' retains timeout status and key release',
               by_name[name]['fresh_press']['status'] == 'RESPONSE_NOT_OBSERVED_BEFORE_ORIGINAL_DEADLINE'
               and by_name[name]['keys'] == [['w', True], ['w', False]])
    verify('failed key down still attempts up', by_name['dispatch_failure_still_releases']['keys'] == [['w', True], ['w', False]])
    verify('existing late predicate success remains observable',
           by_name['predicate_returns_after_original_deadline']['observation'] == 'LIVING_MOVEMENT_OBSERVED'
           and by_name['predicate_returns_after_original_deadline']['final_clock'] == 11)
    full_names = {'valid_living_movement', 'original_dead_release', 'local_actor.alive_before',
                 'local_actor.alive_during', 'local_actor.deaths_during', '.phase_during', '.round_number_during',
                 'wrong_local_input_NoneType_before', 'wrong_local_input_NoneType_during', 'wrong_baseline_actor',
                 'non_dict_before_NoneType', 'non_dict_before_str', 'boolean_neutral_move',
                 'dead_bad_counter_wall_msec_MISSING', 'dead_bad_counter_wall_msec_-1',
                 'dead_bad_counter_wall_msec_later', 'changed_scope_through_actual_reader_guard',
                 'whole_deadline_limits_wait', 'predicate_returns_after_original_deadline'}
    receipt = {'source_freeze': '19304d5d736b09326d5d2503da09dc8cf7b45129',
               'review_base': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
               'controller_sha256': hashlib.sha256((ROOT / 'scripts/verify_offline_export.py').read_bytes()).hexdigest(),
               'helper_sha256': hashlib.sha256((ROOT / 'scripts/native_focus_fence.py').read_bytes()).hexdigest(),
               'scope': 'Pure declared snapshots; actual observed/wait_for AST; no native gameplay evidence',
               'assertion_count': len(checks), 'assertions': checks,
               'case_count': len(rows), 'case_summaries': [
                   {'name': row['name'], 'expectation': row['expectation'], 'observation': row['observation'],
                    'exception': row['exception'], 'keys': row['keys'], 'final_clock': row['final_clock'],
                    'context_status': row['context_fence'].get('status'),
                    'fresh_press_status': row['fresh_press'].get('status'),
                    'reason': row['context_fence'].get('precondition_loss', {}).get('reason')}
                   for row in rows], 'cases': [row for row in rows if row['name'] in full_names]}
    output = Path(__file__).with_name('counterexamples.json')
    output.write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({'cases': len(rows), 'output': str(output), 'summary': [
        {'name': row['name'], 'observation': row['observation'], 'keys': row['keys'],
         'status': row['context_fence'].get('status')} for row in rows]}))


if __name__ == '__main__':
    main()
