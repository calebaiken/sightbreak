"""Operation-derived interval witnesses; no native or whole-fixture provenance.

The fixed amended seed and synthetic frame/resource/client fields retain their
existing limits. Every added tick below completes the ordered peer-pop loop.
"""
from copy import deepcopy
import itertools
import unittest

import analyze_input_consumption as reader
from test_input_consumption_deterministic_phase import TimedAuthority
from test_input_consumption_observation import declared_rows, text


class CompleteAuthority(TimedAuthority):
    def complete_tick(self, now):
        self.tick(now)
        for peer, entry in self.peers.items():
            queue = self.queues[peer]
            if not entry['actor'] or not queue:
                continue
            ordered = sorted(queue)
            if len(ordered) > 6:
                while len(ordered) > 2:
                    del queue[ordered.pop(0)]
                    self.skipped += 1
            sequence = ordered[0]
            command = queue.pop(sequence)
            self.acks[peer] = sequence
            self.actors[entry['actor']]['input'] = deepcopy(command)
            self._hook('input_consumed', now, peer,
                       dict(command, peer=peer, actor=entry['actor'],
                            generation=entry['generation']))

    def select(self, peer, now):
        # This hook changes sticky selection but does not mutate the stream.
        self._hook('input_gate_rejected', now, peer)


def uncertain_history(*, switch=False, sequence=2, phase=0):
    model = CompleteAuthority()
    model.connect(10, 11200)
    model.bind(10, 2, 11300)
    model.rpc(9, sequence, 11400, 11400+phase)
    model.rpc(10, 1, 11500, 11500+phase)
    model.complete_tick(13000)
    model.select(9, 13100)
    model.complete_tick(14500)
    if switch:
        model.select(10, 14600)
        model.complete_tick(16000)
        model.select(9, 16100)
        model.complete_tick(17500)
    else:
        model.complete_tick(16000)
    return model


