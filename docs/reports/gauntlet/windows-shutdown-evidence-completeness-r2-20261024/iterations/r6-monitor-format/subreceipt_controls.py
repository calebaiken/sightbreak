"""Isolated HUD/reload/settings graph; no withheld consumer/helper invocation."""
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
from shutdown_evidence_fixtures import _snapshot
BASE=json.loads(Path('/workspace/reviews/shutdown-study-evidence-independent-20261024/docs/reports/gauntlet/shutdown-study-evidence-independent-20261024/final-source-r1/own-independent/baseline/results.json').read_bytes())
CASES=[]

def graph(result):
    rows=[];held=set();now=0.;ocr=copy.deepcopy(result['ocr_commands'])
    def emit(event,**fields):
        nonlocal now
        now+=.01;row=dict(event=event,seconds=now,held_keys=sorted(held),**fields);rows.append(row);return row
    def key(name,down):emit('key_before',key=name,down=down);(held.add if down else held.discard)(name);emit('key_after',key=name,down=down)
    def direct(down,scope):(held.add if down else held.discard)('Escape');emit('key_after',key='Escape',down=down,scope=scope)
    def observed(label,state,budget=5):
        emit('wait_begin',label=label,budget_seconds=budget);emit('wait_completed',label=label);emit('offline_observation',label=label,state=copy.deepcopy(state))
    def capture(name):emit('capture_begin',capture=name);emit('capture_end',capture=name)
    def read(number):
        nonlocal now
        ocr[number-1]['started_seconds']=now;now+=.02;ocr[number-1]['finished_seconds']=now
    def hud(name,first):
        nonlocal now
        receipt=next(row for row in result['hud_analysis_pauses'] if row['capture']==name)
        key('Escape',True);now+=.1;direct(False,'saved_hud_analysis')
        observed('Native pause before saved-HUD OCR: '+name,receipt['paused'],10)
        read(first);read(first+1)
        observed('Fresh paused observation after saved-HUD OCR: '+name,receipt['after_analysis'],5)
        if receipt['resume_after_analysis']:
            direct(True,'saved_hud_analysis_cleanup');now+=.1;direct(False,'saved_hud_analysis')
            observed('Explicit native resume after saved-HUD OCR: '+name,receipt['resumed'],10)
    reload=result['native_reload']
    for name in evidence.CAPTURES:
        if name=='05-after-fire':observed('Authoritative depleted sidearm and two drawn frames',reload['before'])
        if name=='06-after-reload':
            reload['input_seconds']=now;key('r',True)
            observed('Real R input starts authoritative offline reload',reload['started']);key('r',False)
            observed('Authoritative offline reload completion',reload['completed'],15)
            observed('Two rendered frames after authoritative reload transfer',reload['capture_ready'])
            reload['wall_seconds_after_input']=now-reload['input_seconds']
        if name=='07d-explicit-resume':
            settings=result['native_settings_resume'];observed('Fresh paused player after native settings change',settings['paused_after_settings'])
            key('Escape',True);observed('Actual living player explicitly resumes after field settings',settings['resumed'],5.)
            direct(False,'field_settings_resume');observed('Two drawn frames after explicit native settings resume',settings['capture_ready'],4.)
        capture(name)
        if name=='05-after-fire':hud(name,1)
        elif name=='06-after-reload':hud(name,3)
        elif name=='06d-funded-requisition':read(5)
        elif name=='06e-purchased-smg':hud(name,6)
        elif name=='06f-switched-sidearm':hud(name,8)
        elif name=='06g-switched-primary':hud(name,10)
        elif name=='07-field-menu':read(12)
        elif name=='07b-field-settings':read(13)
        elif name=='07d-explicit-resume':hud(name,14);read(16)
    return rows,ocr

def sync(state):
    state['actors']=[copy.deepcopy(state['local_actor']) if row['id']==state['local_actor']['id'] else row for row in state['actors']]

def run(name,expected,mutate=lambda row:None,post=lambda result,actions,ocr:None):
    result=copy.deepcopy(BASE);result['native_reload']['before']=_snapshot(20000,phase='live',ammo=13)
    mutate(result);actions,ocr=graph(result);post(result,actions,ocr)
    checker=evidence.Evidence('/unit-subreceipt-only',None);checker.result_data=result;checker.actions=actions;checker.ocr=ocr
    error=None
    try:
        model=evidence.ProducerLinks(checker)
        for method in ('held_keys','hud_pauses','reload','settings'):getattr(model,method)()
    except (ValueError,TypeError,KeyError,IndexError) as caught:error=type(caught).__name__+': '+str(caught)
    CASES.append(dict(name=name,expected_valid=expected,actual_valid=error is None,error=error,result=result,actions=actions,ocr=ocr))

