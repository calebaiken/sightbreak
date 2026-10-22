#!/usr/bin/env python3
"""Independent static audit of retained focus actions and source receipts."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = Path('/workspace/sightbreak-offline-flow')
packet = HERE / 'focus-r1/native-focus-r1'
result = json.loads((packet / 'results.json').read_text())
actions = json.loads((packet / 'actions.json').read_text())
focus = result['native_focus_recovery']
receipt = result['focus_only_driver']
driver = ROOT / 'docs/reports/gauntlet/m1-offline-flow-observation/verify_native_focus_only.py'
tree = ast.parse(driver.read_text())
# Evaluate construction only. Exclude the final exec that launches the client.
assert isinstance(tree.body[-1], ast.Expr) and isinstance(tree.body[-1].value, ast.Call)
assert isinstance(tree.body[-1].value.func, ast.Name) and tree.body[-1].value.func.id == 'exec'
namespace = {'__file__': str(driver), '__name__': 'independent_construction_audit'}
exec(compile(ast.Module(body=tree.body[:-1], type_ignores=[]), str(driver), 'exec'), namespace)
assert namespace['receipt'] == receipt

labels = {
    'held_input_acknowledged': 'Game consumed physical W and LMB before native focus loss',
    'lost': 'Native focus loss pauses actual offline match',
    'restored_paused': 'Actual game observes restored focus',
    'released': 'Released held focus-test controls',
    'fresh_press_movement': 'Fresh W press moves actual player after focus recovery',
}
receipts = []
for key, label in labels.items():
    matched = [a for a in actions if a['event'] == 'offline_observation' and a.get('label') == label]
    assert len(matched) == 1 and matched[0]['state'] == focus[key]
    receipts.append(matched[0])
held = focus['held_neutral_samples']
assert len(held) >= 3
for state in held:
    matched = [a for a in actions if a['event'] == 'offline_observation' and a.get('state') == state]
    assert len(matched) == 1
    native = matched[0]['native_state']
    assert native['target_focused'] and native['lmb_down'] and native['keys_down']['w']
    assert state['ui']['waiting_for_input_release'] is True
    assert state['local_input']['move'] == [0, 0] and state['local_input']['fire'] is False
    assert state['local_actor']['ammo'] == 14 and state['local_actor']['alive'] is True
for before, after in zip(held, held[1:]):
    assert all(after[k] > before[k] for k in ['wall_msec', 'simulation_tick', 'drawn_frames'])
    assert after['local_actor']['position'] == before['local_actor']['position']
released, moved = focus['released'], focus['fresh_press_movement']
assert released['ui']['waiting_for_input_release'] is False
assert moved['simulation_tick'] > released['simulation_tick'] > held[-1]['simulation_tick']
assert moved['drawn_frames'] > released['drawn_frames'] > held[-1]['drawn_frames']
assert moved['local_actor']['alive'] and moved['local_input']['move'] == [0, 1]
assert moved['round_number'] == released['round_number'] == 1
assert moved['local_actor']['id'] == released['local_actor']['id'] == 1
assert moved['phase'] == released['phase'] == 'live'
assert moved['time_scale'] == released['time_scale'] == 1
assert moved['local_actor']['ammo'] == released['local_actor']['ammo'] == 14
initial = json.loads((packet / 'initial-offline-trace/events.jsonl').read_text().splitlines()[0])
assert initial['initial_conditions'] == 'stock_spawns_teams_random_seeds'
assert initial['scenario'] == 'standard' and initial['prediction_enabled'] is False and initial['protocol'] == 6
assert initial['rules'] == {'buy_seconds':15.0, 'defuse_seconds':5.0, 'device_seconds':35.0, 'plant_seconds':3.0, 'round_seconds':100.0, 'win_score':7}
source = result['source']
assert all(source[k] == result['artifact_source'][k] for k in source)
assert source['source_dirty'] is False and source['source_game_dirty'] is False
assert subprocess.check_output(['git','rev-parse',source['source_commit']+':game'],cwd=ROOT,text=True).strip() == source['source_game_tree']
binary = ROOT / 'builds/focus-r1/linux/sightbreak.x86_64'
assert hashlib.sha256(binary.read_bytes()).hexdigest() == result['executable_sha256'] == result['artifact_source']['artifact']['sha256']
assert result['passed'] and result['native_focus_only'] and result['clean_exit'] and result['initial_exit'] == 0
assert result['cleanup_errors'] == [] and all(c['exit_code'] == 0 for c in result['commands'])
summary = {
    'passed': True,
    'scope': 'Retained source-bound Linux focus-only evidence; no new native launch or full-journey acceptance',
    'candidate_head': subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
    'native_source': source,
    'reconstructed_receipt_matches_all_four_hashes': True,
    'all_focus_receipts_equal_raw_actions': True,
    'held_samples': [{k:s[k] for k in ['wall_msec','simulation_tick','drawn_frames']} for s in held],
    'release_identity': {k:released[k] for k in ['wall_msec','simulation_tick','drawn_frames']},
    'movement_identity': {k:moved[k] for k in ['wall_msec','simulation_tick','drawn_frames']},
    'movement_metres': sum((a-b)**2 for a,b in zip(moved['local_actor']['position'],released['local_actor']['position']))**0.5,
    'display_limit': 'Raw PNGs show distinct rendered views; captures have no embedded simulation-tick identity. Fresh PNG health100 differs from authority82.74397 and does not establish numeric HUD synchronization.',
}
(HERE / 'focus-audit.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
