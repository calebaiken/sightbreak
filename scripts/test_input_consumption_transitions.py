#!/usr/bin/env python3
"""Pure observation-transition controls; no native/source-readiness approval."""
from copy import deepcopy
import unittest

from analyze_input_consumption import analyze
from test_input_consumption_observation import control, declared_rows, text
from test_input_consumption_state import append_event, second_peer
from test_input_consumption_stream import packet


def hidden_accept(sequence=2, count=1, epoch=1, pop=False):
    rows = declared_rows('authority')
    row = append_event(rows, 'authority_tick', queue_count=0 if pop else 1)
    for stage in ('input_received', 'input_accepted'):
        row['counters'][stage] += 1
        row['latest'][stage] = packet(row['wall_msec'] - 2, sequence, sequence, count, 1, epoch)
    if pop:
        row['counters']['input_consumed'] += 1
        row['stream_ack'] = 2
        row['latest']['input_consumed'].update(sequence=2, wall_msec=row['wall_msec'] - 1)
        row['actor']['input'] = control(2, True)
    return rows


def two_queued_commands(popped=1):
    rows = declared_rows('authority')[:5]
    for reason in ('input_received', 'input_accepted'):
        row = append_event(rows, reason, queue_count=1 if reason == 'input_received' else 2,
                           wall_msec=9000, wall_unix_msec=109000,
                           process_frames=5, physics_frames=10, drawn_frames=5)
        row['latest'][reason] = packet(9000, 2, 2, fire=0)
    row = append_event(rows, 'input_consumed', stream_ack=popped, queue_count=1,
                       wall_msec=9001, wall_unix_msec=109001,
                       process_frames=6, physics_frames=12, drawn_frames=6)
    row['counters']['authority_tick'] = 1
    command = control(popped, popped == 1)
    row['latest']['input_consumed'] = {**command, 'peer': 9, 'actor': 1,
                                       'generation': 1, 'wall_msec': 9001}
    row['actor']['input'] = deepcopy(command)
    append_event(rows, 'authority_tick', process_frames=7, physics_frames=14, drawn_frames=7)
    return rows


def partially_known_queue(count=3, last=1, size=2, popped=1, skipped=0):
    rows = declared_rows('authority')
    for row in rows:
        for stage in ('input_received', 'input_accepted'):
            if stage in row['latest']:
                row['latest'][stage].update(count=count, last=last)
        if row['reason'] == 'input_accepted':
            row['queue_count'] = size
        if row['reason'] in ('input_consumed', 'authority_tick'):
            row.update(stream_ack=popped, queue_count=size-skipped-1, stream_skipped=skipped)
            row['latest']['input_consumed']['sequence'] = popped
            row['actor']['input']['sequence'] = popped
    return rows


def aggregate_pops(total_fire, first_fire, second_fire, hidden=False):
    rows = declared_rows('authority')[:5]
    for row in rows:
        for stage in ('input_received', 'input_accepted'):
            if stage in row['latest']:
                row['latest'][stage].update(count=2, first=1, last=2, fire=total_fire)
        if row['reason'] == 'input_accepted':
            row['queue_count'] = 2
    row = append_event(rows, 'input_consumed', stream_ack=1, queue_count=1,
                       wall_msec=9001, wall_unix_msec=109001)
    row['counters']['authority_tick'] = 1
    row['latest']['input_consumed'] = {**control(1, first_fire), 'peer':9,
                                       'actor':1, 'generation':1, 'wall_msec':9001}
    row['actor']['input'] = control(1, first_fire)
    row = append_event(rows, 'authority_tick' if hidden else 'input_consumed',
                       stream_ack=2, queue_count=0)
    row['counters'].update(input_consumed=2, authority_tick=3 if hidden else 2)
    row['latest']['input_consumed'].update(sequence=2, fire=second_fire,
                                          wall_msec=row['wall_msec']-500 if hidden else row['wall_msec'])
    row['actor']['input'] = control(2, second_fire)
    if not hidden:
        append_event(rows, 'authority_tick')
    return rows


