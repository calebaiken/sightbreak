"""Builder-discovered necessary facts; complete callback witnesses only."""
import argparse
from copy import deepcopy
import hashlib,json,sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args();args.output.mkdir(parents=True,exist_ok=False)
sys.path.insert(0,str(args.source/'scripts'))
import analyze_input_consumption as r
from test_input_consumption_intervals import uncertain_history
from test_input_consumption_observation import declared_rows,text
assert hashlib.sha256((args.source/'scripts/analyze_input_consumption.py').read_bytes()).hexdigest()=='fab0711b9f239654a31cac745d4778eed8691d617eccea39c7fccabc6593fdf0'
models=[]
other=uncertain_history();other.rpc(10,2,16200,16200);other.complete_tick(18000);other.select(9,18100);other.complete_tick(19500)
assert other.rows[-1]['stream_ack']==2 and other.rows[-1]['latest']['input_consumed']['peer']==10
before=next(row for row in reversed(other.rows[:-1]) if row['peer']==9)
assert other.rows[-1]['counters']['input_consumed']-before['counters']['input_consumed']==1
bad=deepcopy(other.rows);bad[-1]['stream_ack']=3
models.append(('sole-other-pop',other,bad))
same=uncertain_history();same.rpc(9,3,16200,16200);same.complete_tick(18000);same.complete_tick(19500)
assert same.rows[-1]['stream_ack']==same.rows[-1]['latest']['input_consumed']['sequence']==3
bad=deepcopy(same.rows);bad[-1]['stream_ack']=bad[-1]['latest']['input_consumed']['sequence']=2
models.append(('same-pop-replayed-ack',same,bad))
outcomes=[]
for name,model,bad in models:
    for label,rows,expected in [('positive',model.rows,'UNKNOWN'),('contradiction',bad,'INVALID')]:
        for row in rows:r.record_valid(row)
        original=deepcopy(rows);result=r.analyze(text(declared_rows('client')),text(rows));assert rows==original
        item=dict(name=name+'/'+label,expected=expected,actual=result['transition_status'],matched=result['transition_status']==expected,result=result,authority=rows,client=declared_rows('client'),operations=model.operations)
        (args.output/(name+'-'+label+'.json')).write_text(json.dumps(item,indent=2)+'\n');outcomes.append({k:item[k] for k in ('name','expected','actual','matched')})
summary=dict(outcomes=outcomes,matches=sum(x['matched'] for x in outcomes),count=len(outcomes),scope='builder query, requires independent assessment')
(args.output/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2));raise SystemExit(not all(x['matched'] for x in outcomes))
