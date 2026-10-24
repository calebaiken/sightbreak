#!/usr/bin/env python3
"""Pure stream lifetime/projection controls; no engine or native qualification."""
from copy import deepcopy
import unittest

from analyze_input_consumption import analyze
from test_input_consumption_observation import control, declared_rows, text
from test_input_consumption_state import append_event


def packet(now, first=1, last=1, count=1, fire=1, epoch=1):
    return dict(epoch=epoch, count=count, first=first, last=last, fire=fire,
                reload=0, moving=0, wall_msec=now)


def second_accept(first, last=None, count=1):
    rows = declared_rows('authority')
    for reason in ('input_received', 'input_accepted'):
        row = append_event(rows, reason)
        row['latest'][reason] = packet(row['wall_msec'], first,
                                      first if last is None else last, count, count)
        if reason == 'input_accepted':
            row['queue_count'] = 1
    return rows


def rejected_then_valid(count=1, first=-9, last=-9):
    rows = declared_rows('authority')
    malformed = packet(rows[3]['wall_msec'], first, last, count, 0, -1)
    rows[3]['latest']['input_received'] = deepcopy(malformed)
    incoming = deepcopy(rows[3])
    incoming.update(wall_msec=8500, wall_unix_msec=108500, stream_rejected=1)
    incoming['counters'].update(input_received=2, input_stream_rejected=1)
    valid = packet(8500)
    rejected = deepcopy(malformed)
    rejected['wall_msec'] += 1
    incoming['latest'].update(input_received=deepcopy(valid),
                              input_stream_rejected=deepcopy(rejected))
    for row in rows[4:]:
        row['counters'].update(input_received=2, input_stream_rejected=1)
        row['stream_rejected'] = 1
        row['latest'].update(input_received=deepcopy(valid),
                             input_stream_rejected=deepcopy(rejected))
    rows.insert(4, incoming)
    for index, row in enumerate(rows, 1):
        row.update(index=index, process_frames=index, physics_frames=index * 2,
                   drawn_frames=index)
    return rows


def lobby_reset():
    rows = rejected_then_valid()
    append_event(rows, 'peer_disconnected')
    fresh_actor = deepcopy(rows[-1]['actor'])
    fresh_actor['input'] = control()
    # Guest reset replaces the stream, respawns the roster, then begins a round:
    # both reset_server_match and begin_round advance the epoch.
    append_event(rows, 'authority_tick', authority_epoch=3, stream_rejected=0,
                 stream_ack=-1, queue_count=0, bound_actor=0, peer_bound=False,
                 joined=False, generation=-1, actor=fresh_actor)
    return rows


def full_queue():
    rows = declared_rows('authority')[:3]
    for batch in range(10):
        for reason in ('input_received', 'input_accepted'):
            row = append_event(rows, reason)
            # Receive ten batches before the next physics step. Alternating
            # action aggregates force the direct receive/accept edge records.
            row.update(wall_msec=3000, wall_unix_msec=103000, process_frames=3,
                       physics_frames=6, drawn_frames=3)
            row['latest'][reason] = packet(row['wall_msec'], batch * 12 + 1,
                                          batch * 12 + 12, 12, 12 if batch % 2 else 0)
            if reason == 'input_accepted':
                row['queue_count'] = (batch + 1) * 12
    row = append_event(rows, 'input_consumed', stream_ack=119, queue_count=1,
                       stream_skipped=118)
    row.update(wall_msec=3001, wall_unix_msec=103001, process_frames=4,
               physics_frames=8, drawn_frames=4)
    # The tick observer runs before pop but coalesces only1ms after acceptance.
    row['counters']['authority_tick'] = 1
    # Backlog truncation keeps119/120, then pops119 from the final batch.
    row['latest']['input_consumed'] = {**control(119, True), 'peer': 9,
                                       'actor': 1, 'generation': 1,
                                       'wall_msec': row['wall_msec']}
    row['actor']['input'] = control(119, True)
    append_event(rows, 'authority_tick', process_frames=5, physics_frames=10,
                 drawn_frames=5)
    return rows


