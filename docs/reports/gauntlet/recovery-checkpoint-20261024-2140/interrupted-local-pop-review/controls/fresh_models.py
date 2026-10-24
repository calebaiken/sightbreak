#!/usr/bin/env python3
import argparse,ast,hashlib,itertools,json,sys,types
from copy import deepcopy
from pathlib import Path
HOME=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HOME.parent/'windows-input-foundation-r6-independent-20261024/controls'))
from models_r2 import Complete,mixed,Keys
SHA='b381fb2da957102debd7247b15be244e4a76023ede7c72c9fdc690d03152f30d'

def batch(m,peer,sequences,now):
    assert 1<=len(sequences)<=12 and all(m.ack.get(peer,0)<x<=m.ack.get(peer,0)+120 for x in sequences)
    value=dict(epoch=m.epoch,count=len(sequences),first=sequences[0],last=sequences[-1],fire=len(sequences),reload=0,moving=0)
    m.hook('input_received',now,peer,value)
    for x in sequences:m.queue[peer].setdefault(x,m.command(x,True))
    m.entries[peer][2]=now;m.hook('input_accepted',now,peer,value)

def fill(m,peer,start,count,now):
    for offset in range(0,count,12):batch(m,peer,list(range(start+offset,min(start+count,start+offset+12))),now+offset//12*20)

def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    sys.path.insert(0,str(a.source.resolve()/'scripts'));import analyze_input_consumption as r
    from test_input_consumption_observation import declared_rows,text
    source=(a.source/'scripts/analyze_input_consumption.py').read_text();assert hashlib.sha256(source.encode()).hexdigest()==SHA
    oldraw=(HOME/'frozen-baseline/analyze_input_consumption.py').read_bytes();assert hashlib.sha256(oldraw).hexdigest()=='fab0711b9f239654a31cac745d4778eed8691d617eccea39c7fccabc6593fdf0';old=types.ModuleType('held_6ef');old.__file__=str(HOME/'frozen-baseline/analyze_input_consumption.py');exec(compile(oldraw,old.__file__,'exec'),old.__dict__)
    cases=[];failures=[];comparisons=[]
    def record(name,expected,actual,inputs,result=None):
        item=dict(name=name,expected=expected,actual=actual,matched=actual in expected,inputs=inputs,result=result);cases.append(item)
        if not item['matched']:failures.append(item)
    def interval(name,before,after,expected):
        v=r.StreamObservationIntervals();actual='POSSIBLE';error=None
        try:v.observe(deepcopy(before),{(9,1),(10,2)});v.observe(deepcopy(after),{(9,1),(10,2)})
        except ValueError as e:actual='INVALID';error=str(e)
        record(name,[expected],actual,[before,after],error)
    for ack,n,length in itertools.product((0,10),(0,1,6,7,12,120),range(4)):
        for word in itertools.product('DXOT',repeat=length):
            m=Keys(ack,n);before=m.row();legal=True
            for op in word:
                peer=9 if op in 'DO' else 10
                if op in 'OT':
                    if not m.q[peer]:legal=False;break
                    m.pop(peer)
                else:
                    key=min(m.q[peer]) if m.q[peer] else m.ack[peer]+1;m.accept(peer,[key])
            if not legal:continue
            after=m.row();name='component/%d/%d/%s'%(ack,n,''.join(word));interval(name,before,after,'POSSIBLE')
            if not word:
                bad=deepcopy(after);bad['stream_ack']=max(0,after['stream_ack'])+1;interval(name+'/no-write-ACK',before,bad,'INVALID')
                if n<120:bad=deepcopy(after);bad['queue_count']+=1;interval(name+'/no-write-growth',before,bad,'INVALID')
                if n:bad=deepcopy(after);bad['queue_count']-=1;interval(name+'/no-write-loss',before,bad,'INVALID')
            if ack and after['counters']['input_consumed']>before['counters']['input_consumed'] and after['latest']['input_consumed']['peer']==9:
                bad=deepcopy(after);bad['stream_ack']=bad['latest']['input_consumed']['sequence']=ack;interval(name+'/guaranteed-local-strict',before,bad,'INVALID')
    seed=declared_rows('authority');client=text(declared_rows('client'))
    def whole(name,m,expected=('UNKNOWN',),rows=None):
        rows=m.rows if rows is None else rows
        for x in rows:r.record_valid(x)
        untouched=deepcopy(rows);result=r.analyze(client,text(rows));assert rows==untouched;record(name,list(expected),result['transition_status'],rows,result);return result
    other=mixed(seed);other.rpc(2,True,16200,0,peer=10);other.finish(18000);other.select(9,18100);other.finish(19500)
    same=mixed(seed);same.rpc(3,True,16200,0);same.finish(18000);same.finish(19500)
    one=mixed(seed);fill(one,9,3,7,16200);one.finish(18000);one.finish(19500)
    two=mixed(seed);fill(two,9,3,7,16200);fill(two,10,2,1,16300);two.select(9,17900);two.finish(18000);two.select(9,18100);two.finish(19500)
    huge=mixed(seed);fill(huge,9,3,120,16200);fill(huge,10,2,120,16600);huge.select(9,17900);huge.finish(18000);huge.select(9,18100);huge.finish(19500)
    other_skip=mixed(seed);fill(other_skip,10,2,120,16200);other_skip.select(9,17900);other_skip.finish(18000);other_skip.select(9,18100);other_skip.finish(19500)
    assert one.rows[-1]['stream_skipped']==5 and one.rows[-1]['queue_count']==1 and one.rows[-1]['stream_ack']==8
    assert two.rows[-1]['stream_skipped']==5 and two.rows[-1]['queue_count']==1
    assert huge.rows[-1]['stream_skipped']==236 and huge.rows[-1]['queue_count']==1
    triggers={}
    bad=deepcopy(other.rows);bad[-1]['stream_ack']=3;triggers['other-owner-exclusion']=(other,bad)
    bad=deepcopy(same.rows);bad[-1]['stream_ack']=bad[-1]['latest']['input_consumed']['sequence']=2;triggers['local-floor']=(same,bad);triggers['rank']=(same,deepcopy(bad))
    bad=deepcopy(one.rows);bad[-1]['queue_count']=2;triggers['skipped-min']=(one,bad)
    bad=deepcopy(huge.rows);bad[-1]['queue_count']=0;triggers['skipped-max']=(huge,bad)
    bad=deepcopy(two.rows);bad[-1]['queue_count']=0;triggers['queue-lower']=(two,bad)
    bad=deepcopy(same.rows);bad[-1]['queue_count']=1;triggers['queue-upper']=(same,bad)
    for name,m in [('other',other),('same',same),('one-skip',one),('two-skips',two),('huge',huge),('other-skip',other_skip)]:whole('complete/'+name,m)
    rankbad=deepcopy(one.rows);rankbad[-1]['stream_ack']=rankbad[-1]['latest']['input_consumed']['sequence']=7;triggers['rank']=(one,deepcopy(rankbad));whole('complete/skipped-rank',one,('INVALID',),rankbad)
    for seq,phase in itertools.product((3,12,62,122),(0,1)):
        m=mixed(seed);m.rpc(seq,True,16200,phase);m.finish(18000);m.finish(19500);whole('complete/gap/%d/%d'%(seq,phase),m)
    epoch=deepcopy(huge);epoch.epoch+=1;epoch.ack.clear();epoch.queue={p:{} for p in epoch.entries};epoch.finish(21000);whole('complete/retained-skips-epoch-reset',epoch)
    replacement=deepcopy(huge);replacement.disconnect(9,19600);replacement.disconnect(10,19700);replacement.epoch+=2;replacement.ack.clear();replacement.queue.clear();replacement.skips=replacement.rejections=0;replacement.finish(21000);replacement.connect(9,21100);replacement.admit(9,3,21200);replacement.rpc(1,False,21300,0);replacement.finish(22500);replacement.finish(24000);whole('complete/replacement-new-generation',replacement)
    pending=mixed(seed);pending.rpc(3,False,16200,0);pending.hook('input_received',16300,9,dict(epoch=1,count=1,first=4,last=4,fire=1,reload=0,moving=0));whole('complete/pending-RX',pending)
    duplicate=mixed(seed);duplicate.rpc(3,False,16200,0);duplicate.rpc(3,True,16300,1);duplicate.finish(18000);duplicate.finish(19500);whole('complete/queued-duplicate',duplicate)
    for name,(m,bad) in triggers.items():
        new=whole('trigger/'+name,m,('INVALID',),bad);baseline=old.analyze(client,text(bad));comparisons.append(dict(name=name,baseline=baseline,repair=new,baseline_status=baseline['transition_status'],repair_status=new['transition_status']))
    mutants=[]
    for name,(m,bad) in triggers.items():
        tree=ast.parse(source);cls=next(x for x in tree.body if isinstance(x,ast.ClassDef) and x.name=='StreamObservationIntervals')
        class Change(ast.NodeTransformer):
            def visit_Assign(self,n):
                if len(n.targets)==1 and isinstance(n.targets[0],ast.Name):
                    target=n.targets[0].id
                    if name=='other-owner-exclusion' and target=='local_max':n.value=ast.Name(id='consumed',ctx=ast.Load())
                    if name=='local-floor' and target=='local_min':n.value=ast.Constant(0)
                    if name=='skipped-min' and target=='skipped_min':n.value=ast.Constant(0)
                    if name=='skipped-max' and target=='skipped_max':n.value=ast.Name(id='skipped',ctx=ast.Load())
                return self.generic_visit(n)
            def visit_Expr(self,n):
                if isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='need' and len(n.value.args)>1 and isinstance(n.value.args[1],ast.Constant):
                    message=n.value.args[1].value
                    if name=='rank' and message=='nonnull local pops did not advance stream ACK by consumed/skipped ranks':return ast.Pass()
                    if message=='queue cardinality has no accepted/pop/skipped transition':
                        compare=n.value.args[0]
                        if name=='queue-lower':compare.left=ast.parse("max(0, previous['queue_count'] - consumed - skipped)",mode='eval').body
                        if name=='queue-upper':compare.comparators[-1]=ast.parse("min(120, previous['queue_count'] + 12 * accepted)",mode='eval').body
                return self.generic_visit(n)
        Change().visit(cls);mutant=ast.unparse(ast.fix_missing_locations(tree))+'\n';(a.output/('mutant-'+name+'.py')).write_text(mutant);mod=types.ModuleType('mutant_'+name);mod.__file__=str(a.source/'scripts/analyze_input_consumption.py');exec(compile(mutant,name,'exec'),mod.__dict__);result=mod.analyze(client,text(bad));mutants.append(dict(name=name,killed=result['transition_status']!='INVALID',result=result,sha256=hashlib.sha256(mutant.encode()).hexdigest()))
    (a.output/'CASES.json').write_text(json.dumps(cases,indent=2)+'\n');(a.output/'BASELINE_COMPARISON.json').write_text(json.dumps(comparisons,indent=2)+'\n');summary=dict(expectations=len(cases),matches=len(cases)-len(failures),failures=failures,mutants=mutants,meaningful_kills=sum(x['killed'] for x in mutants),baseline_changes=[dict(name=x['name'],baseline=x['baseline_status'],repair=x['repair_status']) for x in comparisons]);(a.output/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({k:v for k,v in summary.items() if k not in ('failures','mutants')},indent=2));return bool(failures) or not all(x['killed'] for x in mutants)

if __name__=='__main__':raise SystemExit(main())
