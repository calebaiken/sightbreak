#!/usr/bin/env python3
"""Reassess corrected source against independent scheduling counterexamples."""
from copy import deepcopy
from contextlib import redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, '/workspace/sightbreak-capture-fences/scripts')

def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result

baseline_stdout = io.StringIO()
with redirect_stdout(baseline_stdout):
    prior = module('prior_critic', ROOT.parent / 'offline-capture-phase-critic-aaa1929/reproduce.py')
(ROOT / 'prior-counterexample-replay.log').write_text(baseline_stdout.getvalue())
candidate = module('revised_observer', ROOT / 'frozen/scripts/verify_offline_export.py')
prior.observer = candidate

outcomes = []

def run_case(name, poller, expected_exception=None):
    error = None
    try:
        poller.run()
    except Exception as caught:
        error = caught
    if expected_exception:
        assert isinstance(error, expected_exception), (name, error)
    else:
        assert error is None, (name, error)
    outcomes.append({'case': name, 'outcome': 'correctly_rejected' if error else 'accepted_declared_control',
                     'error': str(error) if error else None, 'capture_called': bool(poller.captures),
                     'accepted_after_capture': 'after_capture' in poller.receipt,
                     'receipt_stages': list(poller.receipt), 'sample_history': poller.history})

for field in ('drawn_frames', 'simulation_tick', 'wall_msec'):
    rollback = prior.sample(1, wall_delta=150)
    rollback[field] = prior.base[field] + (50 if field == 'wall_msec' else 0)
    poller = prior.Poller([prior.sample(0), prior.sample(1), rollback,
                           prior.sample(2), prior.sample(3), prior.sample(4), prior.sample(5)])
    run_case(field + '_rollback_inside_frame_wait', poller, RuntimeError)
    assert not poller.captures

poller = prior.PreCaptureStall()
run_case('buffered_pre_capture_publication_then_stopped_producer', poller, TimeoutError)
assert 'after_capture_barrier' in poller.receipt and 'after_capture' not in poller.receipt

class RecoveringProducer(prior.PreCaptureStall):
    def capture(self, name):
        super().capture(name)
        self.capture_context = {'phase': 'buy', 'local_actor_alive': True,
                                'scope': 'Declared valid context; no image was captured'}

    def observed(self, predicate, seconds, label, after=-1):
        if 'beyond post-capture barrier' in label:
            self.states.append(prior.sample(5))
        return super().observed(predicate, seconds, label, after)

poller = RecoveringProducer()
run_case('post_capture_new_valid_publication', poller)
assert poller.receipt['after_capture']['wall_msec'] > poller.receipt['after_capture_barrier']['wall_msec']

class LateContextLoss(prior.PreCaptureStall):
    def observed(self, predicate, seconds, label, after=-1):
        if 'beyond post-capture barrier' in label:
            state = prior.sample(5)
            state['phase'] = 'live'
            self.states.append(state)
        return super().observed(predicate, seconds, label, after)

poller = LateContextLoss()
run_case('new_post_capture_publication_loses_buy_phase', poller, RuntimeError)
assert 'after_capture' not in poller.receipt

class ExpiredBarrier(prior.PreCaptureStall):
    def observed(self, predicate, seconds, label, after=-1):
        result = super().observed(predicate, seconds, label, after)
        if 'Observation barrier after raw capture' in label:
            self.driver_seconds = 160
        return result

poller = ExpiredBarrier()
run_case('original_deadline_expires_at_post_capture_barrier', poller, TimeoutError)
assert 'after_capture' not in poller.receipt

poller = prior.Poller([prior.sample(0), prior.sample(1), prior.sample(2),
                       prior.sample(3), prior.sample(4), prior.sample(5)])
run_case('normal_monotonic_two_frame_and_post_capture_barrier', poller)

assert len(outcomes) == 8
(ROOT / 'independent-recheck.json').write_text(json.dumps({'candidate': '65c3b8bfdfa14342411c9aa6519244628cc12c81',
                                                         'scope': 'Declared observer scheduling only',
                                                         'controls': outcomes}, indent=2) + '\n')
print('Independent revision controls: 8 passed; native pixels remain unverified.')
