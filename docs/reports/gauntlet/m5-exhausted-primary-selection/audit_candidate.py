#!/usr/bin/env python3
"""Builder candidate audit adapted from independent b5fa18a1 audit_raw.py.

The original reviewer file is untouched. This adaptation is not independent
acceptance. It extends registration and expected selection, retains all-row
resource/event/geometry checks, and compares exact baseline request deltas.

Float tolerances cover Godot Vector3 float32 geometry and JSON rounding. This
checks observable snapshots/events, not unlogged transient planning events.
"""
import argparse
import copy
import gzip
import hashlib
import itertools
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

DT = .12
WEAPONS = ('sidearm','smg','rifle','marksman')
PRIMARIES = WEAPONS[1:]
DIFFICULTIES = ('easy','normal','hard')
TARGETS = [('near',6,True),('fallback_boundary',20,True),('far',24,True),('outside_sidearm',45.5,True),('outside_vision',60,True),('no_target',6,False)]
SETTINGS = [('idle_loaded',5,'exhausted','loaded'),('far_loaded',2,'exhausted','loaded'),('near_loaded',0,'exhausted','loaded'),('outside_sidearm_loaded',3,'exhausted','loaded'),('far_dry',2,'exhausted','dry'),('idle_unknown',5,'exhausted','unknown'),('far_reloadable_primary',2,'reloadable','loaded'),('near_reserve_only_sidearm',0,'exhausted','reserve_only')]
ACTOR_KEYS = set('actor_id actual_action_spread alive ammo ammo_store assists cooldowns credits crouching deaths deploy fire_previous floor_contact grenades health inventory kills pitch position recoil reload reserve smokes team velocity weapon yaw'.split())
OBJECTIVE_KEYS = set('attack_score carrier contributions defend_score elapsed interactions phase position progress round state tick time_left timer'.split())
SOLIDS = [((0,-.3,0),(48,.6,48)),((-24,3,0),(1,6,49)),((24,3,0),(1,6,49)),((0,3,24),(48,6,1)),((0,3,-24),(48,6,1))]
SOLIDS += [((x,1.55,z),(3,3.1,n)) for x,z,n in [(-7,-11,9),(7,-11,9),(-7,4,8),(7,4,8),(-20,0,5),(20,0,5)]]
SOLIDS += [((x,.65,z),(2.5,1.3,2.5)) for x,z in [(-14,-5),(14,-5),(-18,13),(18,13),(0,8),(-3,-1),(3,-1)]]
SOLIDS += [((x,.45,12.4),(1,.9,1)) for x in [-15,15]]
SOLIDS += [((x,4,z),(.18,8,.18)) for x,z in itertools.product([-22,22],[-18,16])]
SOLIDS += [((x,3.4,16),(.5,6.8,.5)) for x in [-21,21]]


def close(a,b,tol=1e-5):
    if isinstance(a,bool) or isinstance(b,bool):
        return type(a) is type(b) and a == b
    if isinstance(a,(int,float)) and isinstance(b,(int,float)):
        return math.isfinite(a) and math.isfinite(b) and abs(a-b) <= tol
    if type(a) is not type(b):
        return False
    if isinstance(a,dict):
        return a.keys() == b.keys() and all(close(a[k],b[k],tol) for k in a)
    if isinstance(a,list):
        return len(a) == len(b) and all(close(x,y,tol) for x,y in zip(a,b))
    return a == b


def add(a,b): return [x+y for x,y in zip(a,b)]
def sub(a,b): return [x-y for x,y in zip(a,b)]
def mul(a,t): return [x*t for x in a]
def dot(a,b): return sum(x*y for x,y in zip(a,b))
def norm(a): return math.sqrt(dot(a,a))
def overlap(a,b): return max(a[0],b[0]), min(a[1],b[1])


def slab(o,d,lo,hi):
    if abs(d)<1e-12:
        return (-math.inf,math.inf) if lo<=o<=hi else (math.inf,-math.inf)
    a,b=(lo-o)/d,(hi-o)/d
    return min(a,b),max(a,b)


def world_trace(origin,direction,limit):
    best = limit
    found = False
    for center,size in SOLIDS:
        span = (0,limit)
        for o,d,c,s in zip(origin,direction,center,size):
            span = overlap(span,slab(o,d,c-s/2,c+s/2))
        if span[0] <= span[1] and span[0] < best:
            best,found=span[0],True
    return best,found


def ellipsoid(o,d,c,r):
    u=[(x-y)/s for x,y,s in zip(o,c,r)]
    v=[x/s for x,s in zip(d,r)]
    a,b,c=dot(v,v),dot(u,v),dot(u,u)-1
    if c<=0: return 0
    disc=b*b-a*c
    if a<=0 or disc<0: return math.inf
    t=(-b-math.sqrt(disc))/a
    return t if t>=0 else math.inf


def sphere_span(o,d,r):
    a=dot(d,d)
    t=-dot(o,d)/a
    p=add(o,mul(d,t))
    h=r*r-dot(p,p)
    if h<=1e-6: return math.inf,-math.inf
    delta=math.sqrt(h/a)
    return t-delta,t+delta


