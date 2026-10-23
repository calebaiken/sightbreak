#!/usr/bin/env python3
"""Mutate in-memory copies of actual rows; preserve all original evidence."""
import copy
import json
import sys
from pathlib import Path
from audit_raw import audit, parse

def falsifiers(records,repo):
    tests=[]
    def run(name,mutate):
        rows=copy.deepcopy(records)
        mutate(rows)
        try:
            audit(rows,repo)
        except (AssertionError,KeyError,TypeError) as exc:
            tests.append(dict(name=name,rejected=True,reason=str(exc)))
        else: raise AssertionError('False acceptance: '+name)
    def control(rows,name,step=0):return next(r for _,k,r in rows if k=='CONTROL_STEP' and r['label']=='control/'+name and r['step']==step)
    def case(rows):return next(r for _,k,r in rows if k=='CASE')
    def wrong_lane(rows):
        # Continuous wrong 20 m actor poses, retaining the claimed 2 m scenario
        # and original ray fields. The exact pose binding must reject first.
        for _,kind,r in rows:
            if kind!='CONTROL_STEP' or r['label']!='control/kill_rifle':continue
            for field in ['before','after_decision','after_action']:r[field]['position']=[-10.,0.,-20.]
            for field in ['enemy_before','enemy_after_decision','enemy_after_action']:r[field]['position']=[10.,0.,-20.]
            r['lane']['shooter']=[-10.,0.,-20.];r['lane']['target']=[10.,0.,-20.]
    def unconsumed_round(rows):
        # Preserve continuity after the actual kill while returning its spent
        # rifle round; header and claimed control success remain untouched.
        for _,kind,r in rows:
            if kind!='CONTROL_STEP' or r['label']!='control/kill_rifle':continue
            if r['step']>=2:r['after_action']['ammo']=1
            if r['step']>2:
                r['before']['ammo']=1;r['after_decision']['ammo']=1
    def illegal_transfer(rows):control(rows,'reload_rifle',19)['after_action']['ammo']=31
    def decision_target(rows):control(rows,'kill_rifle')['enemy_after_decision']['health']=9
    def decision_objective(rows):control(rows,'reload_smg')['objective_after_decision']['carrier']=6
    def snapshot_forgery(rows):control(rows,'kill_rifle',2)['elimination_events'][0]['shooter_state']['credits']=800
    def shot_no_damage(rows):control(rows,'kill_rifle',2)['damage_events']=[]
    def reward_missing(rows):control(rows,'kill_rifle',2)['after_action']['credits']=800
    def initial_cache(rows):
        r=case(rows)
        for field in ['before','after_decision']:r[field]['ammo_store'][r['scenario']['primary']]=[30,120]
    run('continuous_wrong_20m_control_lane',wrong_lane)
    run('continuous_unconsumed_kill_round',unconsumed_round)
    run('duplicate_matrix_identity',lambda rows:case(rows).__setitem__('label','wrong/cell'))
    run('decision_target_mutation',decision_target)
    run('decision_objective_mutation',decision_objective)
    run('illegal_reload_transfer',illegal_transfer)
    run('forged_elimination_snapshot',snapshot_forgery)
    run('actual_shot_without_damage_event',shot_no_damage)
    run('missing_kill_reward',reward_missing)
    run('unexpected_initial_active_cache',initial_cache)
    run('unsettled_world_query',lambda rows:control(rows,'reload_smg')['lane']['pose_settle'].__setitem__('after_frame',0))
    run('forged_ray_endpoint',lambda rows:control(rows,'reload_smg')['lane'].__setitem__('ray_to',[99.,0.,0.]))
    run('missing_positive_control',lambda rows:rows.__setitem__(slice(None),[entry for entry in rows if not (entry[1]=='CONTROL_STEP' and entry[2]['label']=='control/reload_marksman')]))
    run('terminal_control_not_bound',lambda rows:next(r for _,k,r in rows if k=='RESULT')['positive_controls'][0].__setitem__('shots',2))
    return dict(synthetic_mutations_of_actual_memory_copies=True,originals_modified=False,rejected=len(tests),cases=tests)

if __name__=='__main__':
    records,_=parse(Path(sys.argv[1]))
    print(json.dumps(falsifiers(records,Path(sys.argv[2])),indent=2,sort_keys=True))