class InputObservationStreamControls(unittest.TestCase):
    def report(self, rows):
        return analyze(text(declared_rows('client')), text(rows))

    def test_single_command_is_fresh_and_inside_ack_window(self):
        for sequence, expected in ((1, False), (2, True), (121, True), (122, False)):
            with self.subTest(sequence=sequence):
                result = self.report(second_accept(sequence))
                self.assertEqual(result['diagnostic_complete'], expected, result['errors'])

    def test_only_fully_exposed_batches_need_a_fresh_endpoint(self):
        for first, last, count, expected in ((1, 1, 2, False), (2, 1, 2, True),
                                              (2, 2, 2, True), (1, 1, 3, True)):
            with self.subTest(first=first, last=last, count=count):
                # For count3, [acknowledged1, fresh2, acknowledged1] is legal.
                # Both exposed endpoints are stale; the middle is not reported.
                result = self.report(second_accept(first, last, count))
                self.assertEqual(result['diagnostic_complete'], expected, result['errors'])

    def test_queue_window_bound_includes_valid_full_queue_and_later_ticks(self):
        rows = full_queue()
        result = self.report(rows)
        self.assertTrue(result['diagnostic_complete'], result['errors'])
        self.assertEqual(max(row['queue_count'] for row in rows), 120)
        for index in (-3, -1):
            with self.subTest(index=index):
                altered = deepcopy(rows)
                altered[index]['queue_count'] = 121
                self.assertFalse(self.report(altered)['diagnostic_complete'])

    def test_empty_array_has_no_endpoints_but_nondictionaries_are_observable(self):
        for count, first, last, expected in ((0, -1, -1, True), (0, 21, 21, False),
                                               (0, -1, 21, False), (2, -1, -1, True)):
            with self.subTest(count=count, first=first, last=last):
                result = self.report(rejected_then_valid(count, first, last))
                self.assertEqual(result['diagnostic_complete'], expected, result['errors'])

    def test_rejection_state_and_calls_agree_in_both_directions(self):
        rows = declared_rows('authority')
        rows[-1]['stream_rejected'] = 1
        self.assertFalse(self.report(rows)['diagnostic_complete'])
        rows = rejected_then_valid()
        self.assertTrue(self.report(rows)['diagnostic_complete'])
        for row in rows:
            row['stream_rejected'] = 0
        self.assertFalse(self.report(rows)['diagnostic_complete'])

    def test_zero_peer_lobby_reset_retains_history_and_allows_new_rejections(self):
        rows = lobby_reset()
        result = self.report(rows)
        self.assertTrue(result['diagnostic_complete'], result['errors'])
        self.assertEqual(rows[-1]['counters']['input_stream_rejected'], 1)
        self.assertEqual(rows[-1]['stream_rejected'], 0)
        append_event(rows, 'peer_connected', generation=2)
        row = append_event(rows, 'peer_bound', bound_actor=1, peer_bound=True,
                           joined=True, actor=dict(id=1, alive=True, ammo=30,
                                                   reserve=90, reload=0.0, input=control()))
        row = append_event(rows, 'input_received')
        empty = packet(row['wall_msec'], -1, -1, 0, 0, 3)
        row['latest']['input_received'] = deepcopy(empty)
        row = append_event(rows, 'input_received', stream_rejected=1)
        row['counters']['input_stream_rejected'] = 2
        row['latest']['input_stream_rejected'] = deepcopy(empty)
        row['latest']['input_received'] = packet(row['wall_msec'], epoch=3)
        row = append_event(rows, 'input_accepted', queue_count=1)
        row['latest']['input_accepted'] = packet(row['wall_msec'], epoch=3)
        result = self.report(rows)
        self.assertTrue(result['diagnostic_complete'], result['errors'])
        self.assertEqual(rows[-1]['stream_rejected'], 1)
        self.assertEqual(rows[-1]['counters']['input_stream_rejected'], 2)

    def test_live_binding_round_epoch_change_keeps_rejection_state(self):
        rows = rejected_then_valid()
        append_event(rows, 'authority_tick', authority_epoch=2, stream_ack=-1,
                     queue_count=0)
        result = self.report(rows)
        self.assertTrue(result['diagnostic_complete'], result['errors'])
        rows[-1]['stream_rejected'] = 0
        self.assertFalse(self.report(rows)['diagnostic_complete'])

    def test_zero_peers_alone_cannot_explain_state_reset_without_epoch_advance(self):
        rows = lobby_reset()
        rows[-1]['authority_epoch'] = 1
        self.assertFalse(self.report(rows)['diagnostic_complete'])

    def test_hidden_metadata_calls_stay_inside_observed_time_interval(self):
        for offset, expected in ((-1, False), (0, True), (500, True), (1000, True)):
            with self.subTest(offset=offset):
                rows = declared_rows('authority')
                previous = rows[-1]['wall_msec']
                row = append_event(rows, 'authority_tick', queue_count=1)
                for reason in ('input_received', 'input_accepted'):
                    row['counters'][reason] += 1
                    row['latest'][reason] = packet(previous + offset, 2, 2)
                result = self.report(rows)
                self.assertEqual(result['diagnostic_complete'], expected, result['errors'])

    def test_unchanged_metadata_can_remain_older_than_current_interval(self):
        rows = declared_rows('authority')
        previous = rows[-1]['wall_msec']
        row = append_event(rows, 'authority_tick')
        self.assertLess(row['latest']['input_accepted']['wall_msec'], previous)
        result = self.report(rows)
        self.assertTrue(result['diagnostic_complete'], result['errors'])


if __name__ == '__main__':
    unittest.main()