def target_trace(origin,direction,target,limit):
    if not target['alive']: return limit,False,False
    # Initial target yaw is PI for team 0 and 0 for team 1. The volumes are
    # rotationally symmetric except the helmet's 0.005 m local z offset.
    yaw=target['yaw']; co,si=math.cos(yaw),math.sin(yaw)
    def local(v): return [co*v[0]-si*v[2],v[1],si*v[0]+co*v[2]]
    o,d=local(sub(origin,target['position'])),local(direction)
    body=sub(o,[0,.9,0]); half=.9-.31
    radial_a=d[0]*d[0]+d[2]*d[2]
    if radial_a<1e-12:
        radial=(-math.inf,math.inf) if .31**2-body[0]**2-body[2]**2>1e-6 else (math.inf,-math.inf)
    else:
        t=-(body[0]*d[0]+body[2]*d[2])/radial_a
        h=.31**2-(body[0]+d[0]*t)**2-(body[2]+d[2]*t)**2
        radial=(t-math.sqrt(h/radial_a),t+math.sqrt(h/radial_a)) if h>1e-6 else (math.inf,-math.inf)
    capsule=overlap(radial,slab(body[1],d[1],-half,half))
    for cap_y in [-half,half]:
        cap=sphere_span(sub(body,[0,cap_y,0]),d,.31)
        if cap[0]<cap[1]:
            capsule=cap if capsule[0]>=capsule[1] else (min(capsule[0],cap[0]),max(capsule[1],cap[1]))
    body_span=overlap(capsule,slab(body[1],d[1],-math.inf,1.38-.9))
    body_t=max(0,body_span[0]) if body_span[0]<body_span[1] and body_span[1]>=0 else math.inf
    head_t=min(ellipsoid(o,d,[0,1.56,0],[.16,.195,.165]),ellipsoid(o,d,[0,1.68,.005],[.175,.1175,.18]))
    nearest=min(body_t,head_t)
    return (nearest,True,head_t<body_t) if nearest<limit else (limit,False,False)


def parse(path):
    records=[]; other=[]
    text = gzip.decompress(path.read_bytes()).decode() if path.suffix == '.gz' else path.read_text()
    for line_no,line in enumerate(text.splitlines(),1):
        if line.startswith('BOT_EXHAUSTED_'):
            kind,data=line.split(' ',1)
            records.append((line_no,kind.removeprefix('BOT_EXHAUSTED_'),json.loads(data)))
        else: other.append((line_no,line))
    return records,other


def scenario(d,p,a,s,target,obj='none',stale=False):
    name,distance,visible=target
    return dict(difficulty=d,primary=p,active_resource=a,sidearm_resource=s,target=dict(name=name,distance=distance,visible=visible),objective=obj,stale_active_cache=stale)


def common_records():
    result=[]
    def case(group,s):
        label='/'.join([group,s['difficulty'],s['primary'],s['active_resource'],s['sidearm_resource'],s['target']['name'],s['objective']])
        result.append(('CASE',label,-1,s))
    for d,p in itertools.product(DIFFICULTIES,PRIMARIES):
        for target in TARGETS:
            for a,s in itertools.product(['exhausted','reloadable'],['loaded','dry','unknown']):
                case('core',scenario(d,p,a,s,target))
            case('loaded_primary',scenario(d,p,'loaded','loaded',target))
        for target in [TARGETS[0],TARGETS[2],TARGETS[5]]:
            case('reserve_only_sidearm',scenario(d,p,'exhausted','reserve_only',target))
            case('unowned_sidearm',scenario(d,p,'exhausted','unowned',target))
            for a in ['exhausted','reloadable','loaded']:
                case('stale_active_cache',scenario(d,p,a,'loaded',target,stale=True))
            for obj in ['carrier','defuser']:
                case('objective_guard',scenario(d,p,'exhausted','loaded',target,obj))
        for name,t,a,s in SETTINGS:
            for step in range(8):
                result.append(('STEP',f'sequence/{d}/{p}/{name}',step,scenario(d,p,a,s,TARGETS[t])))
    for name,p,a,s,n,target in [('kill_rifle','rifle','loaded','unowned',8,True),('reload_smg','smg','reloadable','unowned',19,False),('reload_rifle','rifle','reloadable','unowned',22,False),('reload_marksman','marksman','reloadable','unowned',27,False),('reload_sidearm','rifle','exhausted','reserve_only',20,True)]:
        spec=scenario('normal',p,a,s,('positive_clear_2m' if target else 'positive_hidden_2m',2,target))
        spec.update(control=name,positive_lane='2m along z=-20, wholly inside the stock yard',step_budget=n,initial_target_health=10. if name=='kill_rifle' else 100.,visibility_schedule='visible only on first step, then hidden' if name=='reload_sidearm' else 'constant')
        for step in range(n): result.append(('CONTROL_STEP','control/'+name,step,spec))
    return result


def expected_records():
    result = common_records()
    for primary in PRIMARIES:
        for name, distance in [('inside',44.9),('boundary',45.),('outside',45.1)]:
            spec = scenario('hard',primary,'exhausted','loaded',('range_'+name,distance,True))
            result.append(('POLICY_RANGE','policy_range/'+primary+'/'+name,-1,spec))
    spec = scenario('normal','rifle','exhausted','reserve_only',('policy_reserve_24m',24.,True))
    spec['control'] = 'policy_reserve_24m'
    result.extend(('POLICY_RESERVE_STEP','policy_reserve_24m',step,spec) for step in range(20))
    return result


def extension_allowed(before, acquired, interact, distance, profile, definitions):
    stored = before['ammo_store'].get('sidearm')
    return (bool(profile['sidearm_fallback']) and before['weapon'] in PRIMARIES
            and before['ammo'] == 0 and before['reserve'] == 0
            and 'sidearm' in before['inventory'] and stored is not None
            and (stored[0] > 0 or stored[1] > 0) and not interact
            and (not acquired or distance <= definitions['sidearm']['range']))


