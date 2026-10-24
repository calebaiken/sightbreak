#!/usr/bin/env python3
"""Read-only reconstruction of stored living/route/focus observations, no UI call."""
import ast
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
from PIL import Image

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[3]
RAW=ROOT/'.local/windows40089125575/full/offline-input'
r=json.loads((RAW/'results.json').read_text())
actions=json.loads((RAW/'actions.json').read_text())
checks=[]
def check(name,value):
    checks.append({'name':name,'passed':bool(value)})
def finite(x):
    return type(x) in (int,float) and math.isfinite(x)
def semantic(a,b):
    if type(a) is bool or type(b) is bool:return type(a) is bool and type(b) is bool and a is b
    if finite(a) and finite(b):return a==b
    if isinstance(a,dict) and isinstance(b,dict):return a.keys()==b.keys() and all(semantic(a[k],b[k]) for k in a)
    if isinstance(a,list) and isinstance(b,list):return len(a)==len(b) and all(semantic(x,y) for x,y in zip(a,b))
    return type(a) is type(b) and a==b

def brief(s):
    actor=s.get('local_actor',{})
    return {k:s.get(k) for k in ('phase','round_number','elapsed','wall_msec','simulation_tick','drawn_frames')}|{'actor':{k:actor.get(k) for k in ('id','deaths','alive','health','weapon','ammo','reserve','position','credits')},'ui':s.get('ui'),'input':s.get('local_input')}
check('literal passed true',r['passed'] is True)
check('whole elapsed within original300',finite(r['elapsed_seconds']) and 0<r['elapsed_seconds']<=300)
check('normal exits0 and no cleanup errors',type(r['initial_exit']) is int and type(r['reopened_exit']) is int and r['initial_exit']==r['reopened_exit']==0 and r['cleanup_errors']==[])
check('completion-driven WM_CLOSE and audit-success path',r['clean_exit'] is True and r['exit_method']=='completion-driven WM_CLOSE')
check('controller source hash',r['controller_sha256']==hashlib.sha256((ROOT/'scripts/verify_offline_export.py').read_bytes()).hexdigest())
route=r['settings_cover_route'];states=route['observations'];start=route['start'];actor=start['local_actor']
check('original fixed route complete',route['status']=='FIXED_ROUTE_REACHED' and route['requested']==[-7.8,-21.0] and route['remaining_original_second_live_budget']>0)
for i,s in enumerate(states):
    q=s['local_actor'];u=s['ui'];inp=s['local_input'];pos=q['position']
    check('route state'+str(i)+' exact context',s['schema']==1 and type(s['schema']) is int and s['scope']=='debug_offline_read_only_observation' and s['scenario']=='standard' and s['phase']=='live' and type(s['round_number']) is int and s['round_number']==2 and type(q['id']) is int and q['id']==1 and q['alive'] is True and finite(q['health']) and 0<q['health']<=100 and s['time_scale']==1 and u['screen']=='game' and u['focused'] is True and u['paused'] is False and u['scoreboard_visible'] is False)
    check('route state'+str(i)+' original corridor/life/ammo',all(finite(x) for x in pos+q['velocity']) and -8.5<=pos[0]<=-3.9 and -.1<=pos[1]<=.1 and -21.75<=pos[2]<=-20.25 and q['deaths']==actor['deaths'] and q['team']==0 and q['weapon']=='smg' and type(q['ammo']) is int and q['ammo']==30 and type(q['reserve']) is int and q['reserve']==120 and all(inp[k] is False for k in ('fire','interact','reload')) and u['waiting_for_input_release'] is False)
    check('route state'+str(i)+' counter types/order',all(type(s[k]) is int and s[k]>=0 for k in ('wall_msec','simulation_tick')) and (i==0 or all(s[k]>=states[i-1][k] for k in ('wall_msec','simulation_tick'))))
