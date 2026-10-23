"""Retain declared model states/keys; no engine, native input or timing claim."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys


root = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(root / 'scripts'))
from test_native_settings_route import SettingsWalker


rows = []
for name, kwargs, consumed in (
        ('ordinary_fixed_route', {'rate': 1, 'delivery': 0}, 0),
        ('delayed_fixed_route', {'rate': .4, 'delivery': .2, 'publication_lag': .1}, 0),
        ('blocked_route', {'blocked': True}, 0),
        ('readiness_consumed_original_cap', {}, 34.95),
        ('death_during_route', {}, 0)):
    world = SettingsWalker(**kwargs)
    if consumed:
        world.pause(consumed)
    if name == 'death_during_route':
        def dead(state):
            state['local_actor'].update(alive=False, health=0)
            return state
        world.mutation = dead
    error = None
    try:
        world.route(deadline=35)
    except Exception as caught:
        error = {'type': type(caught).__name__, 'message': str(caught)}
    rows.append({'name': name, 'declared_model_options': kwargs, 'readiness_seconds_consumed': consumed,
                 'receipt': world.receipt, 'model_records': world.records, 'exception': error,
                 'elapsed_model_wall_seconds': world.wall, 'requested_controls_after': sorted(world.requested)})
receipt = {'source_freeze': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
           'scope': 'Declared 60 Hz movement model and callbacks only; not native collision, input or survival evidence',
           'source_sha256': {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in (
               'scripts/native_settings_route.py', 'scripts/native_approach.py', 'scripts/test_native_settings_route.py')},
           'cases': rows}
Path(__file__).with_name('pure-model-receipts.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps({'source_freeze': receipt['source_freeze'], 'retained_declared_cases': len(rows)}))
