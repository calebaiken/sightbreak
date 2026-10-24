#!/usr/bin/env python3
"""Independent frozen-source receipt falsifiers; no native code is executed."""
import copy, hashlib, json, math, os
from pathlib import Path
import sys, time
ROOT=Path(sys.argv[1]).resolve()
sys.path.insert(0,str(ROOT/'scripts'))
import test_bot_objective_observation as t
import verify_bot_objective_observation as v
results=[]
def find(rows,kind,label=None,last=False):
    found=[r for k,r in rows if k==kind and (label is None or r.get('label')==label)]
    return found[-1] if last else found[0]
def summary(rows,name): return next(r for k,r in rows if k=='CONTROL' and r['name']==name)
def predicate(row,aid):
    a=row['before']['actors'][aid]
    row['actors_before'][aid].update(position=a['position'],team=a['team'],site=v.site(a['position']),objective_distance=math.dist(a['position'],row['before']['objective_position']),progress=row['before']['interactions'].get(aid,0))
def run(name,change=None):
    rows=t.synthetic_records(); baseline_hash=hashlib.sha256(t.log(rows).encode()).hexdigest()
    if change: change(rows)
    raw=t.log(rows); receipt_hash=hashlib.sha256(raw.encode()).hexdigest(); begin=time.monotonic()
    if change and receipt_hash==baseline_hash: raise AssertionError('mutation must change actual input: '+name)
    try:
        result=v.verify(raw,ROOT)
    except (ValueError,KeyError,TypeError) as e:
        accepted=False; detail=type(e).__name__+': '+str(e)
    else:
        accepted=True; detail=result
    item={'name':name,'expected_rejection':change is not None,'accepted':accepted,'met_expectation':accepted==(change is None),'input_sha256':receipt_hash,'baseline_sha256':baseline_hash,'changed':receipt_hash!=baseline_hash,'wall_seconds':time.monotonic()-begin,'detail':detail}
    results.append(item);print(json.dumps(item),flush=True)
run('complete_synthetic_positive')
def call_actor(rows):
    next(r for k,r in rows if k=='CALL' and r['case']=='live_complete')['output']['decision']['actor_id']=7
run('freshness_complete_decision_for_wrong_actor',call_actor)
def perception(rows):
    next(r for k,r in rows if k=='CALL' and r['case']=='direct_perception')['output']['target_id']=10
run('direct_perception_selects_target_without_candidates',perception)
def defuse_destination(rows):
    r=find(rows,'DECISION','control_defuse');r['observation']['plan']['destination']=[999,0,999];r['observation']['decision']['destination']=[999,0,999]
run('nearest_defuser_ignores_device_destination',defuse_destination)
def invented_role(rows): find(rows,'DECISION','pose_122')['observation']['decision']['role']='invented_role_not_in_source'
run('decision_role_not_produced_by_source',invented_role)
def fabricated_target(rows):
    r=find(rows,'DECISION','pose_122');o=r['observation'];candidate=next(c for c in o['candidates'] if c['distance']<38)
    candidate.update(reason='eligible',score=-999)
    o['decision']['target_id']=candidate['id'];o.update(target_distance=candidate['distance'],aligned=False)
run('fabricated_target_score_navigation_and_bot_memory',fabricated_target)
def fov(rows):
    r=find(rows,'DECISION','pose_122');o=r['observation'];a=r['before']['actors']['6'];c=next(x for x in o['candidates'] if x['distance']<38);b=r['before']['actors'][str(c['id'])]
    d=[b['position'][i]-a['position'][i] for i in range(3)];dot=(-math.sin(a['yaw'])*d[0]-math.cos(a['yaw'])*d[2])/math.sqrt(sum(x*x for x in d))
    assert dot>v.contract()['profiles']['normal']['fov_dot'] and r['before']['bots']['6']['damaged_at']==-100
    c['reason']='fov'
run('in_range_in_fov_candidate_falsely_rejected_by_fov',fov)
def unearned_credit(rows):
    r=find(rows,'INTERACTION','forward_live_122',True);a=find(rows,'AUTHORITY','forward_live_122',True)
    for s in (r['before'],r['after'],a['after']):s['actors']['6']['credits']+=100
run('forward_credits_added_without_kill_or_reward',unearned_credit)
def spontaneous_plant(rows):
    r=find(rows,'INTERACTION','forward_live_122',True);a=find(rows,'AUTHORITY','forward_live_122',True)
    for s in (r['before'],r['after'],a['after']):s.update(objective='planted',objective_position=[-15,0,10],objective_timer=35)
    r['after']['objective_timer']-=v.DT;a['after']['objective_timer']-=v.DT
    r.update(objective_before='planted',objective_after='planted')
    for aid in v.IDS:predicate(r,aid)
run('forward_objective_plants_before_consumer_without_progress',spontaneous_plant)
def injected_progress(rows):
    r=find(rows,'INTERACTION','forward_live_122',True);r['before']['interactions']['6']=2.9;predicate(r,'6')
run('forward_progress_injected_then_correctly_cleared',injected_progress)
def stationary_teleport(rows):
    r=find(rows,'INTERACTION','control_plant',True);s=summary(rows,'plant')
    for state in (r['before'],r['after'],s['final']):state['actors']['1']['position']=[999,999,999]
    predicate(r,'1')
run('isolated_control_stationary_actor_teleports',stationary_teleport)
def match_rng(rows):
    r=find(rows,'INTERACTION','control_plant',True);s=summary(rows,'plant')
    thinking=[d for k,d in rows if k=='DECISION' and d['label']=='control_plant' and d['tick']==r['tick']]
    assert not thinking
    for state in (r['before'],r['after'],s['final']):state['rng']='777'
run('isolated_control_match_rng_changes_without_bot_call',match_rng)
def team_change(rows):
    r=find(rows,'INTERACTION','forward_live_122',True);a=find(rows,'AUTHORITY','forward_live_122',True)
    for state in (r['before'],r['after'],a['after']):state['actors']['6']['team']=1
    predicate(r,'6')
run('forward_action_phase_reassigns_actor_team',team_change)
print(json.dumps({'source':'dce89495d04c9d3fefece0f8c7929e2e01b8e7df','fixture':str(ROOT),'cpu_affinity':sorted(os.sched_getaffinity(0)),'native_executed':False,'distinct_inputs':len({r['input_sha256'] for r in results}),'positive_accepted':results[0]['accepted'],'real_mutations':len(results)-1,'mutations_rejected':sum(not r['accepted'] for r in results[1:]),'false_passes':[r['name'] for r in results[1:] if r['accepted']],'results':results},indent=2))
sys.exit(0 if all(r['met_expectation'] for r in results) else 1)
