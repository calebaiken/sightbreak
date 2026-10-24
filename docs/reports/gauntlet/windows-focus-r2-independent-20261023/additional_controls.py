"""Independent actual-reader publication and exact Escape schedule controls."""
import ast
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

OUT = Path(__file__).resolve().parent
LABEL = 'Explicit resume with W and LMB still physically held'


def bind(tree, name, namespace):
    node = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == name)
    exec(compile(ast.Module(body=[deepcopy(node)], type_ignores=[]), 'actual-controller:' + name, 'exec'), namespace)


def main():
    source = Path(sys.argv[1]).resolve()
    freeze, label = sys.argv[2:4]
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=source, text=True).strip() == freeze
    controller = (source / 'scripts/verify_offline_export.py').read_bytes()
    tree = ast.parse(controller)
    spec = importlib.util.spec_from_file_location('reviewed_helper', source / 'scripts/native_focus_fence.py')
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    raw = json.loads((source / 'scripts/fixtures/offline_focus_observations.json').read_text())
    checks, cases = [], []
    def check(name, condition):
        assert condition, name
        checks.append(name)
    def living(offset=0, moving=False):
        state = deepcopy(raw['last_living_guard'])
        state['wall_msec'] += offset * 100
        state['simulation_tick'] += offset
        state['drawn_frames'] += offset
        state['ui']['waiting_for_input_release'] = False
        if moving:
            state['local_input']['move'] = [0, 1]
            state['local_actor']['position'][2] += 1
        return state

    class Harness:
        def __init__(self, publications, *, deadline=300):
            self.publications = list(publications)
            self.elapsed, self.events, self.held = 0, [], {'w'}
            self.context, self.receipt, self.reads = {}, {}, []
            self.fence = helper.FocusContextFence(raw['focus_start'], self.context)
            outer = self
            class Clock:
                def monotonic(self):
                    return outer.elapsed
                def sleep(self, seconds):
                    outer.events.append({'event': 'sleep', 'seconds': seconds, 'at': outer.elapsed})
                    outer.elapsed += seconds
            class UI:
                def key(self, name, down):
                    outer.events.append({'event': 'physical_key', 'key': name, 'down': down, 'at': outer.elapsed})
            def read(path):
                value = self.publications.pop(0) if self.publications else FileNotFoundError('declared unpublished path')
                self.reads.append({'raw': str(value) if isinstance(value, BaseException) else deepcopy(value),
                                   'last_valid_before_read': deepcopy(self.fence.last_valid)})
                if isinstance(value, BaseException):
                    raise value
                return value
            def trace(event, **values):
                self.events.append({'event': event, 'at': self.elapsed, **deepcopy(values)})
            self.ns = {'time': Clock(), 'deadline': deadline, 'client': None, 'trace': trace,
                       'ui': UI(), 'held_keys': self.held, 'cleanup_errors': [],
                       'read_observation_json': read, 'initial_trace': Path('/declared/trace'), 'result': {},
                       'fence': self.fence}
            for name in ('remaining', 'pause', 'wait_for', 'key', 'tap', 'offline_observation', 'observed',
                         'require_focus_context', 'focus_raw_observation', 'focus_observed'):
                bind(tree, name, self.ns)
        def run(self):
            self.error, self.result = None, None
            try:
                self.result = helper.fresh_focus_movement(fence=self.fence, released=living(),
                    snapshot=self.ns['focus_raw_observation'], observed=self.ns['observed'],
                    key=self.ns['key'], receipt=self.receipt)
            except Exception as error:
                self.error = {'type': type(error).__name__, 'message': str(error)}
            return self
        def capture(self, name):
            cases.append({'name': name, 'error': self.error, 'result': self.result,
                          'context': self.context, 'fresh_press': self.receipt, 'events': self.events,
                          'reads': self.reads, 'remaining_publications': len(self.publications), 'clock': self.elapsed})

    before = living(1)
    stale_buy = deepcopy(raw['focus_start'])
    stale_buy['phase'] = 'buy'
    stale_buy['round_number'] = 2
    trial = Harness([before, FileNotFoundError('declared publication gap'), ValueError('declared incomplete publication'),
                     stale_buy, living(2), living(3, True)]).run()
    check('actual reader gaps and valid stale buy frame permit later living movement', trial.result == living(3, True))
    check('publication gap and stale frame never replace previous valid state',
          all(row['last_valid_before_read'] == before for row in trial.reads[1:5]))
    check('fresh neutral poll becomes previous valid state', trial.reads[5]['last_valid_before_read'] == living(2))
    check('valid sequence releases W', trial.held == set())
    trial.capture('actual_reader_gaps_stale_buy_neutral_then_living_move')

    # Available empty/non-object values must not become the unavailable sentinel.
    for value in ({}, None, [], False, 0, 'raw-string'):
        for boundary in ('before', 'during'):
            publications = [value, living(3, True)] if boundary == 'before' else [before, value, living(3, True)]
            trial = Harness(publications).run()
            name = 'actual_reader_' + type(value).__name__ + '_' + boundary
            check(name + ': structured loss', trial.error['type'] == 'FocusPreconditionLost')
            check(name + ': exact raw retained', trial.context['precondition_loss']['rejected_state'] == value)
            check(name + ': no later substitution', len(trial.publications) == 1)
            check(name + ': key boundary respected', trial.held == ({'w'} if boundary == 'before' else set()))
            trial.capture(name)
    for section, field, value in [('', 'scope', 'other'), ('', 'phase', 'post'), ('', 'round_number', 2),
        ('local_actor', 'deaths', 1), ('local_actor', 'health', 0), ('local_input', 'move', [False, 0]),
        ('local_input', 'move', [0, '1']), ('ui', 'waiting_for_input_release', None),
        ('local_actor', 'position', [0, True, 0])]:
        changed = living(2, True)
        (changed[section] if section else changed)[field] = value
        trial = Harness([before, changed, living(3, True)]).run()
        name = 'actual_reader_' + section + '.' + field
        check(name + ': structured loss', trial.error['type'] == 'FocusPreconditionLost')
        check(name + ': exact raw retained', trial.context['precondition_loss']['rejected_state'] == changed)
        check(name + ': previous valid retained', trial.context['precondition_loss']['previous_valid_state'] == before)
        check(name + ': no later substitution', len(trial.publications) == 1)
        saved = deepcopy(trial.context)
        changed['local_actor']['health'] = 99
        check(name + ': receipt immune to raw mutation', trial.context == saved)
        trial.capture(name)
    trial = Harness([FileNotFoundError('declared immediate snapshot gap'), living(3, True)]).run()
    check('immediate unpublished snapshot rejects before fresh key', trial.error['type'] == 'FocusPreconditionLost' and trial.held == {'w'})
    check('immediate unpublished snapshot is not retried', len(trial.publications) == 1)
    trial.capture('immediate_publication_gap_fails_closed')

    # Exercise the generic active-focus hook, separately from fresh W's hook.
    changed = living(2)
    changed.pop('wall_msec')
    trial = Harness([changed, living(3)])
    trial.error, trial.result = None, None
    try:
        trial.result = trial.ns['focus_observed'](lambda state: True, 10, 'declared held-neutral sample', before['wall_msec'])
    except Exception as error:
        trial.error = {'type': type(error).__name__, 'message': str(error)}
    check('generic active-focus hook validates before freshness', trial.error['type'] == 'FocusPreconditionLost')
    check('generic active-focus hook preserves raw', trial.context['precondition_loss']['rejected_state'] == changed)
    check('generic active-focus hook stops before later state', len(trial.publications) == 1)
    trial.capture('active_focus_hook_missing_timestamp')

    # Execute the precise resume prefix found by the ACK assignment. Nothing
    # after that assignment (inertia, guard samples or captures) is substituted.
    prefix = None
    for node in ast.walk(tree):
        if isinstance(node, ast.Try):
            for index, statement in enumerate(node.body):
                if isinstance(statement, ast.Assign) and any(isinstance(item, ast.Constant) and item.value == LABEL for item in ast.walk(statement)):
                    count = 1 if ast.unparse(node.body[index - 1]) == "tap('Escape')" else 3
                    prefix = node.body[index - count:index + 1]
    assert prefix is not None
    code = compile(ast.Module(body=deepcopy(prefix), type_ignores=[]), 'actual-focus-resume-prefix', 'exec')
    expected_start = 1.3 if label == 'fence' else .3
    for mode in ('immediate_ack', 'delayed_ack', 'dead_ack', 'ack_timeout', 'whole_deadline', 'hold_interrupted'):
        paused = living(0)
        paused['ui']['paused'] = True
        unpaused = living(1)
        dead = living(1)
        dead['local_actor'].update(alive=False, health=0)
        pubs = {'immediate_ack': [unpaused], 'delayed_ack': [paused, unpaused], 'dead_ack': [dead],
                'ack_timeout': [paused], 'whole_deadline': [paused], 'hold_interrupted': [paused]}[mode]
        deadline = .2 if mode == 'hold_interrupted' else (1.75 if mode == 'whole_deadline' else 300)
        trial = Harness(pubs, deadline=deadline)
        trial.ns['restored'] = paused
        trial.error, trial.result = None, None
        try:
            exec(code, trial.ns)
            trial.result = trial.ns['guarded']
        except Exception as error:
            trial.error = {'type': type(error).__name__, 'message': str(error)}
        physical = [event for event in trial.events if event['event'] == 'physical_key']
        if mode == 'hold_interrupted':
            check(mode + ': whole deadline rejects original hold', trial.error['type'] == 'TimeoutError')
            check(mode + ': Escape retained for original cleanup', 'Escape' in trial.held)
            cleanup = next(node for node in ast.walk(tree) if isinstance(node, ast.For) and ast.unparse(node.iter) == 'list(held_keys)')
            exec(compile(ast.Module(body=[deepcopy(cleanup)], type_ignores=[]), 'actual-final-release-loop', 'exec'), trial.ns)
            check(mode + ': original cleanup releases Escape', any(event.get('key') == 'Escape' and event.get('down') is False for event in trial.events))
        else:
            check(mode + ': same physical hold', physical[0]['key'] == physical[1]['key'] == 'Escape'
                  and physical[0]['down'] is True and physical[0]['at'] == 0
                  and physical[1]['down'] is False and physical[1]['at'] == .3)
            begin = next(event for event in trial.events if event['event'] == 'wait_begin')
            check(mode + ': exact ACK scheduling', abs(begin['at'] - expected_start) < 1e-9)
            check(mode + ': original ACK budget', begin['budget_seconds'] == 10)
            check(mode + ': Escape already released', trial.held == {'w'})
            if mode in ('immediate_ack', 'delayed_ack'):
                check(mode + ': actual fresh unpaused ACK required', trial.error is None and trial.result == unpaused)
                expected_end = expected_start if mode == 'immediate_ack' else expected_start + .1
                check(mode + ': expected monotonic schedule', abs(trial.elapsed - expected_end) < 1e-9)
            elif mode == 'dead_ack':
                check(mode + ': dead context rejected', trial.error['type'] == 'FocusPreconditionLost')
            else:
                check(mode + ': original timeout', trial.error['type'] == 'TimeoutError')
                expected_end = 1.75 if mode == 'whole_deadline' else expected_start + 10
                check(mode + ': no deadline extension', expected_end <= trial.elapsed < expected_end + .101)
        trial.capture('resume_' + mode)
    trial = Harness([])
    trial.ns['tap']('Escape')
    check('generic tap retains post-up one second', abs(trial.elapsed - 1.3) < 1e-9)
    check('generic tap holds .3 then sleeps one', [event['seconds'] for event in trial.events if event['event'] == 'sleep'] == [.3, 1])
    trial.error, trial.result = None, None
    trial.capture('generic_tap_preserved')
    receipt = {'source_freeze': freeze, 'scope': 'pure declared read outcomes, actual frozen reader/wait/key/pause/resume/cleanup AST',
        'controller_sha256': hashlib.sha256(controller).hexdigest(), 'assertion_count': len(checks), 'assertions': checks,
        'case_count': len(cases), 'all_passed': True, 'cases': cases}
    (OUT / (label + '-additional-controls.json')).write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({k:v for k,v in receipt.items() if k not in ('assertions', 'cases')}))


if __name__ == '__main__':
    main()
