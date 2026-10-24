"""Registered ownership-link unit model, not a whole-flow/native verdict."""
import copy
import gzip
import hashlib
import json
from pathlib import Path
import sys
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[6]
sys.path.insert(0,str(ROOT/'scripts'))
import shutdown_study_evidence as evidence

ORIGIN=Path('/workspace/reviews/shutdown-study-evidence-independent-20261024/docs/reports/gauntlet/shutdown-study-evidence-independent-20261024/final-source-r1/own-independent')
BASE=json.loads((ORIGIN/'BASELINE_CONTEXT.json').read_bytes())
RESULT=json.loads((ORIGIN/'baseline/results.json').read_bytes())
ACTIONS=json.loads((ORIGIN/'baseline/actions.json').read_bytes())
CASES=[]

def queries(context):
    trial=context['trial']
    return [trial['job_queries'][0],*[row['job'] for row in trial['observations']],trial['job_queries'][1]]

def run(name,expected,mutate=lambda value:None):
    context=copy.deepcopy(BASE);mutate(context)
    checker=evidence.Evidence(context['trial']['output'],context)
    checker.trial=context['trial'];checker.result_data=RESULT
    checker.commands=RESULT['commands'];checker.pids={row['name']:row['pid'] for row in RESULT['commands']}
    checker.actions=ACTIONS;checker.ocr=RESULT['ocr_commands']
    error=None
    try:checker.process_and_closes()
    except (ValueError,TypeError,KeyError,IndexError) as caught:error=type(caught).__name__+': '+str(caught)
    actual=error is None
    CASES.append(dict(name=name,expected_valid=expected,actual_valid=actual,error=error,context=context))

def main():
    import os
    assert os.sched_getaffinity(0)=={4}
    with patch('subprocess.Popen',side_effect=AssertionError('process forbidden')),patch('ctypes.CDLL',side_effect=AssertionError('native forbidden')),patch('os.kill',side_effect=AssertionError('signal forbidden')):
        run('source-shaped-job-history',True)
        # Do not infer that a sampled live process must still be alive at the
        # later completion query: these source calls are not one atomic read.
        def exit_during_query(context):
            launch=context['trial']['observations'][2]['job']
            for held in launch['held_processes']:
                if held['pid']==RESULT['commands'][1]['pid']:held.update(observed_exited=True,exit_code=0)
        run('exit-between-live-list-and-completion-sampling',True,exit_during_query)
        for index in range(6):
            for key,bad in [('job_handle',True),('job_handle',2**64),('baseline_pid',True),('total_processes',2**32),('terminated_processes',2**32),('active_processes',True),('processes',[]),('held_processes',[])]:
                run(f'query{index}/{key}/{bad}',False,lambda c,index=index,key=key,bad=bad:queries(c)[index].__setitem__(key,bad))
            for collection in ('processes','held_processes'):
                for field,bad in [('pid',True),('pid',2**32),('creation_filetime',True),('creation_filetime',2**64),('handle_value',True),('handle_value',2**64)]:
                    run(f'query{index}/{collection}/{field}/{bad}',False,lambda c,index=index,collection=collection,field=field,bad=bad:queries(c)[index][collection][0].__setitem__(field,bad))
            for bad in (True,2**32):
                run(f'query{index}/exit_code/{bad}',False,lambda c,index=index,bad=bad:queries(c)[index]['held_processes'][0].__setitem__('exit_code',bad))
        for index in range(4):
            run(f'callback{index}/wrong-label',False,lambda c,index=index:c['trial']['observations'][index]['job'].__setitem__('label','trial4/wrong'))
            run(f'callback{index}/earlier-query',False,lambda c,index=index:c['trial']['observations'][index]['job'].__setitem__('monotonic',c['trial']['observations'][index]['monotonic']-1))
            run(f'callback{index}/query-after-trial',False,lambda c,index=index:c['trial']['observations'][index]['job'].__setitem__('monotonic',c['trial']['finished_monotonic']+1))
        run('before-query-after-start',False,lambda c:c['trial']['job_queries'][0].__setitem__('monotonic',c['trial']['started_monotonic']+1))
        run('after-query-before-finish',False,lambda c:c['trial']['job_queries'][1].__setitem__('monotonic',c['trial']['finished_monotonic']-1))
        def lose_history(context):
            for row in context['trial']['observations'][2]['job']['held_processes'][:]:
                if row['pid']==RESULT['commands'][0]['pid']:context['trial']['observations'][2]['job']['held_processes'].remove(row)
        run('completed-client-history-disappears',False,lose_history)
    out=Path(__file__).parent
    with gzip.open(out/'process-results.jsonl.gz','wt',encoding='utf-8') as stream:
        for row in CASES:stream.write(json.dumps(row,allow_nan=False)+'\n')
    mismatches=[row['name'] for row in CASES if row['expected_valid']!=row['actual_valid']]
    summary=dict(scope='Isolated process_and_closes source relation model; original baseline remains obsolete for full-source action completeness',source_sha256=hashlib.sha256((ROOT/'scripts/shutdown_study_evidence.py').read_bytes()).hexdigest(),cases=len(CASES),mismatches=mismatches,actual_native_invocations=0)
    (out/'PROCESS_SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary));return bool(mismatches)

if __name__=='__main__':raise SystemExit(main())
