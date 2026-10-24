#!/usr/bin/env python3
"""Independent filesystem/Git/complete-stream review. Never launches Godot."""
import ast
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess

SOURCE=Path('/workspace/sightbreak-exhausted-primary-selection')
RAW=SOURCE/'.local/exhausted-selection-candidate-r1'
HEAD='6276f0b799fde78811075af1fc37434ea4d0aec8'
ACCEPTED='1b7ebc71290e6c4c23017f7a2d8539d7c5eec149'
ENGINE=Path('/workspace/tools/godot-4.7.2/Godot_v4.7.2-stable_linux.x86_64')
ENGINE_SHA='8d106cbe6144c2dc7e881d61d2429c1a8a76e6b22ef48bd5e48dcf934953f71e'
UID='game/tests/bot_exhausted_primary_test.gd.uid'

def sha(data):return hashlib.sha256(data).hexdigest()
def git(*args):return subprocess.check_output(['git',*args],cwd=SOURCE)
def read(name):return json.loads((RAW/name).read_text())
def inventory(root):return {str(p.relative_to(root)):dict(bytes=p.stat().st_size,sha256=sha(p.read_bytes())) for p in sorted(root.rglob('*')) if p.is_file()}
def noncache(mapping):return {k:v for k,v in mapping.items() if '.godot' not in Path(k).parts}
def strict(text):
    return bool(re.search(r'^(?:SCRIPT ERROR|ERROR:)|Parse Error|ObjectDB.*leaked|Leaked instance|Orphan\s*StringName|Orphan StringName',text,re.M|re.I) or re.search(r'\b[1-9][0-9]*\s+unclaimed string names\b',text,re.I))

