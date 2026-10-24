"""Isolated persistent focus predicate graph; not the withheld fixture compiler."""
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
BASE=json.loads(Path('/workspace/reviews/shutdown-study-evidence-independent-20261024/docs/reports/gauntlet/shutdown-study-evidence-independent-20261024/final-source-r1/own-independent/baseline/results.json').read_bytes())
CASES=[]

def graph(result):
    focus=result['native_focus_recovery'];rows=[];held=set()
    def emit(event,**fields):rows.append(dict(event=event,held_keys=sorted(held),**fields))
    def key(name,down):
        emit('key_before',key=name,down=down);(held.add if down else held.discard)(name);emit('key_after',key=name,down=down)
    def wait(label,budget):emit('wait_begin',label=label,budget_seconds=budget);emit('wait_completed',label=label)
    def observed(label,state,budget=10):wait(label,budget);emit('offline_observation',label=label,state=copy.deepcopy(state))
    def capture(name):emit('capture_begin',capture=name);emit('capture_end',capture=name)
    capture('10-reopened-loaded-settings')
    observed('Fresh stock match reaches a living active player before native focus loss',focus['context_fence']['baseline'],60)
    key('w',True);emit('button',down=True)
    observed('Game consumed physical W and LMB before native focus loss',focus['held_input_acknowledged'])
    emit('native_focus_held_input_acknowledged',state=copy.deepcopy(focus['held_input_acknowledged']))
    emit('native_focus_loss_before',method='ShowWindow(SW_MINIMIZE)');emit('native_focus_loss_after')
    observed('Native focus loss pauses actual offline match',focus['lost'])
    emit('native_focus_restore_before');wait('Restore actual native input focus',10);emit('native_focus_restore_after')
    observed('Actual game observes restored focus',focus['restored_paused'])
    capture('11a-restored-focus-still-paused');key('Escape',True);key('Escape',False)
    neutral=focus['held_neutral_samples']
    observed('Explicit resume with W and LMB still physically held',neutral[0])
    for state in neutral[1:-2]:observed('Neutral held input while ordinary inertia settles',state)
    for index,state in enumerate(neutral[-2:],1):observed('Fresh held-input guard sample '+str(index),state)
    capture('11b-resumed-held-input-neutral');key('w',False);emit('button',down=False)
    observed('Released held focus-test controls',focus['released']);key('w',True)
    observed('Fresh W press moves actual player after focus recovery',focus['fresh_press_movement']);key('w',False)
    capture('11c-fresh-press-movement')
    for index,row in enumerate(rows):row['seconds']=index/10
    return rows

def sync(state):
    state['actors']=[copy.deepcopy(state['local_actor']) if actor['id']==state['local_actor']['id'] else actor for actor in state['actors']]

def inertia(result,count):
    receipt=result['native_focus_recovery'];base=copy.deepcopy(receipt['held_neutral_samples'][0]);states=[]
    walls=[16400]+[16400+150*(index+1)//count for index in range(count)]+[16600,16650] if count else [16400,16500,16600]
    for index,wall in enumerate(walls):
        state=copy.deepcopy(base);state.update(wall_msec=wall,elapsed=wall/1000,simulation_tick=wall//16,drawn_frames=wall//16)
        state['frame_diagnostics']['drawn_frames']=wall//16
        state['local_actor']['velocity']=[.1 if count and index<count else 0.,0.,0.];sync(state);states.append(state)
    receipt['held_neutral_samples']=states
    receipt['capture_context']['11b-resumed-held-input-neutral']={field:copy.deepcopy(states[-1]) for field in ('before','after')}

def run(name,expected,mutate=lambda row:None,change_actions=lambda rows:None):
    result=copy.deepcopy(BASE);mutate(result);actions=graph(result);change_actions(actions)
    checker=evidence.Evidence('/isolated-focus-predicate-only',None);checker.result_data=result;checker.actions=actions
    error=None
    try:
        model=evidence.ProducerLinks(checker);model.held_keys();model.focus()
    except (ValueError,TypeError,KeyError,IndexError) as caught:error=type(caught).__name__+': '+str(caught)
    CASES.append(dict(name=name,expected_valid=expected,actual_valid=error is None,error=error,result=result,actions=actions))

def main():
    assert os.sched_getaffinity(0)=={4}
    with patch('subprocess.Popen',side_effect=AssertionError('process forbidden')),patch('ctypes.CDLL',side_effect=AssertionError('API forbidden')),patch('os.kill',side_effect=AssertionError('signal forbidden')):
        for count in range(3):run('declared-inertia-iterations-'+str(count),True,lambda r,count=count:inertia(r,count))
        for field in ('held_input_acknowledged','lost','restored_paused','released','fresh_press_movement'):
            for key,value in [('alive',False),('deaths',7),('health',0)]:
                def actor(result,field=field,key=key,value=value):
                    state=result['native_focus_recovery'][field];state['local_actor'][key]=value;sync(state)
                run(field+'/'+key,False,actor)
        for index in range(3):
            for field,value in [('fire',True),('reload',True),('interact',True),('move',[1,0])]:
                run('guard'+str(index)+'/'+field,False,lambda r,index=index,field=field,value=value:r['native_focus_recovery']['held_neutral_samples'][index]['local_input'].__setitem__(field,value))
        for key in ('native_focus_loss_before','native_focus_loss_after','native_focus_restore_before','native_focus_restore_after','native_focus_held_input_acknowledged'):
            run('missing-'+key,False,change_actions=lambda rows,key=key:rows.__setitem__(slice(None),[r for r in rows if r['event']!=key]))
        for index in (1,2):
            def omitted(rows,index=index):
                matches=[i for i,row in enumerate(rows) if row['event']=='offline_observation' and row['label'].startswith('Fresh held-input guard sample')]
                rows.pop(matches[index-1])
            run('missing-guard-return-'+str(index),False,change_actions=omitted)
        def omit_inertia(rows):
            for index,row in enumerate(rows):
                if row.get('label')=='Neutral held input while ordinary inertia settles' and row['event']=='offline_observation':rows.pop(index);break
        run('two-inertia-but-one-return-missing',False,lambda r:inertia(r,2),omit_inertia)
        def unfocused_after_b(result):result['native_focus_recovery']['capture_context']['11b-resumed-held-input-neutral']['after']['ui']['focused']=False
        run('lost-context-after-neutral-capture',False,unfocused_after_b)
        # Source does not apply check_guard after11b; a later fire flag there
        # alone does not invalidate the retained live/focus context predicate.
        def permitted_after_b(result):result['native_focus_recovery']['capture_context']['11b-resumed-held-input-neutral']['after']['local_input']['fire']=True
        run('source-permitted-non-guard-after11b',True,permitted_after_b)
    out=Path(__file__).parent
    with gzip.open(out/'focus-results.jsonl.gz','wt',encoding='utf-8') as stream:
        for row in CASES:stream.write(json.dumps(row,allow_nan=False)+'\n')
    wrong=[r['name'] for r in CASES if r['expected_valid']!=r['actual_valid']]
    summary=dict(scope='Isolated focus/held source model, no whole-flow or withheld proposal execution',cases=len(CASES),mismatches=wrong,source_sha256=hashlib.sha256((ROOT/'scripts/shutdown_study_evidence.py').read_bytes()).hexdigest(),actual_native_invocations=0)
    (out/'FOCUS_SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary));return bool(wrong)

if __name__=='__main__':raise SystemExit(main())
