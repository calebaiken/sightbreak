#!/usr/bin/env python3
import collections, hashlib, json, math, ntpath, os, pathlib, re, subprocess

ROOT=pathlib.Path('.local/windows40089125575/full')
OUT=pathlib.Path('docs/reports/gauntlet/windows-route-clock-actual-20261024/subcritic')
REF='4cf6ac8e744603ed6af122a362036d276754cc76'
IDENTITY={'source_commit':REF,'source_game_tree':'bca627d5dc8e4482b63e263020a6382f2d36f33c','source_content_sha256':'43a71ef7ea38febc735b67e24337c8f975bf69d57e3e4b06f94d175170d56eb8','source_validation_sha256':'e0e223328351507a02d6b63b845531324c2e432e29e86eebed07740c45a2c496'}
ENGINE='4.7.2.stable.official.ed1daf0bf'
STRICT=re.compile(r'^(?:SCRIPT ERROR|ERROR:)|Parse Error|ObjectDB.*leaked|Leaked instance|^Orphan StringName: [^\r\n]+ \(static: [0-9]+, total: [0-9]+\)\r?$|^StringName: [1-9][0-9]* unclaimed string names at exit\.\r?$',re.M)
EXPECTED={'actor':73,'match':75,'authority_order':178,'state_privacy':55,'movement_prediction':742,'peer_lifecycle':16,'input_mode':462,'menu_focus':30,'offline_diagnostics':60,'hud_objective_hint':1535,'activity_provenance':32,'bot_squad_symmetry':2722,'bot_dry_weapon':590,'bot_exhausted_primary':20116,'transaction_journal':41,'gunplay_rules':2840}
RULES={'buy_seconds':15,'round_seconds':100,'device_seconds':35,'plant_seconds':3,'defuse_seconds':5,'win_score':7}
checks=[]
inputs={}

def check(scope,name,value):
    checks.append({'scope':scope,'name':name,'passed':bool(value)})