def run():
    checks=0
    def check(value,message):
        nonlocal checks
        checks+=1
        assert value,message
    report=read('overall.receipt.json')
    terminal_path=RAW.with_name(RAW.name+'-wrapper.stdout')
    terminal=json.loads(terminal_path.read_text())
    wrapper_err=RAW.with_name(RAW.name+'-wrapper.stderr').read_bytes()
    check(wrapper_err==b'','wrapper stderr empty')
    check(terminal['passed'] is True and terminal['publication_confirmed'] is True and terminal['block']=='candidate','terminal final success/confirmed')
    check(report['passed'] is True and report['failure'] is None and not report['finalization_failures'],'stored no failure')
    check(report['publication_confirmed'] is False and 'wall_seconds' not in report,'explicitly tentative snapshot scope')
    journal=Path(report['journal']);j=json.loads(journal.read_text())
    check(j['passed'] is True and j['source_head']==HEAD and j['output']==str(RAW) and j['block']=='candidate','one-shot completed journal')
    check(journal==SOURCE/('.local/exhausted-selection-acquisition-claims/'+HEAD+'-candidate.json'),'fixed one-shot path')
    check({x['path'] for x in terminal['publication_readbacks']}=={str(RAW/'overall.receipt.json'),str(journal)} and len(terminal['publication_readbacks'])==2,'both unique terminal readbacks')
    check(report['wall_seconds_before_publication']<=terminal['wall_seconds']<=240 and all(x['readback_elapsed_seconds']<=terminal['wall_seconds'] for x in terminal['publication_readbacks']),'final original whole deadline')
    check(report['expected_source_head']==HEAD and report['accepted_candidate']==ACCEPTED and report['whole_bound_seconds']==240,'exact acquisition/source scope')
    check(not git('diff',HEAD,ACCEPTED,'--','game','scripts'),'accepted game/scripts immutable')
    check(report['engine_sha256_before']==report['engine_sha256_after']==ENGINE_SHA==sha(ENGINE.read_bytes()),'pinned actual engine unchanged')
    check(report['recognized_godot_before']==report['recognized_godot_after']==[],'no recorded native overlap')
    before,after=read('original-tracked-before.json'),read('original-tracked-after.json')
    check(before==after and report['original_tracked_inventory_unchanged'],'whole original inventory unchanged')
    tree={}
    for item in git('ls-tree','-r','-z',HEAD).split(b'\0'):
        if item:
            meta,name=item.split(b'\t',1);mode,typ,blob=meta.decode().split();tree[name.decode()]=(mode,blob)
    check(len(before)==len(tree) and {x['path'] for x in before}==tree.keys(),'complete exact Git tree inventory')
    present=0
    for row in before:
        name=row['path'];check((row['mode'],row['git_blob'])==tree[name] and row['index_stage']=='0','source index '+name)
        if row['present']:
            present+=1;data=git('cat-file','blob',row['git_blob'])
            check((row['bytes'],row['sha256'])==(len(data),sha(data)),'source bytes vs immutable Git '+name)
    copied=read('project-source-copy-map.json');stage=RAW/'staged';current=inventory(stage)
    check(set(copied)=={p for p in tree if p.startswith('game/')},'every tracked game source copied')
    manifests=[read(n) for n in ('staged-before-preparation.json','staged-before-import.json','staged-after-import.json','staged-after-attempt.json')]
    check(manifests[-1]==current,'complete terminal stage inventory vs disk')
    check(noncache(manifests[0])==noncache(manifests[1]),'first producer made no noncache source addition')
    check(noncache(manifests[2])==noncache(manifests[3]),'prepared source/UID unchanged after suite')
    check(set(noncache(manifests[2]))-set(noncache(manifests[0]))=={UID},'sole generated UID addition')
    for name,row in copied.items():
        data=git('cat-file','blob',tree[name][1]);expect=dict(bytes=len(data),sha256=sha(data))
        check((Path(row['original']),Path(row['staged']))==(SOURCE/name,stage/name),'mechanical copy paths '+name)
        check(row['git_blob']==tree[name][1] and (row['bytes'],row['sha256'])==(len(data),sha(data)),'copy map source identity '+name)
        for m in manifests:check(m[name]==expect,'every original staged byte identity '+name)
        check((stage/name).read_bytes()==data,'current staged immutable bytes '+name)
    uid=(stage/UID).read_bytes()
    check(re.fullmatch(rb'uid://[a-z0-9]+\n?',uid) is not None,'valid generated UID')
    check(uid==(RAW/'preparation-generated-uids'/UID).read_bytes(),'retained generated UID bytes')
    check(report['preparation']==dict(added_source_files=[UID],added_uid_first_observed='after editor import',original_tracked_bytes_unchanged=True,retained_uid_sha256=sha(uid),staged_noncache_source_set_equal_to_original=False),'truthful preparation boundary/set delta')
    check(sum(p.read_bytes()==uid for p in (stage/'game').rglob('*.uid'))==1,'unique generated UID')
    # Literal native probe is inspected without importing the acquisition wrapper.
    probe_ast=ast.parse(git('show',HEAD+':scripts/run_native_regressions.py').decode())
    probe=next(ast.literal_eval(n.value) for n in probe_ast.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='PROBE' for t in n.targets))
    check((RAW/'producer.gd').read_text()==probe and sha(probe.encode())==report['native_producer_source_sha256'],'native producer literal identity')
    baseenv=RAW/'private-state/bot_exhausted_primary'
    env={k:str(baseenv/p) for k,p in [('XDG_DATA_HOME','data'),('XDG_CONFIG_HOME','config'),('XDG_CACHE_HOME','cache'),('ANDROID_USER_HOME','android')]};env['SIGHTBREAK_STATE_DIR']=str(baseenv)
    prefix=[str(ENGINE),'--headless','--audio-driver','Dummy','--path',str(stage/'game')]
    commands=[prefix+['--script',str(RAW/'producer.gd'),'--','--receipt='+str(RAW/'bot_exhausted_primary-before.json')],prefix+['--editor','--import'],prefix+['--script','res://tests/bot_exhausted_primary_test.gd'],prefix+['--script',str(RAW/'producer.gd'),'--','--receipt='+str(RAW/'bot_exhausted_primary-after.json')]]
    labels=['bot_exhausted_primary-producer-before','preparation-import','bot_exhausted_primary','bot_exhausted_primary-producer-after']
    check([p['label'] for p in report['processes']]==labels,'exact four-stage order/no native retry')
    streams=[];phases=[]
    for p,command,cap in zip(report['processes'],commands,[30,120,120,30]):
        label=p['label'];stored=read(label+'.receipt.json')
        check(p['command']==command and p['cwd']==str(RAW) and p['private_environment']==env,'exact native command/environment '+label)
        check(p['phase_cap_seconds']==p['timeout_seconds']==cap and p['wall_seconds_before_publication']<=p['wall_seconds']<=cap,'phase original cap/publication '+label)
        for key in stored:
            if key!='end_utc':check(stored[key]==p[key],'published phase snapshot '+label+'/'+key)
        check(datetime.fromisoformat(stored['end_utc'])<=datetime.fromisoformat(p['end_utc']),'phase snapshot precedes final readback completion '+label)
        check(p['passed'] is True and p['failure'] is None and p['exit_code']==0 and not p['strict_log_failed'] and not p['timed_out'],'native successful result '+label)
        for key in ('signals','cleanup_failures','unexpected_members_after_root_exit','terminal_observed','terminal_same_session','terminal_recognized_godot'):check(p[key]==[],'scoped cleanup '+label+'/'+key)
        root=p['root_identity'];check(root['pid']==p['pid']==root['pgid']==root['sid'] and root['start_ticks']>0 and root['exe']==str(ENGINE),'owned stable PID/session '+label)
        check(len(p['observed_identities'])==1 and p['observed_identities'][0]['pid']==p['pid'] and p['observed_identities'][0]['start_ticks']==root['start_ticks'],'sole observed stable identity '+label)
        check(p['cleanup_seconds']<=5 and len(p['publication_readbacks'])==1 and p['publication_readbacks'][0]['path']==str(RAW/(label+'.receipt.json')),'phase readback and cleanup bound '+label)
        complete=[]
        for stream in ('stdout','stderr'):
            path=RAW/(label+'.'+stream+'.log');data=path.read_bytes();complete.append(data)
            check(p[stream]==dict(path=str(path),bytes=len(data),sha256=sha(data),present=True),'complete original stream hash '+label+'/'+stream)
            check(not strict(data.decode(errors='replace')),'independent complete strict scanner '+label+'/'+stream)
            streams.append(dict(name=path.name,bytes=len(data),sha256=sha(data)))
        check((RAW/(label+'.classification.log')).read_bytes()==b'\n'.join(complete),'classification exact concatenation '+label)
        phases.append(dict(label=label,pid=p['pid'],start_ticks=root['start_ticks'],seconds=p['wall_seconds'],exit=p['exit_code']))
    for a,b in zip(report['processes'],report['processes'][1:]):check(a['start_monotonic']+a['wall_seconds']<b['start_monotonic'],'strict sequential native order')
    data=baseenv/'data';userdata=data/'godot/app_userdata/SIGHTBREAK'
    for when in ('before','after'):
        probe=read('bot_exhausted_primary-'+when+'.json')
        check(probe==report['suites'][0][when]['receipt'],'native producer embedded receipt '+when)
        check(probe['os']=='Linux' and probe['uses_custom_user_dir'] is False and probe['custom_user_dir']=='','stock application identity '+when)
        check(Path(probe['data_dir'])==data and Path(probe['user_data_dir'])==userdata and Path(probe['project_path'])==stage/'game','actual native private paths '+when)
        check(probe['profile_exists'] is False and probe['diagnostics_exist'] is False,'no profile/diagnostics '+when)
        check(report['suites'][0][when]['path']==str(userdata),'producer agreed path '+when)
    check(report['suites'][0]['passed'] is True,'suite producer bracket completed')
    check(read('private-state-after-attempt.json')==inventory(RAW/'private-state'),'retained complete private state')
    check(read('bot_exhausted_primary-userdata-inventory.json')==inventory(userdata),'native userdata inventory')
    check(not any(p.is_symlink() for p in (RAW/'private-state').rglob('*')),'private state contains no symlinks')
    # Strict positive controls include the known gaps in frozen native_log.
    for text in ('Orphan StringName: Master','1 unclaimed string names at exit','WARNING: 2 ObjectDB instances were leaked at exit','Leaked instance: AudioStreamWAV','ERROR: failure'):
        check(strict(text),'strict known-pattern control '+text)
    check(not strict('0 unclaimed string names at exit'),'zero unclaimed names is not a positive count')
    return dict(independent_provenance_predicates=checks,source_head=HEAD,index_entries=len(tree),present_source_files=present,copied_game_files=len(copied),staged_files=len(current),new_uid=uid.decode().strip(),new_uid_sha256=sha(uid),terminal=terminal,wrapper_stdout_sha256=sha(terminal_path.read_bytes()),wrapper_stderr_sha256=sha(wrapper_err),phases=phases,strict_original_streams=streams,private_state_files=len(inventory(RAW/'private-state')),strict_native_pass=True,scope='Actual native identities/streams and observed cleanup only; outer zero exit separately retained by root, unobserved escaping descendants unqualified.')

if __name__=='__main__':print(json.dumps(run(),indent=2,sort_keys=True))