end=route['after'];endpoint=route['endpoint'];speed=math.hypot(end['local_actor']['velocity'][0],end['local_actor']['velocity'][2])
check('route actual neutral/stopped endpoint original.45 tolerance',endpoint==end['local_actor']['position'] and math.hypot(endpoint[0]+7.8,endpoint[2]+21)<.45 and end['local_input']['move']==[0,0] and speed<=.05)
pulses=route['native_pulses'];pulse_facts=[]
for i,q in enumerate(pulses):
    h=q['hold_until_monotonic'];deadline=q['absolute_deadline'];first=q['first_wait'];last=q['last_wait']
    check('pulse'+str(i)+' source status/release',q['status']=='API_RETURNED_WITH_OS_RELEASE' and q['release_complete'] is True and q['release_errors']==[] and q['keys']==q['attempted_keys']==q['released_keys'])
    check('pulse'+str(i)+' fixed software boundary/deadline',all(finite(q[k]) for k in ('requested_seconds','absolute_deadline','hold_until_monotonic','finished_monotonic','operation_initial_monotonic','elapsed_watchdog_start','elapsed_watchdog_budget_seconds')) and 0<q['requested_seconds']<=2.5 and h<=deadline and h<=q['finished_monotonic']<deadline and q['elapsed_watchdog_budget_seconds']==deadline-q['operation_initial_monotonic'])
    check('pulse'+str(i)+' literal residual request counters',type(q['sleep_calls']) is int and q['sleep_calls']>=1 and all(0<x['requested_sleep_seconds']<=h-x['before_monotonic'] for x in (first,last)) and last['after_monotonic']>=h)
    pulse_facts.append({k:q[k] for k in ('keys','requested_seconds','absolute_deadline','operation_initial_monotonic','elapsed_watchdog_budget_seconds','hold_until_monotonic','first_wait','last_wait','sleep_calls','finished_monotonic','release_complete')})
