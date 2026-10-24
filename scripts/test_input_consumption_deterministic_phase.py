"""Frozen R5 operation witnesses and contradictions; pure source scope only.

These constructors do not repair supplied rows. They extend the exact amended
declared baseline with named source operations at explicit wall clocks. Engine
frames, actor resources and client rows remain synthetic and unqualified.
"""
from copy import deepcopy
import unittest

from test_input_consumption_observation import control, declared_rows, text


def packet(sequence, fire=True, epoch=1):
    return dict(epoch=epoch, count=1, first=sequence, last=sequence,
                fire=int(fire), reload=0, moving=0)


class TimedAuthority:
    """Small forward operation witness, not an arbitrary-row normalizer.

    Fixed seed: C9=2000, A9=3000, accepted activity=9000, D9=22000,
    ACK9=1, queue9 empty. Only single-command packets are generated. Explicit
    rejection uses a wrong epoch, so its source outcome requires no packet-body
    inference. Hook suppression follows the fixed observer's aggregate edges.
    """
    def __init__(self):
        self.rows = deepcopy(declared_rows('authority'))
        self.template = deepcopy(self.rows[-1])
        self.counters = deepcopy(self.rows[-1]['counters'])
        self.latest = deepcopy(self.rows[-1]['latest'])
        self.peers = {9: dict(generation=1, deadline=22000, last=9000,
                             joined=True, actor=1)}
        self.actors = {1: deepcopy(self.rows[-1]['actor'])}
        self.queues, self.acks = {9: {}}, {9: 1}
        self.generation = self.epoch = 1
        self.selected, self.sticky = 9, 1
        self.clock = self.last_emit = 11000
        self.rejected = self.skipped = 0
        self.tick_number = self.rows[-1]['simulation_tick']
        self.edges = {'input_received': (1, 0, 0),
                      'input_accepted': (1, 0, 0),
                      'input_consumed': (True, False, (0.0, 0.0))}
        self.pending = None
        self.operations = [dict(operation='seed', connected=2000, admitted=3000,
                                active=9000, deadline=22000, ack=1)]

    def _hook(self, reason, now, peer=0, value=None):
        assert type(now) is int and now >= self.clock
        self.clock = now
        self.counters[reason] = self.counters.get(reason, 0) + 1
        if peer:
            self.selected = peer
            if self.peers.get(peer, {}).get('actor'):
                self.sticky = self.peers[peer]['actor']
        if value is not None:
            self.latest[reason] = dict(deepcopy(value), wall_msec=now)
        if reason in ('input_received', 'input_accepted'):
            edge = tuple(value[k] for k in ('fire', 'reload', 'moving'))
        elif reason == 'input_consumed':
            edge = (value['fire'], value['reload'], tuple(value['move']))
        else:
            edge = None
        changed = edge != self.edges.get(reason)
        self.edges[reason] = edge
        lifecycle = reason in ('peer_connected', 'peer_bound', 'peer_disconnected')
        direct_control = reason in ('input_received', 'input_accepted', 'input_consumed') and changed
        emitted = lifecycle or direct_control or (reason == 'authority_tick' and now-self.last_emit >= 1000)
        self.operations.append(dict(operation='hook', reason=reason, now=now,
                                    peer=peer, emitted=emitted))
        if not emitted:
            return None
        entry = self.peers.get(self.selected)
        actor = entry['actor'] if entry else 0
        row = deepcopy(self.template)
        index = len(self.rows)+1
        row.update(reason=reason, index=index, wall_msec=now,
                   wall_unix_msec=100000+now, process_frames=now,
                   physics_frames=now*2, drawn_frames=now,
                   peer=self.selected, generation=entry['generation'] if entry else -1,
                   joined=entry['joined'] if entry else False,
                   bound_actor=actor, peer_bound=actor > 0,
                   last_bound_actor=self.sticky,
                   input_age_msec=now-entry['last'] if entry else -1,
                   deadline_remaining_msec=entry['deadline']-now if entry else -1,
                   authority_epoch=self.epoch, simulation_tick=self.tick_number,
                   stream_ack=self.acks.get(self.selected, -1),
                   queue_count=len(self.queues.get(self.selected, {})),
                   stream_rejected=self.rejected, stream_skipped=self.skipped,
                   counters=deepcopy(self.counters), latest=deepcopy(self.latest),
                   actor=deepcopy(self.actors.get(self.sticky, {})))
        self.rows.append(row)
        self.last_emit = now
        return row

    def connect(self, peer, now):
        assert self.pending is None and peer not in self.peers and len(self.peers) < 10
        self.generation += 1
        self.peers[peer] = dict(generation=self.generation, deadline=now+20000,
                                last=now, joined=False, actor=0)
        self.queues[peer] = {}
        self.operations.append(dict(operation='connected', peer=peer, now=now))
        return self._hook('peer_connected', now, peer)

    def bind(self, peer, actor, now):
        assert self.pending is None and not self.peers[peer]['joined']
        assert now < self.peers[peer]['deadline']
        assert actor not in [p['actor'] for p in self.peers.values()]
        self.peers[peer].update(joined=True, actor=actor, last=now)
        self.actors[actor] = dict(deepcopy(self.template['actor']), id=actor, input=control())
        self.operations.append(dict(operation='admitted', peer=peer, actor=actor, now=now))
        return self._hook('peer_bound', now, peer)

    def receive(self, peer, sequence, now, fire=True, reject=False):
        assert self.pending is None and self.peers[peer]['joined']
        assert now-self.peers[peer]['last'] < 30000
        value = packet(sequence, fire, self.epoch+1 if reject else self.epoch)
        self.pending = (peer, sequence, fire, reject, value)
        return self._hook('input_received', now, peer, value)

    def outcome(self, now):
        assert self.pending is not None
        peer, sequence, fire, reject, value = self.pending
        self.pending = None
        if reject:
            self.rejected += 1
            return self._hook('input_stream_rejected', now, peer, value)
        assert self.acks.get(peer, 0) < sequence <= self.acks.get(peer, 0)+120
        self.queues[peer].setdefault(sequence, control(sequence, fire))
        assert now-self.peers[peer]['last'] < 30000
        self.peers[peer]['last'] = now
        self.operations.append(dict(operation='active', peer=peer, now=now))
        return self._hook('input_accepted', now, peer, value)

    def rpc(self, peer, sequence, receive_at, outcome_at, fire=True, reject=False):
        self.receive(peer, sequence, receive_at, fire, reject)
        self.outcome(outcome_at)

    def tick(self, now):
        assert self.pending is None
        self.tick_number += 1
        return self._hook('authority_tick', now)

    def pop(self, peer, now):
        assert self.pending is None and self.queues[peer]
        self.tick(now)
        assert len(self.queues[peer]) <= 6  # This witness never truncates backlog.
        sequence = min(self.queues[peer])
        command = self.queues[peer].pop(sequence)
        self.acks[peer] = sequence
        actor = self.peers[peer]['actor']
        self.actors[actor]['input'] = deepcopy(command)
        value = dict(command, peer=peer, generation=self.peers[peer]['generation'], actor=actor)
        return self._hook('input_consumed', now, peer, value)

    def disconnect(self, peer, now):
        assert self.pending is None
        row = self._hook('peer_disconnected', now, peer)
        self.peers.pop(peer)
        self.queues.pop(peer, None)
        self.acks.pop(peer, None)
        return row

    def reset_empty_guest(self, now):
        assert not self.peers and self.pending is None
        # Match replaces InputStream and calls begin_round; each advances epoch.
        self.epoch += 2
        self.rejected = self.skipped = 0
        self.acks.clear()
        self.queues.clear()
        for actor in self.actors.values():
            actor['input'] = control()
        self.operations.append(dict(operation='empty_guest_reset', now=now, epoch=self.epoch))
        return self.tick(now)


