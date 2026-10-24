#!/usr/bin/env python3
"""Source-state counterexamples; synthetic observations are never native proof."""
from copy import deepcopy
import unittest

from analyze_input_consumption import analyze
from test_input_consumption_lifecycle import restamp
from test_input_consumption_observation import control, declared_rows, text


def append_event(rows, reason, **updates):
    row = deepcopy(rows[-1])
    index, now = len(rows) + 1, row['wall_msec'] + 1000
    row.update(reason=reason, index=index, wall_msec=now,
               wall_unix_msec=100000 + now, process_frames=index,
               physics_frames=index * 2, drawn_frames=index)
    row['counters'][reason] = row['counters'].get(reason, 0) + 1
    if reason in row['latest']:
        row['latest'][reason]['wall_msec'] = now
    if row['snapshot']:
        row['snapshot_age_msec'] = now - row['snapshot']['wall_msec']
    row.update(updates)
    rows.append(row)
    return row


def second_peer(hidden_accept):
    rows = declared_rows('authority')
    for row in rows:
        for stage in ('input_received', 'input_accepted'):
            if stage in row['latest']:
                row['latest'][stage]['moving'] = 1
        if 'input_consumed' in row['latest']:
            row['latest']['input_consumed']['move'] = [1.0, 0.0]
        if row['reason'] in ('input_consumed', 'authority_tick'):
            row['actor']['input']['move'] = [1.0, 0.0]
    append_event(rows, 'peer_connected', peer=10, generation=2,
                 bound_actor=0, peer_bound=False, joined=False,
                 stream_ack=-1, queue_count=0)
    row = append_event(rows, 'peer_bound', bound_actor=2,
                       last_bound_actor=2, peer_bound=True, joined=True)
    row['actor'].update(id=2, input=control())
    row = append_event(rows, 'input_consumed', stream_ack=1)
    row['latest']['input_consumed'].update(peer=10, generation=2, actor=2,
                                          move=[-1.0, 0.0])
    row['actor']['input'] = {**control(1, True), 'move': [-1.0, 0.0]}
    if hidden_accept:
        for stage in ('input_received', 'input_accepted'):
            row['counters'][stage] = 2
            row['latest'][stage]['wall_msec'] = row['wall_msec'] - 1
    return rows


class InputObservationStateControls(unittest.TestCase):
    def report(self, rows, role='authority'):
        client = rows if role == 'client' else declared_rows('client')
        authority = rows if role == 'authority' else declared_rows('authority')
        return analyze(text(client), text(authority))

    def test_current_reason_must_increment_even_when_other_counters_advance(self):
        for role, reason in (('authority', 'authority_tick'), ('client', 'client_tick')):
            with self.subTest(role=role):
                rows = declared_rows(role)
                old = rows[-1]['counters'][reason]
                row = append_event(rows, reason)
                row['counters'][reason] = old
                self.assertFalse(self.report(rows, role)['diagnostic_complete'])

    def test_lifecycle_counters_cannot_claim_hidden_events(self):
        for stage in ('ready', 'peer_connected', 'peer_bound'):
            with self.subTest(stage=stage):
                rows = declared_rows('authority')
                for row in rows:
                    if stage in row['counters']:
                        row['counters'][stage] += 1
                self.assertFalse(self.report(rows)['diagnostic_complete'])

    def test_one_peer_cannot_gain_another_live_generation(self):
        rows = declared_rows('authority')
        append_event(rows, 'peer_connected', generation=2, joined=False)
        row = append_event(rows, 'peer_bound', bound_actor=2, last_bound_actor=2,
                           joined=True)
        row['actor']['id'] = 2
        self.assertFalse(self.report(rows)['diagnostic_complete'])

    def test_latest_cannot_disappear_or_change_without_a_call(self):
        for mutation in ('delete', 'change'):
            with self.subTest(mutation=mutation):
                rows = declared_rows('authority')
                if mutation == 'delete':
                    rows[-1]['latest'].pop('input_accepted')
                else:
                    rows[-1]['latest']['input_accepted']['fire'] = 0
                self.assertFalse(self.report(rows)['diagnostic_complete'])

    def test_counted_metadata_stage_requires_its_persistent_projection(self):
        rows = declared_rows('client')
        for row in rows:
            row['latest'].pop('welcome_received', None)
        self.assertFalse(self.report(rows, 'client')['diagnostic_complete'])

    def test_receive_outcome_counts_allow_only_current_receive_to_be_pending(self):
        rows = declared_rows('authority')
        rows[-1]['counters']['input_received'] += 1
        self.assertFalse(self.report(rows)['diagnostic_complete'])

    def test_another_accept_requires_another_receive_even_when_coalesced(self):
        rows = declared_rows('authority')
        row = append_event(rows, 'input_accepted', queue_count=1)
        self.assertFalse(self.report(rows)['diagnostic_complete'])

    def test_accepted_projection_matches_receive_but_timestamps_can_differ(self):
        rows = declared_rows('authority')
        self.assertLess(rows[4]['latest']['input_received']['wall_msec'],
                        rows[4]['latest']['input_accepted']['wall_msec'])
        self.assertTrue(self.report(rows)['diagnostic_complete'])
        rows[4]['latest']['input_accepted']['fire'] = 0
        self.assertFalse(self.report(rows)['diagnostic_complete'])

    def test_successful_accept_requires_nonempty_queue(self):
        rows = declared_rows('authority')
        rows[4]['queue_count'] = 0
        self.assertFalse(self.report(rows)['diagnostic_complete'])

    def test_direct_consumption_agrees_with_ack_and_all_actor_controls(self):
        for key, value in (('stream_ack', 0), ('sequence', 2), ('fire', False),
                           ('reload', True), ('move', [1.0, 0.0])):
            with self.subTest(key=key):
                rows = declared_rows('authority')
                if key == 'stream_ack':
                    rows[5][key] = value
                else:
                    rows[5]['actor']['input'][key] = value
                self.assertFalse(self.report(rows)['diagnostic_complete'])

    def test_fresh_peer_needs_acceptance_progress_but_not_a_direct_accept_row(self):
        negative, positive = self.report(second_peer(False)), self.report(second_peer(True))
        self.assertFalse(negative['diagnostic_complete'])
        self.assertTrue(positive['diagnostic_complete'], positive['errors'])
        self.assertEqual(len(positive['roles']['authority']['accepted_events']), 1)
        self.assertEqual(len(positive['roles']['authority']['consumed_events']), 2)

    def test_single_command_receive_endpoints_agree_before_validation(self):
        rows = declared_rows('authority')
        rows[3]['latest']['input_received'].update(first=-1, last=-9)
        self.assertFalse(self.report(rows)['diagnostic_complete'])

    def test_queued_duplicate_accepts_without_queue_growth_or_command_replacement(self):
        original = declared_rows('authority')
        duplicate = deepcopy(original[3:5])
        duplicate[0]['queue_count'] = 1
        for row in duplicate:
            for stage in ('input_received', 'input_accepted'):
                if stage in row['latest']:
                    row['latest'][stage]['fire'] = 0
        rows = restamp(original[:5] + duplicate + original[5:])
        self.assertEqual([row['queue_count'] for row in rows if row['reason'] == 'input_accepted'], [1, 1])
        self.assertTrue(rows[-2]['actor']['input']['fire'])
        report = self.report(rows)
        self.assertTrue(report['diagnostic_complete'], report['errors'])


if __name__ == '__main__':
    unittest.main()
