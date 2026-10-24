"""Pure pre-edit source model/case construction; no reader or old-helper edits."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import unittest

import input_consumption_foundation_model as model
from analyze_input_consumption import analyze
from test_input_consumption_observation import declared_rows,text

ROOT=Path(__file__).resolve().parents[1]
SOURCE_HASHES={
    'game/scripts/network/peer_lifecycle.gd':'8a57cc07bdc007fe143a5e8c51c99238732fcc4acf9f209fd4718af937f22078',
    'game/scripts/gameplay/match.gd':'80c1cc2fceeb44dd4bf8c9726a8f6a77124e649a8535a9e508ea6d904ec9f238',
}


def versioned_rows():return model.reproject_authority_rows(declared_rows('authority'))[0]


def source_negative_proposals():
    """One named necessary source contradiction each, not finite-grid absence."""
    result=[]
    def add(identity,proof,mutate):
        rows=versioned_rows();mutate(rows)
        result.append(dict(id=identity,proof=proof,expected_after_adjudicated_foundation='INVALID',rows=rows))
    add('connected/missing-age','live successful entry always has last_input; absence sentinel is impossible',lambda rows:rows[1].update(input_age_msec=-1))
    add('connected/wrong-sum','C+JOIN fixed: captured age+remaining must equal20000',lambda rows:rows[1].update(input_age_msec=1))
    add('connected/joined-before-admission','connected creates joinedfalse before bound hook',lambda rows:rows[1].update(joined=True))
    def skipped_generation(rows):
        for row in rows[1:]:
            row['generation']=2
            if 'input_consumed' in row['latest']:row['latest']['input_consumed']['generation']=2
    add('generation/skipped-first','fresh lifecycle generation starts0 and every successful connect hook is emitted',skipped_generation)
    add('bound/future-last','last_input cannot predate clock0',lambda rows:rows[2].update(input_age_msec=5000))
    add('received/invented-active','no accepted activity between bound and receive counters; receive itself does not call active',lambda rows:rows[3].update(input_age_msec=0))
    add('tick/future-rejection','changed D=41000 implies R40500 after observed now11000',lambda rows:rows[-1].update(deadline_remaining_msec=30000))
    add('tick/joined-lost','joined remains true while bound until pre-forget disconnect',lambda rows:rows[-1].update(joined=False))
    return result


class LiteralLifecycleModelControls(unittest.TestCase):
    def test_fixed_source_identity_and_named_constants(self):
        for name,sha in SOURCE_HASHES.items():self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),sha)
        self.assertEqual((model.JOIN,model.IDLE,model.REJECT,model.MAX_PEERS),(20000,30000,500,10))

    def test_delayed_successful_connection_capture_is_not_forced_age_zero(self):
        for connected in (0,1,1000):
            for delay in (0,1,19999,20000,20001):
                m=model.AuthorityProjectionEmitter();accepted,row=m.connect(9,connected,connected+delay)
                self.assertTrue(accepted);self.assertEqual(row['input_age_msec'],delay);self.assertEqual(row['deadline_remaining_msec'],20000-delay)
                self.assertTrue(model.source_successful_connection(row));self.assertFalse(row['joined'])

    def test_begin_join_and_admission_use_strict_original_deadline(self):
        for delta,allowed in ((19999,True),(20000,False),(20001,False)):
            p=model.PeerLifecycle();self.assertTrue(p.connected(9,1000));attempt=p.begin_join(9,1000+delta)
            self.assertEqual(attempt>0,allowed)
            self.assertEqual(p.admitted(9,1,1000+delta),allowed)
            self.assertEqual(p.peers[9]['last_input'],1000+delta if allowed else 1000)

    def test_active_and_allow_gate_boundaries_and_rate_window_are_literal(self):
        for age,allowed in ((29999,True),(30000,False),(30001,False)):
            p=model.PeerLifecycle();p.connected(9,0);p.begin_join(9,0);p.admitted(9,1,0)
            self.assertEqual(p.allow_input(9,age),allowed);p.active(9,age)
            self.assertEqual(p.peers[9]['last_input'],age if allowed else 0)
        p=model.PeerLifecycle();p.connected(9,0);p.begin_join(9,0);p.admitted(9,1,0)
        self.assertTrue(all(p.allow_input(9,0) for _ in range(90)));self.assertFalse(p.allow_input(9,0));self.assertTrue(p.allow_input(9,1000))

    def test_rejection_is_absorbing_and_repeated_reject_does_not_move_deadline(self):
        for joined in (False,True):
            p=model.PeerLifecycle();p.connected(9,0)
            if joined:p.begin_join(9,0);p.admitted(9,1,0)
            p.reject(9,100);p.reject(9,200);p.active(9,300)
            self.assertFalse(p.allow_input(9,300));self.assertFalse(p.admitted(9,1,300))
            self.assertEqual((p.peers[9]['deadline'],p.peers[9]['last_input'],p.peers[9]['joined']),(600,0,joined))

    def test_source_expired_predicate_boundaries_with_joined_rejected_priority(self):
        for kind,boundary in (('join',20000),('idle',30000),('reject',600)):
            for offset in (-1,0,1):
                p=model.PeerLifecycle();p.connected(9,0)
                if kind=='idle':p.begin_join(9,0);p.admitted(9,1,0)
                if kind=='reject':p.reject(9,100)
                self.assertEqual(p.expired(boundary+offset),[9] if offset>=0 else [])
        p=model.PeerLifecycle();p.connected(9,0);p.begin_join(9,0);p.admitted(9,1,0);p.reject(9,29999)
        self.assertEqual(p.peers[9]['deadline'],30499);self.assertEqual(p.expired(30000),[9])

    def test_admitted_and_active_operation_clocks_are_separate_from_later_hooks(self):
        m=model.AuthorityProjectionEmitter();m.connect(9,0);row=m.bind(9,1,19999,30000)
        self.assertTrue(row['joined']);self.assertEqual(row['input_age_msec'],10001);self.assertEqual(row['deadline_remaining_msec'],-10000)
        m=model.AuthorityProjectionEmitter();m.connect(9,0);m.bind(9,1,0)
        self.assertTrue(m.lifecycle.allow_input(9,29999));m.lifecycle.active(9,30000)
        row=m.capture('input_accepted',30001,9)
        self.assertEqual(row['input_age_msec'],30001);self.assertEqual(m.lifecycle.expired(30001),[9])

    def test_selected_peer_and_sticky_last_actor_are_distinct(self):
        m=model.AuthorityProjectionEmitter();m.connect(9,0);m.bind(9,1,1);_,other=m.connect(10,2)
        self.assertEqual((other['peer'],other['bound_actor'],other['last_bound_actor'],other['joined']),(10,0,1,False))
        m.bind(10,2,3);row=m.capture('authority_tick',4)
        self.assertEqual((row['peer'],row['bound_actor'],row['last_bound_actor']),(10,2,2))
        row=m.capture('input_received',5,9)
        self.assertEqual((row['peer'],row['bound_actor'],row['last_bound_actor']),(9,1,1))

    def test_disconnect_captures_before_forget_and_reconnect_has_new_timer_generation(self):
        m=model.AuthorityProjectionEmitter();m.connect(9,0);m.bind(9,1,1);row=m.disconnect(9,2)
        self.assertEqual((row['generation'],row['bound_actor'],row['joined']),(1,1,True))
        after=m.capture('authority_tick',3)
        self.assertEqual((after['generation'],after['joined'],after['input_age_msec'],after['deadline_remaining_msec'],after['last_bound_actor']),(-1,False,-1,-1,1))
        accepted,new=m.connect(9,4)
        self.assertTrue(accepted);self.assertEqual((new['generation'],new['input_age_msec'],new['deadline_remaining_msec'],new['last_bound_actor']),(2,0,20000,1))

    def test_failed_duplicate_hook_does_not_invent_new_generation_timer_or_forget(self):
        m=model.AuthorityProjectionEmitter();m.connect(9,0);m.bind(9,1,1)
        before=deepcopy(m.lifecycle.peers[9]);accepted,row=m.connect(9,2,3)
        self.assertFalse(accepted);self.assertEqual(m.lifecycle.generation,1);self.assertEqual(m.lifecycle.peers[9],before)
        self.assertEqual((row['generation'],row['joined'],row['bound_actor'],row['input_age_msec']),(1,True,1,2))

    def test_capacity_hook_has_absent_projection_and_no_generation_increment(self):
        m=model.AuthorityProjectionEmitter()
        for peer in range(1,11):self.assertTrue(m.connect(peer,0)[0])
        accepted,row=m.connect(11,1)
        self.assertFalse(accepted);self.assertEqual(m.lifecycle.generation,10);self.assertEqual(len(m.lifecycle.peers),10)
        self.assertEqual((row['generation'],row['joined'],row['input_age_msec'],row['deadline_remaining_msec']),(-1,False,-1,-1))

    def test_service_captures_expiry_then_preforget_disconnect(self):
        m=model.AuthorityProjectionEmitter();m.connect(9,0);m.service(20000)
        self.assertEqual([row['reason'] for row in m.rows],['peer_connected','peer_expired','peer_disconnected']);self.assertEqual(m.rows[-1]['generation'],1)
        self.assertNotIn(9,m.lifecycle.peers);self.assertEqual(m.capture('authority_tick',20001)['generation'],-1)

    def test_model_rejects_impossible_operation_order_without_using_reader(self):
        m=model.AuthorityProjectionEmitter()
        with self.assertRaises(ValueError):m.bind(9,1,0)
        m.connect(9,1)
        with self.assertRaises(ValueError):m.capture('authority_tick',0)
        with self.assertRaises(ValueError):m.bind(9,1,20001)


class VersionedPreEditConstructionControls(unittest.TestCase):
    def test_minimal_authority_delta_preserves_original_whole_rows_and_other_fields(self):
        original=declared_rows('authority');before=deepcopy(original);rows,emitter=model.reproject_authority_rows(original)
        self.assertEqual(original,before);self.assertEqual(original[1]['input_age_msec'],-1);self.assertEqual(original[1]['deadline_remaining_msec'],-1)
        self.assertEqual([(row['input_age_msec'],row['deadline_remaining_msec']) for row in rows],
                         [(-1,-1),(0,20000),(0,19000),(5000,14000),(0,13000),(1000,12000),(2000,11000)])
        for old,new in zip(original,rows):
            self.assertEqual({k:v for k,v in old.items() if k not in model.PROJECTION},{k:v for k,v in new.items() if k not in model.PROJECTION})
        self.assertEqual(emitter.lifecycle.peers[9]['last_input'],9000)

    def test_preedit_reader_false_complete_baseline_and_versioned_positive_are_separate(self):
        # This test intentionally retains a known bad baseline, not approval.
        original=analyze(text(declared_rows('client')),text(declared_rows('authority')))
        projected=analyze(text(declared_rows('client')),text(versioned_rows()))
        self.assertTrue(original['diagnostic_complete']);self.assertTrue(projected['diagnostic_complete'])
        self.assertFalse(model.source_successful_connection(declared_rows('authority')[1]));self.assertTrue(model.source_successful_connection(versioned_rows()[1]))

    def test_known_schema_valid_source_negatives_are_frozen_as_preedit_false_completes(self):
        proposals=source_negative_proposals();self.assertEqual(len(proposals),8)
        for case in proposals:
            result=analyze(text(declared_rows('client')),text(case['rows']))
            with self.subTest(id=case['id']):self.assertTrue(result['diagnostic_complete'],result['errors'])
            self.assertEqual(case['expected_after_adjudicated_foundation'],'INVALID')

    def test_generated_successful_connection_negatives_contradict_a_closed_identity(self):
        base=versioned_rows()[1]
        negatives=[dict(base,input_age_msec=-1),dict(base,input_age_msec=1),dict(base,deadline_remaining_msec=19999),
                   dict(base,joined=True),dict(base,peer_bound=True),dict(base,bound_actor=1),dict(base,generation=-1),
                   dict(base,input_age_msec=True),dict(base,deadline_remaining_msec=20000.0)]
        for row in negatives:self.assertFalse(model.source_successful_connection(row))
        # Positive delayed capture remains possible with both fields changed.
        self.assertTrue(model.source_successful_connection(dict(base,input_age_msec=1,deadline_remaining_msec=19999)))

    def test_all54_histories_are_oneway_concrete_witnesses_not_exhaustive_classification(self):
        cases=model.declared_histories();self.assertEqual(len(cases),54);self.assertEqual(len({row['id'] for row in cases}),54)
        for case in cases:
            self.assertEqual(case['kind'],'source_projection_witness')
            first=next(row for row in case['rows'] if row['reason']=='peer_connected')
            self.assertTrue(model.source_successful_connection(first))
            self.assertTrue(all(a['wall_msec']<=b['wall_msec'] for a,b in zip(case['rows'],case['rows'][1:])))


if __name__=='__main__':unittest.main()
