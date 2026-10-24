#!/usr/bin/env python3
"""Source-derived necessary handoff projections, not an engine/combat model."""
import argparse
from copy import deepcopy
import gzip
import hashlib
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys

p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
assert sorted(os.sched_getaffinity(0))==[4]
a.source=a.source.resolve();a.output.mkdir(parents=True,exist_ok=False)
sys.path.insert(0,str(a.source/'scripts'));t=importlib.import_module('test_bot_objective_observation');v=importlib.import_module('verify_bot_objective_observation')

def initial():
    value=t.protected(122)
    for actor in value['actors'].values():
        actor.update(alive=True,health=100,kills=0,deaths=0,assists=0,credits=800,collision_disabled=False)
    return value

template=initial();carrier=str(template['carrier']);team=template['actors'][carrier]['team']
ally=next(i for i in sorted(v.IDS) if i!=carrier and template['actors'][i]['team']==team)
enemies=[i for i in sorted(v.IDS) if template['actors'][i]['team']!=team]
opponent=enemies[0]

def elimination(before,after,victim,killer=None,post_position=None):
    actor=after['actors'][victim]
    actor.update(alive=False,health=0,velocity=[0,0,0])
    if post_position is not None:actor['position']=post_position
    actor['deaths']+=1
    if killer is not None and before['actors'][killer]['team']!=before['actors'][victim]['team']:
        after['actors'][killer]['kills']+=1
        after['actors'][killer]['credits']=min(9000,after['actors'][killer]['credits']+300)
    if int(victim)==before['carrier'] and before['objective']=='carried':
        after.update(objective='dropped',carrier=0,objective_position=deepcopy(actor['position']))

cases=[]
def run(name,before,after,expected,basis,events=None):
    v.state(before);v.state(after)
    error=None
    try:v.action_handoff(before,after)
    except (ValueError,KeyError,TypeError) as e:accepted=False;error=str(e)
    else:accepted=True
    raw=json.dumps(dict(current=before,observed=after,reference_events=events or []),separators=(',',':')).encode()
    (a.output/(name+'.json.gz')).write_bytes(gzip.compress(raw,mtime=0))
    cases.append(dict(name=name,expected_accepted=expected,actual_accepted=accepted,error=error,met_expectation=accepted==expected,input_sha256=hashlib.sha256(raw).hexdigest(),source_basis=basis))

run('unchanged_live_handoff',template,deepcopy(template),True,'No actor action changes the source-required protected fields.')
for credits in [800,8800,8900,9000]:
    before=deepcopy(template);before['actors'][opponent]['credits']=credits;after=deepcopy(before)
    elimination(before,after,ally,opponent)
    run('opposing_kill_credit_'+str(credits),before,after,True,'_eliminated gives one opposing kill and mini(9000, credits+300). Projection validates necessary award fields, not damage attribution.',[dict(victim=ally,killer=opponent)])
for kind,killer in [('world',None),('suicide',ally),('teammate',carrier)]:
    before=deepcopy(template);after=deepcopy(before);elimination(before,after,ally,killer)
    run('uncredited_'+kind+'_elimination',before,after,True,'_eliminated increments victim deaths; absent/self/same-team source receives no kill award. This tests hook semantics, not the existence of a gameplay world hazard.',[dict(victim=ally,killer=killer)])
