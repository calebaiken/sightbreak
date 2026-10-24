#!/usr/bin/env python3
"""Builder pure expiry oracle from PeerLifecycle, not independent approval.

Closure is over the projected expiry guard only, not every Match callback.
No native/helper/actual-log replay. Original declared_rows helper stays intact.
"""
from copy import deepcopy
import hashlib
import itertools
import json
from pathlib import Path
import random
import re
import unittest

from analyze_input_consumption import analyze,expiry_projection
from test_input_consumption_observation import declared_rows,text
from test_input_consumption_state import append_event
from test_input_consumption_stream import packet

ROOT=Path(__file__).resolve().parents[1]
JOIN,IDLE,REJECT=20000,30000,500
PEER_SHA='8a57cc07bdc007fe143a5e8c51c99238732fcc4acf9f209fd4718af937f22078'
REPORT=ROOT/'docs/reports/gauntlet/windows-input-consumption-r7-expiry-builder-tests-20261024'
CRITIC=REPORT/'originals/history-model-v1'


class SourcePeer:
    """Literal single-peer source transitions; clocks are declared monotonic."""
    def __init__(self):self.entry=None;self.generation=0;self.clock=-1;self.events=[]
    def event(self,name,now):
        assert type(now) is int and now>=0 and now>=self.clock
        self.clock=now;self.events.append((name,now))
    def connected(self,now):
        self.event('connected',now)
        if self.entry is not None:return False
        self.generation+=1
        self.entry=dict(generation=self.generation,deadline=now+JOIN,joined=False,attempted=False,rejected=False,last_input=now)
        return True
    def begin_join(self,now):
        self.event('begin_join',now);e=self.entry
        if not e or e['attempted'] or e['rejected'] or now>=e['deadline']:return -1
        e['attempted']=True;return e['generation']
    def admitted(self,generation,now):
        self.event('admitted',now);e=self.entry
        if not e or e['generation']!=generation or e['rejected'] or now>=e['deadline']:return False
        e['joined']=True;e['last_input']=now;return True
    def active(self,now):
        self.event('active',now);e=self.entry
        if e and e['joined'] and not e['rejected'] and now-e['last_input']<IDLE:e['last_input']=now
    def reject(self,now):
        self.event('reject',now);e=self.entry
        if e and not e['rejected']:e['rejected']=True;e['deadline']=now+REJECT
    def expired(self,now):
        e=self.entry
        if not e:return False
        if (e['rejected'] or not e['joined']) and now>=e['deadline']:return True
        elif e['joined'] and now-e['last_input']>=IDLE:return True
        return False
    def projection(self,now):
        assert now>=self.clock
        e=self.entry
        return dict(wall_msec=now,input_age_msec=now-e['last_input'],deadline_remaining_msec=e['deadline']-now,joined=e['joined'])


def admit(model,now):
    generation=model.begin_join(now)
    assert generation>0 and model.admitted(generation,now)


def projected_witnesses(query):
    """Exhaustive canonical witnesses, justified by the registered closure proof.

    Every unrejected state fixes connect=d-JOIN. Unjoined last=connect;
    joined can reach every later last via active increments<IDLE. Every rejected
    state fixes reject=d-REJECT and last<=reject<=now. Connect/admit at last
    constructs all such projections. Both modes exhaust the hidden rejected bit.
    No finite grid absence is treated as a proof of impossibility.
    """
    if set(query)!=set(('wall_msec','input_age_msec','deadline_remaining_msec','joined')):return []
    now,age,remaining=query['wall_msec'],query['input_age_msec'],query['deadline_remaining_msec']
    if type(query['joined']) is not bool or any(type(x) is not int for x in (now,age,remaining)) or now<0 or age<0 or now<age:return []
    last=now-age;deadline=now+remaining;result=[]
    connected_at=deadline-JOIN
    if 0<=connected_at<=last:
        model=SourcePeer();model.connected(connected_at)
        if query['joined']:
            admit(model,connected_at)
            # Active ignores the original join deadline after admission.
            while model.entry['last_input']<last:model.active(min(last,model.entry['last_input']+IDLE-1))
        if model.projection(now)==query:result.append(model)
    rejected_at=deadline-REJECT
    if last<=rejected_at<=now:
        model=SourcePeer();model.connected(last)
        if query['joined']:admit(model,last)
        model.reject(rejected_at)
        if model.projection(now)==query:result.append(model)
    return result


