#!/usr/bin/env python3
"""Synthetic negative controls for the evidence validator; never match acceptance."""
from copy import deepcopy
import unittest

from test_account_match import RULES, verify_earned_payload, verify_match


def fixture():
    identities = [f'fictional-{i}' for i in range(10)]
    accounts = {str(i + 1): identity for i, identity in enumerate(identities)}
    bindings = {str(i + 100): i for i in range(1, 11)}
    base = dict(protocol=6, stock_rules=RULES.copy(), ranked_started=True, ranked_eligible=True,
                accounts=accounts, bindings=bindings, attack=0, defend=0, match_duration=523,
                match_id='synthetic-match', summary={'scoreboard': [dict(id=i, objectives=6 if i == 1 else 0, bot=False) for i in range(1, 11)]},
                activity_seconds={str(i): 520 for i in range(1, 11)},
                reward_status='eligible_pending_completion')
    transitions = [dict(base, phase='waiting', round=0, elapsed=0, ranked_started=False)]
    for number in range(1, 8):
        start = (number - 1) * 68
        score = {'attack': number - 1, 'defend': 0} if number <= 6 else {'attack': 0, 'defend': 6}
        transitions.extend([dict(base, **score, phase='buy', round=number, elapsed=start, objective='carried'),
                            dict(base, **score, phase='live', round=number, elapsed=start + 15, objective='carried')])
        if number <= 6:
            transitions.extend([dict(base, **score, phase='live', round=number, elapsed=start + 28, objective='planted'),
                                dict(base, attack=number, phase='post', round=number, elapsed=start + 63, objective='planted')])
    end = dict(base, attack=0, defend=7, phase='match_over', round=7, elapsed=523, reward_status='queued_for_delivery')
    transitions.append(end)
    clients = []
    for index in range(10):
        client_states = [dict(s, joined=True, connection='connected', initial_id=index + 1,
                             local_id=index + 1, display_name=f'Account Match {index}',
                             summary=dict(offline=False, rounds=7, attack_score=0, defend_score=7, won=index < 5, draw=False,
                                          objectives=6 if index == 0 else 0, kills=0, deaths=0, assists=0),
                             snapshots=1000, team=(0 if index < 5 else 1) if s['round'] <= 6 else (1 if index < 5 else 0))
                         for s in transitions if s['round'] >= 1]
        clients.append({'latest': client_states[-1], 'transitions': client_states})
    return deepcopy((dict(latest=end, transitions=transitions), clients, identities))


class EvidenceControls(unittest.TestCase):
    def setUp(self):
        self.server, self.clients, self.identities = fixture()

    def check(self):
        verify_match(self.server, self.clients, self.identities)

    def rejects(self):
        with self.assertRaises((AssertionError, KeyError, StopIteration)):
            self.check()

    def test_complete_synthetic_validator_control(self): self.check()

    def test_incomplete_match(self):
        self.server['latest']['phase'] = 'live'
        self.rejects()

    def test_short_match_or_activity(self):
        self.server['latest']['match_duration'] = 299
        self.rejects()
        self.setUp()
        self.server['latest']['activity_seconds']['1'] = 100
        self.rejects()

    def test_wrong_rules(self):
        self.server['latest']['stock_rules']['device'] = 1
        self.rejects()

    def test_lost_or_changed_identity(self):
        self.clients[0]['latest']['local_id'] = 2
        self.rejects()
        self.setUp()
        self.server['transitions'][2]['accounts']['1'] = 'other'
        self.rejects()

    def test_short_stock_fuse(self):
        self.server['transitions'][4]['elapsed'] -= 20
        self.rejects()

    def test_missing_round(self):
        self.server['transitions'] = [s for s in self.server['transitions'] if s['round'] != 3]
        self.rejects()

    def test_reconnect_ineligible_or_missing_replica_result(self):
        self.server['latest']['ranked_eligible'] = False
        self.rejects()
        self.setUp()
        self.clients[9]['latest']['reward_status'] = 'eligible_pending_completion'
        self.rejects()

    def test_missing_halftime(self):
        self.clients[0]['latest']['team'] = 0
        self.rejects()

    def test_premature_score(self):
        for state in self.server['transitions']:
            state['attack'], state['defend'] = 0, 7
        self.rejects()

    def test_missing_client_rounds(self):
        self.clients[0]['transitions'] = [self.clients[0]['latest']]
        self.rejects()

    def test_unrelated_activity_actor_keys(self):
        self.server['latest']['activity_seconds'] = {str(i): 520 for i in range(1000, 1010)}
        self.rejects()

    def test_contradictory_client_summary(self):
        self.clients[0]['latest']['summary'].update(won=False, draw=True, attack_score=99, defend_score=-5)
        self.rejects()

    def test_payload_awards_must_agree_with_observations(self):
        payload = dict(match_id='synthetic-match', mode='ranked_5v5', started_at='2026-10-22T00:00:00Z', ended_at='2026-10-22T00:10:00Z',
                       participants=[dict(player_id=identity, won=i < 5, active_seconds=520,
                                          objective_contributions=6 if i == 0 else 0, abandoned=False)
                                     for i, identity in enumerate(self.identities)])
        verify_earned_payload(payload, self.server, self.clients)
        for key, value in [('won', False), ('objective_contributions', 7), ('active_seconds', 599), ('abandoned', True)]:
            changed = deepcopy(payload)
            changed['participants'][0][key] = value
            with self.assertRaises(AssertionError):
                verify_earned_payload(changed, self.server, self.clients)


if __name__ == '__main__': unittest.main()