before=deepcopy(template);after=deepcopy(before)
elimination(before,after,ally,opponent);elimination(before,after,opponent,ally)
run('mutual_queued_eliminations',before,after,True,'All traces precede queued damage; resolve_shot_hit does not require the source still alive. Both opposing awards are conserved.')
before=deepcopy(template);after=deepcopy(before)
elimination(before,after,ally,opponent);elimination(before,after,enemies[1],carrier)
run('two_independent_eliminations',before,after,True,'Independent opposing eliminations can occur in one authority damage phase; each victim increments once.')
before=deepcopy(template);after=deepcopy(before);after['actors'][ally]['health']=75
run('damage_without_death',before,after,True,'apply_damage may reduce health while leaving alive/death/kill/credit counters unchanged; damage geometry and memory effects are outside this projection corpus.')
before=deepcopy(template);after=deepcopy(before);after['actors'][carrier]['position']=[1,0,1]
run('moving_carrier_keeps_stored_objective_position',before,after,True,'Movement changes actor position; stored objective_position does not follow a living carried actor in the pre-consumer interval.')
before=deepcopy(template);after=deepcopy(before)
elimination(before,after,carrier,opponent,[1,0,1])
run('carrier_drop_uses_post_movement_position',before,after,True,'_eliminated unconditionally drops a carried device at killed.position after movement, with carrier0.')
bad=deepcopy(after);bad.update(objective=before['objective'],carrier=before['carrier'],objective_position=deepcopy(before['objective_position']))
run('carrier_death_suppresses_required_drop',before,bad,False,'Same elimination/award as the valid pair, but source _eliminated cannot leave its dead carrier in carried state. The drop is mandatory, not merely permitted.')
bad=deepcopy(after);bad['objective_position']=deepcopy(before['actors'][carrier]['position'])
run('carrier_drop_uses_stale_position',before,bad,False,'Dropped position must be post-movement killed.position, not the prior pose.')
before=deepcopy(template);after=deepcopy(before);after.update(objective='dropped',carrier=0,objective_position=deepcopy(after['actors'][carrier]['position']))
run('carrier_drop_without_death',before,after,False,'Action-phase carried→dropped transition requires carrier elimination.')
before=deepcopy(template);before['actors'][carrier]['input']['fire']=True;after=deepcopy(before)
after['actors'][carrier]['rng']='111';after['actors'][carrier]['ammo']-=1
run('actor_rng_and_resources_can_advance',before,after,True,'Actor firing uses its own RNG/resources. Necessary handoff projection permits them; it does not reconstruct the shot.')
before=deepcopy(template);before['rng']='777';after=deepcopy(before)
run('post_decision_match_rng_reaches_consumer',before,after,True,'Current is already the post-decision state; its match RNG must reach the consumer unchanged. This does not establish which RNG value the decision should have produced.')
after['rng']='778'
run('match_rng_changes_during_actions',before,after,False,'Actions use actor RNG; no intervening Match RNG draw occurs in this synchronous interval.')

for name,change,basis in [
    ('unearned_credit',lambda x:x['actors'][ally].update(credits=900),'No objective award occurs before the consumer; kill0 cannot produce credit100.'),
    ('team_reassignment',lambda x:x['actors'][ally].update(team=1-team),'Movement/actions cannot reassign a team.'),
    ('kill_without_opposing_death',lambda x:(x['actors'][ally].update(kills=1,credits=1100)),'A credited kill needs an opposing victim elimination.'),
    ('death_counter_without_death',lambda x:x['actors'][ally].update(deaths=1),'Deaths increment only on alive→dead elimination.'),
    ('preconsumer_plant',lambda x:x.update(objective='planted'),'Planting belongs inside _objective_tick.'),
    ('preconsumer_defuse',lambda x:x.update(objective='defused'),'Defusing belongs inside _objective_tick.'),
    ('preconsumer_progress',lambda x:x['interactions'].update({ally:2.9}),'Interaction progress changes inside the later consumer.'),
    ('preconsumer_timer',lambda x:x.update(objective_timer=1),'Objective timer does not advance in movement/actions.'),
    ('preconsumer_contribution',lambda x:x['contributions'].update({ally:1}),'Objective contributions change in the consumer.'),
    ('input_substitution',lambda x:x['actors'][ally]['input'].update(fire=True),'The complete actual command must reach the consumer.'),
    ('action_phase_transition',lambda x:x.update(phase='post'),'Round/phase handling occurs after the consumer, not before it.')]:
    before=deepcopy(template);after=deepcopy(before);change(after);run(name,before,after,False,basis)
before=deepcopy(template);after=deepcopy(before);after['actors'][ally].update(alive=False,health=0)
run('elimination_without_death_counter',before,after,False,'apply_damage emits one elimination, which increments victim deaths once.')
before=deepcopy(template);before['actors'][ally].update(alive=False,health=0);after=deepcopy(before);after['actors'][ally].update(alive=True,health=100)
run('action_revives_dead_actor',before,after,False,'No action in this interval revives an actor.')
before=deepcopy(template);before['actors'][opponent]['credits']=8900;after=deepcopy(before);elimination(before,after,ally,opponent);after['actors'][opponent]['credits']=9200
run('kill_credit_ignores_cap',before,after,False,'Repeated or single opposing awards use mini(9000, credits+300).')

report=dict(frozen_source='f48c8461b3b6cb26c5ab2a79f2b51c444e94a0ec',checkout_head=subprocess.check_output(['git','-C',str(a.source),'rev-parse','HEAD'],text=True).strip(),cpu_affinity=[4],
            scope='Necessary source-field projections only; not damage/physics/attribution/engine qualification',cases=cases,cases_total=len(cases),expectations_met=sum(x['met_expectation'] for x in cases),
            false_accepts=[x['name'] for x in cases if not x['expected_accepted'] and x['actual_accepted']],false_rejects=[x['name'] for x in cases if x['expected_accepted'] and not x['actual_accepted']])
(a.output/'results.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:x for k,x in report.items() if k!='cases'},indent=2));raise SystemExit(report['expectations_met']!=len(cases))