def oracle(query):
    witnesses=projected_witnesses(query)
    outcomes={model.expired(query['wall_msec']) for model in witnesses}
    if True not in outcomes:return 'INVALID'
    return 'UNKNOWN' if False in outcomes else 'CONSISTENT'


def faithful_authority_rows():
    """Existing schema template; independently correct its lifecycle projection.

    This is a declared lifecycle-consistent parser fixture, not acquired output
    or a proof of every game/packet/physical callback history.
    """
    rows=deepcopy(declared_rows('authority'));model=SourcePeer()
    for row in rows:
        now=row['wall_msec'];reason=row['reason']
        if reason=='peer_connected':model.connected(now)
        elif reason=='peer_bound':admit(model,now)
        elif reason=='input_accepted':model.active(now) # Match active precedes accept observation.
        if model.entry:row.update(model.projection(now))
    return rows,model


def expiry_rows(mode='idle'):
    rows,model=faithful_authority_rows();last=model.entry['last_input']
    if mode=='idle':now=last+IDLE
    elif mode=='rejected':model.reject(23500);now=24000
    elif mode=='early':now=last+IDLE-1
    else:raise ValueError(mode)
    row=append_event(rows,'peer_expired',**model.projection(now),wall_unix_msec=100000+now)
    return rows,row


def full_report(authority):return analyze(text(declared_rows('client')),text(authority))


def unbound_expiry_rows(timer,delta):
    rows,_=faithful_authority_rows();now=rows[-1]['wall_msec']+1000
    model=SourcePeer();model.generation=1;model.connected(now)
    append_event(rows,'peer_connected',peer=10,generation=2,peer_bound=False,bound_actor=0,
                 stream_ack=-1,queue_count=0,**model.projection(now))
    if timer=='reject':model.reject(now)
    now+=(REJECT if timer=='reject' else JOIN)+delta
    append_event(rows,'peer_expired',**model.projection(now),wall_unix_msec=100000+now)
    return rows


