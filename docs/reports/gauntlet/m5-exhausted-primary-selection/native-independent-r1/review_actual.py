#!/usr/bin/env python3
"""Independent read-only all-row candidate replay, supplements and baseline deltas."""
import copy
import gzip
import hashlib
import importlib.util
import json
from collections import Counter, defaultdict
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
SOURCE = Path('/workspace/sightbreak-exhausted-primary-selection')
BASE = SOURCE/'docs/reports/gauntlet/m5-exhausted-primary-benchmark/actual-r2/baseline-probe.stdout.log.gz'

def module(name, path):
    spec=importlib.util.spec_from_file_location(name,path)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result)
    return result

rows=module('independent_rows',HERE/'audit_rows.py')
original=module('original_independent_rows',HERE/'original-independent-audit.py')

def normalize(value):
    value=copy.deepcopy(value)
    lane=value['lane']
    for field in ('pose_settle','observation_frame','world_hit_path'):
        lane.pop(field)
    for kind in ('actual_shots','damage_events','elimination_events'):
        for event in value[kind]:event.pop('serial')
    return value

def extra_audit(records,baseline):
    checks=0
    def check(value,message):
        nonlocal checks
        checks+=1
        assert value,message
    by=defaultdict(list)
    for _,kind,row in records:by[kind].append(row)
    check(by['POLICY_HEADER']==[dict(range_cases_expected=9,reserve_steps_expected=20,total_policy_rows_expected=1268,common_fixture_sha256='540d24dda8e58f4685030e81b55ac3778ccbf31a89f76f9873ac598c32770731')],'supplement source/count header')
    check(by['POLICY_RESULT']==[dict(policy_rows=1268,range_rows=9,reserve_rows=20,failures_so_far=[])],'supplement result')
    far=[]
    for difficulty in ('normal','hard'):
        for primary in rows.PRIMARIES:
            label=f'sequence/{difficulty}/{primary}/far_loaded'
            seq=[r for r in by['STEP'] if r['label']==label]
            shot_count=sum(len(r['actual_shots']) for r in seq)
            draws=sum(r['before']['weapon']!=r['after_action']['weapon'] for r in seq)
            check(len(seq)==8 and draws==1 and shot_count>0,'actual 24m draw/fire '+label)
            check(all(not r['empty_reload_request'] for r in seq),'no impossible reload '+label)
            check(seq[-1]['after_action']['weapon']=='sidearm' and seq[-1]['after_action']['ammo']==15-shot_count and seq[-1]['after_action']['reserve']==0,'consumed sidearm ammunition '+label)
            far.append(dict(label=label,draws=draws,shots=shot_count,final_ammo=seq[-1]['after_action']['ammo'],damage=sum(r['target_damage_delta'] for r in seq)))
    reserve=by['POLICY_RESERVE_STEP'];summary=by['POLICY_RESERVE'][0]
    check(len(reserve)==20 and [r['step'] for r in reserve]==list(range(20)),'reserve exact steps')
    starts=[r['step'] for r in reserve if r['before']['weapon']==r['after_action']['weapon'] and r['before']['reload']==0<r['after_action']['reload']]
    ends=[r['step'] for r in reserve if r['before']['weapon']==r['after_action']['weapon'] and r['before']['reload']>0==r['after_action']['reload']]
    check(starts==[1] and ends==[14],'reserve legal 1.45s reload')
    check(summary['initial_shooter']==reserve[0]['before'] and summary['final_shooter']==reserve[-1]['after_action'] and summary['initial_target']==reserve[0]['enemy_before'] and summary['final_target']==reserve[-1]['enemy_after_action'],'reserve summary snapshots')
    check(summary['name']=='policy_reserve_24m' and summary['steps']==20 and summary['visibility_schedule']=='visible only on step 0, then hidden','reserve identity')
    check(summary['reload_start_step']==1 and summary['reload_completion_step']==14 and summary['draws']==summary['reload_starts']==summary['reload_completions']==1 and summary['impossible_reload_requests']==0,'reserve reported actions')
    check(reserve[-1]['after_action']['weapon']=='sidearm' and (reserve[-1]['after_action']['ammo'],reserve[-1]['after_action']['reserve'],reserve[-1]['after_action']['reload'])==(15,0,0),'reserve final legal resources')
    check(summary['initial_target']==summary['final_target'] and all(not r['actual_shots'] and not r['damage_events'] and not r['elimination_events'] and not r['empty_reload_request'] for r in reserve),'reserve target/no-shot/no-loop')
    before={(kind,r['label'],r['step']):r for _,kind,r in baseline if kind in ('CASE','STEP','CONTROL_STEP')}
    after={(kind,r['label'],r['step']):r for _,kind,r in records if kind in ('CASE','STEP','CONTROL_STEP')}
    check(before.keys()==after.keys(),'original 1239 exact identities')
    header=baseline[0][2]
    changed_cases=[];changed_seq=[]
    for key,b in before.items():
        kind,label,step=key
        if kind!='CASE' and not(kind=='STEP' and step==0):continue
        s=b['scenario'];acquired=s['target']['visible'] and b['enemy_before']['alive'] and s['target']['distance']<=header['profiles'][s['difficulty']]['vision_range']
        desired=rows.selection(b['before'],acquired,s['objective']!='none',s['target']['distance'],s['difficulty'])
        if desired!=b['command']['weapon']:
            check(desired=='sidearm' and b['command']['weapon']=='','only new sidearm requests')
            (changed_cases if kind=='CASE' else changed_seq).append(label)
    check(len(changed_cases)==51 and len(changed_seq)==15,'independent exact 51/15 request forecast')
    preserved=0
    for key,b in before.items():
        kind,label,step=key;a=after[key]
        if kind=='CASE':
            check(a['before']==b['before'] and a['enemy_before']==b['enemy_before'] and a['decision_bot_state']==b['decision_bot_state'],'matrix input and planning equality '+label)
            expected=dict(b['command'])
            if label in changed_cases:expected.update(weapon='sidearm',reload=False)
            check(a['command']==expected,'exact matrix request delta '+label)
        if kind=='CONTROL_STEP' or (kind=='CASE' and label not in changed_cases) or (kind=='STEP' and label not in changed_seq):
            check(rows.close(normalize(a),normalize(b),1e-4),'preserved complete action '+label+'/'+str(step))
            preserved+=1
        if kind=='STEP' and step==0:
            check((a['command']['weapon']!=b['command']['weapon'])==(label in changed_seq),'exact first sequence change '+label)
    check(preserved==516+57*8+96,'all 1068 preserved action rows')
    return dict(independent_comparison_predicates=checks,changed_matrix_labels=changed_cases,changed_sequence_labels=changed_seq,preserved_matrix_requests=516,preserved_complete_sequences=57,preserved_common_action_rows=preserved,actual_24m=far,reserve_reload_start=starts,reserve_reload_end=ends)

