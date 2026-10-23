#!/usr/bin/env python3
"""Finite timeline/socket/group joins and later absence, with observation gaps."""
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import time

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('independent_actual_helpers',HERE/'verify_actual.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def main():
    started=time.monotonic();audit.check(sorted(os.sched_getaffinity(0)) == [4],'live-boundary replay CPU4')
    rows=[json.loads(x) for x in (HERE/'live-observer.jsonl').read_text().splitlines()]
    overall=audit.read_json(audit.RAW/'overall.json'); block=audit.read_json(audit.RAW/'native-block/block.json')
    ready=audit.read_json(audit.RAW/'native-block/xvfb-readiness.json'); first=block['records'][0]
    seen={}
    for row in rows:
        for item in row.get('observed',[]): seen.setdefault((item['pid'],item['start_ticks']),[]).append(item)
    covered=[];missed=[]
    for n,c in enumerate(overall['commands'],1):
        key=(c['pid'],c['root_identity']['start_ticks']);samples=seen.get(key,[])
        out={'number':n,'label':c['label'],'pid':key[0],'start_ticks':key[1],'recorded_elapsed_seconds':c['elapsed_seconds'],'live_samples':len(samples),'detail_read_errors':sum('read_error' in r for r in samples)}
        (covered if samples else missed).append(out)
    audit.check(all(c['label'] in ('git','version') for c in missed),'only short Git/version commands missed live')
    ownership=ready['ownership'];owned=set(ownership['owned_kernel_socket_inodes'])
    xvfb_seen=seen[(ownership['pid'],ownership['start_ticks'])]
    audit.check(any(owned <= {fd['inode'] for fd in r.get('sockets',[])} and r.get('identity_revalidated') is True for r in xvfb_seen),'independent Xvfb FD joins original owned display socket inodes')
    joined=[r for r in rows if any(x.get('pid')==ownership['pid'] and x.get('start_ticks')==ownership['start_ticks'] for x in r.get('observed',[])) and any('X99127' in line and any(inode in line.split() for inode in owned) for line in r.get('listeners',{}).get('unix_display_or_owned',[]))]
    audit.check(bool(joined),'independent owned kernel socket joins fixed display publication')
    baseline=rows[0]['preexisting_listeners'];terminal=next(r for r in rows if r['event']=='terminal')
    audit.check(all(terminal['listeners'][key] == baseline[key] for key in baseline),'terminal listeners and fixed display match pre-acquisition baseline')
    current=audit.proc_snapshot();owned_roots=[c['root_identity'] for c in overall['commands']]
    owned_roots.extend([{'pid':first['pid'],'start_ticks':first['pid_start_ticks'],'pgid':first['pid'],'sid':first['pid']}, {'pid':ownership['pid'],'start_ticks':ownership['start_ticks'],'pgid':ownership['pid'],'sid':ownership['pid']}, {'pid':168507,'start_ticks':2861205,'pgid':168505,'sid':168505}])
    for root in owned_roots:
        audit.check(not any((r['pid']==root['pid'] and r['start_ticks']==root['start_ticks']) or r['pgid']==root['pgid'] or r['sid']==root['sid'] for r in current.values()),'later exact identity and original group/session absent '+str(root['pid']))
    for r in terminal['observed']:audit.check(False,'terminal observed identity remains '+str(r['pid']))
    result={'passed':True,'checks':audit.checks,'covered_command_roots':covered,'missed_command_roots':missed,'observed_exact_identities':len(seen),'xvfb_ownership':ownership,'independent_socket_join_samples':len(joined),'later_roots_checked':owned_roots,'scope':'Finite original timeline, explicit observed identity and group/session socket joins, and later absence only. Short process/detail races and arbitrary between-poll escaped/reparented descendants remain unobserved; no complete-descendant guarantee.','started_monotonic':started,'ended_monotonic':time.monotonic(),'utc':datetime.now(timezone.utc).isoformat()}
    (HERE/'live-boundaries-readback.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passed':True,'checks':len(audit.checks),'covered':len(covered),'missed':missed,'display_join_samples':len(joined)}))


if __name__ == '__main__':main()