class SourceExpiryOracleControls(unittest.TestCase):
    def test_source_identity_constants_and_transition_anchors_are_pinned(self):
        source=(ROOT/'game/scripts/network/peer_lifecycle.gd').read_bytes()
        self.assertEqual(hashlib.sha256(source).hexdigest(),PEER_SHA)
        constants={name:int(value) for name,value in re.findall(rb'const (JOIN|IDLE|REJECT)_MSEC := (\d+)',source)}
        self.assertEqual(constants,{b'JOIN':JOIN,b'IDLE':IDLE,b'REJECT':REJECT})
        match=(ROOT/'game/scripts/gameplay/match.gd').read_text()
        start=match.index('func _service_peers()');end=match.index('\nfunc ',start+1);block=match[start:end]
        self.assertLess(block.index('_native_input_observe("peer_expired"'),block.index('_peer_disconnected(peer_id)'))

    def test_source_join_rejection_and_idle_boundaries(self):
        # Expected labels are justified by exact source transition witnesses,
        # not by candidate branch arithmetic or absent finite samples.
        for joined in (False,True):
            model=SourcePeer();model.connected(10)
            if joined:admit(model,10)
            expected=['INVALID','UNKNOWN','UNKNOWN'] if joined else ['INVALID','CONSISTENT','CONSISTENT']
            for delta,want in zip((-1,0,1),expected):
                query=model.projection(10+JOIN+delta)
                self.assertEqual(oracle(query),want);self.assertEqual(expiry_projection(query),want)
        for joined in (False,True):
            model=SourcePeer();model.connected(0)
            if joined:admit(model,0);model.active(1000)
            model.reject(1100)
            for delta,want in [(-1,'INVALID'),(0,'CONSISTENT'),(1,'CONSISTENT')]:
                query=model.projection(1100+REJECT+delta)
                self.assertEqual(oracle(query),want);self.assertEqual(expiry_projection(query),want)
        model=SourcePeer();model.connected(0);admit(model,0);model.active(10000)
        for delta,want in [(-1,'UNKNOWN'),(0,'CONSISTENT'),(1,'CONSISTENT')]:
            query=model.projection(10000+IDLE+delta)
            self.assertEqual(oracle(query),want);self.assertEqual(expiry_projection(query),want)

    def test_complete_canonical_projection_closure_over_boundaries(self):
        # Each query's two hidden modes are exhaustively closed by witnesses;
        # this Cartesian grid chooses queries, not hidden history candidates.
        times=[0,1,499,500,501,19999,20000,20001,29999,30000,30001,40000,100000]
        ages=[-1,0,1,499,500,501,19999,20000,20001,29999,30000,30001,40000]
        remains=[-30001,-30000,-29999,-20001,-20000,-19999,-501,-500,-499,-1,0,1,499,500,501,19999,20000,20001]
        count=0
        for now,age,remaining,joined in itertools.product(times,ages,remains,(False,True)):
            query=dict(wall_msec=now,input_age_msec=age,deadline_remaining_msec=remaining,joined=joined)
            want=oracle(query);got=expiry_projection(query)
            if want!=got:self.fail(f'closed source witnesses disagree query={query} expected={want} actual={got}')
            for witness in projected_witnesses(query):self.assertEqual(witness.projection(now),query)
            count+=1
        self.assertEqual(count,6084)

    def test_arbitrary_concrete_histories_are_feasible_oneway_without_grid_unknown_claim(self):
        rng=random.Random(0x455850495259)
        for _ in range(256):
            model=SourcePeer();now=rng.randrange(40000);model.connected(now)
            if rng.randrange(2):now+=rng.randrange(JOIN);admit(model,now)
            for _ in range(rng.randrange(6)):
                now+=rng.choice([0,1,499,500,501,19999,20000,29999,30000,30001])
                if rng.randrange(5)==0:model.reject(now)
                else:model.active(now)
            now+=rng.randrange(40001);query=model.projection(now);status=expiry_projection(query)
            # One concrete feasible eligible state forbids INVALID. One concrete
            # feasible ineligible state forbids CONSISTENT; UNKNOWN stays open.
            self.assertNotEqual(status,'INVALID' if model.expired(now) else 'CONSISTENT',(model.events,query))

    def test_explicit_impossibilities_and_supported_c882_false_complete(self):
        for query in [dict(wall_msec=40000,input_age_msec=0,deadline_remaining_msec=20000,joined=True),
                      dict(wall_msec=100,input_age_msec=-1,deadline_remaining_msec=0,joined=False),
                      dict(wall_msec=100,input_age_msec=101,deadline_remaining_msec=0,joined=True),
                      dict(wall_msec=40000,input_age_msec=30000,deadline_remaining_msec=20000,joined=True),
                      dict(wall_msec=0,input_age_msec=0,deadline_remaining_msec=-1,joined=False)]:
            self.assertEqual(oracle(query),'INVALID');self.assertEqual(expiry_projection(query),'INVALID')

    def test_hidden_rejected_and_unrejected_witnesses_prove_unknown(self):
        query=dict(wall_msec=40000,input_age_msec=1000,deadline_remaining_msec=0,joined=True)
        witnesses=projected_witnesses(query)
        self.assertEqual({m.entry['rejected'] for m in witnesses},{False,True})
        self.assertEqual({m.expired(40000) for m in witnesses},{False,True})
        self.assertEqual(expiry_projection(query),'UNKNOWN')


