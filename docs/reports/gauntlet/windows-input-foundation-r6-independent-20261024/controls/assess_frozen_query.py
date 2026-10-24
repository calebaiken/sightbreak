#!/usr/bin/env python3
import argparse,hashlib,json,sys
from copy import deepcopy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from models_r2 import Complete,mixed,SHA

def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    sys.path.insert(0,str(a.source.resolve()/'scripts'));import analyze_input_consumption as r
    from test_input_consumption_observation import declared_rows,text
    assert hashlib.sha256((a.source/'scripts/analyze_input_consumption.py').read_bytes()).hexdigest()==SHA
    home=Path(__file__).resolve().parents[1];folder=home/'frozen-additional-query/query-local-pop-r1';seed=declared_rows('authority')
    other=mixed(seed);other.rpc(2,True,16200,0,peer=10);other.finish(18000);other.select(9,18100);other.finish(19500)
    same=mixed(seed);same.rpc(3,True,16200,0);same.finish(18000);same.finish(19500)
    keys=['reason','index','wall_msec','wall_unix_msec','peer','generation','joined','bound_actor','peer_bound','last_bound_actor','input_age_msec','deadline_remaining_msec','authority_epoch','simulation_tick','stream_ack','queue_count','stream_skipped','stream_rejected','counters','latest']
    outcomes=[];proofs=[]
    for name,m,owner in [('sole-other-pop',other,10),('same-pop-replayed-ack',same,9)]:
        original=json.loads((folder/(name+'-positive.json')).read_text());bad=json.loads((folder/(name+'-contradiction.json')).read_text());assert len(m.rows)==len(original['authority'])
        for n,(mine,provided) in enumerate(zip(m.rows,original['authority']),1):
            for key in keys:assert mine[key]==provided[key],(name,n,key,mine[key],provided[key])
            assert mine['actor'].get('input')==provided['actor'].get('input'),(name,n,'actor.input')
        previous=next(x for x in reversed(original['authority'][:-1]) if x['peer']==9);last=original['authority'][-1];assert (previous['peer'],previous['generation'],previous['authority_epoch'])==(last['peer'],last['generation'],last['authority_epoch'])==(9,1,1)
        progress=last['counters']['input_consumed']-previous['counters']['input_consumed'];assert progress==1 and last['latest']['input_consumed']['peer']==owner
        expected_bad=deepcopy(original['authority'])
        if owner==10:assert last['stream_ack']==previous['stream_ack']==2;expected_bad[-1]['stream_ack']=3
        else:assert previous['stream_ack']==2 and last['stream_ack']==3;expected_bad[-1]['stream_ack']=expected_bad[-1]['latest']['input_consumed']['sequence']=2
        assert bad['authority']==expected_bad
        proofs.append(dict(name=name,selected_previous=previous,selected_current=last,global_consumed_progress=progress,new_latest_owner=owner,compared_projection_keys=keys,forward_trace=m.trace))
        for label,data,expected in [('positive',original,'UNKNOWN'),('contradiction',bad,'INVALID')]:
            rows=data['authority'];client=data['client'];before=deepcopy(rows)
            for row in rows:r.record_valid(row)
            result=r.analyze(text(client),text(rows));assert rows==before;item=dict(name=name+'/'+label,expected=expected,actual=result['transition_status'],matched=result['transition_status']==expected,result=result,authority=rows,client=client);(a.output/(name+'-'+label+'.json')).write_text(json.dumps(item,indent=2)+'\n');outcomes.append({k:item[k] for k in ['name','expected','actual','matched']})
    (a.output/'INDEPENDENT_PROJECTION_PROOF.json').write_text(json.dumps(proofs,indent=2)+'\n');summary=dict(count=len(outcomes),matches=sum(x['matched'] for x in outcomes),outcomes=outcomes);(a.output/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2));return not all(x['matched'] for x in outcomes)

if __name__=='__main__':raise SystemExit(main())
