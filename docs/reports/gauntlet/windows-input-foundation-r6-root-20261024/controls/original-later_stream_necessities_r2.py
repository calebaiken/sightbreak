#!/usr/bin/env python3
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
from independent_models import Forward


def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    sys.path.insert(0,str(a.source.resolve()/'scripts'))
    import analyze_input_consumption as r
    from test_input_consumption_observation import declared_rows,text
    assert hashlib.sha256((a.source/'scripts/analyze_input_consumption.py').read_bytes()).hexdigest()=='104d998dc504e30fb6702426025b611aa5ee86390a1734f06142d92a3473e4d4'
    m=Forward(declared_rows('authority'));m.connect(10,11200);m.admit(10,2,11300);m.rpc(2,True,11400,0);m.rpc(1,True,11500,0,peer=10);m.tick(13000)
    # Finish the same authority tick: pop each bound peer in source insertion order.
    for peer in (9,10):
        seq=min(m.queue[peer]);command=m.queue[peer].pop(seq);m.ack[peer]=seq;e=m.entries[peer];m.actor[e[3]]['input']=deepcopy(command)
        m.hook('input_consumed',13000,peer,dict(command,peer=peer,actor=e[3],generation=e[0]))
    m.hook('input_gate_rejected',13100,9);m.tick(14500);m.tick(16000)
    assert (m.rows[-2]['peer'],m.rows[-2]['generation'],m.rows[-2]['authority_epoch'])==(9,1,1)
    assert m.rows[-2]['stream_ack']==m.rows[-1]['stream_ack']==2
    assert m.rows[-2]['queue_count']==m.rows[-1]['queue_count']==0
    assert m.rows[-2]['counters']=={**m.rows[-1]['counters'],'authority_tick':m.rows[-2]['counters']['authority_tick']}
    variants=[('source-positive','UNKNOWN',None,None),('ack-cleared','INVALID','stream_ack',-1),('ack-regressed','INVALID','stream_ack',1),('queue-grown','INVALID','queue_count',1),('frame-sanity','INVALID','process_frames',1)]
    outcomes=[]
    for name,expected,key,value in variants:
        rows=deepcopy(m.rows)
        if key:rows[-1][key]=value
        for row in rows:r.record_valid(row)
        before=deepcopy(rows);result=r.analyze(text(declared_rows('client')),text(rows));assert rows==before
        dest=a.output/name;dest.mkdir();(dest/'authority.json').write_text(json.dumps(rows,indent=2)+'\n');(dest/'authority.txt').write_text(text(rows));(dest/'client.txt').write_text(text(declared_rows('client')));(dest/'RESULT.json').write_text(json.dumps(dict(name=name,expected=expected,actual=result['transition_status'],matched=result['transition_status']==expected,result=result),indent=2)+'\n');outcomes.append(dict(name=name,expected=expected,actual=result['transition_status'],matched=result['transition_status']==expected))
    (a.output/'TRACE.json').write_text(json.dumps(m.trace,indent=2)+'\n');summary=dict(outcomes=outcomes,matches=sum(x['matched'] for x in outcomes),count=len(outcomes));(a.output/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2));return not all(x['matched'] for x in outcomes)


if __name__=='__main__':raise SystemExit(main())