class FullExpiryReaderControls(unittest.TestCase):
    def assert_status(self,rows,want):
        report=full_report(rows)
        self.assertEqual(report['transition_status'],want,report['errors'])
        self.assertEqual(report['diagnostic_complete'],want=='CONSISTENT',report['errors'])
        return report

    def test_new_positive_lifecycle_projection_and_old_helper_unchanged(self):
        original=declared_rows('authority');before=deepcopy(original);rows,model=faithful_authority_rows()
        self.assertEqual(original[1]['input_age_msec'],-1);self.assertEqual(original[1]['deadline_remaining_msec'],-1)
        self.assertEqual(rows[1]['input_age_msec'],0);self.assertEqual(rows[1]['deadline_remaining_msec'],JOIN)
        self.assertEqual(rows[2]['deadline_remaining_msec'],19000)
        self.assertEqual(rows[3]['input_age_msec'],5000);self.assertEqual(rows[4]['input_age_msec'],0)
        self.assert_status(rows,'CONSISTENT');self.assertEqual(declared_rows('authority'),before)

    def test_full_source_idle_boundary_and_latent_rejection_unknown(self):
        rows,row=expiry_rows('idle');self.assert_status(rows,'CONSISTENT')
        self.assertEqual(row['input_age_msec'],IDLE)
        rows,row=expiry_rows('early');self.assert_status(rows,'UNKNOWN')
        self.assertTrue(any('unobserved rejection' in error for error in full_report(rows)['errors']))
        # Proved C=2000 excludes an unrejected deadline24000; only the
        # supported hidden rejection can explain this otherwise valid row.
        rows,row=expiry_rows('rejected');self.assert_status(rows,'CONSISTENT')

    def test_full_join_reject_boundaries_and_idle_plus_one(self):
        for timer in ('join','reject'):
            for delta in (-1,0,1):
                with self.subTest(timer=timer,delta=delta):
                    self.assert_status(unbound_expiry_rows(timer,delta),'INVALID' if delta<0 else 'CONSISTENT')
        rows,row=expiry_rows('idle');row.update(wall_msec=row['wall_msec']+1,wall_unix_msec=row['wall_unix_msec']+1,
                                               input_age_msec=IDLE+1,deadline_remaining_msec=row['deadline_remaining_msec']-1)
        self.assert_status(rows,'CONSISTENT')

    def test_full_c882_age0_futuredeadline_no_longer_completes(self):
        rows,row=expiry_rows('idle');row.update(input_age_msec=0,deadline_remaining_msec=20000)
        report=self.assert_status(rows,'INVALID')
        self.assertTrue(report['errors']) # History may reject before the local guard.

    def test_negative_missing_age_and_wrong_types_are_invalid_full_records(self):
        for mutation in ('negative','missing','bool','string','future_last'):
            rows,row=expiry_rows('idle')
            if mutation=='missing':del row['input_age_msec']
            elif mutation=='future_last':row['input_age_msec']=row['wall_msec']+1
            else:row['input_age_msec']={'negative':-1,'bool':True,'string':'30000'}[mutation]
            with self.subTest(mutation=mutation):self.assert_status(rows,'INVALID')

    def test_expiry_requires_connected_current_peer_generation_and_not_retired(self):
        for field,value in [('peer',10),('generation',2),('generation',-1)]:
            rows,row=expiry_rows('idle');row[field]=value
            with self.subTest(field=field,value=value):self.assert_status(rows,'INVALID')
        rows,row=expiry_rows('idle');append_event(rows,'peer_expired')
        self.assert_status(rows,'INVALID')
        rows,_=expiry_rows('idle');rows[-1]['reason']='peer_disconnected'
        rows[-1]['counters'].pop('peer_expired');rows[-1]['counters']['peer_disconnected']=1
        append_event(rows,'peer_expired');self.assert_status(rows,'INVALID')

    def test_later_invalid_is_not_masked_by_deferred_unknown_expiry(self):
        for mutation in ('index','regressed_clock','input_after_retirement','same_generation_reconnect'):
            rows,_=expiry_rows('early');self.assert_status(rows,'UNKNOWN')
            if mutation=='input_after_retirement':append_event(rows,'input_received')
            elif mutation=='same_generation_reconnect':
                append_event(rows,'peer_disconnected');append_event(rows,'peer_connected',peer_bound=False,bound_actor=0,joined=False)
            else:
                row=append_event(rows,'authority_tick')
                if mutation=='index':row['index']+=1
                else:row['wall_msec']-=2000
            with self.subTest(mutation=mutation):self.assert_status(rows,'INVALID')

    def test_retired_generation_can_reconnect_only_with_fresh_identity(self):
        rows,row=expiry_rows('idle');before=deepcopy(row);disconnected=append_event(rows,'peer_disconnected')
        elapsed=disconnected['wall_msec']-before['wall_msec']
        disconnected.update(input_age_msec=before['input_age_msec']+elapsed,
                            deadline_remaining_msec=before['deadline_remaining_msec']-elapsed)
        now=rows[-1]['wall_msec']+1000;model=SourcePeer();model.generation=1;model.connected(now)
        append_event(rows,'peer_connected',peer_bound=False,bound_actor=0,generation=2,stream_ack=-1,queue_count=0,
                     **model.projection(now))
        self.assert_status(rows,'CONSISTENT')