def expected_weapon(before, acquired, interact, distance, profile, definitions):
    if (acquired and profile['sidearm_fallback'] and before['ammo'] == 0
            and before['weapon'] != 'sidearm' and 'sidearm' in before['inventory']
            and distance < 20 and not interact):
        return 'sidearm'
    if extension_allowed(before,acquired,interact,distance,profile,definitions):
        return 'sidearm'
    if not acquired and before['weapon'] == 'sidearm':
        return next((w for w in ['rifle','marksman','smg']
                     if w in before['inventory'] and before['ammo_store'].get(w) != [0,0]),'')
    return ''


def audit(records,repo):
    checks=0; stats=Counter(); by=defaultdict(list); outcomes=[]
    def check(value,message):
        nonlocal checks
        checks+=1
        if not value: raise AssertionError(message)
    for line,kind,row in records: by[kind].append((line,row))
    check({k:len(v) for k,v in by.items()}=={'HEADER':1,'CASE':567,'STEP':576,'SEQUENCE':72,'CONTROL_STEP':96,'CONTROL':5,'POLICY_HEADER':1,'POLICY_RANGE':9,'POLICY_RESERVE_STEP':20,'POLICY_RESERVE':1,'POLICY_RESULT':1,'RESULT':1},'exact row-kind inventory')
    check(records[0][1]=='HEADER' and records[-1][1]=='RESULT','header/result ordering')
    h=by['HEADER'][0][1]; defs=h['weapon_definitions']; profiles=h['profiles']
    for const,file,field in [('DATA','weapons.gd','weapon_definitions'),('PROFILES','bot_ai.gd','profiles')]:
        text=(repo/'game/scripts/gameplay'/file).read_text()
        literal=text.split('const '+const+' := ',1)[1].split('\n}',1)[0]+'\n}'
        colors={}
        def color(m):
            key=m.group(1);colors[key]=[int(key[i:i+2],16)/255 for i in [0,2,4]]+[1]
            return json.dumps(colors[key])
        literal=re.sub(r'Color\("([0-9a-f]{6})"\)',color,literal)
        check(close(json.loads(literal),h[field]),'source/header '+field)
    check(h['engine']['major']==4 and h['engine']['minor']==7 and h['engine']['patch']==2 and h['engine']['hash']=='ed1daf0bf001b61586d9930840f2f1394092c079','header engine identity')
    check(h['dt']==DT and h['seed']==52039 and h['deploy_seconds']==.3,'header constants')
    check([h[k] for k in ['matrix_cases_expected','sequences_expected','sequence_steps_expected','positive_controls_expected','control_steps_expected']]==[567,72,576,5,96],'header counts')
    raw_rows=[(line,kind,row) for line,kind,row in records if kind in ['CASE','STEP','CONTROL_STEP','POLICY_RANGE','POLICY_RESERVE_STEP']]
    expected=expected_records()
    check(len(raw_rows)==len(expected)==1268,'all action rows')
    serials=[]; prior={}; summaries={}; initial={}; reload_starts=defaultdict(list); reload_ends=defaultdict(list); shot_indices=defaultdict(int)
    for (line,kind,r),(want_kind,label,step,s) in zip(raw_rows,expected):
        ctx=f'line {line} {label} step {step}: '
        def ck(v,m): check(v,ctx+m)
        ck((kind,r['label'],r['step'])==(want_kind,label,step) and r['scenario']==s,'exact registered identity/order')
        b,q,a=r['before'],r['after_decision'],r['after_action']; eb,eq,ea=[r[k] for k in ['enemy_before','enemy_after_decision','enemy_after_action']]
        ob,oq,oa=[r[k] for k in ['objective_before','objective_after_decision','objective_after_action']]
        cmd=r['command']; state=r['decision_bot_state']; wd=defs[b['weapon']]
        for snap in [b,q,a]: ck(snap.keys()==ACTOR_KEYS,'full shooter snapshot')
        for snap in [eb,eq,ea]: ck(snap.keys()==ACTOR_KEYS|{'input_state'},'full target snapshot')
        for snap in [ob,oq,oa]: ck(snap.keys()==OBJECTIVE_KEYS,'full objective snapshot')
        ck(b==q and eb==eq and ob==oq,'all planning authority fences')
        ck(ob==oa,'objective action purity')
        ck(b['actor_id']==6 and eb['actor_id']==1 and b['team']!=eb['team'],'actor identities')
        ck(r['bot_state_after_action']==state,'action does not mutate logged bot state')
        ck(set(cmd)==set('crouch fire grenade interact jump look move reload smoke weapon'.split()),'complete player input')
        ck(all(type(cmd[k]) is bool for k in ['crouch','fire','grenade','interact','jump','reload','smoke']),'command booleans')
        ck(not cmd['grenade'] and not cmd['smoke'],'utility disabled by initial resources')
        ck(close(r['elapsed'],20+DT*max(0,step)) and ob['elapsed']==r['elapsed'],'controlled simulation clock')
        expected_objective=dict(phase='live',round=2,attack_score=0,defend_score=0,time_left=100.,state='planted' if s['objective']=='defuser' else 'carried',timer=0.,progress=0.,position=[-15.,0.,10.],carrier=6 if s['objective']=='carrier' else 0,contributions={str(i):0 for i in range(1,11)},interactions={},elapsed=r['elapsed'],tick=0)
        ck(ob==expected_objective,'all initial/preserved objective authority fields')
        # Bind exact poses, fixed aim, distance and actual query endpoints.
        distance=s['target']['distance']; direction=[1.,0.,0.]
        spawn=[-distance/2,0,-20]
        if distance>45.5:
            direction=[math.sqrt(.5),0,math.sqrt(.5)];spawn=mul(direction,-distance/2)
        if s['objective']!='none': spawn=[-15,0,10]
        target=add(spawn,mul(direction,distance))
        ck(close(b['position'],spawn,1e-4) and close(eb['position'],target,1e-4),'exact registered shooter/target poses')
        ck(close(b['yaw'],math.atan2(-direction[0],-direction[2])) and close(b['pitch'],math.atan2(-.35,distance)),'fixed aim')
        lane=r['lane'];origin=add(b['position'],[0,1.62,0]);pitch,yaw=b['pitch'],b['yaw']
        ray=[-math.sin(yaw)*math.cos(pitch),math.sin(pitch),-math.cos(yaw)*math.cos(pitch)]
        endpoint=add(origin,mul(ray,norm(sub(eb['position'],b['position']))+.5))
        ck(close(lane['shooter'],spawn,1e-4) and close(lane['target'],target,1e-4),'lane actor bindings')
        ck(close(lane['ray_from'],origin,1e-4) and close(lane['ray_to'],endpoint,1e-4),'actual ray endpoints')
        ck(type(lane['in_bounds']) is bool and lane['in_bounds'] and all(abs(p[i])+.31<23.5 for p in [spawn,target] for i in [0,2]),'actual capsule footprints')
        settle=lane['pose_settle'];ck(settle['barriers']==2 and settle['after_frame']>settle['before_frame'] and lane['observation_frame']>=settle['after_frame'],'settled world query')
        ck(type(lane['world_clear']) is bool and lane['world_mask']==1,'world query flags')
        world_distance,world_hit=world_trace(origin,ray,norm(sub(endpoint,origin)))
        ck(lane['world_clear']==(not world_hit),'world ray vs all 26 stock solid AABBs')
        if world_hit:
            ck(close(lane['world_hit_position'],add(origin,mul(ray,world_distance)),2e-4) and lane['world_hit_path']!='','world hit evidence')
        else: ck(lane['world_hit_position'] is None and lane['world_hit_path']=='','clear line evidence')
        trace=lane['stock_trace'];td,wh=world_trace(origin,ray,wd['range']);td,hit_actor,head=target_trace(origin,ray,eq,td)
        ck(trace['actor_id']==(1 if hit_actor else 0) and trace['hit']==(hit_actor or wh),'stock trace contact identity')
        ck(close(trace['distance'],td,2e-4) and close(trace['position'],add(origin,mul(ray,td)),3e-4) and trace['headshot']==head,'stock center trace geometry')
        # State continuity includes both actors; only the fixture's elapsed clock
        # advances on objectives between successive action rows.
        if label in prior:
            old=prior[label]
            ck(step==old['step']+1 and b==old['after_action'] and eb==old['enemy_after_action'],'continuous full actor states')
            old_obj=dict(old['objective_after_action'],elapsed=r['elapsed'])
            ck(ob==old_obj,'continuous objective state')
        else:
            initial[label]=r
            ck(step in [-1,0],'scenario starts at first step')
            inventory=[s['primary']] if s['sidearm_resource']=='unowned' else ['sidearm',s['primary']]
            clip=1 if s['active_resource']=='loaded' else 0; reserve=defs[s['primary']]['magazine'] if s['active_resource']=='reloadable' else 0
            store={};side={'loaded':[15,0],'reserve_only':[0,15],'dry':[0,0]}.get(s['sidearm_resource'])
            if side is not None: store['sidearm']=side
            if s['stale_active_cache']: store[s['primary']]=[defs[s['primary']]['magazine'],defs[s['primary']]['reserve']] if s['active_resource']=='exhausted' else [0,0]
            ck(b['weapon']==s['primary'] and (b['ammo'],b['reserve'])==(clip,reserve) and b['ammo_store']==store and b['inventory']==inventory,'exact initial ammo/cache/inventory')
            ck(b['reload']==b['deploy']==0 and b['cooldowns']=={} and b['credits']==800 and b['kills']==b['deaths']==0 and b['health']==100 and b['alive'],'initial shooter authority')
            ck(eb['health']==s.get('initial_target_health',100) and eb['alive'] and eb['deaths']==0 and eb['credits']==800,'initial target authority')
            expected_initial=dict(actor_id=6,team=0 if s['objective']=='carrier' else 1,weapon=s['primary'],ammo=clip,reserve=reserve,reload=0.,deploy=0.,cooldowns={},inventory=inventory,ammo_store=store,health=100.,alive=True,credits=800,kills=0,assists=0,deaths=0,grenades=0,smokes=0,recoil=[0.,0.],position=spawn,velocity=[0.,0.,0.],yaw=math.atan2(-direction[0],-direction[2]),pitch=math.atan2(-.35,distance),fire_previous=False,floor_contact=False,crouching=False,actual_action_spread=defs[s['primary']]['spread']+.045)
            ck(close(b,expected_initial,1e-4),'full initial shooter state')
            expected_target=dict(actor_id=1,team=1-expected_initial['team'],weapon='sidearm',ammo=15,reserve=60,reload=0.,deploy=0.,cooldowns={},inventory=['sidearm'],ammo_store={'sidearm':[15,60]},health=s.get('initial_target_health',100.),alive=True,credits=800,kills=0,assists=0,deaths=0,grenades=1,smokes=1,recoil=[0.,0.],position=target,velocity=[0.,0.,0.],yaw=math.pi if expected_initial['team']==1 else 0.,pitch=0.,fire_previous=False,floor_contact=False,crouching=False,actual_action_spread=.048,input_state={})
            ck(close(eb,expected_target,1e-4),'full initial target resource state')
        prior[label]=r
        # Recompute active-first and holstered/default accounting per weapon.
        def resources(snap):
            result={}
            for weapon in WEAPONS:
                definition=defs[weapon]; owned=weapon in snap['inventory']; source='unowned';clip=reserve=None
                if owned:
                    if weapon==snap['weapon']: source='active_fields';clip,reserve=snap['ammo'],snap['reserve']
                    elif weapon in snap['ammo_store']: source='holstered_store';clip,reserve=snap['ammo_store'][weapon]
                    else: source='unknown'
                result[weapon]=dict(owned=owned,source=source,clip=clip,reserve=reserve,equip_default=[definition['magazine'],definition['reserve']])
            return result
        rb,ra=resources(b),resources(a)
        ck(r['resources_before']==rb and r['resources_after']==ra,'all raw resource projections')
        for snap in [b,a,eb,ea]:
            ck(snap['ammo']>=0 and snap['reserve']>=0 and all(len(v)==2 and min(v)>=0 for v in snap['ammo_store'].values()),'all stores nonnegative')
            spread=defs[snap['weapon']]['spread']+norm([snap['velocity'][0],snap['velocity'][2]])/5.2*.026+(.045 if not snap['floor_contact'] else 0)
            if snap['crouching']: spread*=.6
            ck(close(snap['actual_action_spread'],spread),'actual spread from logged stance/contact')
        def projected(res):
            return {w:(sum(v['equip_default']) if v['source']=='unknown' else v['clip']+v['reserve']) if v['owned'] else 0 for w,v in res.items()}
        pb,pa=projected(rb),projected(ra)
        ck(r['equip_semantics_total_before']==sum(pb.values()) and r['equip_semantics_total_after']==sum(pa.values()),'projected totals')
        known=rb['sidearm']['source'] in ['active_fields','holstered_store'] and rb['sidearm']['clip']+rb['sidearm']['reserve']>0
        ck(r['known_sidearm_resources']==known,'known availability excludes unknown/unowned')
        # Independently bind selection and protected profile/range/objective policy.
        visible=s['target']['visible']
        if s.get('control') in ['reload_sidearm','policy_reserve_24m']: visible=step==0
        ck(r['visibility_injected']==visible,'exact visibility schedule')
        acquired=visible and eq['alive'] and distance<=profiles[s['difficulty']]['vision_range']
        ck(state['target']==(1 if acquired else 0),'FOV/range acquisition')
        interact=s['objective']!='none'
        ck(cmd['interact']==interact,'objective guard')
        request=expected_weapon(b,acquired,interact,distance,profiles[s['difficulty']],defs)
        ck(cmd['weapon']==request,'registered candidate request rule')
        safe_reload=not acquired and r['elapsed']-state['seen_at']>2.5 and b['ammo']<=wd['magazine']/3
        ck(cmd['reload']==(not interact and not request and (b['ammo']==0 or safe_reload)),'reload command cause')
        if acquired:
            desired_pitch=math.atan2(-.35,distance)-b['recoil'][1]*profiles[s['difficulty']]['recoil_compensation']
            # All registered fixed poses can reach every profile's complete aim
            # error in one turn; command.look therefore equals desired, within
            # the observed source profile's bounded horizontal error.
            base_yaw=math.atan2(-direction[0],-direction[2])-b['recoil'][0]*profiles[s['difficulty']]['recoil_compensation']
            ck(abs(cmd['look'][0]-base_yaw)<=profiles[s['difficulty']]['aim_error']+1e-5 and close(cmd['look'][1],desired_pitch),'bounded profile aim')
            fire=state['reaction']>=profiles[s['difficulty']]['reaction_delay'] and not interact and state['burst_cooldown']<=0
            if not wd['automatic'] and b['fire_previous']:fire=False
        else: fire=False
        ck(cmd['fire']==fire,'fire command reaction/profile cause')
        # Independent stock action-step model, including completed transfer,
        # equip defaults, overlapping deploy/reload, cooldown and trigger edges.
        pred=copy.deepcopy(b);pred['deploy']=max(0,b['deploy']-DT)
        pred['cooldowns']={w:t-DT for w,t in b['cooldowns'].items()}
        length=norm(b['recoil']);pred['recoil']=mul(b['recoil'],max(0,length-DT*.11)/length) if length else [0.,0.]
        if b['reload']>0:
            pred['reload']=max(0,b['reload']-DT)
            if pred['reload']==0:
                transfer=min(wd['magazine']-b['ammo'],b['reserve']);pred['ammo']+=transfer;pred['reserve']-=transfer
        if request and request!=pred['weapon']:
            pred['ammo_store'][pred['weapon']]=[pred['ammo'],pred['reserve']]
            pred['weapon']=request; spec=defs[request]
            pred['ammo'],pred['reserve']=pred['ammo_store'].get(request,[spec['magazine'],spec['reserve']])
            pred['reload']=0;pred['deploy']=.3
            shot_indices[label]=0
        spec=defs[pred['weapon']]
        def start_reload():
            if pred['reload']<=0 and pred['ammo']<spec['magazine'] and pred['reserve']>0:
                pred['reload']=spec['reload'];shot_indices[label]=0
        if cmd['reload']:start_reload()
        shot=0
        if fire and (spec['automatic'] or not b['fire_previous']) and pred['deploy']<=1e-6 and pred['cooldowns'].get(pred['weapon'],0)<=1e-6 and pred['reload']<=0:
            if pred['ammo']>0:
                shot=1;pred['ammo']-=1
                carry=pred['cooldowns'].get(pred['weapon'],0)
                carry=carry if b['fire_previous'] and -1/60*.999<carry<=0 else 0
                pred['cooldowns'][pred['weapon']]=spec['interval']+carry
            else:start_reload()
        for w in pred['cooldowns']:
            if not shot or w!=pred['weapon']:pred['cooldowns'][w]=max(0,pred['cooldowns'][w])
        pred['fire_previous']=fire
        ck(len(r['actual_shots'])==shot==r['shot_delta'],'actual shot trigger and one-round consumption')
        ck(all(pa[w]+(shot if w==pred['weapon'] else 0)==pb[w] for w in WEAPONS),'per-weapon conservation with equip defaults')
        for event in r['actual_shots']:
            ck(event['weapon']==pred['weapon'] and event['ammo_after_shot']==pred['ammo'] and event['reserve']==pred['reserve'],'shot resource snapshot')
            ck(close(event['origin'],origin,1e-4) and close(norm(event['direction']),1),'actual shot pose/unit direction')
            shot_yaw=math.atan2(-event['direction'][0],-event['direction'][2]);shot_pitch=math.asin(event['direction'][1])
            ck(abs(shot_yaw-b['yaw']-pred['recoil'][0])<=b['actual_action_spread']+1e-5 and abs(shot_pitch-b['pitch']-pred['recoil'][1])<=b['actual_action_spread']+1e-5,'shot spread/recoil cone')
            serials.append(event['serial'])
        # All recorded target damage must come from that row's actual shot,
        # target volume intersection, stock falloff/head damage and health clamp.
        expected_enemy=copy.deepcopy(eq);damage=0.;killed=False
        if shot:
            ev=r['actual_shots'][0];limit,hit_world=world_trace(ev['origin'],ev['direction'],spec['range'])
            contact,hit_actor,head=target_trace(ev['origin'],ev['direction'],eq,limit)
            if hit_actor:
                amount=spec['damage']*(1+(spec['falloff']-1)*max(0,min(1,contact/spec['range'])))*(spec['head'] if head else 1)
                damage=min(eq['health'],amount);expected_enemy['health']=max(0,eq['health']-amount)
                killed=expected_enemy['health']<=0;expected_enemy['alive']=not killed
                if killed:expected_enemy['deaths']+=1
        ck(len(r['damage_events'])==int(damage>0) and len(r['elimination_events'])==int(killed),'physical shot damage/death causes')
        for ev in r['damage_events']:
            damage_snap=copy.deepcopy(eq);damage_snap['health']=expected_enemy['health']
            ck(ev['victim']==1 and ev['attacker']==6 and close(ev['amount'],damage,1e-3),'damage identity/amount')
            ck(close(ev['victim_state'],damage_snap,1e-3),'serial damage snapshot before death flag')
            serials.append(ev['serial'])
        ck(close(ea,expected_enemy,1e-3),'complete target action snapshot')
        pred['kills']+=int(killed);pred['credits']=min(9000,pred['credits']+300*int(killed))
        for ev in r['elimination_events']:
            ck(ev['victim']==1 and ev['killer']==6 and close(ev['victim_state'],expected_enemy,1e-3),'elimination target event')
            ck(close(ev['shooter_state'],dict(pred,fire_previous=b['fire_previous'])),'elimination shooter snapshot before recoil/trigger latch')
            ck(r['damage_events'][0]['serial']<ev['serial']<r['actual_shots'][0]['serial'],'damage/elimination/shot serial order')
            serials.append(ev['serial'])
        if shot:
            shot_indices[label]+=1
            pred['recoil'][1]=min(pred['recoil'][1]+spec['recoil'],.16)
            pred['recoil'][0]+=math.sin(shot_indices[label]*1.7)*spec['recoil']*.55
        if not fire and norm(pred['recoil'])==0:shot_indices[label]=0
        pred['actual_action_spread']=spec['spread']+(.045 if not pred['floor_contact'] else 0)
        ck(close(a,pred),'complete shooter action consumption')
        ck(close(r['target_damage_delta'],eq['health']-ea['health']) and r['reward_delta']==a['credits']-q['credits'],'reported deltas')
        switched=b['weapon']!=a['weapon']
        ck(r['switched']==switched and r['sidearm_center_distance_within_trace_range']==(distance<=defs['sidearm']['range']),'derived switch/range flags')
        er=cmd['reload'] and b['ammo']==0 and b['reserve']==0 and not switched
        ef=cmd['fire'] and b['ammo']==0 and shot==0 and not switched
        ck(r['empty_reload_request']==er and r['empty_fire_request']==ef,'ineffective-command flags')
        if b['weapon']==a['weapon'] and b['reload']==0<a['reload']:reload_starts[label].append(step)
        if b['weapon']==a['weapon'] and b['reload']>0==a['reload']:reload_ends[label].append(step)
        values=dict(switches=int(switched),empty_reload_requests=int(er),empty_fire_requests=int(ef),shots=shot,known_sidearm_resource_steps=int(known),damage_events=len(r['damage_events']),target_damage=eq['health']-ea['health'],eliminations=int(killed),reward_delta=r['reward_delta'])
        summary=summaries.setdefault(label,Counter());summary.update(values)
        by['_'+label].append(r)
        for k,v in values.items():stats[k]+=v
    check(sorted(serials)==list(range(1,len(serials)+1)),'all global event serials exactly once')
    check(len(serials)>0,'event witnesses present; exact per-control requirements below')
    for _,summary in by['SEQUENCE']:
        label=summary['label'];want={k:summaries[label][k] for k in ['switches','empty_reload_requests','empty_fire_requests','shots','known_sidearm_resource_steps']}
        check(summary==dict(want,label=label),'sequence summary '+label)
        outcomes.append(dict(label=label,**dict(summaries[label]),reload_start_steps=reload_starts[label],reload_completion_steps=reload_ends[label]))
    controls=[]
    for _,summary in by['CONTROL']:
        name=summary['name'];label='control/'+name;first=initial[label];last=prior[label];derived=summaries[label]
        check(summary['initial_shooter']==first['before'] and summary['initial_target']==first['enemy_before'] and summary['initial_lane']==first['lane'],'control initial binding '+name)
        check(summary['final_shooter']==last['after_action'] and summary['final_target']==last['enemy_after_action'],'control final binding '+name)
        for key,source in [('shots','shots'),('damage_events','damage_events'),('eliminations','eliminations'),('target_damage','target_damage'),('draws','switches')]:check(close(summary[key],derived[source]),name+' derived '+key)
        check(summary['reload_start_steps']==reload_starts[label] and summary['reload_completion_steps']==reload_ends[label] and summary['reload_starts']==len(reload_starts[label]) and summary['reload_completions']==len(reload_ends[label]),name+' reload summary')
        if name=='kill_rifle':
            check(derived['shots']==derived['damage_events']==derived['eliminations']==1 and close(derived['target_damage'],10) and derived['reward_delta']==300 and derived['switches']==0 and not reload_starts[label],'mandatory rifle kill')
        else:
            weapon='sidearm' if name=='reload_sidearm' else name.removeprefix('reload_');spec=defs[weapon]
            expected_start,expected_end=(1,14) if weapon=='sidearm' else {'smg':(0,16),'rifle':(0,19),'marksman':(0,24)}[weapon]
            check(reload_starts[label]==[expected_start] and reload_ends[label]==[expected_end],name+' mandatory full duration')
            check(spec['reload']<=DT*(expected_end-expected_start)<=spec['reload']+DT,name+' completion time')
            check(last['after_action']['weapon']==weapon and last['after_action']['ammo']==spec['magazine'] and last['after_action']['reserve']==0,name+' final full clip')
            check(not derived['shots'] and not derived['damage_events'] and not derived['eliminations'] and summary['initial_target']==summary['final_target'],name+' target/no-shot guard')
        controls.append(dict(name=name,steps=summary['steps'],**dict(derived),reload_start_steps=reload_starts[label],reload_completion_steps=reload_ends[label]))
    check(by['POLICY_HEADER'][0][1] == dict(range_cases_expected=9,reserve_steps_expected=20,total_policy_rows_expected=1268,common_fixture_sha256='540d24dda8e58f4685030e81b55ac3778ccbf31a89f76f9873ac598c32770731'),'supplement header identity')
    for difficulty,primary in itertools.product(['normal','hard'],PRIMARIES):
        label=f'sequence/{difficulty}/{primary}/far_loaded'
        derived=summaries[label]; last=prior[label]['after_action']
        check(derived['switches']==1 and derived['shots']>0 and not derived['empty_reload_requests'],'24m maintained actual shot/no impossible reload '+label)
        check(last['weapon']=='sidearm' and last['ammo']==15-derived['shots'] and last['reserve']==0,'24m sidearm shot consumption '+label)
    reserve=by['POLICY_RESERVE'][0][1]; label='policy_reserve_24m'; first=initial[label]; last=prior[label]
    derived=summaries[label]
    check(reserve['name']==label and reserve['steps']==20 and reserve['visibility_schedule']=='visible only on step 0, then hidden','24m reserve summary identity')
    check(reserve['initial_shooter']==first['before'] and reserve['initial_target']==first['enemy_before'] and reserve['final_shooter']==last['after_action'] and reserve['final_target']==last['enemy_after_action'],'24m reserve complete snapshot binding')
    check(reload_starts[label]==[1] and reload_ends[label]==[14] and reserve['reload_start_step']==1 and reserve['reload_completion_step']==14,'24m reserve stock reload timing')
    check(reserve['draws']==reserve['reload_starts']==reserve['reload_completions']==1 and derived['switches']==1,'24m reserve one draw/start/completion')
    check(not derived['shots'] and not derived['damage_events'] and not derived['eliminations'] and not derived['empty_reload_requests'] and reserve['impossible_reload_requests']==0,'24m reserve no damage/impossible reload')
    check(last['after_action']['weapon']=='sidearm' and last['after_action']['ammo']==15 and last['after_action']['reserve']==0 and last['after_action']['reload']==0 and reserve['initial_target']==reserve['final_target'],'24m reserve completed usable magazine')
    check(by['POLICY_RESULT'][0][1]==dict(policy_rows=1268,range_rows=9,reserve_rows=20,failures_so_far=[]),'supplement terminal binding')
    result=by['RESULT'][0][1]
    check(result['matrix_cases']==567 and result['sequences']==72 and result['sequence_steps']==576 and result['control_steps']==96,'terminal count binding')
    check(result['positive_controls']==[x for _,x in by['CONTROL']],'terminal full control binding')
    check(result['failures']==[] and result['authority_checks_passed'] is True and type(result['checks']) is int and result['checks']>0,'retained claimed fixture terminal; assertion counter is reported, not independently totaled')
    case_buckets=defaultdict(Counter)
    for _,r in by['CASE']:
        s=r['scenario'];key='/'.join([r['label'].split('/')[0],s['difficulty'],s['active_resource'],s['sidearm_resource'],s['target']['name'],s['objective']])
        case_buckets[key].update(cases=1,switches=int(r['switched']),empty_reload_requests=int(r['empty_reload_request']),empty_fire_requests=int(r['empty_fire_request']),shots=r['shot_delta'])
    return dict(builder_predicates=checks,row_counts={k:len(by[k]) for k in ['CASE','STEP','SEQUENCE','CONTROL_STEP','CONTROL','POLICY_RANGE','POLICY_RESERVE_STEP']},reported_fixture_checks=result['checks'],observed_event_serial_count=len(serials),all_row_totals=dict(stats),case_buckets={k:dict(v) for k,v in sorted(case_buckets.items())},sequences=outcomes,controls=controls,geometry_solid_count=len(SOLIDS),scope='Builder adaptation: all emitted protected snapshots, per-weapon resources, candidate requests, stock action transitions and observable event causes; no independent acceptance, unlogged planning event-count trace or native object types')


