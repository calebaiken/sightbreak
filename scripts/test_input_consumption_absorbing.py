"""Frozen-before-candidate builder source oracle for absorbing rejection.

Complete timer closure is claimed for the declared unbound/explicit-event
prefixes only. Hidden activity histories are checked one-way or stay UNKNOWN.
No acquired/native log, engine, process or helper replay.
"""
from copy import deepcopy
import hashlib
import itertools
import json
from pathlib import Path
import unittest

import analyze_input_consumption as candidate
from test_input_consumption_expiry import SourcePeer,admit,JOIN,IDLE,REJECT,expiry_rows,full_report
from test_input_consumption_state import append_event

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/'docs/reports/gauntlet/windows-input-consumption-r7-absorbing-lifecycle-20261024'
CONTROLS=REPORT/'originals/deadline-histories-db912'
PREFIX='SIGHTBREAK_INPUT_OBSERVATION '
CERTIFIED_UNREJECTED={'peer_bound','input_received','input_accepted','input_decode_rejected','input_stream_rejected'}


def decoded(raw):return [json.loads(line[len(PREFIX):]) for line in raw.splitlines() if line.startswith(PREFIX)]


def literal_timer_outcomes(rows):
    """Literal source executions; unique rejection-clock/cut closure.

    Every rejection visible at any observation fixes r=that deadline-REJECT.
    Coincidence with initial D is included. Rejection's insertion cut is between
    complete atomic activity+hook observations, with inclusive equal clocks.
    No arbitrary rejection-time grid is used. The declared test domain has no
    unobserved local activity; incomplete activity domains return None.
    """
    if not rows or rows[0]['reason']!='peer_connected':return None
    first=rows[0];age=first['input_age_msec'];c=first['wall_msec']-age
    if age<0 or c<0 or age+first['deadline_remaining_msec']!=JOIN:return None
    for previous,current in zip(rows,rows[1:]):
        old_last=previous['wall_msec']-previous['input_age_msec'];new_last=current['wall_msec']-current['input_age_msec']
        extra=current.get('counters',{}).get('input_accepted',0)-previous.get('counters',{}).get('input_accepted',0)
        if current['joined'] and previous['joined'] and new_last>old_last:
            if current['reason'] not in {'peer_bound','input_accepted'} and extra>0:return None
            if current['reason']=='input_accepted' and extra>1:return None
    choices=[None]
    reject_times={row['wall_msec']+row['deadline_remaining_msec']-REJECT for row in rows}
    for reject_at,cut in itertools.product(sorted(reject_times),range(1,len(rows))):
        if rows[cut-1]['wall_msec']<=reject_at<=rows[cut]['wall_msec']:choices.append((reject_at,cut))
    outcomes=[]
    for choice in choices:
        model=SourcePeer();model.connected(c);valid=True
        for index,row in enumerate(rows):
            try:
                if choice is not None and index==choice[1]:model.reject(choice[0])
                now=row['wall_msec'];last=now-row['input_age_msec'];reason=row['reason']
                if reason in CERTIFIED_UNREJECTED and model.entry['rejected']:valid=False;break
                if reason=='peer_bound':
                    if last<rows[index-1]['wall_msec']:return None
                    attempt=model.begin_join(last)
                    if attempt<0 or not model.admitted(attempt,last):valid=False;break
                elif reason=='input_accepted':
                    # Only explicit update clocks in this oracle domain; a
                    # possible hidden earlier update is not disproved here.
                    if last<model.entry['last_input']:valid=False;break
                    if last<rows[index-1]['wall_msec']:return None
                    model.active(last)
                projected=model.projection(now)
                if any(row[key]!=value for key,value in projected.items()):valid=False;break
                if reason in CERTIFIED_UNREJECTED-{'peer_bound'} and not model.entry['joined']:valid=False;break
            except AssertionError:
                valid=False;break
        if valid:outcomes.append(dict(rejected=model.entry['rejected'],deadline=model.entry['deadline'],
                                      last_input=model.entry['last_input'],eligible=model.expired(rows[-1]['wall_msec']),
                                      rejection_clock=None if choice is None else choice[0],
                                      rejection_cut=None if choice is None else choice[1]))
    return outcomes


def oracle_status(rows):
    outcomes=literal_timer_outcomes(rows)
    if outcomes is None:return 'UNKNOWN'
    values={x['eligible'] for x in outcomes}
    if True not in values:return 'INVALID'
    return 'UNKNOWN' if False in values else 'CONSISTENT'


def target_prefix(authority):
    rows=decoded(authority);expiry=next(row for row in rows if row['reason']=='peer_expired')
    identity=expiry['peer'],expiry['generation']
    selected=[]
    for row in rows:
        if (row['peer'],row['generation'])==identity:selected.append(row)
        if row is expiry:break
    return selected