def exact_critic_pair(name):
    manifest=json.loads((REPORT/'CRITIC_COPY_MANIFEST.json').read_text())
    for suffix in ('client.txt','authority.txt'):
        record=next(x for x in manifest['files'] if x['path']==name+'/'+suffix)
        raw=(CRITIC/name/suffix).read_bytes()
        assert len(raw)==record['bytes'] and hashlib.sha256(raw).hexdigest()==record['sha256']
    return ((CRITIC/name/'client.txt').read_text(),(CRITIC/name/'authority.txt').read_text())


def interleaved_activity(direct):
    rows,model=faithful_authority_rows()
    # Initial accepted batch holds1(fire) and3(neutral). Consume1;3 stays
    # queued. A later accepted duplicate3 can refresh activity without changing
    # queue size, so global receipt count alone cannot name its owner.
    for row in rows:
        for stage in ('input_received','input_accepted'):
            if stage in row['latest']:row['latest'][stage].update(count=2,first=1,last=3,fire=1)
        if row['reason']=='input_accepted':row['queue_count']=2
        elif row['reason'] in ('input_consumed','authority_tick'):row['queue_count']=1
    other=SourcePeer();other.generation=1;other.connected(12000)
    append_event(rows,'peer_connected',peer=10,generation=2,bound_actor=0,peer_bound=False,last_bound_actor=1,
                 stream_ack=-1,queue_count=0,**other.projection(12000))
    admit(other,13000)
    row=append_event(rows,'peer_bound',peer=10,generation=2,bound_actor=2,peer_bound=True,last_bound_actor=2,
                     stream_ack=-1,queue_count=0,**other.projection(13000))
    row['actor'].update(id=2,input={'sequence':-1,'fire':False,'reload':False,'move':[0.,0.]})
    command=packet(20000,3,3,1,0,1)
    if direct:
        row=append_event(rows,'input_received',peer=9,generation=1,bound_actor=1,peer_bound=True,last_bound_actor=1,
                         stream_ack=1,queue_count=1,**model.projection(19999))
        row['wall_unix_msec']=119999;row['latest']['input_received']=dict(command,wall_msec=19999)
        row['actor'].update(id=1,input={'sequence':1,'fire':True,'reload':False,'move':[0.,0.]})
        model.active(20000)
        row=append_event(rows,'input_accepted',**model.projection(20000));row['wall_unix_msec']=120000
        row['latest']['input_accepted']=deepcopy(command)
    else:
        model.active(20000) # One declared feasible local realization, not proved owner.
        row=append_event(rows,'authority_tick',peer=9,generation=1,bound_actor=1,peer_bound=True,last_bound_actor=1,
                         stream_ack=1,queue_count=1,**model.projection(20001))
        row['wall_unix_msec']=120001;row['counters']['input_received']+=1;row['counters']['input_accepted']+=1
        row['latest']['input_received']=deepcopy(command);row['latest']['input_accepted']=deepcopy(command)
        row['actor'].update(id=1,input={'sequence':1,'fire':True,'reload':False,'move':[0.,0.]})
    append_event(rows,'peer_expired',**model.projection(50000),wall_unix_msec=150000)
    return rows