BASELINE_STDOUT_SHA256 = 'e6606c22b5d5cc5c33090a97b1a832e60a376465a0edfa112146b7f743b10d7f'


def file_data(path):
    data = path.read_bytes()
    return gzip.decompress(data) if path.suffix == '.gz' else data


def planned_deltas(records):
    header = next(row for _,kind,row in records if kind == 'HEADER')
    changed_cases, changed_sequences = [], []
    case_rows = [(kind,row['label'],row['step'],row['scenario']) for _,kind,row in records if kind == 'CASE']
    assert case_rows == [row for row in common_records() if row[0] == 'CASE'], 'baseline matrix registration'
    for _,kind,row in records:
        if kind != 'CASE' and not (kind == 'STEP' and row['step'] == 0):
            continue
        acquired = bool(row['decision_bot_state']['target'])
        interacting = row['scenario']['objective'] != 'none'
        request = expected_weapon(row['before'],acquired,interacting,row['scenario']['target']['distance'],
                                  header['profiles'][row['scenario']['difficulty']],header['weapon_definitions'])
        if request != row['command']['weapon']:
            assert request == 'sidearm' and row['command']['weapon'] == '', 'only new sidearm requests'
            (changed_cases if kind == 'CASE' else changed_sequences).append(row['label'])
    assert len(changed_cases) == 51 and len(changed_sequences) == 15, 'preregistered exact request deltas'
    return dict(changed_matrix_labels=changed_cases, changed_first_sequence_labels=changed_sequences,
                changed_matrix_requests=51, preserved_matrix_requests=516,
                changed_first_sequence_requests=15, preserved_first_sequence_requests=57,
                baseline_stdout_sha256=BASELINE_STDOUT_SHA256,
                scope='Pure forecast from independently audited baseline inputs; no candidate game output yet.')


