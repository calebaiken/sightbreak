#!/usr/bin/env python3
"""Independent actual receipt/source/cleanup audit. Never launches native work."""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import traceback

HERE=Path(__file__).resolve().parent
BUILDER=Path('/workspace/sightbreak-aggregate-combined-28a3e294')
BUILDER_COMMIT='bcfc7c3c57b33ad373b0a9e787eb187bc38d463f'
SOURCE='28a3e294c850482475b7ab74067c08538ae6310d'
RELATIVE='docs/reports/gauntlet/aggregate-combined-28a3e294-20261023'
PORTS={27991,29900,29901,29902,33540,33541,33542,33543}

def sha(data):return hashlib.sha256(data).hexdigest()
def git(root,*args):return subprocess.check_output(['git','-C',str(root),*args])

def main(args):
    frozen,run,out=args.frozen.resolve(),args.run.resolve(),args.output.resolve()
    out.mkdir(parents=True,exist_ok=False)
    report=dict(checks=0,failures=[],scope='Pure receipt/source audit plus read-only actual PID/session/socket observation; no native launch or signal.')
    def check(value,label):
        report['checks']+=1
        if not value:report['failures'].append(label)
    def read(name):return json.loads((run/name).read_text())
    try:
        pre=json.loads((HERE/'pre-run-source-review.json').read_text())
        before,after,command,result,engine,cleanup,resources,observed,supervisor=[read(n) for n in ['source-before.json','source-after.json','command.json','result.json','engine.json','cleanup.json','preflight-resources.json','observed-processes.json','supervisor-launch.json']]
        independent=json.loads((HERE/'independent-outer-live.json').read_text())
        check(pre['passed'] and pre['expected_source']==SOURCE and pre['builder_commit']==BUILDER_COMMIT,'passing exact prereleased source review')
        check(before==after,'all before/after source/input/UID receipts identical')
        check(before['source']['source_commit']==SOURCE and not before['source']['source_dirty'] and not before['source']['source_game_dirty'],'exact clean runtime source receipts')
        check(git(frozen,'rev-parse','HEAD').decode().strip()==SOURCE and not git(frozen,'status','--porcelain','--untracked-files=all'),'whole actual frozen checkout remains exact and clean')
        expected={r['path']:dict(bytes=r['bytes'],sha256=r['sha256']) for r in pre['inventory']}
        check(before['inputs']==expected,'all launch input paths/sizes/hashes equal independent preflight')
        for path,row in expected.items():
            data=(frozen/path).read_bytes()
            check(len(data)==row['bytes'] and sha(data)==row['sha256'],'actual retained exact input: '+path)
        check(before['uids']=={p:r for p,r in expected.items() if p.startswith('game/') and p.endswith('.uid')} and len(before['uids'])==138,'all tracked UIDs unchanged; no generated-source substitution')
        shipping,validation=hashlib.sha256(),hashlib.sha256()
        for p in sorted((frozen/'game').rglob('*')):
            relative=p.relative_to(frozen/'game')
            if p.is_file() and '.godot' not in relative.parts and 'tests' not in relative.parts:
                shipping.update(relative.as_posix().encode()+b'\0'+p.read_bytes()+b'\0')
        for directory in ('scripts','.github','game/tests'):
            for p in sorted((frozen/directory).rglob('*')):
                if p.is_file() and not any(part in ('__pycache__','.godot') for part in p.parts) and p.suffix!='.pyc':validation.update(p.relative_to(frozen).as_posix().encode()+b'\0'+p.read_bytes()+b'\0')
        check(shipping.hexdigest()==before['source']['source_content_sha256']==pre['source_content_sha256'],'independent post-run shipping digest')
        check(validation.hexdigest()==before['source']['source_validation_sha256']==pre['source_validation_sha256'],'independent post-run validation digest')
        check(git(frozen,'rev-parse','HEAD:game').decode().strip()==before['source']['source_game_tree']==pre['source_game_tree'],'exact game tree after run')
        runner=(BUILDER/RELATIVE/'run_aggregate.py').read_bytes()
        check((run/'runner.py').read_bytes()==runner==git(BUILDER,'show',BUILDER_COMMIT+':'+RELATIVE+'/run_aggregate.py'),'executed retained wrapper exact committed bytes')
        check(command['runner_sha256']==supervisor['runner_sha256']==pre['wrapper']['run_aggregate.py']['sha256']==sha(runner),'all wrapper hash bindings agree')
        check(command['command']==['./scripts/validate.sh'] and command['cwd']==str(frozen),'actual unmodified full maintained argv/cwd without backend')
        check(command['timeout_seconds']==1200 and command['per_godot_timeout_seconds']==540,'original whole/stage bounds')
        check(command['pid']==command['pgid']==command['sid'],'actual child new session/group identity')
        check(all(result.get(k)==v for k,v in command.items()),'every launch field retained unchanged in result')
        env=command['environment']
        check(env['DISPLAY'] is None and env['SIGHTBREAK_TEST_TIMEOUT'] is None,'no DISPLAY or stage-timeout override')
        check(env['GODOT_BIN']==engine['path']=='/workspace/tools/godot-4.7.2/Godot_v4.7.2-stable_linux.x86_64' and env['SIGHTBREAK_TOOLS_DIR']=='/workspace/tools','actual fixed engine/tools selector')
        check(env['SIGHTBREAK_STATE_DIR']==str(frozen/'.local/aggregate-state-r1') and env['SIGHTBREAK_BACKEND_PYTHON']=='/workspace/sightbreak/.venv/bin/python','actual private state and required catalog interpreter')
        check(env['DATABASE_URL']=='postgresql+psycopg://fixture:fixture@127.0.0.1:1/fixture','explicit unavailable fixture-only SQL selector')
        check(engine['sha256']==pre['engine']['sha256']==sha(Path(engine['path']).read_bytes()),'actual engine still pinned after run')
        check(engine['archive_sha512']==pre['engine']['archive_sha512'] and hashlib.sha512(Path(engine['archive']).read_bytes()).hexdigest()==engine['archive_sha512'],'actual toolchain archive unchanged')
        check(engine['backend_python']==pre['backend']['path'] and engine['backend_sha256']==pre['backend']['sha256']==sha(Path(engine['backend_python']).read_bytes()),'catalog interpreter bytes unchanged')
        check(result['passed'] is True and result['exit_code']==0 and result['failure'] is None and result['source_unchanged'] is True and result['log_failures']==[] and result['forced_cleanup'] is False,'actual successful terminal receipt without forced cleanup or suppressed failure')
        check(result['whole_budget_met'] is True and 0<result['seconds']<1200,'finite declared terminal duration inside original budget')
        started,completed=dt.datetime.fromisoformat(result['started_utc']),dt.datetime.fromisoformat(result['completed_utc'])
        check(started<completed and abs((completed-started).total_seconds()-result['seconds'])<1,'ordered UTC and monotonic window agree within receipt granularity')
        check(resources['processes']==resources['listeners']==[],'actual original preflight empty')
        check(cleanup['remaining']==cleanup['listeners']==[] and not any('signal' in row for row in cleanup['signal_and_reap_events']),'actual terminal owned identities/listeners empty without signals')
        check(PORTS<=set(cleanup['ports_checked']),'all eight fixed source ports included in terminal receipt')
        check(supervisor['subreaper'] is True and supervisor['pid']==independent['pid'] and supervisor['start_ticks']==independent['start_ticks'] and supervisor['pgid']==independent['pgid'] and supervisor['sid']==independent['sid'] and supervisor['argv_sha256']==independent['argv_sha256'],'actual outer self receipt matches independent live proc identity')
        expected_argv=['python3',str(BUILDER/RELATIVE/'run_aggregate.py'),str(frozen),SOURCE,str(run)]
        check(independent['argv']==expected_argv and independent['cwd']==str(frozen),'independent actual outer argv/cwd')
        check(supervisor['argv']==expected_argv[1:] and supervisor['cwd']==str(frozen),'supervisor actual sys.argv/cwd receipt agrees')
        check(started<dt.datetime.fromisoformat(independent['observed_utc'])<completed,'independent live observation falls inside actual child execution')
        check(bool(observed) and len({(r['pid'],r['start_ticks']) for r in observed})==len(observed),'nonempty unique retained observed child identities')
        raw=(run/'aggregate.log').read_text()
        log_dirs=re.findall(r'^Validation completed\. Logs: (.+)$',raw,re.M)
        smoke_dirs=re.findall(r'^NETWORK_LOG_DIR=(.+)$',raw,re.M)
        check(len(log_dirs)==len(smoke_dirs)==1,'unique original validation/ENet directory receipts')
        log_paths=list(Path(log_dirs[0]).rglob('*.log'))+list(Path(smoke_dirs[0]).glob('*.log'))
        ports=PORTS|set(cleanup['ports_checked'])|{int(p) for path in log_paths for p in re.findall(r'SIGHTBREAK_SERVER_READY port=(\d+)',path.read_text())}
        owned={(r['pid'],r['start_ticks']) for r in observed}|{(independent['pid'],independent['start_ticks'])}
        matching=[];session_members=[];reused=[]
        for path in Path('/proc').iterdir():
            if not path.name.isdigit():continue
            try:
                stat=(path/'stat').read_text();v=stat[stat.rindex(')')+2:].split();pid=int(path.name)
                row=dict(pid=pid,ppid=int(v[1]),pgid=int(v[2]),sid=int(v[3]),start_ticks=int(v[19]),state=v[0],comm=(path/'comm').read_text().strip())
                argv=(path/'cmdline').read_bytes();row['argv_sha256']=sha(argv)
                if row['sid'] in (command['sid'],independent['sid']) or row['pgid'] in (command['pgid'],independent['pgid']):session_members.append(row)
                if (pid,row['start_ticks']) in owned or pid==command['pid'] or row['comm'].lower().startswith('godot') and os.fsencode(str(frozen)) in argv:matching.append(row)
                elif pid in {p for p,t in owned}:reused.append(row)
            except (OSError,ValueError,IndexError):pass
        sockets=[]
        for family in ('tcp','tcp6','udp','udp6'):
            for line in Path('/proc/net',family).read_text().splitlines()[1:]:
                f=line.split();port=int(f[1].rsplit(':',1)[1],16)
                if port in ports and (family.startswith('udp') or f[3]=='0A'):sockets.append(dict(family=family,port=port,state=f[3],inode=f[9]))
        check(not matching and not session_members and not sockets,'independent live terminal sampled-identity/group/session/project/socket scan empty')
        report.update(before=before['source'],command=command,result=result,engine=engine,cleanup=cleanup,supervisor=supervisor,
                      independent_outer=independent,observed_identities=len(owned),checked_ports=sorted(ports),
                      matching_live_identities=matching,matching_live_groups_sessions=session_members,pid_reuses=reused,listeners=sockets,
                      observed_utc=dt.datetime.now(dt.timezone.utc).isoformat(),source_input_count=len(expected),
                      boundary='Terminal monotonic sample follows recorded cleanup/source/log/process receipt work and precedes result/console emission; outer tool exit and final archive are reviewed separately. No perpetual immutability or arbitrary unseen descendant claim.')
    except BaseException:
        report['failures'].append('Audit exception; original traceback retained')
        (out/'audit-exception.txt').write_text(traceback.format_exc())
    report['passed']=not report['failures']
    (out/'audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('passed','checks','failures')}))
    return int(not report['passed'])

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--frozen',type=Path,required=True);parser.add_argument('--run',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    raise SystemExit(main(parser.parse_args()))
