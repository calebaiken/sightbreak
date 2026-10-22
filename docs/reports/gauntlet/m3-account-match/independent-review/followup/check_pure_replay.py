#!/usr/bin/env python3
"""Independent replay and counterexamples for post-run pure validators only."""
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

source = Path(sys.argv[1]).resolve()
archive = Path(sys.argv[2]).resolve()
sys.path.insert(0, str(source / 'scripts'))
from test_account_match import verify_earned_payload, verify_match
from test_account_match_output import fixture

server = json.loads((archive / 'completed-server.json').read_text())
clients = [json.loads((archive / f'completed-client-{i}.json').read_text()) for i in range(10)]
payload = json.loads((archive / 'earned-result.json').read_text())
identities = list(server['latest']['accounts'].values())
verify_match(server, clients, identities)
verify_earned_payload(payload, server, clients)


def swapped_winners(p, s, c):
    p['participants'][0]['won'], p['participants'][5]['won'] = False, True


def swapped_objectives(p, s, c):
    p['participants'][0]['objective_contributions'], p['participants'][1]['objective_contributions'] = 0, 6


def bot(p, s, c):
    s['latest']['summary']['scoreboard'][0]['bot'] = True


def combat(p, s, c):
    c[0]['latest']['summary']['kills'] = 1


negative = []
for label, mutation in [('swapped_winners_preserve_five', swapped_winners),
                        ('swapped_objectives_preserve_six', swapped_objectives),
                        ('bot_in_server_scoreboard', bot), ('client_combat', combat)]:
    p, s, c = deepcopy((payload, server, clients))
    mutation(p, s, c)
    try:
        verify_earned_payload(p, s, c)
    except (AssertionError, KeyError, StopIteration):
        negative.append(dict(case=label, rejected=True))
    else:
        negative.append(dict(case=label, rejected=False))
assert all(r['rejected'] for r in negative)

synthetic_server, synthetic_clients, synthetic_ids = fixture()
end = synthetic_server['latest']
end['elapsed'] = 523.0
end['summary']['duration'] = 523.0
end['match_duration'] = 519.9999999999999
end['activity_seconds'] = {str(i): 520.0000000000001 for i in range(1, 11)}
terminal = end['match_duration'] - (end['elapsed'] - end['summary']['duration'])
active = min(int(terminal), int(end['activity_seconds']['1']))
synthetic_payload = dict(match_id=end['match_id'], mode='ranked_5v5',
                         started_at='2026-10-22T00:00:00Z', ended_at='2026-10-22T00:10:00Z',
                         participants=[dict(player_id=identity, won=i < 5, active_seconds=active,
                                            objective_contributions=6 if i == 0 else 0, abandoned=False)
                                       for i, identity in enumerate(synthetic_ids)])
try:
    verify_earned_payload(synthetic_payload, synthetic_server, synthetic_clients)
except AssertionError:
    boundary_accepted = False
else:
    boundary_accepted = True
result = dict(checked_at_utc=datetime.now(timezone.utc).isoformat(),
              source_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=source, text=True).strip(),
              native_execution_source='471fbd8fe17611c0c93728bc571ea6158838b458',
              archived_verify_match='passed', archived_verify_earned_payload='passed',
              negative_mutations=negative,
              truncation_boundary=dict(terminal_duration=terminal, activity=end['activity_seconds']['1'],
                                       production_expected_active=active, accepted=boundary_accepted),
              scope='Pure Python validation and archived-byte replay only; no native execution')
print(json.dumps(result, indent=2))