class ExpiryHistoryControls(unittest.TestCase):
    def test_exact_four_registered_caller_false_complete_pairs_reject(self):
        for name in ('expiry_last_input_before_proved_connect','expiry_cannot_unjoin_live_bound_generation',
                     'expiry_cannot_drop_live_actor_binding_before_disconnect','expiry_last_input_advances_without_activity'):
            with self.subTest(name=name):
                report=analyze(*exact_critic_pair(name))
                self.assertEqual(report['transition_status'],'INVALID',report['errors']);self.assertFalse(report['diagnostic_complete'])

    def test_exact_registered_source_positive_siblings_keep_complete(self):
        for name in ('joined_idle_positive','long_idle_source_positive','unbound_join20000_positive',
                     'unbound_rejected500_positive','unique_early_rejected'):
            with self.subTest(name=name):
                report=analyze(*exact_critic_pair(name))
                self.assertEqual(report['transition_status'],'CONSISTENT',report['errors']);self.assertTrue(report['diagnostic_complete'])

    def test_exact_later_invalid_pairs_still_outrank_unknown(self):
        for name in ('authority_UNKNOWN_plus_client_cache_INVALID','deferred_UNKNOWN_then_later_authority_ACK_INVALID'):
            with self.subTest(name=name):
                report=analyze(*exact_critic_pair(name))
                self.assertEqual(report['transition_status'],'INVALID',report['errors']);self.assertFalse(report['diagnostic_complete'])

    def test_proved_connection_narrows_unrejected_deadline_without_changing_default(self):
        query=dict(wall_msec=40000,input_age_msec=1000,deadline_remaining_msec=0,joined=True)
        self.assertEqual(expiry_projection(query),'UNKNOWN')
        self.assertEqual(expiry_projection(query,connected_at=20000),'UNKNOWN')
        self.assertEqual(expiry_projection(query,connected_at=0),'CONSISTENT')
        self.assertEqual(expiry_projection(query,connected_at=40000),'INVALID')

    def test_missing_legacy_connected_foundation_stays_unknown_then_later_invalid(self):
        rows,_=expiry_rows('idle');rows[1].update(input_age_msec=-1,deadline_remaining_msec=-1)
        report=full_report(rows);self.assertEqual(report['transition_status'],'UNKNOWN',report['errors'])
        self.assertTrue(any('source-faithful prior' in error for error in report['errors']))
        append_event(rows,'input_received')
        self.assertEqual(full_report(rows)['transition_status'],'INVALID')

    def test_interleaved_global_activity_does_not_prove_local_advance(self):
        hidden=full_report(interleaved_activity(False))
        self.assertEqual(hidden['transition_status'],'UNKNOWN',hidden['errors']);self.assertFalse(hidden['diagnostic_complete'])
        self.assertTrue(any('ownership' in error for error in hidden['errors']))
        direct=full_report(interleaved_activity(True))
        self.assertEqual(direct['transition_status'],'CONSISTENT',direct['errors']);self.assertTrue(direct['diagnostic_complete'])


if __name__=='__main__':unittest.main()
