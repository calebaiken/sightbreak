"""Read-only audit of retained actual native Windows artifacts; never launches Godot."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path, PureWindowsPath
import re
import subprocess

SOURCE='c32415148db1f110bbc7eadfca3793d4693429ff'
BASELINE='49ae54b0e4f5d880bdf06e4eb783a616b2dff684'
SUITES=['actor','match','authority_order','state_privacy','movement_prediction','peer_lifecycle','input_mode','menu_focus','offline_diagnostics','hud_objective_hint','activity_provenance','bot_squad_symmetry','bot_dry_weapon','bot_exhausted_primary','transaction_journal','gunplay_rules']
EXPECTED=[73,75,178,55,742,16,462,30,60,1535,32,2722,590,20116,41,2840]
KEYS=['source_commit','source_game_tree','source_content_sha256','source_validation_sha256']
SHA=lambda raw:hashlib.sha256(raw).hexdigest()
READ=lambda path:json.loads(path.read_text(encoding='utf-8-sig'))
NORMAL=lambda p:str(p).replace('\\','/').rstrip('/').lower()

def git(checkout,*args):
    return subprocess.check_output(['git',*args],cwd=checkout)

def prepare_source(checkout):
    tracked=git(checkout,'ls-tree','-rz',SOURCE).split(b'\0')
    trees={}
    for row in tracked:
        if row:
            info,path=row.split(b'\t',1)
            mode,kind,blob=info.decode().split()
            trees[path.decode()]={'mode':mode,'type':kind,'blob':blob}
    attrs=[p for p in trees if Path(p).name=='.gitattributes' and (p=='.gitattributes' or any(p.startswith(d+'/') for d in ('game','scripts','.github')))]
    attr_checks=[]
    for p in attrs:
        blob=git(checkout,'show',SOURCE+':'+p)
        materialized=checkout/p
        attr_checks.append({'path':p,'source_sha256':SHA(blob),'materialized_exists':materialized.is_file(),'materialized_equals_candidate':materialized.is_file() and materialized.read_bytes()==blob})
    if not all(r['materialized_equals_candidate'] for r in attr_checks):
        raise AssertionError('Candidate attributes are not materialized identically; filters cannot be admitted')
    paths=list(trees)
    groups=[[p for p in paths if p.startswith('game/') and 'tests' not in Path(p).parts and '.godot' not in Path(p).parts]]
    groups += [[p for p in paths if p.startswith(d+'/')] for d in ('scripts','.github','game/tests')]
    digests={flavor:{scope:hashlib.sha256() for scope in ('shipping','validation')} for flavor in ('git','windows')}
    files=[]; filtered={}; rawbytes={}
    for index,group in enumerate(groups):
        for p in sorted(group):
            if any(part in ('__pycache__','.godot') for part in Path(p).parts) or p.endswith('.pyc'):continue
            raw=git(checkout,'show',SOURCE+':'+p)
            win=git(checkout,'-c','core.autocrlf=true','-c','core.eol=crlf','-c','core.safecrlf=false','cat-file','--filters',SOURCE+':'+p)
            attrs_raw=git(checkout,'check-attr','-z','text','eol','filter','--',p).decode().split('\0')
            attrmap={attrs_raw[i+1]:attrs_raw[i+2] for i in range(0,len(attrs_raw)-1,3)}
            if attrmap['filter']!='unspecified':raise AssertionError('Unexpected external checkout filter: '+p)
            name=p.removeprefix('game/') if index==0 else p
            scope='shipping' if index==0 else 'validation'
            for flavor,data in [('git',raw),('windows',win)]:digests[flavor][scope].update(name.encode()+b'\0'+data+b'\0')
            filtered[p]=win;rawbytes[p]=raw
            files.append({'scope':scope,'path':p,**trees[p],'git_bytes':len(raw),'git_sha256':SHA(raw),'windows_bytes':len(win),'windows_sha256':SHA(win),'changed_by_windows_filter':raw!=win,'attributes':attrmap,'materialized_exists':(checkout/p).is_file(),'materialized_equals_git':(checkout/p).is_file() and (checkout/p).read_bytes()==raw})
    tree=git(checkout,'rev-parse',SOURCE+':game').decode().strip()
    identity=lambda flavor:{'source_commit':SOURCE,'source_game_tree':tree,'source_content_sha256':digests[flavor]['shipping'].hexdigest(),'source_validation_sha256':digests[flavor]['validation'].hexdigest()}
    unchanged=[]; changed=[]
    for p in sorted(p for p in paths if p.startswith('game/')):
        try:old=git(checkout,'show',BASELINE+':'+p)
        except subprocess.CalledProcessError:changed.append(p);continue
        (unchanged if old==git(checkout,'show',SOURCE+':'+p) else changed).append(p)
    uids=[{'path':p,'uid':rawbytes[p].decode().strip(),'sha256':SHA(rawbytes[p])} for p in sorted(rawbytes) if p.endswith('.uid')]
    source_result={'source_commit':SOURCE,'method':'Exact Git blobs; shipping and validation framing/order independently matches build_manifest.source; Windows materialization uses Git --filters with explicit core.autocrlf=true/core.eol=crlf and candidate-matching attributes. No local engine or native launch.','native_identity':identity('windows'),'git_identity':identity('git'),'attributes':attr_checks,'files':files,'windows_changed_paths':[r['path'] for r in files if r['changed_by_windows_filter']],'uid_inventory':uids,'uid_count':len(uids),'uid_values_unique':len({r['uid'] for r in uids})==len(uids),'materialized_game_bytes_equal_git':all(r['materialized_equals_git'] for r in files if r['path'].startswith('game/')),'baseline_comparison':{'baseline':BASELINE,'unchanged_game_paths':unchanged,'changed_game_paths':changed,'stock_semantic_oracle_dependencies_unchanged':changed==['game/scripts/gameplay/match.gd','game/tests/movement_prediction_test.gd']},'strict_matcher_source_sha256':SHA(rawbytes['scripts/native_log.py'])}
    return source_result,filtered

def log_audit(base,matcher_source):
    namespace={}
    exec(compile(matcher_source,'exact-c324-native_log.py','exec'),namespace)
    failed=namespace['failed']; rows=[];hits=[];warning_rows=[]
    for p in sorted(base.rglob('*')):
        if not p.is_file() or not (p.suffix=='.log' or p.name.endswith(('.stdout.txt','.stderr.txt'))):continue
        raw=p.read_bytes(); text=raw.decode('utf-8-sig',errors='replace')
        linehits=[];warnings=[];embedded=[]
        for n,line in enumerate(text.splitlines(),1):
            if failed(line):linehits.append({'line':n,'text':line})
            if re.search(r'(^|\s)WARNING:',line):warnings.append({'line':n,'text':line})
            if line.startswith('COMPETING_PROCESS '):
                for stream_index,stream in enumerate(json.loads(line.removeprefix('COMPETING_PROCESS '))):
                    if not isinstance(stream,str):continue
                    stream_hits=[{'line':i,'text':text} for i,text in enumerate(stream.splitlines(),1) if failed(text)]
                    stream_warn=[{'line':i,'text':text} for i,text in enumerate(stream.splitlines(),1) if re.search(r'(^|\s)WARNING:',text)]
                    embedded.append({'outer_line':n,'stream_index':stream_index,'sha256_utf8':SHA(stream.encode()),'strict_failed':failed(stream),'strict_lines':stream_hits,'warnings':stream_warn})
                    linehits.extend({'line':n,'embedded_stream':stream_index,'embedded_line':x['line'],'text':x['text']} for x in stream_hits)
                    warnings.extend({'line':n,'embedded_stream':stream_index,'embedded_line':x['line'],'text':x['text']} for x in stream_warn)
        row={'path':p.relative_to(base).as_posix(),'bytes':len(raw),'sha256':SHA(raw),'strict_failed':failed(text) or any(x['strict_failed'] for x in embedded),'strict_lines':linehits,'warnings':warnings,'embedded_child_streams':embedded,'replacement_character_count':text.count('\ufffd'),'collector_emission_lines':sum(x.startswith('SIGHTBREAK_INPUT_OBSERVATION ') for x in text.splitlines())}
        rows.append(row)
        hits.extend({'path':row['path'],**x} for x in linehits)
        warning_rows.extend({'path':row['path'],**x} for x in warnings)
    return {'logs':rows,'log_count':len(rows),'strict_failure_lines':hits,'warning_lines':warning_rows,'candidate_strict_logs_clean':bool(rows) and not hits,'preregistered_warning_gate_clean':bool(rows) and not warning_rows,'complete_retained_logs_clean':bool(rows) and not hits and not warning_rows,'scope':'All retained log bytes, exact candidate native_log.failed; additional WARNING inventory. Producer clean flags are separately cross-checked.'}

def native_audit(base,filtered):
    reg=base/'regressions'; iso=READ(reg/'isolation.json');results=READ(reg/'results.json')
    checks={};rows=[];count_deviations=[]
    checks['original_sixteen_order']=[r['suite'] for r in results]==SUITES
    checks['original_limits_engine']=iso['suite_timeout_seconds']==120 and iso['probe_timeout_seconds']==30 and iso['engine']=='4.7.2.stable.official.ed1daf0bf'
    checks['private_namespace_shape']=re.fullmatch(r'SIGHTBREAK-native-tests-[a-f0-9]{32}',iso['namespace']) is not None
    checks['original_import_argv']=iso['import']['command'][1]=='--path' and iso['import']['command'][3:]==['--headless','--editor','--import','--quit']
    checks['original_import_log_retained']=(reg/PureWindowsPath(iso['import']['log']).name).is_file()
    checks['clean_import_receipt']=iso['import']['exit']==0 and iso['import']['clean_log'] is True and 0<iso['import']['wall_seconds']<120
    resource_expected={p.removeprefix('game/'):SHA(raw) for p,raw in filtered.items() if p.startswith('game/')}
    checks['complete_source_resource_inventory']=iso['source_resources_sha256']==resource_expected
    checks['source_copied_resource_invariance_receipts']=iso['source_resources_unchanged'] is True and iso['copied_resources_unchanged'] is True
    checks['finalization_owned_cleanup_receipt']=iso['passed'] is True and iso['failure'] is None and iso['finalization_failures']==[] and iso['temporary_project_removed'] is True and len(iso['cleanup'])==1 and all(r['removed'] is True and NORMAL(r['user_namespace']).endswith('/'+iso['namespace'].lower()) for r in iso['cleanup'])
    producers=sorted(reg.glob('producer-*.json'))
    checks['33_original_native_producer_files']=len(producers)==33
    checks['exact_bootstrap_json_log_retained']=(reg/'producer-01-bootstrap.json').is_file() and (reg/'producer-01-bootstrap.log').is_file()
    checks['bootstrap_private_identity']=READ(reg/'producer-01-bootstrap.json')['custom_user_dir']==iso['namespace']+'/bootstrap'
    producer_rows=[]
    for p in producers:
        r=READ(p);private=r['custom_user_dir']
        good=r['os']=='Windows' and r['uses_custom_user_dir'] is True and private.startswith(iso['namespace']+'/') and NORMAL(r['user_data_dir'])==NORMAL(r['data_dir']+'/'+private) and NORMAL(r['project_path'])==NORMAL(iso['import']['command'][2])
        checks['producer_identity:'+p.name]=good
        producer_rows.append({'path':p.name,'sha256':SHA(p.read_bytes()),'receipt':r})
    summary_counts={};competing=[]
    for r in results:
        suite=r['suite'];pre=suite+':';command=r['command']
        suffix=['--headless','--script','res://tests/'+suite+'_test.gd']
        if suite in ('bot_dry_weapon','bot_exhausted_primary','gunplay_rules'):
            target='gunplay_rules_probe' if suite=='gunplay_rules' else suite+'_test'
            suffix=['--headless','--audio-driver','Dummy','--script','res://tests/'+target+'.gd']
        checks[pre+'exact_argv']=command[:3]==iso['import']['command'][:3] and command[1]=='--path' and command[3:]==suffix
        checks[pre+'normal_exit_original_limit']=r['exit']==0 and r['clean_log'] is True and 0<r['wall_seconds']<120
        log=(reg/(suite+'.log')).read_text(encoding='utf-8-sig')
        counts=[]
        for a,b,c,d,e,f in re.findall(r'checks=(\d+) failures=(\d+)|(?<!\d)(\d+) checks, (\d+) failures|(?<!\d)(\d+)/(\d+) passed',log):counts.append((int(a),int(b)) if a else (int(c),int(d)) if c else (int(f),int(f)-int(e)))
        for key,prefix in [('gunplay_rules','GUNPLAY_RULES '),('bot_dry_weapon','BOT_DRY_WEAPON_RESULT '),('bot_exhausted_primary','BOT_EXHAUSTED_RESULT ')]:
            if suite==key:
                native=[json.loads(x[len(prefix):]) for x in log.splitlines() if x.startswith(prefix)]
                counts=[(x['checks'],len(x['failures']) if isinstance(x['failures'],list) else x['failures']) for x in native]
        checks[pre+'single_zero_failure_native_summary']=len(counts)==1 and type(counts[0][0]) is int and counts[0][0]>0 and counts[0][1]==0
        if counts!=[(EXPECTED[SUITES.index(suite)],0)]:count_deviations.append({'suite':suite,'expected':EXPECTED[SUITES.index(suite)],'actual':counts})
        if len(counts)==1:summary_counts[suite]=counts[0][0]
        checks[pre+'fresh_before_state']=r['before']['profile_exists'] is False and r['before']['diagnostics_exist'] is False
        producer_names=[]
        for stage in ('before','after'):
            x=r[stage];name=PureWindowsPath(x['producer_receipt']).name;original=READ(reg/name);run=x['run']
            checks[pre+stage+'_exact_ordinal_producer_file']=name==('producer-%02d-%s-%s.json' % (2+2*SUITES.index(suite)+(stage=='after'),stage,suite))
            checks[pre+stage+'_producer_matches']=original=={k:v for k,v in x.items() if k not in ('producer_receipt','run')}
            checks[pre+stage+'_probe_argv_limit_normal_exit']=run['exit']==0 and run['clean_log'] is True and 0<run['wall_seconds']<30 and run['command'][:3]==command[:3] and len(run['command'])==8 and run['command'][3:5]==['--headless','--script'] and PureWindowsPath(run['command'][5]).name=='user_directory_probe.gd' and PureWindowsPath(run['command'][5]).parent==PureWindowsPath(command[2]).parent and run['command'][-2:]==['--','--receipt='+x['producer_receipt']] and x['custom_user_dir']==iso['namespace']+'/'+suite
            checks[pre+stage+'_complete_probe_log']=(reg/PureWindowsPath(run['log']).name).is_file()
            producer_names.append(name)
        produced={p.relative_to(reg/(suite+'-userdata')).as_posix():SHA(p.read_bytes()) for p in sorted((reg/(suite+'-userdata')).rglob('*')) if p.is_file()}
        checks[pre+'retained_userdata_inventory_matches']=produced==r['produced_files_sha256']
        if suite=='transaction_journal':
            children=[json.loads(x.removeprefix('COMPETING_PROCESS ')) for x in log.splitlines() if x.startswith('COMPETING_PROCESS ')]
            for child in children:
                for stream in child:competing.extend(json.loads(x.removeprefix('OWNER_BLOCKED ')) for x in stream.splitlines() if x.startswith('OWNER_BLOCKED '))
            checks[pre+'competing_child_ownership_receipt']=len(children)==len(competing)==1 and competing[0]['unchanged'] is True and competing[0]['pid']>0 and all(competing[0][k]==22 for k in ('claim','clear','stage'))
        rows.append({'suite':suite,'native_summary_counts':counts,'command':command,'exit':r['exit'],'wall_seconds':r['wall_seconds'],'producer_records':producer_names,'produced_files_sha256':produced,'raw_log_sha256':SHA((reg/(suite+'.log')).read_bytes())})
    return {'checks':checks,'all_checks_passed':all(checks.values()),'failed_checks':[k for k,v in checks.items() if not v],'suite_records':rows,'native_assertion_total':sum(summary_counts.values()) if len(summary_counts)==16 else None,'expected_count_deviations':count_deviations,'expected_counts_are_original_acceptance_gate':False,'original_producers':producer_rows,'bootstrap_success_scope':'Bootstrap JSON/private identity and original log retained. Its execute exit/wall receipt is discarded by the runner; later reached source plus passed isolation implies source checks succeeded, but bootstrap exit/time is not a separately retained raw receipt.','source_resource_count':len(iso['source_resources_sha256']),'retained_initial_inventory_independently_equals_exact_filtered_candidate':checks['complete_source_resource_inventory'],'resource_invariance_scope':'Initial inventory compared directly to exact Git-filtered bytes; final source and copied resource inventories are retained equality booleans, not per-file before/after inventories. No independent native filesystem observation.','cleanup_scope':'Raw owned namespace/removal/finalization receipts; no claim of host-wide escaped or short-lived descendant absence.','journal_competing_process_receipts':competing}

def provenance_audit(base,source,full=None):
    identity=source['native_identity'];rows=[];mismatches=[]
    def current(r):return all(r.get(k)==identity[k] for k in KEYS) and r.get('source_dirty') is False and r.get('source_game_dirty') is False
    for p in sorted(base.rglob('*.json')):
        try:v=READ(p)
        except (ValueError,UnicodeError):continue
        if not isinstance(v,dict):continue
        candidates=[('top',v)] if 'source_commit' in v else []
        candidates += [(k,v[k]) for k in ('source','authority_source','reopen_source','artifact_source') if isinstance(v.get(k),dict) and 'source_commit' in v[k]]
        candidates += [('exports['+str(i)+']',r) for i,r in enumerate(v.get('exports',[])) if isinstance(r,dict) and 'source_commit' in r]
        for name,r in candidates:
            row={'path':p.relative_to(base).as_posix(),'key':name,'matches':current(r),'identity':{k:r.get(k) for k in KEYS+['source_dirty','source_game_dirty']},'sha256':SHA(p.read_bytes())};rows.append(row)
            if not row['matches']:mismatches.append(row)
    manifest=READ(base/'manifest.json');exports=[x for x in manifest['exports'] if x['target']=='windows'];verification=READ(base/'verification/results.json');windows=exports[0];artifact=windows['artifact']
    checks={'all_source_receipts_exact_clean':bool(rows) and not mismatches,'one_complete_export':len(exports)==1 and windows['export_completed'] is True,'build_pinned_debug':manifest['build_type']=='debug' and manifest['engine']=='Godot 4.7.2','manifest_payload_artifact_join':artifact in manifest['artifacts'] and artifact in windows['payload'],'native_PCK_inspection_receipt':verification['targets']['windows']['artifact_inspection'] is True and verification['targets']['windows']['pck_resources']>0,'native_startup_receipts':len(verification['runs'])==3 and all(r['exit_code']==0 and r['clean_log'] is True for r in verification['runs'])}
    checks['startup_target_receipt_labels']=verification['targets']['windows']['native_execution']=='PASS (headless startup only)' and verification['targets']['windows']['native_graphical_menu']=='PASS'
    expected_labels=['windows-menu','windows-demo','windows-graphical-menu']
    checks['startup_exact_three_labels']=[r['label'] for r in verification['runs']]==expected_labels
    native_executable=verification['runs'][0]['command'][0]
    for run in verification['runs']:
        label=run['label'];cmd=run['command'];log=base/'verification'/(label+'.log')
        expected=['--headless','--','--smoke'] if label=='windows-menu' else ['--headless','--quit-after','120','--','--demo'] if label=='windows-demo' else ['--audio-driver','Dummy','--','--smoke']
        good=cmd[0]==native_executable and NORMAL(cmd[0]).endswith('/windows/sightbreak.exe')
        good=good and (cmd[1:]==expected if label!='windows-graphical-menu' else cmd[1:5]==expected and len(cmd)==6 and cmd[-1].startswith('--capture=') and PureWindowsPath(cmd[-1].removeprefix('--capture=')).name=='windows-menu.png')
        checks['startup_exact_argv:'+label]=good
        checks['startup_complete_log:'+label]=log.is_file()
        if label in ('windows-menu','windows-graphical-menu'):checks['startup_menu_ready:'+label]=log.is_file() and 'SIGHTBREAK_MAIN_READY screen=menu' in log.read_text(encoding='utf-8-sig')
    png=(full if full is not None else base)/'verification/windows-menu.png'
    checks['startup_original_graphical_PNG_retained']=png.is_file() and png.read_bytes().startswith(b'\x89PNG\r\n\x1a\n')
    required_runtime=['native-input','reload-release-first','reload-legacy-delayed','offline-input','offline-plant','offline-defuse','offline-full-match']
    for location in ['windows/source.json','manifest.json','verification/results.json']:
        required=base/location
        checks['required_build_source_receipt:'+location]=required.is_file() and current(READ(required))
    for location in required_runtime:
        required=base/location/'results.json'
        checks['required_runtime_identity_receipt:'+location]=required.is_file()
        if required.is_file():
            record=READ(required)
            checks['required_runtime_executable:'+location]=record.get('executable_sha256')==artifact['sha256']
            checks['required_runtime_source:'+location]=any(isinstance(record.get(key),dict) and current(record[key]) for key in ('source','authority_source'))
            checks['required_runtime_artifact_source:'+location]=isinstance(record.get('artifact_source'),dict) and current(record['artifact_source'])
    executable_joins=[];controllers=[]
    for p in sorted(base.rglob('*.json')):
        try:v=READ(p)
        except (ValueError,UnicodeError):continue
        if not isinstance(v,dict):continue
        if 'executable_sha256' in v:
            joined=v['executable_sha256']==artifact['sha256'];checks['executable_join:'+p.relative_to(base).as_posix()]=joined;executable_joins.append({'path':p.relative_to(base).as_posix(),'sha256':v['executable_sha256'],'matches':joined})
        if 'controller_sha256' in v:controllers.append({'path':p.relative_to(base).as_posix(),'controller_sha256':v['controller_sha256']})
    return {'checks':checks,'all_checks_passed':all(checks.values()),'failed_checks':[k for k,v in checks.items() if not v],'source_receipts':rows,'source_receipt_mismatches':mismatches,'artifact':artifact,'exports':exports,'runtime_executable_joins':executable_joins,'controller_receipts':controllers,'verification_runs':verification['runs'],'runner_PCK_resource_count':verification['targets']['windows']['pck_resources'],'graphical_PNG_path':str(png),'graphical_PNG_sha256':SHA(png.read_bytes()) if png.is_file() else None,'independent_executable_reparse':'BLOCKED: official development artifact12554384657 is146423542bytes, above supported32MiB transfer limit; not requested or transferred. No binary/embedded-PCK reparse.','independent_PCK_and_PE_resources_reparse':'BLOCKED with executable transfer; runner receipts establish separate reported scope only.'}

def main():
    p=argparse.ArgumentParser();p.add_argument('checkout',type=Path);p.add_argument('--raw',type=Path);p.add_argument('--full',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    a.output.mkdir(exist_ok=False)
    result,filtered=prepare_source(a.checkout)
    (a.output/'source.json').write_text(json.dumps(result,indent=2)+'\n')
    if not a.raw:
        print(json.dumps({'source_prepared':True,'files':len(result['files']),'uids':result['uid_count'],'windows_changed_paths':result['windows_changed_paths'],'identity':result['native_identity']}));return
    base=a.raw/'evidence' if (a.raw/'evidence').is_dir() else a.raw
    outputs={}
    for name,fn in [('strict_logs',lambda:log_audit(base,filtered['scripts/native_log.py'])),('native',lambda:native_audit(base,filtered)),('provenance',lambda:provenance_audit(base,result,a.full))]:
        try:outputs[name]=fn()
        except Exception as e:
            import traceback
            outputs[name]={'audit_error':type(e).__name__,'message':str(e),'traceback':traceback.format_exc()}
        (a.output/(name+'.json')).write_text(json.dumps(outputs[name],indent=2)+'\n')
    print(json.dumps({k:{x:v[x] for x in ('all_checks_passed','failed_checks','log_count','complete_retained_logs_clean','native_assertion_total','expected_count_deviations','audit_error','message') if x in v} for k,v in outputs.items()}))

if __name__=='__main__':main()