def main():
    assert os.sched_getaffinity(0)=={4}
    with patch('subprocess.Popen',side_effect=AssertionError('process forbidden')),patch('ctypes.CDLL',side_effect=AssertionError('API forbidden')),patch('os.kill',side_effect=AssertionError('signal forbidden')):
        run('source-subreceipt-operation-graph',True)
        for index in range(6):
            for fault in ('not-paused','elapsed-advanced','health-changed','wrong-scope','wrong-resume-policy'):
                def mutate(result,index=index,fault=fault):
                    row=result['hud_analysis_pauses'][index]
                    if fault=='not-paused':row['paused']['ui']['paused']=False
                    elif fault=='elapsed-advanced':row['after_analysis']['elapsed']+=1
                    elif fault=='health-changed':row['after_analysis']['local_actor']['health']-=1;sync(row['after_analysis'])
                    elif fault=='wrong-scope':row['scope']='invented'
                    else:row['resume_after_analysis']=not row['resume_after_analysis']
                # A source policy mutation in the fixture grammar may need its
                # missing resumed branch: preserve the malformed input as data.
                if fault=='wrong-resume-policy':
                    def mutate(result,index=index):
                        row=result['hud_analysis_pauses'][index];row['resume_after_analysis']=not row['resume_after_analysis']
                        row.setdefault('resumed',copy.deepcopy(row['before']))
                run(f'HUD{index}/{fault}',False,mutate)
        for field in ('before','started','completed','capture_ready','after_capture'):
            for fault in ('dead','wrong-round','wrong-weapon'):
                def mutate(result,field=field,fault=fault):
                    state=result['native_reload'][field]
                    if fault=='dead':state['local_actor']['alive']=False;sync(state)
                    elif fault=='wrong-round':state['round_number']+=1
                    else:state['local_actor']['weapon']='smg';sync(state)
                run('reload/'+field+'/'+fault,False,mutate)
        for field,value in [('whole_flow_deadline_unchanged',False),('completion_watchdog_seconds',True),('observed_simulation_seconds',100)]:
            run('reload/constant/'+field,False,lambda r,field=field,value=value:r['native_reload'].__setitem__(field,value))
        run('reload/wall-duration-outside-operation',False,post=lambda r,a,o:r['native_reload'].__setitem__('wall_seconds_after_input',100))
        run('reload/input-before-HUD',False,post=lambda r,a,o:r['native_reload'].__setitem__('input_seconds',0.))
        for field,value in [('same_living_player_required',False),('transition_watchdog_seconds',True)]:
            run('settings/constant/'+field,False,lambda r,field=field,value=value:r['native_settings_resume'].__setitem__(field,value))
        for field in ('paused_after_settings','resumed','capture_ready','after_capture'):
            run('settings/'+field+'/different-actor',False,lambda r,field=field:r['native_settings_resume'][field].__setitem__('local_actor',copy.deepcopy(r['native_settings_resume'][field]['actors'][1])))
        def allowed_after(result):
            state=result['native_settings_resume']['after_capture'];state['ui'].update(paused=True,mouse_mode=0)
        run('source-allows-paused-after-settings-capture',True,allowed_after)
    out=Path(__file__).parent
    with gzip.open(out/'subreceipt-results.jsonl.gz','wt',encoding='utf-8') as stream:
        for row in CASES:stream.write(json.dumps(row,allow_nan=False)+'\n')
    wrong=[r['name'] for r in CASES if r['expected_valid']!=r['actual_valid']]
    summary=dict(scope='Isolated HUD/reload/settings and held-source graph, no whole producer/helper/consumer run',cases=len(CASES),mismatches=wrong,source_sha256=hashlib.sha256((ROOT/'scripts/shutdown_study_evidence.py').read_bytes()).hexdigest(),actual_native_invocations=0)
    (out/'SUBRECEIPT_SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary));return bool(wrong)

if __name__=='__main__':raise SystemExit(main())