class InputObservationTransitionControls(unittest.TestCase):
    def report(self, authority=None, client=None):
        return analyze(text(declared_rows('client') if client is None else client),
                       text(declared_rows('authority') if authority is None else authority))

    def test_snapshot_cache_aliases_counted_latest_and_survives_reconnect(self):
        for change in ('empty', 'time', 'header', 'before_first_count'):
            with self.subTest(change=change):
                rows = declared_rows('client')
                if change == 'before_first_count':
                    rows[0]['snapshot'] = dict(tick=50, epoch=1, own_ack=1, wall_msec=1000)
                    rows[0]['snapshot_age_msec'] = 0
                elif change == 'empty':
                    rows[-1].update(snapshot={}, snapshot_age_msec=-1)
                elif change == 'time':
                    rows[-1]['snapshot']['wall_msec'] += 1
                    rows[-1]['snapshot_age_msec'] -= 1
                else:
                    rows[-1]['snapshot']['own_ack'] += 1
                self.assertFalse(self.report(client=rows)['diagnostic_complete'])
        rows = declared_rows('client')
        row = append_event(rows, 'client_disconnected')
        self.assertEqual(row['snapshot'], row['latest']['snapshot_applied'])
        self.assertTrue(self.report(client=rows)['diagnostic_complete'])

    def test_new_counted_snapshot_updates_cache_and_latest_together(self):
        rows = declared_rows('client')
        row = append_event(rows, 'client_tick')
        row['counters']['snapshot_applied'] += 1
        row['snapshot'].update(tick=51, wall_msec=row['wall_msec'] - 1)
        row['snapshot_age_msec'] = 1
        row['latest']['snapshot_applied'] = deepcopy(row['snapshot'])
        self.assertTrue(self.report(client=rows)['diagnostic_complete'])

    def test_shared_accepted_validation_covers_hidden_calls(self):
        for sequence, count, epoch, expected in ((2, 1, 1, True), (1, 1, 1, False),
                                                   (122, 1, 1, False), (2, 1, 2, False),
                                                   (2, 13, 1, False), (1, 3, 1, True)):
            with self.subTest(sequence=sequence, count=count, epoch=epoch):
                result = self.report(authority=hidden_accept(sequence, count, epoch))
                self.assertEqual(result['diagnostic_complete'], expected, result['errors'])

    def test_hidden_accept_before_hidden_pop_uses_pre_pop_ack_interval(self):
        result = self.report(authority=hidden_accept(pop=True))
        self.assertTrue(result['diagnostic_complete'], result['errors'])
        self.assertEqual(len(result['roles']['authority']['accepted_events']), 1)
        self.assertEqual(len(result['roles']['authority']['consumed_events']), 1)
        self.assertFalse(self.report(authority=hidden_accept(sequence=1, pop=True))['diagnostic_complete'])
        rows = hidden_accept(sequence=122, count=3, pop=True)
        rows[-1]['stream_ack'] = 122
        rows[-1]['latest']['input_consumed']['sequence'] = 122
        rows[-1]['actor']['input']['sequence'] = 122
        # The sole later pop cannot lend its ACK to the earlier acceptance,
        # even when the batch hides middle command identities.
        self.assertFalse(self.report(authority=rows)['diagnostic_complete'])

    def test_same_stream_ack_and_queue_need_corresponding_calls(self):
        for changes in ({'stream_ack': 2}, {'stream_ack': 0}, {'stream_ack': -1},
                        {'queue_count': 1}):
            with self.subTest(changes=changes):
                rows = declared_rows('authority')
                append_event(rows, 'authority_tick', **changes)
                self.assertFalse(self.report(authority=rows)['diagnostic_complete'])
        rows = declared_rows('authority')
        append_event(rows, 'authority_tick')
        self.assertTrue(self.report(authority=rows)['diagnostic_complete'])

    def test_one_exposed_command_cannot_inflate_local_queue(self):
        for count in (2, 120):
            with self.subTest(queue=count):
                rows = declared_rows('authority')
                rows[4]['queue_count'] = count
                self.assertFalse(self.report(authority=rows)['diagnostic_complete'])

    def test_exposed_queue_pops_oldest_instead_of_latest_accepted_packet(self):
        result = self.report(authority=two_queued_commands())
        self.assertTrue(result['diagnostic_complete'], result['errors'])
        self.assertEqual(result['roles']['authority']['consumed_events'][0]['sequence'], 1)
        self.assertFalse(self.report(authority=two_queued_commands(2))['diagnostic_complete'])

    def test_queued_control_intent_is_immutable_when_its_signature_is_exposed(self):
        rows = two_queued_commands()
        for row in rows:
            if 'input_consumed' in row['latest']:
                row['latest']['input_consumed']['fire'] = False
                row['actor']['input']['fire'] = False
        self.assertFalse(self.report(authority=rows)['diagnostic_complete'])

    def test_multi_peer_forced_flow_passes_but_ambiguous_header_is_unknown(self):
        rows = second_peer(True)
        self.assertTrue(self.report(authority=rows)['diagnostic_complete'])
        row = append_event(rows, 'authority_tick', queue_count=1)
        for stage in ('input_received', 'input_accepted'):
            row['counters'][stage] += 2
            row['latest'][stage] = packet(row['wall_msec'] - 1, 2, 2, fire=1)
        result = self.report(authority=rows)
        self.assertFalse(result['diagnostic_complete'])
        self.assertEqual(result.get('transition_status'), 'UNKNOWN')
        client = declared_rows('client')
        client[-1]['snapshot']['own_ack'] += 1
        self.assertEqual(self.report(authority=rows, client=client).get('transition_status'), 'INVALID')

    def test_new_coalesced_consumed_metadata_needs_its_explicit_live_identity(self):
        rows = hidden_accept(pop=True)
        rows[-1]['latest']['input_consumed']['actor'] = 2
        self.assertFalse(self.report(authority=rows)['diagnostic_complete'])

    def test_unknown_middle_does_not_erase_definite_endpoint_order(self):
        self.assertTrue(self.report(authority=partially_known_queue())['diagnostic_complete'])
        self.assertFalse(self.report(authority=partially_known_queue(popped=2))['diagnostic_complete'])

    def test_large_duplicate_batch_cannot_erase_earlier_immutable_intent(self):
        rows = declared_rows('authority')[:5]
        for reason in ('input_received', 'input_accepted'):
            row = append_event(rows, reason, queue_count=1)
            row['latest'][reason] = packet(row['wall_msec'], 1, 1, 3, 0)
        now = rows[-1]['wall_msec'] + 1
        row = append_event(rows, 'input_consumed', stream_ack=1, queue_count=0,
                           wall_msec=now, wall_unix_msec=100000+now)
        row['counters']['authority_tick'] = 1
        row['latest']['input_consumed'] = {**control(1, True), 'peer':9,
                                           'generation':1, 'actor':1, 'wall_msec':row['wall_msec']}
        row['actor']['input'] = control(1, True)
        append_event(rows, 'authority_tick')
        self.assertTrue(self.report(authority=rows)['diagnostic_complete'])
        for row in rows[-2:]:
            row['latest']['input_consumed']['fire'] = False
            row['actor']['input']['fire'] = False
        self.assertFalse(self.report(authority=rows)['diagnostic_complete'])

    def test_observed_empty_queue_recovers_exactness_after_unknown_middle(self):
        rows = partially_known_queue()
        now = rows[-1]['wall_msec']
        row = append_event(rows, 'input_consumed', stream_ack=2, queue_count=0,
                           wall_msec=now, wall_unix_msec=100000+now)
        row['latest']['input_consumed'].update(sequence=2, fire=False, wall_msec=now)
        row['actor']['input'] = control(2, False)
        self.assertTrue(self.report(authority=rows)['diagnostic_complete'])
        row = append_event(rows, 'authority_tick')
        for stage in ('input_received', 'input_accepted'):
            row['counters'][stage] += 1
            row['latest'][stage] = packet(row['wall_msec'], 3, 3)
        self.assertFalse(self.report(authority=rows)['diagnostic_complete'])

    def test_backlog_order_statistics_hold_without_middle_command_bodies(self):
        positive = self.report(authority=partially_known_queue(7, 7, 7, 6, 5))
        self.assertTrue(positive['diagnostic_complete'], positive['errors'])
        self.assertFalse(self.report(authority=partially_known_queue(7, 7, 7, 5, 5))['diagnostic_complete'])

    def test_explicit_unselected_pop_is_inferred_when_prior_state_proves_it(self):
        rows = hidden_accept()
        row = append_event(rows, 'peer_connected', peer=10, generation=2,
                           bound_actor=0, peer_bound=False, joined=False,
                           stream_ack=-1, queue_count=0)
        row['counters']['input_consumed'] += 1
        row['latest']['input_consumed'].update(sequence=2, wall_msec=row['wall_msec']-1)
        row['actor']['input'] = control(2, True)
        row = append_event(rows, 'peer_bound', bound_actor=2, last_bound_actor=2,
                           peer_bound=True, joined=True)
        row['actor'].update(id=2, input=control())
        result = self.report(authority=rows)
        self.assertTrue(result['diagnostic_complete'], result['errors'])

    def test_receipt_aggregate_retains_one_joint_payload_history_across_pops(self):
        for total, first, second, hidden, expected in (
                (1,False,True,False,True), (1,False,False,False,False),
                (1,True,True,False,False), (1,False,False,True,False),
                (1,True,True,True,False), (0,False,False,True,True),
                (2,True,True,True,True)):
            with self.subTest(total=total, first=first, second=second, hidden=hidden):
                result = self.report(authority=aggregate_pops(total, first, second, hidden))
                self.assertEqual(result['diagnostic_complete'], expected, result['errors'])

    def test_epoch_boundary_uses_acceptance_epoch_and_preserves_new_receipts(self):
        for accepted_epoch, queued, expected in ((1,0,True), (1,1,False),
                                                 (2,1,True), (2,0,False), (3,0,False)):
            with self.subTest(accepted_epoch=accepted_epoch, queued=queued):
                rows = declared_rows('authority')
                row = append_event(rows, 'authority_tick', authority_epoch=2,
                                   stream_ack=-1, queue_count=queued)
                row['actor']['input'] = control()
                for stage in ('input_received', 'input_accepted'):
                    row['counters'][stage] += 1
                    row['latest'][stage] = packet(row['wall_msec']-1,
                                                  2 if accepted_epoch == 1 else 1,
                                                  2 if accepted_epoch == 1 else 1,
                                                  epoch=accepted_epoch)
                result = self.report(authority=rows)
                self.assertEqual(result['diagnostic_complete'], expected, result['errors'])
                if expected and accepted_epoch == 2:
                    row = append_event(rows, 'input_consumed', stream_ack=1, queue_count=0)
                    row['latest']['input_consumed'].update(sequence=1)
                    row['actor']['input'] = control(1, True)
                    self.assertTrue(self.report(authority=rows)['diagnostic_complete'])

if __name__ == '__main__':
    unittest.main()