def normalized(row):
    value = copy.deepcopy(row)
    # Native query frame numbers and Node auto-names depend on the process.
    # The all-row audit binds settlement, actual geometry and stock traces.
    lane = value.pop('lane')
    value['lane_geometry'] = {k:v for k,v in lane.items() if k not in
                              ('pose_settle','observation_frame','world_hit_path')}
    for key in ('actual_shots','damage_events','elimination_events'):
        for event in value[key]:
            event.pop('serial')  # Whole candidate serial order is checked by audit().
    return value


def compare(records, baseline_records):
    plan = planned_deltas(baseline_records)
    baseline = {(kind,row['label'],row['step']):row for _,kind,row in baseline_records
                if kind in ('CASE','STEP','CONTROL_STEP')}
    candidate = {(kind,row['label'],row['step']):row for _,kind,row in records
                 if kind in ('CASE','STEP','CONTROL_STEP')}
    assert baseline.keys() == candidate.keys(), 'all common row identities'
    changed_cases = set(plan['changed_matrix_labels'])
    changed_sequences = set(plan['changed_first_sequence_labels'])
    seen_changes = []
    preserved_rows = 0
    for key,b in baseline.items():
        kind,label,step = key
        a = candidate[key]
        if kind == 'CASE':
            assert a['before'] == b['before'] and a['enemy_before'] == b['enemy_before'], label + ': common matrix resource inputs'
            assert a['decision_bot_state'] == b['decision_bot_state'], label + ': planning state otherwise unchanged'
            want = dict(b['command'])
            if label in changed_cases:
                want.update(weapon='sidearm',reload=False)
                seen_changes.append(label)
            assert a['command'] == want, label + ': exact allowed matrix command delta'
        if kind == 'CONTROL_STEP' or (kind == 'CASE' and label not in changed_cases) or (kind == 'STEP' and label not in changed_sequences):
            assert close(normalized(a),normalized(b),1e-4), label + '/' + str(step) + ': preserved common authority/action output'
            preserved_rows += 1
        if kind == 'STEP' and step == 0:
            should_change = label in changed_sequences
            assert (a['command']['weapon'] != b['command']['weapon']) == should_change, label + ': exact first-step request delta'
    assert seen_changes == plan['changed_matrix_labels'], 'complete exact changed matrix identities'
    return dict(plan, preserved_common_action_rows=preserved_rows,
                comparison_scope='Exact 51 allowed matrix command changes; 516 unchanged matrix actions, 57 unchanged complete sequences and all 96 original positive-control actions. Stateful consequences in the 15 changed sequences are separately audited.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline',required=True,type=Path)
    parser.add_argument('--source',required=True,type=Path)
    parser.add_argument('--candidate',type=Path)
    args = parser.parse_args()
    assert hashlib.sha256(file_data(args.baseline)).hexdigest() == BASELINE_STDOUT_SHA256, 'immutable baseline stdout hash'
    common = args.source / 'game/tests/bot_exhausted_primary_probe.gd'
    assert hashlib.sha256(common.read_bytes()).hexdigest() == '540d24dda8e58f4685030e81b55ac3778ccbf31a89f76f9873ac598c32770731', 'common probe source hash'
    baseline,other = parse(args.baseline)
    output = {'plan':planned_deltas(baseline),'scope':'Builder source/pure forecast; no candidate acceptance.'}
    if args.candidate:
        records,other = parse(args.candidate)
        output.update(candidate_stdout_sha256=hashlib.sha256(file_data(args.candidate)).hexdigest(),
                      resource_authority_audit=audit(records,args.source),
                      comparison=compare(records,baseline),nonrecord_stdout=other,
                      scope='Builder actual-output audit only; fresh independent review and separate strict log/process/source receipts are mandatory.')
    print(json.dumps(output,indent=2,sort_keys=True))


if __name__ == '__main__':
    main()