def run(path):
    raw=gzip.decompress(BASE.read_bytes())
    assert hashlib.sha256(raw).hexdigest()=='e6606c22b5d5cc5c33090a97b1a832e60a376465a0edfa112146b7f743b10d7f'
    baseline,_=rows.parse(BASE);records,other=rows.parse(path)
    result=dict(original_baseline_replay=original.audit(copy.deepcopy(baseline),SOURCE),candidate=rows.audit(copy.deepcopy(records),SOURCE),supplements_comparison=extra_audit(records,baseline),nonrecord_stdout=other,candidate_stdout_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    rejected=[]
    def extra_round(r):
        r['after_action']['ammo']+=1
        r['resources_after']['sidearm']['clip']+=1
        r['equip_semantics_total_after']+=1
    def wrong_lane(r):
        r['before']['position']=[0,0,0]
        r['after_decision']['position']=[0,0,0]
    mutations={
        'planning_ammo_mutation':lambda r:r['after_decision'].__setitem__('ammo',1),
        'missing_actual_draw':lambda r:r['after_action'].__setitem__('weapon',r['before']['weapon']),
        'free_deploy':lambda r:r['after_action'].__setitem__('deploy',0),
        'extra_round_with_consistent_projection':extra_round,
        'unreported_shot':lambda r:r['actual_shots'].append(dict(serial=999)),
        'unexplained_reward':lambda r:r['after_action'].__setitem__('credits',1100),
        'wrong_registered_lane_with_matching_planning_snapshot':wrong_lane,
        'false_resource_projection':lambda r:r['resources_after']['sidearm'].__setitem__('clip',16),
    }
    index=next(i for i,(_,k,r) in enumerate(records) if k=='CASE' and r['scenario']['difficulty']=='normal' and r['scenario']['primary']=='smg' and r['scenario']['target']['name']=='far' and r['scenario']['active_resource']=='exhausted' and r['scenario']['sidearm_resource']=='loaded')
    for name,mutate in mutations.items():
        altered=copy.deepcopy(records);mutate(altered[index][2])
        try:rows.audit(altered,SOURCE)
        except (AssertionError,KeyError,TypeError) as error:rejected.append(dict(name=name,error=str(error)))
        else:raise AssertionError('counterfeit accepted: '+name)
    result['candidate_corruption_rejections']=rejected
    return result

if __name__=='__main__':print(json.dumps(run(Path(sys.argv[1])),indent=2,sort_keys=True))
