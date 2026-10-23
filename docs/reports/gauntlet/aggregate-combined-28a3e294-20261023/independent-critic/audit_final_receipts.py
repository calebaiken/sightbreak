#!/usr/bin/env python3
"""Independent final outer/origin/journal receipts; no native execution."""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import re

HERE=Path(__file__).resolve().parent
SOURCE='28a3e294c850482475b7ab74067c08538ae6310d'

def sha(data):return hashlib.sha256(data).hexdigest()

def identity(pid):
    path=Path('/proc',str(pid))
    try:
        raw=(path/'stat').read_text();v=raw[raw.rindex(')')+2:].split()
        return dict(pid=pid,start_ticks=int(v[19]),state=v[0],pgid=int(v[2]),sid=int(v[3]))
    except (OSError,ValueError,IndexError):return None

def main(args):
    run=args.run.resolve();out=args.output.resolve()
    if out.exists():raise RuntimeError('Preserve earlier final review; choose a fresh output')
    failures=[];checks=0
    def check(value,label):
        nonlocal checks
        checks+=1
        if not value:failures.append(label)
    read=lambda n:json.loads((run/n).read_text())
    result,launch,terminal,originals,observed=[read(n) for n in ['result.json','outer-launch.json','outer-terminal.json','outer-originals.json','observed-processes.json']]
    live=json.loads((HERE/'independent-outer-live.json').read_text())
    check(launch['source_commit']==SOURCE and launch['root_release']=='0e66bc78','actual outer launch names frozen source and prereleased root checkpoint')
    check(launch['tool_result']['session_id']==terminal['session_id']==live['tool_session_id']==41224,'all original outer session identities agree')
    check(terminal['tool_result']['exit_code']==0 and terminal['tool_result']['output']==launch['tool_result']['output']=='','root retained immediate original outer terminal fields report zero; streams redirected')
    started=dt.datetime.fromisoformat(result['started_utc']);completed=dt.datetime.fromisoformat(result['completed_utc'])
    outer_done=dt.datetime.strptime(terminal['observed_utc'],'%Y-%m-%d %H:%M:%S UTC').replace(tzinfo=dt.timezone.utc)
    check(outer_done>=completed>started,'outer terminal observation follows finite inner terminal receipt')
    expected=dict(passed=True,exit_code=0,failure=None,log_failures=[],seconds=result['seconds'],source_unchanged=True,remaining=0,listeners=0)
    check(json.loads((run/'outer-wrapper.stdout').read_text())==expected,'actual redirected outer stdout agrees with all inner completion fields')
    check((run/'outer-wrapper.stderr').read_bytes()==b'','actual outer stderr empty')
    check(len(originals['records'])==4,'four original root tool/stream artifacts bound before archive')
    for record in originals['records']:
        data=Path(record['origin']).read_bytes();retained=Path(record['retained']).read_bytes()
        check(data==retained and len(data)==record['bytes'] and sha(data)==record['sha256'],'original root artifact equals retained exact bytes: '+record['origin'])
    current=identity(live['pid'])
    check(current is None or current['start_ticks']!=live['start_ticks'],'actual observed original outer PID/start no longer alive')
    logdir=Path(re.findall(r'^Validation completed\. Logs: (.+)$',(run/'aggregate.log').read_text(),re.M)[0])
    raw=(logdir/'transaction-journal.log').read_text()
    streams=[json.loads(line.split(' ',1)[1]) for line in raw.splitlines() if line.startswith('COMPETING_PROCESS ')]
    children=[json.loads(line.split(' ',1)[1]) for stream in streams for part in stream for line in part.splitlines() if line.startswith('OWNER_BLOCKED ')]
    check(len(children)==1,'one original competing journal child marker')
    child_samples=[]
    for child in children:
        check(all(type(child[k]) is int and child[k]==22 for k in ('claim','clear','stage')) and child['unchanged'] is True,'actual child blocks all three writes with unchanged receipt')
        samples=[row for row in observed if row['pid']==child['pid']];child_samples+=samples
        check(len(samples)==1 and samples[0]['sid']==result['pid'] and samples[0]['comm'].lower().startswith('godot'),'printed journal child bound to observed native PID/start and original session')
        now=identity(child['pid'])
        check(now is None or bool(samples) and now['start_ticks']!=samples[0]['start_ticks'],'original journal child identity absent at final receipt check')
    report=dict(passed=not failures,checks=checks,failures=failures,observed_utc=dt.datetime.now(dt.timezone.utc).isoformat(),outer_launch=launch,outer_terminal=terminal,outer_originals=originals,outer_current_identity=current,journal_children=children,journal_child_observed_identities=child_samples,scope='Finite read-only original-byte/tool-field/journal child review. The root labels tool fields as immediate-response transcription; this critic independently observed the live outer identity. Poll-return wall time is not full runtime or an exact kernel exit clock. No signal or native work launched.')
    out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('passed','checks','failures')}))
    return int(bool(failures))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    raise SystemExit(main(parser.parse_args()))
