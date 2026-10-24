# Proposal evidence only; original maintained test source remains unchanged.
from copy import deepcopy
from pathlib import Path
import hashlib,json,unittest
from analyze_input_consumption import analyze,record_valid
from test_input_consumption_observation import declared_rows,text
def versioned_rows():
    raw=Path(__file__).with_name('versioned-rows.json').read_bytes()
    assert hashlib.sha256(raw).hexdigest()=='8a25d86941a97d659183e4c690aaa5e5fbfc416a4af85aed583ae919c1fa3f22'
    return json.loads(raw)
class ProposalOnlyControl(unittest.TestCase):

    def test_definite_prefix_faults_are_not_hidden_by_unknown_lifecycle(self):
        unresolved = versioned_rows()
        control = analyze(text(declared_rows('client')), text(unresolved))
        self.assertEqual(control['transition_status'], 'UNKNOWN', control)
        mutations = {'process-frame': lambda row: row.update(process_frames=1), 'physics-frame': lambda row: row.update(physics_frames=1), 'drawn-frame': lambda row: row.update(drawn_frames=1), 'index': lambda row: row.update(index=9), 'counter-regression': lambda row: row['counters'].update(input_received=1, input_accepted=1), 'unobserved-lifecycle': lambda row: row['counters'].update(peer_connected=2), 'stale-latest': lambda row: row['latest']['input_received'].update(wall_msec=1)}
        for label, mutate in mutations.items():
            rows = deepcopy(unresolved)
            mutate(rows[-1])
            before = deepcopy(rows)
            with self.subTest(case=label):
                for row in rows:
                    record_valid(row)
                result = analyze(text(declared_rows('client')), text(rows))
                self.assertEqual(result['transition_status'], 'INVALID', result)
                self.assertEqual(rows, before)
