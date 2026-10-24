"""Independent finite operation grammar for trace held-set serialization only."""
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
CASES=[]

def declared(operations):
    rows=[];held=set()
    def emit(event,**fields):rows.append(dict(event=event,held_keys=sorted(held),**fields))
    for operation in operations:
        kind=operation[0]
        if kind=='key':
            name,down=operation[1:];emit('key_before',key=name,down=down)
            (held.add if down else held.discard)(name);emit('key_after',key=name,down=down)
        elif kind=='direct':
            name,down,scope=operation[1:];(held.add if down else held.discard)(name)
            emit('key_after',key=name,down=down,scope=scope)
        elif kind=='wait':
            for event in ('wait_begin','wait_completed','offline_observation'):emit(event,label=operation[1])
        elif kind=='button':emit('button',down=operation[1])
        elif kind=='pulse':
            names=operation[1];emit('settings_route_native_pulse_before',keys=names,requested_seconds=.125)
            held.update(names)
            # Native key edges are receipt fields, never invented controller
            # key_before/after records. Success releases them before after trace.
            held.difference_update(names)
            emit('settings_route_native_pulse_after',receipt=dict(attempted_keys=names,release_complete=True))
        elif kind=='diagnostic-error':emit('capture_begin',native_state_error='declared diagnostics failure')
        else:raise AssertionError(kind)
    return rows

VALID=[
 [('key','r',True),('wait','reload starts'),('key','r',False)],
 [('key','Escape',True),('wait','explicit settings resume'),('direct','Escape',False,'field_settings_resume')],
 [('key','Escape',True),('direct','Escape',False,'saved_hud_analysis'),('wait','paused HUD'),('direct','Escape',True,'saved_hud_analysis_cleanup'),('direct','Escape',False,'saved_hud_analysis')],
 [('key','w',True),('button',True),('wait','held input'),('wait','lost focus'),('wait','restored focus'),('key','Escape',True),('key','Escape',False),('wait','logically neutral but physically held'),('key','w',False),('button',False),('wait','released controls'),('key','w',True),('wait','fresh movement'),('key','w',False)],
 [('pulse',['a'])],
 [('key','w',True),('key','Escape',True),('wait','nested held keys'),('key','Escape',False),('key','w',False)],
 [('diagnostic-error',)],
]

def run(name,expected,rows):
    checker=evidence.Evidence('/unit-model-only',None);checker.actions=rows;checker.result_data={}
    error=None
    try:evidence.ProducerLinks(checker).held_keys()
    except (ValueError,TypeError,KeyError,IndexError) as caught:error=type(caught).__name__+': '+str(caught)
    CASES.append(dict(name=name,expected_valid=expected,actual_valid=error is None,error=error,actions=rows))

def main():
    assert os.sched_getaffinity(0)=={4}
    with patch('subprocess.Popen',side_effect=AssertionError('process forbidden')),patch('ctypes.CDLL',side_effect=AssertionError('API forbidden')),patch('os.kill',side_effect=AssertionError('signal forbidden')):
        for ordinal,operations in enumerate(VALID):
            base=declared(operations);run('declared-source-grammar-'+str(ordinal),True,base)
            for index,row in enumerate(base):
                if row['held_keys']:
                    changed=copy.deepcopy(base);changed[index]['held_keys']=[];run(f'{ordinal}/lost-held/{index}',False,changed)
                    changed=copy.deepcopy(base);changed[index]['held_keys']+=changed[index]['held_keys'];run(f'{ordinal}/duplicated-held/{index}',False,changed)
                else:
                    changed=copy.deepcopy(base);changed[index]['held_keys']=['r'];run(f'{ordinal}/invented-held/{index}',False,changed)
                if row['event'] in ('key_before','key_after'):
                    changed=copy.deepcopy(base);changed.pop(index);run(f'{ordinal}/missing-edge/{index}',False,changed)
                    changed=copy.deepcopy(base);changed[index]['down']=int(changed[index]['down']);run(f'{ordinal}/bool-as-int/{index}',False,changed)
        for ordinal in range(6):
            base=declared(VALID[ordinal]);changed=copy.deepcopy(base)
            for row in changed:row['held_keys']=[]
            # A pulse emits only before/after and is already released at both
            # trace points; those two empty snapshots are source-correct.
            run('all-waits-empty-'+str(ordinal),ordinal==4,changed)
    out=Path(__file__).parent
    with gzip.open(out/'held-results.jsonl.gz','wt',encoding='utf-8') as stream:
        for row in CASES:stream.write(json.dumps(row,allow_nan=False)+'\n')
    wrong=[r['name'] for r in CASES if r['expected_valid']!=r['actual_valid']]
    summary=dict(scope='Pure held-key/source-action grammar only, not whole-flow or physical delivery',cases=len(CASES),mismatches=wrong,source_sha256=hashlib.sha256((ROOT/'scripts/shutdown_study_evidence.py').read_bytes()).hexdigest(),actual_native_invocations=0)
    (out/'HELD_SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary));return bool(wrong)

if __name__=='__main__':raise SystemExit(main())