partial=json.loads((OUT/'PARTIAL_ROUTE_PULSES.json').read_text())
check('partial selected array exactly matches complete native result',json.dumps(partial['original_array_values'],sort_keys=True)==json.dumps(pulses,sort_keys=True))
node=next(n for n in ast.parse((ROOT/'scripts/verify_offline_export.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='require_living_capture_phase')
ns={};exec(compile(ast.Module(body=[node],type_ignores=[]),'require_living_capture_phase','exec'),ns)
fences=[]
for name,round_number,pid,trace in [('06c-next-round',2,r['commands'][0]['pid'],'initial-offline-trace'),('10-reopened-loaded-settings',1,r['commands'][1]['pid'],'restart-profile-trace')]:
    f=r['phase_capture_fences'][name];ordered=[f[k] for k in ('acknowledged','ready','before_capture','after_capture_barrier','after_capture')]
    for index,s in enumerate(ordered):
        try:ns['require_living_capture_phase'](s,1,round_number);valid=True
        except Exception:valid=False
        check(name+' living fence state'+str(index),valid)
    check(name+' original two frames and fresh postcapture barrier',ordered[1]['drawn_frames']>=ordered[0]['drawn_frames']+2 and all(ordered[i+1]['wall_msec']>ordered[i]['wall_msec'] for i in range(4)) and all(ordered[i+1]['simulation_tick']>=ordered[i]['simulation_tick'] for i in range(4)))
    for key in ('binding_before_capture','binding_after_capture'):
        b=f[key]
        check(name+key+' source/PID/trace binding',b['process_pid']==pid and b['process_running'] is True and b['trace_directory'].endswith(trace) and b['source']==r['source'])
    fences.append({'name':name,'frames':[s['drawn_frames'] for s in ordered],'ticks':[s['simulation_tick'] for s in ordered],'remaining_budget':f['remaining_original_budget_seconds']})
settings=r['native_settings_resume'];pb=settings['paused_before_settings'];pa=settings['paused_after_settings']
check('settings actual same paused life/time/health',all(x['ui']['paused'] is True for x in (pb,pa)) and pb['elapsed']==pa['elapsed'] and pb['simulation_tick']==pa['simulation_tick'] and pb['local_actor']['health']==pa['local_actor']['health'] and pb['local_actor']['id']==pa['local_actor']['id']==1)
check('explicit resume preserves original life/round and frames',settings['same_living_player_required'] is True and settings['transition_watchdog_seconds']==10 and all(x['phase']=='live' and x['round_number']==2 and x['local_actor']['alive'] is True and x['local_actor']['id']==1 and x['ui']['paused'] is False for x in (settings['resumed'],settings['capture_ready'],settings['after_capture'])) and settings['capture_ready']['drawn_frames']>=settings['resumed']['drawn_frames']+2)
focus=r['native_focus_recovery'];ns={};exec(compile((ROOT/'scripts/native_focus_fence.py').read_text(),'native_focus_fence.py','exec'),ns)
focus_states=[('baseline',focus['context_fence']['baseline'],True,False,False),('held',focus['held_input_acknowledged'],True,False,False),('lost',focus['lost'],False,True,False),('restored',focus['restored_paused'],True,True,False),('released',focus['released'],True,False,True),('fresh_before',focus['fresh_press']['before_key'],True,False,True),('fresh_moved',focus['fresh_press_movement'],True,False,False)]
for name,s in enumerate(focus['held_neutral_samples']):focus_states.append(('held_neutral'+str(name),s,True,False,False))
for name,pair in focus['capture_context'].items():
    for which,s in pair.items():focus_states.append((name+which,s,True,name.startswith('11a'),False))
fence=ns['FocusContextFence'](focus['context_fence']['baseline'],{})
for name,s,f,p,released in sorted(focus_states,key=lambda value:value[1]['wall_msec']):
    try:fence.require(s,name,focused=f,paused=p,released=released);valid=True
    except Exception:valid=False
    check('focus '+name+' original context guard',valid)
check('focus consumed held controls',focus['held_input_acknowledged']['local_input']['fire'] is True and focus['held_input_acknowledged']['local_input']['move']!=[0,0])
check('focus loss freezes time until explicit resume',focus['lost']['elapsed']==focus['restored_paused']['elapsed'] and focus['lost']['simulation_tick']==focus['restored_paused']['simulation_tick'])
neutral=focus['held_neutral_samples'];check('held guards neutral and final stable position',all(s['local_input']['move']==[0,0] and s['local_input']['fire'] is False for s in neutral) and neutral[-1]['local_actor']['position']==neutral[-2]['local_actor']['position'])
before=focus['fresh_press']['before_key'];moved=focus['fresh_press_movement'];check('fresh native W produced new actual movement',focus['fresh_press']['status']=='LIVING_MOVEMENT_OBSERVED' and focus['fresh_press']['key_down_dispatched'] is True and moved['simulation_tick']>before['simulation_tick'] and moved['local_input']['move']!=[0,0] and moved['local_actor']['position']!=before['local_actor']['position'])
initial=[json.loads(x) for x in (RAW/'initial-offline-trace/events.jsonl').read_text().splitlines()];reopened=[json.loads(x) for x in (RAW/'restart-profile-trace/events.jsonl').read_text().splitlines()];disk=json.loads((RAW/'state/roaming/Godot/app_userdata/SIGHTBREAK/offline_training.json').read_text())
check('both ordinary stock trace initializations',all(x[0]['initial_conditions']=='stock_spawns_teams_random_seeds' and x[0]['protocol']==6 and x[0]['prediction_enabled'] is False for x in (initial,reopened)))
check('reopened runtime profile equals exact final stored settings',semantic(reopened[0]['initial_profile'],disk) and r['settings_restart_equal'] is True and r['settings_loaded_into_reopened_process'] is True and r['incomplete_training_unchanged_after_reopened_exit'] is True)
check('unfinished matches earned no training progression',all(semantic(initial[0]['initial_profile'][k],disk[k]) for k in ('credits','xp','matches','wins','kills','deaths','history')))
check('actual sensitivity setting changed and loaded',initial[0]['initial_profile']['settings']['sensitivity']==.0028 and disk['settings']['sensitivity']==.0051)
images=[]
for capture in r['captures']:
    path=RAW/(capture['name']+'.png')
    with Image.open(path) as im:size=im.size;im.verify()
    check('native original image '+capture['name'],size==(976,549));images.append({'name':capture['name'],'size':list(size),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
report={'scope':'Independent actual stored-data/source-predicate reconstruction; no UI/native call or new test','run_id':40089125575,'checks':checks,'failures':[c['name'] for c in checks if not c['passed']],'route':{'status':route['status'],'observations':len(states),'start':brief(start),'after':brief(end),'endpoint':endpoint,'remaining_original_budget':route['remaining_original_second_live_budget']},'pulse_facts':pulse_facts,'repeated_residual_wait_observed':any(x['sleep_calls']>1 for x in pulses),'physical_timing_or_prior_cause_established':False,'capture_fences':fences,'focus':{'status':focus['context_fence']['status'],'samples':len(focus_states),'fresh_before':brief(before),'fresh_moved':brief(moved),'fresh_displacement_m':math.dist(before['local_actor']['position'],moved['local_actor']['position'])},'profile':{'initial_sensitivity':.0028,'stored_and_reopened_sensitivity':disk['settings']['sensitivity'],'credits':disk['credits'],'xp':disk['xp'],'scope':disk['scope']},'hud':{k:r[k] for k in ('fired_hud','reloaded_hud','resumed_hud')},'images':images,'cleanup_limits':'Source-bound success path reaches original Windows job descendant predicate; raw query bytes and every short-lived/escaped process are not independently sampled'}
(OUT/'LIVING_ROUTE_FOCUS_REVIEW.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'checks':len(checks),'failures':report['failures'],'route_endpoint':endpoint,'pulses':len(pulses),'repeat_residual_observed':report['repeated_residual_wait_observed'],'focus_movement_m':report['focus']['fresh_displacement_m'],'images':len(images)}))