def bind(path):
    data=path.read_bytes();inputs[path.relative_to(ROOT).as_posix()]={'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()};return data

def load(name):
    return json.loads(bind(ROOT/name).decode('utf-8'),parse_constant=lambda v:(_ for _ in ()).throw(ValueError(v)))

def lines(name):
    return [json.loads(l) for l in bind(ROOT/name).decode('utf-8').splitlines() if l.strip()]

def git(*a):return subprocess.check_output(['git',*a])
def same_json(a,b):return json.dumps(a,sort_keys=True,separators=(',',':'))==json.dumps(b,sort_keys=True,separators=(',',':'))
def number(x):return type(x) in (int,float) and math.isfinite(x)
def integer(x):return type(x) is int

def semantic(a,b):
    if type(a) is dict and type(b) is dict:return a.keys()==b.keys() and all(semantic(a[k],b[k]) for k in a)
    if type(a) is list and type(b) is list:return len(a)==len(b) and all(semantic(x,y) for x,y in zip(a,b))
    if number(a) and number(b):return a==b
    return type(a) is type(b) and a==b

def source(scope,record):
    check(scope,'source object',type(record) is dict)
    if type(record) is not dict:return
    for k,v in IDENTITY.items():check(scope,k,record.get(k)==v)
    for k in ['source_dirty','source_game_dirty']:check(scope,k+' literal false',record.get(k) is False)

def norm(p):return ntpath.normcase(ntpath.normpath(p))
def present_json(path):return json.loads(bind(path).decode('utf-8'))

def loginfo(path):
    data=bind(path);text=data.decode('utf-8',errors='replace')
    return {'path':path.relative_to(ROOT).as_posix(),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'utf8_replacement': '\ufffd' in text,'strict_failed':bool(STRICT.search(text)),'warnings':[{'line_number':i,'raw_text':l} for i,l in enumerate(text.splitlines(),1) if 'WARNING' in l],'strict_lines':[{'line_number':i,'raw_text':l} for i,l in enumerate(text.splitlines(),1) if STRICT.search(l)]}

assert set(os.sched_getaffinity(0))=={4}
manifest=load('manifest.json');export=load('windows/source.json');verification=load('verification/results.json')
for label,r in [('manifest',manifest),('export',export),('verification',verification)]:source(label,r)
check('metadata','manifest export exact type-sensitive copy',len(manifest['exports'])==1 and same_json(manifest['exports'][0],export))
check('metadata','export version/build/completed',export['target']=='windows' and export['version']=='0.3.3-dev' and export['build_number']==6 and export['export_completed'] is True)
check('metadata','pinned manifest engine',manifest['engine']=='Godot 4.7.2')
artifact=export['artifact'];exe=artifact['sha256']
check('metadata','artifact SHA256 shape',re.fullmatch('[0-9a-f]{64}',exe) is not None)
check('metadata','artifact matches manifest',same_json(artifact,manifest['artifacts'][0]))
check('metadata','artifact allowed payload set',{x['path'] for x in export['payload']}=={'windows/SIGHTBREAK.exe','windows/SIGHTBREAK.console.exe','windows/GODOT-LICENSE.txt','windows/GODOT-COPYRIGHT.txt'})
check('metadata','payload main artifact equality',same_json(next(x for x in export['payload'] if x['path']=='windows/SIGHTBREAK.exe'),artifact))
check('metadata','archive receipt shape',len(manifest['artifacts'])==2 and manifest['artifacts'][1]['path']=='sightbreak-windows-debug.zip' and re.fullmatch('[0-9a-f]{64}',manifest['artifacts'][1]['sha256']) is not None)
check('verification','headless/demo/graphical ordered runs',[r['label'] for r in verification['runs']]==['windows-menu','windows-demo','windows-graphical-menu'])
for row in verification['runs']:
    check('verification',row['label']+' exit/log',type(row['exit_code']) is int and row['exit_code']==0 and row['clean_log'] is True)
    check('verification',row['label']+' no verbose','--verbose' not in row['command'])
check('verification','PCK/menu receipt',verification['targets']['windows']['artifact_inspection'] is True and verification['targets']['windows']['pck_resources']==134 and verification['targets']['windows']['native_graphical_menu']=='PASS')

reg=load('regressions/results.json');iso=load('regressions/isolation.json')
check('native','exact ordered16 suite names',[r['suite'] for r in reg]==list(EXPECTED))
check('native','pinned engine',iso['engine']==ENGINE)
check('native','original bounds',iso['suite_timeout_seconds']==120 and iso['probe_timeout_seconds']==30)
for k in ['passed','source_resources_unchanged','copied_resources_unchanged','temporary_project_removed']:check('native',k+' literal true',iso[k] is True)
check('native','empty finalization failure',iso['finalization_failures']==[] and iso['failure'] is None)
check('native','cleanup one owned namespace',len(iso['cleanup'])==1 and iso['cleanup'][0]['removed'] is True and ntpath.basename(iso['cleanup'][0]['user_namespace'])==iso['namespace'])
# Independently reproduce the captured resource inventory from Windows-filtered exact Git bytes.
expected_resources={}
for raw in git('ls-tree','-rz','--name-only',REF,'--','game').split(b'\0'):
    if not raw:continue
    p=raw.decode();rel=p.removeprefix('game/')
    if '.godot' in pathlib.PurePosixPath(rel).parts:continue
    data=git('--attr-source='+REF,'-c','core.autocrlf=true','-c','core.eol=crlf','-c','core.attributesfile=/dev/null','cat-file','--filters','--path='+p,REF+':'+p)
    expected_resources[rel]=hashlib.sha256(data).hexdigest()
check('native','327 exact Windows source resource hashes',len(expected_resources)==327 and expected_resources==iso['source_resources_sha256'])
probes=sorted((ROOT/'regressions').glob('producer-*.json'))
check('native','33 producing path receipts',len(probes)==33)
probe_records={p.name:present_json(p) for p in probes}
# Verify each expected exact sequence separately without relying on lexicographic fixture names.
expected_probe_names=['producer-01-bootstrap.json']
for i,name in enumerate(EXPECTED):expected_probe_names.extend([f'producer-{2+i*2:02d}-before-{name}.json',f'producer-{3+i*2:02d}-after-{name}.json'])
check('native','exact probe sequence',sorted(probe_records)==expected_probe_names)
for name,item in probe_records.items():
    suffix='bootstrap' if name=='producer-01-bootstrap.json' else name.split('-',3)[-1].removesuffix('.json')
    check('native/probes',name+' native producer directory',item['uses_custom_user_dir'] is True and item['custom_user_dir']==iso['namespace']+'/'+suffix and norm(item['user_data_dir'])==norm(ntpath.join(item['data_dir'],iso['namespace'],suffix)) and item['os']=='Windows')
bootstrap=probe_records['producer-01-bootstrap.json']
check('native','bootstrap empty state',bootstrap['profile_exists'] is False and bootstrap['diagnostics_exist'] is False)

summary_rows=[]
for i,row in enumerate(reg):
    name=row['suite'];scope='native/'+name
    check(scope,'exit0 and strict receipt',type(row['exit']) is int and row['exit']==0 and row['clean_log'] is True)
    check(scope,'finite suite wall',number(row['wall_seconds']) and 0<=row['wall_seconds']<=120)
    check(scope,'no native verbose','--verbose' not in row['command'])
    expected_script='res://tests/gunplay_rules_probe.gd' if name=='gunplay_rules' else 'res://tests/'+name+'_test.gd'
    check(scope,'exact suite resource argument',row['command'][-1]==expected_script and '--headless' in row['command'])
    for position in ['before','after']:
        item=row[position];base=ntpath.basename(item['producer_receipt'])
        check(scope,position+' standalone producing receipt matches',base in probe_records and same_json({k:v for k,v in item.items() if k not in ['producer_receipt','run']},probe_records.get(base)))
        check(scope,position+' native path identity',item['uses_custom_user_dir'] is True and item['custom_user_dir']==iso['namespace']+'/'+name and norm(item['user_data_dir'])==norm(ntpath.join(item['data_dir'],iso['namespace'],name)) and norm(item['project_path'])==norm(row['command'][row['command'].index('--path')+1]) and item['os']=='Windows')
        check(scope,position+' probe success',type(item['run']['exit']) is int and item['run']['exit']==0 and item['run']['clean_log'] is True and number(item['run']['wall_seconds']) and 0<=item['run']['wall_seconds']<=30)
    check(scope,'empty before state',row['before']['profile_exists'] is False and row['before']['diagnostics_exist'] is False)
    copied=ROOT/'regressions'/(name+'-userdata')
    actual_files={p.relative_to(copied).as_posix():hashlib.sha256(bind(p)).hexdigest() for p in copied.rglob('*') if p.is_file()}
    check(scope,'produced copied file hashes exact',actual_files==row['produced_files_sha256'])
    text=bind(ROOT/'regressions'/(name+'.log')).decode('utf-8')
    matches=re.findall(r'(?:checks[=:] ?|"checks":)([0-9]+)',text)
    if not matches:matches=re.findall(r'([0-9]+)/[0-9]+ passed',text)
    if not matches:matches=re.findall(r'([0-9]+) checks',text)
    count=int(matches[-1]) if matches else None
    check(scope,'named summary check count',count==EXPECTED[name])
    final=[l for l in text.splitlines() if ('checks' in l or re.search(r'\d+/\d+ passed',l)) and 'failures_so_far' not in l][-1]
    if '{' in final:
        payload=json.loads(final[final.index('{'):]);fail=payload.get('failures');check(scope,'zero summary failures',fail==[] or type(fail) is int and fail==0)
        if name=='bot_exhausted_primary':check(scope,'authority checks true',payload.get('authority_checks_passed') is True)
    elif 'failures' in final:check(scope,'zero summary failures',re.search(r'(?:failures=0|0 failures)',final) is not None)
    else:check(scope,'all summary checks pass',str(EXPECTED[name])+'/'+str(EXPECTED[name])+' passed' in final)
    summary_rows.append({'suite':name,'checks':count,'exit':row['exit'],'wall_seconds':row['wall_seconds'],'summary_line':final if len(final)<500 else final[:final.index('{')].strip()+' [large JSON summary separately bound in log]'})
check('native','29567 actual checks',sum(x['checks'] for x in summary_rows)==29567)
check('native','import exit0/strict',type(iso['import']['exit']) is int and iso['import']['exit']==0 and iso['import']['clean_log'] is True)

integration=[]
for name,schedule,delay,observer,armory in [('native-input','legacy',0,True,True),('reload-release-first','release-first',4,False,False),('reload-legacy-delayed','legacy',4,False,False)]:
    scope=name;r=load(name+'/results.json');cmd=load(name+'/commands.json');a=load(name+'/actions.json');authority=load(name+'/authority.json');telemetry=load(name+'/authority-telemetry.json')['samples'];join=load(name+'/join-snapshot.json')
    source(scope+'/artifact',r['artifact_source']);source(scope+'/authority',r['authority_source'])
    check(scope,'metadata/export/engine',r['engine']==ENGINE and r['executable_sha256']==exe and same_json(r['artifact_source'],export))
    check(scope,'success and exits',r['passed'] is True and type(r['client_exit']) is int and r['client_exit']==0 and type(r['server_exit']) is int and r['server_exit']==0)
    check(scope,'schedule distinct',r['input_schedule']==schedule and number(r['synthetic_fire_capture_delay_seconds']) and r['synthetic_fire_capture_delay_seconds']==delay and r['inventory_navigation_captured'] is armory)
    check(scope,'observer selection',(r.get('input_consumption_observation',{}).get('enabled') is True)==observer)
    check(scope,'whole budget and cleanup',number(r['elapsed_seconds']) and 0<=r['elapsed_seconds']<=240 and r['cleanup_errors']==[])
    check(scope,'two ordered roots',[x['name'] for x in cmd]==['server','client'] and same_json(cmd,r['commands']) and all(type(x['pid']) is int and x['pid']>0 and type(x['exit_code']) is int and x['exit_code']==0 for x in cmd) and cmd[0]['pid']!=cmd[1]['pid'])
    check(scope,'no verbose/automatic reload override',all('--verbose' not in x['command'] and '--automatic-reload' not in x['command'] for x in cmd))
    check(scope,'observer argument position',all((x['command'].count('--native-input-observation')==1 and x['command'].index('--native-input-observation')>x['command'].index('--')) if observer else '--native-input-observation' not in x['command'] for x in cmd))
    check(scope,'authority exact result copy',same_json(authority,r['authority']))
    check(scope,'authority protocol/mode',authority['protocol']==6 and authority['prediction_default'] is False and authority['passed'] is True and authority['reload_trigger']=='native client input' and r['reload_trigger']=='native client input')
    check(scope,'authority fire/reload fields',all(authority[k] is True for k in ['reload_seen','reload_completed','reload_command_seen']) and type(authority['shots']) is int and authority['shots']>0 and authority['lowest_ammo']==30-authority['shots'])
    fire_down=next(i for i,x in enumerate(a) if x['event']=='button_after' and x['down'] is True);fire_up=next(i for i,x in enumerate(a) if x['event']=='button_after' and x['down'] is False)
    capture_begin=next(i for i,x in enumerate(a) if x['event']=='capture_begin' and x['capture']=='04-fire-input');capture_end=next(i for i,x in enumerate(a) if x['event']=='capture_end' and x['capture']=='04-fire-input')
    check(scope,'literal capture/fire release schedule',fire_down<capture_begin<capture_end<fire_up if schedule=='legacy' else fire_down<fire_up<capture_begin<capture_end)
    delays=[x for x in a if x['event'].startswith('synthetic_capture_delay_')]
    check(scope,'literal delay actions',len(delays)==0 if delay==0 else len(delays)==2 and delays[0]['event']=='synthetic_capture_delay_begin' and delays[1]['event']=='synthetic_capture_delay_end' and delays[0]['delay_seconds']==delay and delays[1]['seconds']-delays[0]['seconds']>=delay)
    for timing_key,select in [('fire_button_edges',lambda x:x['event'] in ['button_before','button_after']),('reload_key_edges',lambda x:x['event'] in ['key_before','key_after'] and x.get('key')=='r')]:check(scope,timing_key+' actual action copy',same_json(r['input_timing'][timing_key],[x for x in a if select(x)]))
    check(scope,'timeline finite monotonic',all(number(x['seconds']) and x['seconds']>=0 for x in a) and all(a[i]['seconds']<=a[i+1]['seconds'] for i in range(len(a)-1)))
    check(scope,'telemetry present and monotonic',len(telemetry)>0 and all(type(x['simulation_tick']) is int for x in telemetry) and all(telemetry[i]['simulation_tick']<=telemetry[i+1]['simulation_tick'] for i in range(len(telemetry)-1)))
    required_reasons=['shot','native_reload_command','reload_started','reload_completed','report']
    reasons=collections.Counter(x['reason'] for x in telemetry)
    check(scope,'native consumed reload observations',all(reasons[k]>0 for k in required_reasons))
    completed=[x for x in telemetry if x['reason']=='reload_completed'][-1]
    check(scope,'completed ammunition conservation',completed['ammo']==30 and completed['reserve']==90-authority['shots'] and completed['reload_remaining']==0 and completed['shots']==authority['shots'])
    started=[x for x in telemetry if x['reason']=='reload_started'][-1];native_command=[x for x in telemetry if x['reason']=='native_reload_command'][-1]
    check(scope,'reload start/completion ordering',native_command['reload_input'] is True and started['reload_remaining']>0 and native_command['simulation_tick']<=started['simulation_tick']<completed['simulation_tick'])
    captures=[x['capture'] for x in a if x['event']=='capture_end'];check(scope,'required reached captures',all(x in captures for x in ['04-fire-input','05-after-fire-input','06-after-authority-reload-start','07-after-authority-reload-completion','08-settled']))
    capture_files=[ROOT/name/(x+'.png') for x in captures]
    check(scope,'all declared PNG files present',all(p.is_file() for p in capture_files))
    pngs={p.name:hashlib.sha256(bind(p)).hexdigest() for p in capture_files}
    if name=='reload-legacy-delayed':
        outer=load(name+'/diagnostic-exit.json');check(scope,'legacy wrapper exit0',type(outer['exit_code']) is int and outer['exit_code']==0)
    collector={}
    for logname,role in [('client.log','client'),('server.log','authority')]:
        text=bind(ROOT/name/logname).decode('utf-8');cl=[json.loads(l.split(' ',1)[1]) for l in text.splitlines() if l.startswith('SIGHTBREAK_INPUT_OBSERVATION ')]
        check(scope,logname+' observer gated presence',bool(cl)==observer)
        if cl:
            check(scope,logname+' basic collector identity',all(x['schema']==1 and x['role']==role for x in cl) and all(cl[i]['index']<cl[i+1]['index'] for i in range(len(cl)-1)))
            collector[logname]={'printed_rows':len(cl),'last_index':cl[-1]['index'],'last_counters':cl[-1]['counters'],'last_actor':cl[-1]['actor'],'reason_counts':dict(collections.Counter(x['reason'] for x in cl))}
    integration.append({'gate':name,'schedule':schedule,'synthetic_delay_seconds':delay,'elapsed_seconds':r['elapsed_seconds'],'authority':authority,'reload_started_tick':started['simulation_tick'],'reload_completed_tick':completed['simulation_tick'],'completed_ammunition':[completed['ammo'],completed['reserve']],'captures':captures,'fire_and_after_fire_png_identical':pngs['04-fire-input.png']==pngs['05-after-fire-input.png'],'collector_summary_only':collector,'cleanup_errors':r['cleanup_errors'],'windows_job_accounting':'Success receipt and exact source imply original query reached; numeric runtime accounting buffer is not separately serialized'})

scenarios=[]
for name,scenario,budget in [('offline-plant','plant',180),('offline-defuse','defuse',180),('offline-full-match','full-match',1800)]:
    scope=name;r=load(name+'/results.json');cmd=load(name+'/commands.json');events=lines(name+'/trace/events.jsonl');actions=lines(name+'/actions.jsonl');initial=events[0]
    source(scope+'/source',r['source']);source(scope+'/artifact',r['artifact_source'])
    check(scope,'engine/export/executable',r['engine']==ENGINE and r['executable_sha256']==exe and same_json(r['artifact_source'],export))
    check(scope,'controller hash exact Git LF',r['controller_sha256']==hashlib.sha256(git('show',REF+':scripts/verify_offline_match.py')).hexdigest())
    check(scope,'passed/timeout/target',r['passed'] is True and r['timeout_seconds']==budget and r['target']=='windows' and r['scenario']==scenario and number(r['elapsed_seconds']) and 0<=r['elapsed_seconds']<=budget)
    check(scope,'controller original suffix',r['controller_command'][1:]==['scripts/verify_offline_match.py','--target','windows','--hosted-render-priority','below-normal','--scenario',scenario,'--display',{'plant':':103','defuse':':104','full-match':':105'}[scenario],'--timeout',str(budget),'--output','builds/desktop-playability/'+name])
    check(scope,'ordered close roots and exits',[x['name'] for x in cmd]==['client','reopened'] and same_json(cmd,r['commands']) and all(type(x['pid']) is int and x['pid']>0 and type(x['exit_code']) is int and x['exit_code']==0 for x in cmd) and cmd[0]['pid']!=cmd[1]['pid'] and type(r['initial_exit']) is int and r['initial_exit']==0 and type(r['reopened_exit']) is int and r['reopened_exit']==0)
    check(scope,'no new verbose',all('--verbose' not in x['command'] for x in cmd))
    check(scope,'cleanup and normal close receipt',r['cleanup_errors']==[] and r['exit_method']=='WM_CLOSE' and r['progression_settings_restart_equal'] is True)
    check(scope,'initial exact result copy',same_json(r['initial'],initial))
    check(scope,'initial conditions/rules',initial['event']=='initial' and initial['initial_conditions']==('stock_spawns_teams_random_seeds' if scenario=='full-match' else 'declared_initial_spawns_side_and_seeds_only') and initial['rules']==RULES and initial['protocol']==6 and initial['prediction_enabled'] is False and initial['time_scale']==1)
    check(scope,'initial ten alive stock actors',len(initial['actors'])==10 and len({x['id'] for x in initial['actors']})==10 and all(x['alive'] is True and x['health']==100 for x in initial['actors']))
    old=initial['initial_profile'];check(scope,'initial empty isolated profile',old['scope']=='offline_training' and old['matches']==0 and old['history']==[] and old['xp']==0 and old['credits']==0)
    check(scope,'trace indices/order/no drops',all(type(x['event_index']) is int for x in events) and all(events[i]['event_index']+1==events[i+1]['event_index'] for i in range(len(events)-1)) and all(x.get('events_dropped',0)==0 for x in events) and all(events[i]['simulation_tick']<=events[i+1]['simulation_tick'] for i in range(len(events)-1)))
    check(scope,'actions monotonic and final released',all(number(x['seconds']) and x['seconds']>=0 for x in actions) and all(actions[i]['seconds']<=actions[i+1]['seconds'] for i in range(len(actions)-1)) and actions[-1]['held_keys']==[])
    captures=r['captures'];missing=[];png_hashes={}
    for cap in captures:
        file=ROOT/name/(cap['name']+'.png')
        if file.exists():
            data=bind(file);png_hashes[file.name]=hashlib.sha256(data).hexdigest()
            check(scope,'PNG signature/dimensions '+cap['name'],data[:8]==b'\x89PNG\r\n\x1a\n' and data[12:16]==b'IHDR' and [int.from_bytes(data[16:20],'big'),int.from_bytes(data[20:24],'big')]==cap['dimensions'])
        else:missing.append(file.name)
        fr=cap.get('render_freshness')
        if fr:
            check(scope,'drawn frame fence '+cap['name'],type(fr['before_drawn_frames']) is int and fr['ready_drawn_frames']>=fr['before_drawn_frames']+2 and fr['after_capture_drawn_frames']>=fr['ready_drawn_frames'])
    check(scope,'only bounded round screenshots absent',all(x.startswith('round-') for x in missing))
    check(scope,'no reported capture phase mutation',all(x.get('render_phase_changed') is not True for x in captures))
    facts={'scenario':scenario,'elapsed_seconds':r['elapsed_seconds'],'trace_events':len(events),'actions':len(actions),'captures_declared':len(captures),'captures_present':len(png_hashes),'bounded_round_pngs_absent':missing,'normal_exits':[r['initial_exit'],r['reopened_exit']],'cleanup_errors':r['cleanup_errors'],'partial_checks':r['partial_checks']}
    observed=[x['observed'] for x in actions if x['event']=='observed']
    if scenario in ['plant','defuse']:
        check(scope,'declared objective seed42',initial['match_seed']=='42' and any('--offline-seed=42' in x['command'] for x in cmd))
        check(scope,'no completed profile file in objective fixture',not (ROOT/name/'state/roaming/Godot/app_userdata/SIGHTBREAK/offline_training.json').exists())
        required=3 if scenario=='plant' else 5;goal='planted' if scenario=='plant' else 'defused';message='Relay device armed' if scenario=='plant' else 'Relay device defused';h=r['objective_hold'];prior_tick=h['command_simulation_tick']
        completed=[x for x in events if x['event']=='notification' and message in x.get('message','') and x['simulation_tick']>prior_tick];check(scope,'one matching final completion notification',len(completed)==1)
        done=completed[0];held=[x for x in events if x['event']=='local_interact_input' and prior_tick<x['simulation_tick']<=done['simulation_tick']]
        check(scope,'one uninterrupted consumed held-E edge',len(held)==1 and held[0]['held'] is True)
        start=held[0];secs=done['elapsed']-start['elapsed'];ticks=done['simulation_tick']-start['simulation_tick']
        check(scope,'copied hold edges exact',same_json(start,h['input_started']) and same_json(done,h['completion_notification']))
        check(scope,'full source consumed hold duration',secs+1/60+1e-6>=required and ticks+1+1e-6>=required*60 and done['elapsed']-h['command_elapsed']+1/60+1e-6>=required)
        check(scope,'hold duration receipts exact',h['simulation_seconds']==secs and h['simulation_ticks']==ticks and h['one_tick_tolerance_seconds']==1/60 and r['objective_hold_wall_budget_seconds']==required*3)
        samples=h['samples'];check(scope,'authoritative progress monotonic',len(samples)>0 and all(x['progress']>0 for x in samples) and all(samples[i]['progress']<=samples[i+1]['progress']+1e-6 and samples[i]['simulation_tick']<samples[i+1]['simulation_tick'] for i in range(len(samples)-1)))
        transition=next(x for x in events if x['event']=='local_contribution' and x['simulation_tick']>=done['simulation_tick'])
        check(scope,'actual contribution identity/state',transition['local_actor']['id']==initial['local_actor']['id'] and transition['objective_state']==goal and transition['local_contribution']==r['local_contribution_before']+1==r['local_contribution_after'] and r['local_contribution_before']==0)
        count=r['credits_before'];actor=transition['local_actor'];expected=min(9000,count+300)
        if transition['phase']=='post':
            before_score=initial['attack_score'] if actor['team']==0 else initial['defend_score'];after_score=transition['attack_score'] if actor['team']==0 else transition['defend_score'];expected=min(9000,expected+(2700 if after_score>before_score else 1900))
        check(scope,'ordinary objective funds',r['credits_after']==actor['credits']==expected)
        check(scope,'real approach displacement',math.isclose(math.hypot(r['approach_end'][0]-r['approach_origin'][0],r['approach_end'][2]-r['approach_origin'][2]),r['approach_distance'],abs_tol=1e-9) and r['approach_distance']>(4.2 if scenario=='plant' else 2))
        input_edges=[x for x in events if x['event']=='local_interact_input'];check(scope,'invalid/interrupted/final consumed edges',len(input_edges)==6 and [x['held'] for x in input_edges]==[True,False,True,False,True,False] and input_edges[0]['interaction_progress']==0 and input_edges[1]['interaction_progress']==0 and input_edges[2]['interaction_progress']>0 and input_edges[3]['interaction_progress']==0)
        utility=next(x for x in events if x['event']=='utility');check(scope,'ordinary smoke inventory consumption',utility['local_actor']['id']==initial['local_actor']['id'] and utility['local_actor']['smokes']==initial['local_actor']['smokes']-1 and any(x['event']=='key' and x.get('key')=='q' and x.get('down') is True for x in actions))
        check(scope,'natural resolution and next round',any(x['event']=='phase' and x['phase']=='post' for x in events) and any(x['event']=='round_number' and x['round_number']==2 and x['phase']=='buy' for x in events))
        if scenario=='plant':
            guidance=next(x for x in actions if x['event']=='capture_begin' and x['capture']=='06b-postplant-role-guidance');ctx=[x['observed'] for x in actions if x['event']=='observed' and x['seconds']<guidance['seconds']][-1]
            check(scope,'living postplant role context',ctx['phase']=='live' and ctx['objective_state']=='planted' and ctx['round_number']==1 and ctx['local_actor']['id']==initial['local_actor']['id'] and ctx['local_actor']['alive'] is True and ctx['local_actor']['team']==0 and ctx['local_actor']['health']>0)
        else:
            planter=next(x for x in initial['actors'] if x['id']==r['bot_planter_id']);check(scope,'independent ordinary bot planter',planter['team']==0 and planter['id']!=initial['local_actor']['id'] and any(x['event']=='objective_state' and x['objective_state']=='planted' and x['simulation_tick']<prior_tick for x in events))
        facts.update({'hold_input_tick':start['simulation_tick'],'completion_tick':done['simulation_tick'],'simulation_seconds':secs,'simulation_ticks':ticks,'credits_before_after':[r['credits_before'],r['credits_after']],'objective_resolution':r['objective_resolution'],'actor_death_ticks':[x['simulation_tick'] for x in events if x['event']=='alive' and x['local_actor']['alive'] is False],'approach_distance':r['approach_distance']})
    else:
        check(scope,'no seed/scenario overrides',all(not any(v.startswith('--offline-seed=') or v.startswith('--offline-scenario=') for v in x['command']) for x in cmd))
        done=[x for x in events if x['event']=='completed'];check(scope,'exact one completion no duplicates',len(done)==1 and not any(x['event']=='duplicate_completion' for x in events))
        completed=done[0];summary=completed['summary'];training=completed['training_after'];check(scope,'completed raw summary/profile exact result copies',same_json(summary,r['summary']) and same_json(training,r['training_after']))
        check(scope,'one completion counter no drops',completed['completion_calls']==1 and completed['events_dropped']==0)
        visible=r['final_roster_visibility'];check(scope,'actual final roster visibility',visible['phase']=='match_over' and visible['ui']['scoreboard_visible'] is True and semantic(visible['summary'],summary))
        n=summary['rounds'];attack=summary['attack_score'];defend=summary['defend_score'];roster=summary['scoreboard'];humans=[x for x in roster if x.get('local') is True];human=humans[0]
        check(scope,'stock score rules',summary['offline'] is True and 7<=n<=12 and attack+defend==n and (max(attack,defend)==7 or n==12))
        check(scope,'exact5v5 final roster',len(roster)==10 and len({x['id'] for x in roster})==10 and len(humans)==1 and all(sum(x['team']==team for x in roster)==5 for team in [0,1]))
        check(scope,'summary matches human',all(summary[k]==human[k] for k in ['kills','assists','deaths','objectives']))
        check(scope,'outcome after halftime',summary['won'] is ((attack>defend) if human['team']==0 else (defend>attack)) and summary['draw'] is (attack==defend))
        natural={x['round_number'] for x in events if x['event'] in ['initial','round_number']};check(scope,'every natural round',natural==set(range(1,n+1)) and sorted(natural)==r['natural_rounds'])
        seventh=next(x for x in events if x['event']=='round_number' and x['round_number']==7);check(scope,'natural halftime switch',seventh['local_actor']['team']!=initial['local_actor']['team'] and human['team']==seventh['local_actor']['team'])
        xp=old['xp']+120+15*summary['kills']+50*summary['objectives'];level=1+int(math.sqrt(xp/150));earned=100+(75 if summary['won'] else 0)+(150 if old['last_daily']!=training['last_daily'] else 0)+(level-old['level'])*250
        check(scope,'recomputed earned formulas',r['expected_xp']==xp and r['expected_credits_earned']==earned and training['scope']=='offline_training' and training['matches']==1 and len(training['history'])==1)
        expected={'xp':xp,'level':level,'credits':old['credits']+earned,'wins':old['wins']+int(summary['won']),'kills':old['kills']+summary['kills'],'deaths':old['deaths']+summary['deaths']}
        check(scope,'all additive profile counters',all(number(training[k]) and training[k]==v for k,v in expected.items()))
        check(scope,'exact earned history summary',all(semantic(training['history'][0].get(k),v) for k,v in summary.items()) and training['history'][0]['credits_earned']==earned)
        disk=load(name+'/state/roaming/Godot/app_userdata/SIGHTBREAK/offline_training.json');reopen=lines(name+'/trace-reopened/events.jsonl');runtime=reopen[0]
        check(scope,'disk/result/runtime semantic equality',semantic(disk,training) and semantic(r['reopened_initial_profile'],training) and semantic(runtime['initial_profile'],training) and semantic(r['training_before'],old))
        check(scope,'reopen fresh stock uncompleted buy',runtime['initial_conditions']=='stock_spawns_teams_random_seeds' and runtime['completion_calls']==0 and runtime['phase']=='buy' and all(x.get('completion_calls',0)==0 for x in reopen))
        check(scope,'unchanged settings',semantic(training['settings'],old['settings']) and semantic(disk['settings'],old['settings']))
        fired=r['fired_ammunition'];reload=r['reloaded_ammunition'];check(scope,'stock firearm conservation',r['initial_displacement']>=.3 and 0<fired[0]<15 and fired[1]==60 and reload[0]==15 and reload[1]<60 and sum(fired)==sum(reload))
        shot=[x for x in events if x['event']=='local_shot'];reload_events=[x for x in events if x['event']=='reload'];check(scope,'raw shot/reload events present',len(shot)>0 and len(reload_events)>=2)
        facts.update({'rounds':n,'score':[attack,defend],'local_final_team':human['team'],'won':summary['won'],'draw':summary['draw'],'human_kills_deaths':[summary['kills'],summary['deaths']],'xp':xp,'earned_credits':earned,'new_profile_counters':{k:training[k] for k in expected},'completion_tick':completed['simulation_tick'],'halftime_tick':seventh['simulation_tick'],'fire_ammunition':fired,'reload_ammunition':reload,'initial_displacement':r['initial_displacement']})
    scenarios.append(facts)

# Read every non-living complete original log, including copied user logs; parent owns offline-input.
all_logs=[loginfo(p) for p in sorted(ROOT.rglob('*.log')) if p.relative_to(ROOT).parts[0]!='offline-input']
for info in all_logs:
    check('strict_logs',info['path']+' no strict error/leak',not info['strict_failed'])
    check('strict_logs',info['path']+' UTF8 complete decode',not info['utf8_replacement'])
warning_logs=[x for x in all_logs if x['warnings']]
report={'scope':'Independent read-only actual non-living sub-audit in reused thread; parent owns living route/focus/verbose and final qualification','run_id':40089125575,'attempt':1,'job_id':120858007351,'source_identity':IDENTITY,'evidence_checks':checks,'failed_evidence_checks':[x for x in checks if not x['passed']],'native_suites':summary_rows,'native_resource_paths':len(expected_resources),'native_producer_receipts':len(probes),'integration_gates':integration,'objective_and_stock_scenarios':scenarios,'artifact_receipt':artifact,'development_zip_receipt':manifest['artifacts'][1],'all_non_living_logs':all_logs,'warning_log_count':len(warning_logs),'warning_occurrences':sum(len(x['warnings']) for x in warning_logs),'warning_blockers_retained':warning_logs,'input_bindings':inputs,'audit_corrections':['Attempt1 used another controller exit_method literal, producing three decoder-only mismatches. Source/results use WM_CLOSE; original helper/output/report are retained. No raw/runtime change.','Attempt2 expected numeric42 for observer match_seed, producing two decoder-only mismatches. Pinned offline_diagnostics.gd243 intentionally serializes str(game._rng.seed); original seed/command facts remain exact, corrected comparison is literal string42. Attempt2 helper/output/report are retained.'],'overall_product_acceptance':False,'limits':['Generic ANGLE warnings remain strict qualification blockers even when native_log.failed returns false','No physical-device/input feel/performance/causal/retaining-owner claims','Ordinary 04-fire-input and05-after-fire-input PNGs are byte-identical; four authoritative shots and reload completion do not establish rendered firing response or physical latency','Large executable/development ZIP not transferred: receipt hashes/manifest identity are checked; binary/PCK/archive bytes are not independently rehashed here','Windows job numeric accounting buffer is not serialized; exact source and success receipts establish original success branch, not a separate live process observation','Native isolation cleanup is verified from bound receipts and copied evidence; no live filesystem/process probe was performed','Collector extraction is a basic presence/type/authority-summary check; sparse emission, late tails, overhead and comprehensive input coverage remain unmeasured','Full-match round PNGs absent from supported bounded QA are inventoried as unseen; retained captures need separate visual judgement','Prior40080238905 leak,40083894472 route failure and legacy-delay historical failure remain unchanged; this run gives no cause/fix inference']}
OUT.mkdir(parents=True,exist_ok=True);dest=OUT/'NON_LIVING_ACTUAL_AUDIT.json';dest.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'report':str(dest),'bytes':dest.stat().st_size,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'checks':len(checks),'failed_checks':report['failed_evidence_checks'],'native_checks':sum(x['checks'] for x in summary_rows),'producer_probes':len(probes),'non_living_logs':len(all_logs),'warning_logs':len(warning_logs),'warning_occurrences':report['warning_occurrences'],'scenarios':scenarios}))