def anonymous_parent(two_peers=False):
    model = TimedAuthority()
    if two_peers:
        model.connect(10, 11200)
        model.bind(10, 2, 11300)
    model.rpc(9, 2, 11400, 11401)  # Same aggregate edges: RX/A are coalesced.
    if two_peers:
        model.rpc(10, 1, 11500, 11501)
    model.tick(12501)
    return model


class DeterministicAuthorityPhaseControls(unittest.TestCase):
    def report(self, rows):
        # Candidate imports occur only when a frozen test is explicitly run.
        from analyze_input_consumption import analyze
        return analyze(text(declared_rows('client')), text(rows))

    def status(self, rows, expected):
        before = deepcopy(rows)
        result = self.report(rows)
        self.assertEqual(result['transition_status'], expected, result)
        self.assertEqual(result['diagnostic_complete'], expected == 'CONSISTENT', result)
        self.assertEqual(rows, before)
        return result

    def test_direct_synchronous_receive_pending_and_acceptance_balance(self):
        model = TimedAuthority()
        model.receive(9, 2, 11200, fire=False)
        self.status(model.rows, 'CONSISTENT')  # A source cut inside _input_rpc.
        model.outcome(11201)
        self.status(model.rows, 'CONSISTENT')
        self.assertEqual(model.rows[-1]['counters']['input_received'], 2)
        for stage in ('input_received', 'input_accepted', 'input_stream_rejected'):
            altered = deepcopy(model.rows)
            altered[-1]['counters'][stage] = altered[-1]['counters'].get(stage, 0)+1
            if stage == 'input_stream_rejected':
                altered[-1]['latest'][stage] = dict(packet(2, False, 2), wall_msec=11201)
                altered[-1]['stream_rejected'] += 1
            with self.subTest(stage=stage):
                self.status(altered, 'INVALID')

    def test_direct_outcome_pairs_its_exact_receive_ordinal(self):
        model = TimedAuthority()
        model.rpc(9, 2, 11200, 11201, fire=False)
        self.status(model.rows, 'CONSISTENT')
        for field, value in (('first', 3), ('last', 3), ('fire', 1)):
            altered = deepcopy(model.rows)
            altered[-1]['latest']['input_accepted'][field] = value
            with self.subTest(field=field):
                self.status(altered, 'INVALID')

    def test_hidden_rejection_preserves_source_timers_and_exact_receive(self):
        model = TimedAuthority()
        model.rpc(9, 2, 11200, 11201, fire=False, reject=True)
        model.tick(12201)
        self.status(model.rows, 'CONSISTENT')
        self.assertEqual(model.rows[-1]['input_age_msec'], 3201)
        for field, value in (('first', 3), ('epoch', 1), ('fire', 1)):
            altered = deepcopy(model.rows)
            altered[-1]['latest']['input_stream_rejected'][field] = value
            with self.subTest(field=field):
                self.status(altered, 'INVALID')

    def test_sole_hidden_acceptance_pairs_known_receive_without_certifying_activity(self):
        model = TimedAuthority()
        model.rpc(9, 2, 11200, 11201, fire=False, reject=True)
        model.tick(12201)
        model.rpc(9, 2, 12300, 12301)  # RX changes, A aggregate remains fire1.
        model.tick(13301)
        self.status(model.rows, 'UNKNOWN')
        for field, value in (('first', 3), ('last', 3), ('fire', 0)):
            altered = deepcopy(model.rows)
            altered[-1]['latest']['input_accepted'][field] = value
            with self.subTest(field=field):
                self.status(altered, 'INVALID')
        altered = deepcopy(model.rows)
        # Same header, but it cannot be accepted before its observed receive.
        altered[-1]['latest']['input_accepted']['wall_msec'] = 12299
        self.status(altered, 'INVALID')

    def test_same_kind_hidden_outcomes_pair_final_ordinal_not_first_known_receive(self):
        for reject in (False, True):
            model = TimedAuthority()
            if not reject:
                model.rpc(9, 2, 11200, 11201, fire=False, reject=True)
                model.tick(12201)
                start = 12300
            else:
                start = 11200
            model.rpc(9, 2, start, start+1, fire=not reject, reject=reject)
            model.rpc(9, 3, start+2, start+3, fire=not reject, reject=reject)
            model.tick(start+1003)
            with self.subTest(reject=reject):
                self.status(model.rows, 'CONSISTENT' if reject else 'UNKNOWN')
                stage = 'input_stream_rejected' if reject else 'input_accepted'
                self.assertEqual(model.rows[-1]['latest'][stage]['first'], 3)
                altered = deepcopy(model.rows)
                altered[-1]['latest'][stage].update(first=2, last=2)
                self.status(altered, 'INVALID')

    def test_mixed_hidden_kinds_do_not_compare_unrelated_latest_packets(self):
        model = TimedAuthority()
        model.rpc(9, 2, 11200, 11201, fire=False, reject=True)
        model.tick(12201)
        model.rpc(9, 2, 12300, 12301)
        model.rpc(9, 3, 12302, 12303, reject=True)
        model.tick(13303)
        self.assertNotEqual(model.rows[-1]['latest']['input_received']['epoch'],
                            model.rows[-1]['latest']['input_accepted']['epoch'])
        self.status(model.rows, 'UNKNOWN')
        altered = deepcopy(model.rows)
        altered[-1]['counters']['input_received'] += 1
        self.status(altered, 'INVALID')

    def test_hidden_accepted_headers_still_obey_unconditional_shape_and_epoch(self):
        parent = anonymous_parent()
        self.status(parent.rows, 'UNKNOWN')
        for field, value in (('count', 13), ('first', 0), ('last', 0), ('epoch', 2)):
            altered = deepcopy(parent.rows)
            altered[-1]['latest']['input_accepted'][field] = value
            with self.subTest(field=field):
                self.status(altered, 'INVALID')

    def test_foundation_unknown_cannot_hide_later_structural_contradictions(self):
        model = anonymous_parent()
        model.tick(13501)
        self.status(model.rows, 'UNKNOWN')
        mutations = {
            'process': lambda r: r.update(process_frames=1),
            'physics': lambda r: r.update(physics_frames=1),
            'index': lambda r: r.update(index=r['index']+1),
            'epoch': lambda r: r.update(authority_epoch=0),
            'skipped': lambda r: r.update(stream_skipped=-1),
            'lifecycle-count': lambda r: r['counters'].update(peer_connected=2),
        }
        for label, mutate in mutations.items():
            altered = deepcopy(model.rows)
            mutate(altered[-1])
            with self.subTest(case=label):
                self.status(altered, 'INVALID')

    def test_multi_peer_queue_unknown_cannot_hide_later_direct_contradictions(self):
        model = anonymous_parent(two_peers=True)
        self.status(model.rows, 'UNKNOWN')
        model.rpc(10, 2, 12600, 12601, fire=False)
        self.status(model.rows, 'UNKNOWN')
        for field, value in (('queue_count', 0), ('bound_actor', 1), ('stream_ack', 2)):
            altered = deepcopy(model.rows)
            altered[-1][field] = value
            with self.subTest(field=field):
                self.status(altered, 'INVALID')

    def test_unknown_prefix_cannot_hide_later_direct_consumed_actor_controls(self):
        model = anonymous_parent()
        model.rpc(9, 3, 12600, 12601, fire=False)
        model.pop(9, 12602)  # Existing fire1 edge may coalesce.
        model.pop(9, 12603)  # Fire0 changes the consumed edge and emits directly.
        self.assertEqual(model.rows[-1]['reason'], 'input_consumed')
        self.status(model.rows, 'UNKNOWN')
        for label in ('actor-input', 'consumed-owner'):
            altered = deepcopy(model.rows)
            if label == 'actor-input':
                altered[-1]['actor']['input']['fire'] = True
            else:
                altered[-1]['latest']['input_consumed']['actor'] = 2
            with self.subTest(case=label):
                self.status(altered, 'INVALID')

    def test_zero_bound_epoch_reset_replaces_stream_state_without_erasing_counters(self):
        model = TimedAuthority()
        model.rpc(9, 2, 11200, 11201, fire=False, reject=True)
        model.tick(12201)
        model.disconnect(9, 12300)
        model.reset_empty_guest(13300)
        self.assertEqual(model.rows[-1]['counters']['input_stream_rejected'], 1)
        self.assertEqual(model.rows[-1]['stream_rejected'], 0)
        self.status(model.rows, 'CONSISTENT')
        for field, value in (('authority_epoch', 1), ('stream_rejected', 2), ('stream_ack', 1)):
            altered = deepcopy(model.rows)
            altered[-1][field] = value
            with self.subTest(field=field):
                self.status(altered, 'INVALID')

    def test_failed_duplicate_callback_keeps_source_state_unknown_not_invalid(self):
        model = TimedAuthority()
        # connected() returns false; Match still emits this lifecycle hook.
        model._hook('peer_connected', 11200, 9)
        with self.subTest(case='source-duplicate-callback'):
            self.status(model.rows, 'UNKNOWN')
        altered = deepcopy(model.rows)
        altered[-1]['process_frames'] = 1
        with self.subTest(case='independent-later-frame-fault'):
            self.status(altered, 'INVALID')

    def test_failed_capacity_callback_keeps_source_state_unknown_not_invalid(self):
        model = TimedAuthority()
        for position, peer in enumerate(range(10, 19)):
            model.connect(peer, 11200+position*10)
        self.assertEqual(len(model.peers), 10)
        # The eleventh peer is absent after connected() fails its capacity guard.
        model._hook('peer_connected', 11290, 19)
        with self.subTest(case='source-capacity-callback'):
            self.status(model.rows, 'UNKNOWN')
        altered = deepcopy(model.rows)
        altered[-1]['process_frames'] = 1
        with self.subTest(case='independent-later-frame-fault'):
            self.status(altered, 'INVALID')

    def test_generated_source_words_and_independent_counter_contradictions(self):
        from itertools import product

        # Frozen additive matrix: (4+16+64) words * 2 clock phases * 3 cases.
        # Operations are completed synchronously before the next receive; the
        # final emitted tick is outside every last control-event 1000ms window.
        for length in range(1, 4):
            for word in product(('A0', 'A1', 'J0', 'J1'), repeat=length):
                for phase in (0, 1):
                    model = TimedAuthority()
                    for position, operation in enumerate(word):
                        receive_at = 11200+position*10
                        model.rpc(9, 2+position, receive_at, receive_at+phase,
                                  fire=operation[1] == '1', reject=operation[0] == 'J')
                    model.tick(13200)
                    self.assertEqual(model.rows[-1]['reason'], 'authority_tick')
                    self.assertLessEqual(len(model.queues[9]), 3)
                    original = deepcopy(model.rows)
                    with self.subTest(word=word, phase=phase, case='source-positive'):
                        result = self.report(model.rows)
                        self.assertIn(result['transition_status'], ('CONSISTENT', 'UNKNOWN'), result)
                        self.assertEqual(result['diagnostic_complete'],
                                         result['transition_status'] == 'CONSISTENT', result)
                        self.assertEqual(model.rows, original)
                    surplus_receive = deepcopy(original)
                    surplus_receive[-1]['counters']['input_received'] += 1
                    with self.subTest(word=word, phase=phase, case='receive-counter-surplus'):
                        self.status(surplus_receive, 'INVALID')
                    surplus_rejection = deepcopy(original)
                    counted = surplus_rejection[-1]['counters'].get('input_stream_rejected', 0)
                    surplus_rejection[-1]['stream_rejected'] = counted+1
                    with self.subTest(word=word, phase=phase, case='stream-rejection-surplus'):
                        self.status(surplus_rejection, 'INVALID')


if __name__ == '__main__':
    unittest.main()