def exact_cases():
    inventory=json.loads((REPORT/'ASSESSOR_SEALED_INVENTORY.json').read_text())
    hashes={x['path']:x for x in inventory['files']}
    result=[]
    for folder in sorted(p for p in CONTROLS.iterdir() if p.is_dir()):
        data={}
        for name in ('client.txt','authority.txt','RESULT.json'):
            raw=(folder/name).read_bytes();key='deadline-histories-db912/'+folder.name+'/'+name;record=hashes[key]
            assert len(raw)==record['bytes'] and hashlib.sha256(raw).hexdigest()==record['sha256']
            data[name]=raw.decode()
        data['name']=folder.name;data['expected']=json.loads(data['RESULT.json'])['expected'];result.append(data)
    return result


def row(model,reason,now,accepted=0):
    return dict(reason=reason,**model.projection(now),counters={'input_accepted':accepted} if accepted else {},
                peer=9,generation=1,peer_bound=model.entry['joined'],bound_actor=int(model.entry['joined']))


def generated_timer_queries():
    """Finite query selection with a complete rejection-cut oracle per query."""
    cases=[]
    for c,joined,offset in itertools.product((0,10,12002),(False,True),(2,499,500,19500,19999,20000,20001)):
        source=SourcePeer();source.connected(c);base=[row(source,'peer_connected',c)]
        if joined:admit(source,c+1);base.append(row(source,'peer_bound',c+1))
        t=c+offset;last=source.entry['last_input'];original=c+JOIN
        prefix_deadlines={original,c+500,c+501,t+499,t+500}
        for d1 in sorted(prefix_deadlines):
            prefix=dict(reason='authority_tick',wall_msec=t,input_age_msec=t-last,deadline_remaining_msec=d1-t,
                        joined=joined,counters={},peer=9,generation=1,peer_bound=joined,bound_actor=int(joined))
            for finish in sorted({max(t+1,c+20001),max(t+1,c+30000),max(t+1,c+30001),c+40000}):
                deadlines={original,d1-1,d1,d1+1,c+499,c+500,c+501,t+499,t+500,t+501,finish+499,finish+500}
                for d2 in sorted(deadlines):
                    end=dict(prefix,reason='peer_expired',wall_msec=finish,input_age_msec=finish-last,deadline_remaining_msec=d2-finish)
                    rows=base+[prefix,end];cases.append((f'C{c}/J{int(joined)}/T{offset}/D{d1}/N{finish}/E{d2}',rows,oracle_status(rows)))
    return cases


def candidate_status(rows):
    model=candidate.LifecycleHypotheses(rows[0])
    for value in rows[1:-1]:model.observe(value,int(value['joined']))
    return model.expiry(rows[-1],int(rows[-1]['joined']))


