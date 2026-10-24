"""Pure named-transaction source oracle; does not run the held fixture proposal."""
import copy
import gzip
import hashlib
import json
import os
from pathlib import Path
import sys
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[6];sys.path.insert(0,str(ROOT/'scripts'))
import shutdown_study_evidence as evidence
ORIGIN=Path('/workspace/reviews/shutdown-study-evidence-independent-20261024/docs/reports/gauntlet/shutdown-study-evidence-independent-20261024/final-source-r1/own-independent/baseline/results.json')
BASE=json.loads(ORIGIN.read_bytes())['phase_capture_fences']
FIELDS=('acknowledged','ready','before_capture','after_capture_barrier','after_capture')
LABELS=('Named living buy phase','Two drawn frames before named capture','Fresh named context immediately before capture','Observation barrier after raw capture','Fresh named context beyond post-capture barrier')
CASES=[]

def sync(state):
    actor=state['local_actor'];state['actors']=[copy.deepcopy(actor) if row['id']==actor['id'] else row for row in state['actors']]

def graph(fences):
    rows=[]
    for name,fence in fences.items():
        def observed(field,label):
            rows.extend([dict(event='wait_begin',label=label+': '+name,budget_seconds=1),dict(event='wait_completed',label=label+': '+name),dict(event='offline_observation',label=label+': '+name,state=copy.deepcopy(fence[field]))])
        for field,label in zip(FIELDS[:3],LABELS[:3]):observed(field,label)
        rows.extend([dict(event='capture_begin',capture=name),dict(event='capture_end',capture=name)])
        for field,label in zip(FIELDS[3:],LABELS[3:]):observed(field,label)
    for index,row in enumerate(rows):row['seconds']=index/100
    return rows

def run(name,expected,mutate=lambda value:None,actions_change=lambda value:None):
    fences=copy.deepcopy(BASE);mutate(fences);actions=graph(fences);actions_change(actions)
    checker=evidence.Evidence('/synthetic-not-an-observed-trial',None)
    checker.result_data=dict(phase_capture_fences=fences);checker.actions=actions
    error=None
    try:evidence.ProducerLinks(checker).named_captures()
    except (ValueError,TypeError,KeyError,IndexError) as caught:error=type(caught).__name__+': '+str(caught)
    CASES.append(dict(name=name,expected_valid=expected,actual_valid=error is None,error=error,fences=fences,actions=actions))

def change_state(fences,name,field,key,value):
    state=fences[name][field]
    if key.startswith('actor.'):
        state['local_actor'][key.split('.')[1]]=value;sync(state)
    elif key.startswith('ui.'):state['ui'][key.split('.')[1]]=value
    else:state[key]=value

def main():
    assert os.sched_getaffinity(0)=={4}
    with patch('subprocess.Popen',side_effect=AssertionError('process forbidden')),patch('ctypes.CDLL',side_effect=AssertionError('API forbidden')),patch('os.kill',side_effect=AssertionError('signal forbidden')):
        run('source-shaped-two-transactions',True)
        def shared_frames(fences):
            for fence in fences.values():
                for field,frames in zip(FIELDS,(100,102,103,103,104)):
                    fence[field]['drawn_frames']=frames;fence[field]['frame_diagnostics']['drawn_frames']=frames
        run('two-frames-total-not-two-per-step',True,shared_frames)
        for name in BASE:
            for field in FIELDS:
                for key,bad in [('schema',True),('phase','live'),('scenario','fixture'),('actor.alive',False),('actor.health',0),('actor.health',101),('ui.focused',False),('ui.paused',True),('ui.scoreboard_visible',True),('ui.screen','menu'),('round_number',99),('wall_msec',True),('simulation_tick',True),('drawn_frames',True)]:
                    run(name+'/'+field+'/'+key,False,lambda f,name=name,field=field,key=key,bad=bad:change_state(f,name,field,key,bad))
                def actor(f,name=name,field=field):f[name][field]['local_actor']=copy.deepcopy(f[name][field]['actors'][1])
                run(name+'/'+field+'/different-valid-actor-projection',False,actor)
            for field in FIELDS[1:]:
                def missing_frames(f,name=name,field=field):
                    state=f[name][field];state['drawn_frames']=f[name]['acknowledged']['drawn_frames'];state['frame_diagnostics']['drawn_frames']=state['drawn_frames']
                run(name+'/'+field+'/below-two-frames',False,missing_frames)
            for position in range(1,5):
                run(name+'/'+FIELDS[position]+'/stale-wall',False,lambda f,name=name,position=position:f[name][FIELDS[position]].__setitem__('wall_msec',f[name][FIELDS[position-1]]['wall_msec']))
            run(name+'/watchdog-bool',False,lambda f,name=name:f[name].__setitem__('transition_watchdog_seconds',True))
        for ordinal in range(10):
            def omit(rows,ordinal=ordinal):
                index=[i for i,row in enumerate(rows) if row['event']=='offline_observation'][ordinal];rows.pop(index)
            run('missing-observed-return-'+str(ordinal),False,actions_change=omit)
        run('empty-transactions',False,lambda f:f.clear())
    out=Path(__file__).parent
    with gzip.open(out/'named-results.jsonl.gz','wt',encoding='utf-8') as stream:
        for row in CASES:stream.write(json.dumps(row,allow_nan=False)+'\n')
    wrong=[r['name'] for r in CASES if r['expected_valid']!=r['actual_valid']]
    summary=dict(scope='Isolated source named-capture predicate/action model, not whole flow or proposal execution',cases=len(CASES),mismatches=wrong,source_sha256=hashlib.sha256((ROOT/'scripts/shutdown_study_evidence.py').read_bytes()).hexdigest(),actual_native_invocations=0)
    (out/'NAMED_SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary));return bool(wrong)

if __name__=='__main__':raise SystemExit(main())