class IntervalNecessities(unittest.TestCase):
    def analyze(self, rows):
        original = deepcopy(rows)
        for row in rows:
            reader.record_valid(row)
        result = reader.analyze(text(declared_rows('client')), text(rows))
        self.assertEqual(rows, original)
        return result['transition_status']

    def test_complete_callback_keeps_original_ownership_unknown(self):
        model = uncertain_history()
        self.assertEqual(model.acks, {9: 2, 10: 1})
        self.assertTrue(all(not queue for queue in model.queues.values()))
        self.assertEqual(self.analyze(model.rows), 'UNKNOWN')

    def test_three_sealed_contradictions_reject_after_unknown(self):
        rows = uncertain_history().rows
        for field, value in (('stream_ack', -1), ('stream_ack', 1), ('queue_count', 1)):
            with self.subTest(field=field, value=value):
                bad = deepcopy(rows)
                bad[-1][field] = value
                self.assertEqual(self.analyze(bad), 'INVALID')

    def test_generated_selection_phase_and_sequence_gap_siblings(self):
        # Sequence gaps are legal: no count-derived ACK-jump upper bound.
        witnesses = negatives = 0
        for switch, sequence, phase in itertools.product((False, True), (2, 12, 62, 121), (0, 1)):
            with self.subTest(switch=switch, sequence=sequence, phase=phase):
                rows = uncertain_history(switch=switch, sequence=sequence, phase=phase).rows
                self.assertEqual(self.analyze(rows), 'UNKNOWN')
                witnesses += 1
                for field, value in (('stream_ack', -1), ('stream_ack', sequence-1),
                                     ('stream_ack', sequence+1), ('queue_count', 1)):
                    bad = deepcopy(rows)
                    bad[-1][field] = value
                    self.assertEqual(self.analyze(bad), 'INVALID')
                    negatives += 1
        self.assertEqual((witnesses, negatives), (16, 64))

    def test_later_new_acceptance_can_grow_queue_and_pending_receive_cannot_shrink_it(self):
        model = uncertain_history()
        model.rpc(9, 3, 16200, 16201, fire=False)
        self.assertEqual(model.rows[-1]['queue_count'], 1)
        self.assertEqual(self.analyze(model.rows), 'UNKNOWN')
        model.receive(9, 4, 16300, fire=True)
        self.assertEqual(model.rows[-1]['reason'], 'input_received')
        self.assertEqual(self.analyze(model.rows), 'UNKNOWN')
        bad = deepcopy(model.rows)
        bad[-1]['queue_count'] = 0
        self.assertEqual(self.analyze(bad), 'INVALID')
        model.outcome(16301)
        model.complete_tick(18000)
        self.assertEqual(self.analyze(model.rows), 'UNKNOWN')

    def test_queued_duplicate_acceptance_need_not_grow_queue(self):
        model = uncertain_history()
        model.rpc(9, 3, 16200, 16200, fire=False)
        model.rpc(9, 3, 16300, 16301, fire=True)
        self.assertEqual(model.rows[-1]['queue_count'], 1)
        self.assertEqual(self.analyze(model.rows), 'UNKNOWN')
        model.complete_tick(18000)
        self.assertEqual(self.analyze(model.rows), 'UNKNOWN')

    def test_latest_consumption_of_selected_stream_binds_ack(self):
        model = uncertain_history()
        model.rpc(9, 3, 16200, 16200, fire=False)
        model.complete_tick(18000)
        self.assertEqual(model.rows[-1]['reason'], 'input_consumed')
        self.assertEqual(self.analyze(model.rows), 'UNKNOWN')
        bad = deepcopy(model.rows)
        bad[-1]['stream_ack'] = 4
        self.assertEqual(self.analyze(bad), 'INVALID')

    def test_coalesced_latest_pop_still_binds_later_observed_ack(self):
        model = uncertain_history()
        model.rpc(9, 3, 16200, 16200)
        model.complete_tick(18000)
        model.complete_tick(19500)
        self.assertEqual(model.rows[-1]['reason'], 'authority_tick')
        self.assertEqual(model.rows[-1]['latest']['input_consumed']['sequence'], 3)
        self.assertEqual(self.analyze(model.rows), 'UNKNOWN')
        bad = deepcopy(model.rows)
        bad[-1]['stream_ack'] = 4
        self.assertEqual(self.analyze(bad), 'INVALID')

    def test_backlog_discard_and_remaining_queue_have_conservative_global_bounds(self):
        model = uncertain_history()
        for sequence in range(3, 11):
            model.rpc(9, sequence, 16200+sequence*20, 16200+sequence*20)
        model.complete_tick(18000)
        model.complete_tick(19500)
        self.assertEqual(model.rows[-1]['stream_skipped'], 6)
        self.assertEqual(model.rows[-1]['stream_ack'], 9)
        self.assertEqual(model.rows[-1]['queue_count'], 1)
        self.assertEqual(self.analyze(model.rows), 'UNKNOWN')
        bad = deepcopy(model.rows)
        bad[-1]['queue_count'] = 0
        self.assertEqual(self.analyze(bad), 'INVALID')

    def test_observed_disconnect_reset_and_new_generation_can_restart_sequence(self):
        model = uncertain_history()
        model.disconnect(9, 16200)
        model.disconnect(10, 16300)
        model.reset_empty_guest(18000)
        model.connect(9, 18100)
        model.bind(9, 3, 18200)
        model.rpc(9, 1, 18300, 18300, fire=False)
        model.complete_tick(20000)
        model.complete_tick(21500)
        self.assertEqual(model.epoch, 3)
        self.assertEqual(model.peers[9]['generation'], 3)
        self.assertEqual(model.rows[-1]['stream_ack'], 1)
        self.assertEqual(self.analyze(model.rows), 'UNKNOWN')


if __name__ == '__main__':
    unittest.main()