class AbsorbingLifecycleControls(unittest.TestCase):
    def test_exact40_copied_deadline_pairs_and_literal_oracle(self):
        cases=exact_cases();self.assertEqual(len(cases),40);self.assertEqual(sum(x['expected']=='INVALID' for x in cases),32)
        for case in cases:
            with self.subTest(name=case['name']):
                self.assertEqual(oracle_status(target_prefix(case['authority.txt'])),case['expected'])
                result=candidate.analyze(case['client.txt'],case['authority.txt'])
                self.assertEqual(result['transition_status'],case['expected'],result['errors'])
                self.assertEqual(result['diagnostic_complete'],case['expected']=='CONSISTENT')

    def test_generated_prefix_deadline_intersections_match_frozen_source_oracle(self):
        cases=generated_timer_queries();self.assertGreater(len(cases),1000)
        for name,rows,want in cases:
            if candidate_status(rows)!=want:self.fail((name,rows,want,candidate_status(rows)))

    def test_coincident_initial_deadline_keeps_both_hidden_modes_then_filters_reject(self):
        source=SourcePeer();source.connected(0);rows=[row(source,'peer_connected',0)]
        admit(source,1);rows.append(row(source,'peer_bound',1))
        rows.append(row(source,'authority_tick',20000));model=candidate.LifecycleHypotheses(rows[0])
        for value in rows[1:]:model.observe(value,int(value['joined']))
        self.assertEqual({state['rejected'] for state in model.states},{False,True})
        source.active(20001);accepted=row(source,'input_accepted',20001,1);model.observe(accepted,1)
        self.assertEqual({state['rejected'] for state in model.states},{False})
        self.assertEqual(model.expiry(row(source,'peer_expired',50001,1),1),'CONSISTENT')

    def test_rejection_deadline_and_last_input_are_absorbing(self):
        for joined in (False,True):
            source=SourcePeer();source.connected(100);rows=[row(source,'peer_connected',100)]
            if joined:admit(source,101);rows.append(row(source,'peer_bound',101))
            source.reject(200);rows.append(row(source,'authority_tick',201));model=candidate.LifecycleHypotheses(rows[0])
            for value in rows[1:]:model.observe(value,int(value['joined']))
            self.assertTrue(model.states);self.assertTrue(all(x['rejected'] for x in model.states))
            for change in ('restore_deadline','new_deadline','advance_last','unjoin'):
                final=row(source,'peer_expired',40000)
                if change=='restore_deadline':final['deadline_remaining_msec']=20100-40000
                elif change=='new_deadline':final['deadline_remaining_msec']=701-40000
                elif change=='advance_last':final['input_age_msec']-=1
                else:
                    if not joined:continue
                    final.update(joined=False,peer_bound=False,bound_actor=0)
                replay=candidate.LifecycleHypotheses(rows[0])
                for value in rows[1:]:replay.observe(value,int(value['joined']))
                self.assertEqual(replay.expiry(final,int(joined)),'INVALID',change)

    def test_rejected_generation_cannot_admit_or_accept_then_recover(self):
        for event in ('peer_bound','input_received','input_accepted','input_decode_rejected','input_stream_rejected'):
            source=SourcePeer();source.connected(100);initial=row(source,'peer_connected',100)
            if event!='peer_bound':admit(source,101)
            model=candidate.LifecycleHypotheses(initial)
            if event!='peer_bound':model.observe(row(source,'peer_bound',101),1)
            source.reject(200);model.observe(row(source,'authority_tick',201),int(source.entry['joined']))
            impossible=row(source,event,202,1 if event=='input_accepted' else 0)
            if event=='peer_bound':impossible.update(joined=True,peer_bound=True,bound_actor=1,input_age_msec=0)
            model.observe(impossible,1);self.assertFalse(model.states)
            self.assertEqual(model.expiry(dict(impossible,reason='peer_expired',wall_msec=40000,input_age_msec=39800),1),'INVALID')

    def test_source_activity_budget_excludes_known_other_peer_calls(self):
        # Three literal updates are necessary and sufficient for +60000:
        # each active() can advance at most IDLE-1. Other peers' observed calls
        # cannot pay that local budget; unresolved allocations remain UNKNOWN.
        witness=SourcePeer();witness.connected(0);admit(witness,1)
        for clock in (30000,59999,60001):witness.active(clock)
        self.assertEqual(witness.entry['last_input'],60001)
        for total,other,want in [(1,0,'INVALID'),(2,0,'INVALID'),(3,0,'UNKNOWN'),(3,1,'INVALID'),(4,1,'UNKNOWN')]:
            source=SourcePeer();source.connected(0);initial=row(source,'peer_connected',0)
            model=candidate.LifecycleHypotheses(initial);admit(source,1);model.observe(row(source,'peer_bound',1),1)
            model.observe(row(source,'authority_tick',2),1)
            for _ in range(other):model.other_accepted()
            advanced=dict(row(source,'authority_tick',60001,total),input_age_msec=0)
            model.observe(advanced,1)
            expiry=dict(advanced,reason='peer_expired',wall_msec=90001,input_age_msec=IDLE,deadline_remaining_msec=JOIN-90001)
            self.assertEqual(model.expiry(expiry,1),want,(total,other))

    def test_already_idle_cannot_revive_and_new_model_does_not_borrow_rejection(self):
        source=SourcePeer();source.connected(0);initial=row(source,'peer_connected',0)
        model=candidate.LifecycleHypotheses(initial);admit(source,1);model.observe(row(source,'peer_bound',1),1)
        model.observe(row(source,'authority_tick',30001),1)
        impossible=dict(row(source,'authority_tick',60001,100),input_age_msec=0)
        model.observe(impossible,1);self.assertFalse(model.states)
        self.assertEqual(model.expiry(dict(impossible,reason='peer_expired',wall_msec=90001,input_age_msec=IDLE,deadline_remaining_msec=JOIN-90001),1),'INVALID')
        fresh=SourcePeer();fresh.connected(100000)
        replacement=candidate.LifecycleHypotheses(row(fresh,'peer_connected',100000))
        self.assertEqual(replacement.expiry(row(fresh,'peer_expired',120000),0),'CONSISTENT')

    def test_rejected_state_never_uses_unallocated_global_calls_as_local_proof(self):
        for known_other,want in [(False,'UNKNOWN'),(True,'CONSISTENT')]:
            source=SourcePeer();source.connected(0);model=candidate.LifecycleHypotheses(row(source,'peer_connected',0))
            admit(source,1);model.observe(row(source,'peer_bound',1),1)
            source.reject(200);model.observe(row(source,'authority_tick',201),1)
            if known_other:model.other_accepted()
            self.assertEqual(model.expiry(row(source,'peer_expired',40000,1),1),want)

    def test_pre_forget_disconnect_cannot_restore_timer_after_valid_expiry(self):
        for restore,want in [(False,'CONSISTENT'),(True,'INVALID')]:
            rows,expiry=expiry_rows('rejected');last=expiry['wall_msec']-expiry['input_age_msec']
            disconnected=append_event(rows,'peer_disconnected')
            disconnected.update(input_age_msec=disconnected['wall_msec']-last,
                                deadline_remaining_msec=(22000 if restore else 24000)-disconnected['wall_msec'])
            result=full_report(rows)
            self.assertEqual(result['transition_status'],want,result['errors'])


if __name__=='__main__':unittest.main()
