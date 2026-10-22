#!/usr/bin/env python3
"""Independent hostile observations; never a source of match acceptance."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[5]
if len(sys.argv) > 1:
    ROOT = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(ROOT / 'scripts'))
from test_account_match_output import fixture
from test_account_match import verify_match


def run(label, mutate):
    server, clients, identities = fixture()
    mutate(server, clients)
    try:
        verify_match(server, clients, identities)
    except (AssertionError, KeyError, StopIteration):
        return {'case': label, 'rejected': True}
    return {'case': label, 'rejected': False}


def premature_score(server, clients):
    for state in server['transitions']:
        state.update(attack=0, defend=7)


def missing_client_rounds(server, clients):
    for client in clients:
        client['transitions'] = [s for s in client['transitions'] if s['phase'] not in ('buy', 'live')]
        # Preserve the observed initial side so unrelated halftime validation can pass.
        first = dict(client['latest'], round=1, phase='post', team=0 if client['latest']['local_id'] <= 5 else 1)
        client['transitions'].insert(0, first)


cases = [
    ('premature_seven_wins_in_every_round_including_waiting', premature_score),
    ('client_has_never_observed_any_buy_or_live', missing_client_rounds),
    ('activity_for_ten_unrelated_actor_keys', lambda s, c: s['latest'].update(
        activity_seconds={str(i + 1000): 520 for i in range(10)})),
    ('client_summary_contradicts_winner_and_score', lambda s, c: c[0]['latest']['summary'].update(
        won=False, draw=True, attack_score=99, defend_score=-5)),
]
results = [run(label, mutate) for label, mutate in cases]
print(json.dumps(results, indent=2))
