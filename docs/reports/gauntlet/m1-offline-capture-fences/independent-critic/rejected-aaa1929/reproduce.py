#!/usr/bin/env python3
"""Read-only independent scheduling controls on frozen aaa1929; no native pixels."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0, '/workspace/sightbreak-capture-fences/scripts')
spec = importlib.util.spec_from_file_location('frozen_observer', ROOT / 'frozen/scripts/verify_offline_export.py')
observer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(observer)
fixture = json.loads((ROOT / 'frozen/scripts/fixtures/offline_capture_observations.json').read_text())
base = fixture['round_2_buy']


def sample(frame_delta, *, wall_delta=None, **changes):
    state = deepcopy(base)
    state.update(drawn_frames=base['drawn_frames'] + frame_delta,
                 wall_msec=base['wall_msec'] + (frame_delta * 100 if wall_delta is None else wall_delta),
                 simulation_tick=base['simulation_tick'] + frame_delta)
    state.update(changes)
    return state


class Poller:
    """Matches production's fresh-wall gate without using the builder's fake."""
    def __init__(self, states):
        self.states = list(states)
        self.driver_seconds = 0.0
        self.receipt = {}
        self.history = []
        self.captures = []
        self.binding_calls = 0
        self.fixed_binding = {'source': 'frozen', 'process_pid': 20,
                              'process_running': True, 'trace_directory': '/declared/owned-trace'}

    def observed(self, predicate, seconds, label, after=-1):
        end = self.driver_seconds + seconds
        while self.states:
            self.driver_seconds += 0.1
            if self.driver_seconds >= end:
                raise TimeoutError(label)
            state = deepcopy(self.states.pop(0))
            self.history.append({'label': label, 'driver_seconds': self.driver_seconds,
                                 'wall_msec': state['wall_msec'], 'drawn_frames': state['drawn_frames'],
                                 'simulation_tick': state['simulation_tick']})
            if state.get('wall_msec', -1) > after and predicate(state):
                return state
        self.driver_seconds = end
        raise TimeoutError(label)

    def binding(self):
        self.binding_calls += 1
        return deepcopy(self.fixed_binding)

    def capture(self, name):
        self.captures.append(name)

    def run(self):
        return observer.capture_living_phase('declared-only', actor_id=1, round_number=2,
                                             after=-1, until=160, observed=self.observed,
                                             capture=self.capture, binding=self.binding,
                                             expected_binding=self.fixed_binding, receipt=self.receipt,
                                             clock=lambda: self.driver_seconds)


outputs = {'candidate': 'aaa192903a8e5e333abcf9ada7741e13145a123e',
           'scope': 'Pure declared scheduling; neither native execution nor pixel evidence',
           'controls': []}

for counter in ('drawn_frames', 'simulation_tick'):
    regression = sample(1, wall_delta=200)
    regression[counter] = base[counter]
    poller = Poller([sample(0), sample(1), regression, sample(2, wall_delta=300),
                     sample(3, wall_delta=400), sample(4, wall_delta=500)])
    poller.run()
    outputs['controls'].append({'case': counter + '_regresses_inside_frame_wait',
                                 'false_accepted': bool(poller.captures),
                                 'sample_history': poller.history,
                                 'receipt_counters': {stage: poller.receipt[stage][counter]
                                                      for stage in ('acknowledged', 'ready', 'before_capture', 'after_capture')}})


class PreCaptureStall(Poller):
    """A valid update is published during binding, then the status publisher stalls."""
    def __init__(self):
        super().__init__([sample(0), sample(2), sample(3)])
        self.published_before_capture = None
        self.capture_context = None

    def binding(self):
        result = super().binding()
        if self.binding_calls == 2:
            self.driver_seconds += .1
            self.published_before_capture = sample(4)
            self.publication_driver_seconds = self.driver_seconds
            self.states.append(deepcopy(self.published_before_capture))
        return result

    def capture(self, name):
        self.driver_seconds += .1
        self.capture_begin_driver_seconds = self.driver_seconds
        self.capture_context = {'phase': 'live', 'local_actor_alive': False,
                                'scope': 'Declared context loss; no image was captured'}
        self.driver_seconds += .1
        self.capture_end_driver_seconds = self.driver_seconds
        super().capture(name)


poller = PreCaptureStall()
poller.run()
outputs['controls'].append({'case': 'post_capture_accepts_state_published_before_capture',
                             'false_accepted': bool(poller.captures),
                             'publication_driver_seconds': poller.publication_driver_seconds,
                             'capture_begin_driver_seconds': poller.capture_begin_driver_seconds,
                             'capture_end_driver_seconds': poller.capture_end_driver_seconds,
                             'declared_context_during_capture': poller.capture_context,
                             'accepted_after_equals_pre_capture_publication':
                                 poller.receipt['after_capture'] == poller.published_before_capture,
                             'sample_history': poller.history})

assert len(outputs['controls']) == 3
assert all(item['false_accepted'] for item in outputs['controls'])
print(json.dumps(outputs, indent=2))
