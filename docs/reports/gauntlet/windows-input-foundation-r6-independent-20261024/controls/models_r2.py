#!/usr/bin/env python3
import argparse,ast,hashlib,json,sys,types
from copy import deepcopy
from pathlib import Path
import itertools

HOME=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HOME.parent/'windows-input-foundation-r5-independent-20261024/controls'))
from independent_models import Forward
SHA='fab0711b9f239654a31cac745d4778eed8691d617eccea39c7fccabc6593fdf0'

class Complete(Forward):
    def finish(self,now):
        self.tick(now)
        for peer,e in self.entries.items():
            q=self.queue[peer]
            if not e[3] or not q:continue
            if len(q)>6:
                for key in sorted(q)[:-2]:del q[key];self.skips+=1
            seq=min(q);command=q.pop(seq);self.ack[peer]=seq;self.actor[e[3]]['input']=deepcopy(command)
            self.hook('input_consumed',now,peer,dict(command,peer=peer,actor=e[3],generation=e[0]))
    def select(self,peer,now):self.hook('input_gate_rejected',now,peer)

def mixed(seed,seq=2,phase=0,switch=False):
    m=Complete(seed);m.connect(10,11200);m.admit(10,2,11300);m.rpc(seq,True,11400,phase);m.rpc(1,True,11500,phase,peer=10);m.finish(13000);m.select(9,13100);m.finish(14500)
    if switch:m.select(10,14600);m.finish(16000);m.select(9,16100);m.finish(17500)
    else:m.finish(16000)
    return m

class Keys:
    """Source stream transitions; no reader formula or invented local ownership."""
    def __init__(self,ack,amount):
        self.ack={9:0,10:0};self.q={9:{},10:{}};self.a=self.c=self.k=0;self.latest={};self.epoch=1;self.generation=1
        if ack:self.accept(9,[ack]);self.pop(9)
        for start in range(ack+1,ack+amount+1,12):self.accept(9,list(range(start,min(ack+amount+1,start+12))))
        self.accept(10,list(range(1,8)))
    def accept(self,peer,keys):
        assert 1<=len(keys)<=12 and all(1<=x<=self.ack[peer]+120 for x in keys)
        fresh=[x for x in keys if x>self.ack[peer]];assert fresh
        self.a+=1
        for x in fresh:self.q[peer].setdefault(x,True)
    def pop(self,peer):
        q=self.q[peer];assert q
        if len(q)>6:
            for x in sorted(q)[:-2]:del q[x];self.k+=1
        seq=min(q);del q[seq];self.ack[peer]=seq;self.c+=1;self.latest={'input_consumed':dict(peer=peer,generation=1 if peer==9 else 2,sequence=seq)}
    def row(self,reason='authority_tick'):
        return dict(role='authority',reason=reason,peer=9,generation=self.generation,authority_epoch=self.epoch,
                    stream_ack=self.ack[9] if self.ack[9] else -1,queue_count=len(self.q[9]),stream_skipped=self.k,
                    counters={'input_accepted':self.a,'input_consumed':self.c},latest=deepcopy(self.latest))

def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    sys.path.insert(0,str(a.source.resolve()/'scripts'));import analyze_input_consumption as r
    from test_input_consumption_observation import declared_rows,text
    source=(a.source/'scripts/analyze_input_consumption.py').read_text();assert hashlib.sha256(source.encode()).hexdigest()==SHA
    seed=declared_rows('authority');client=text(declared_rows('client'));outcomes=[];failures=[]
    def record(name,expected,actual,inputs,result=None):
        match=actual in expected;item=dict(name=name,expected=expected,actual=actual,matched=match,inputs=inputs,result=result);outcomes.append(item)
        if not match:failures.append(item)
    def interval(name,before,after,expected):
        v=r.StreamObservationIntervals();actual='POSSIBLE';error=None
        try:v.observe(deepcopy(before),{(9,1),(10,2),(9,3)});v.observe(deepcopy(after),{(9,1),(10,2),(9,3)})
        except ValueError as e:actual='INVALID';error=str(e)
        record(name,[expected],actual,[before,after],error)
    for ack,n,op in itertools.product((0,10),(0,1,6,7,12,120),('none','duplicate','other-accept','own-pop','other-pop','batch12','epoch','disconnect-generation')):
        m=Keys(ack,n);before=m.row()
        if op=='duplicate':
            if not n:continue
            m.accept(9,[min(m.q[9])])
        elif op=='other-accept':m.accept(10,[1])
        elif op=='own-pop':
            if not n:continue
            m.pop(9)
        elif op=='other-pop':m.pop(10)
        elif op=='batch12':
            if n>108:continue
            m.accept(9,list(range(ack+n+1,ack+n+13)))
        elif op=='epoch':m.epoch+=1;m.ack={9:0,10:0};m.q={9:{},10:{}}
        elif op=='disconnect-generation':
            v=r.StreamObservationIntervals();v.observe(deepcopy(before),{(9,1),(10,2)});end=deepcopy(before);end['reason']='peer_disconnected';v.observe(end,{(9,1),(10,2)});m.generation=3;m.ack[9]=0;m.q[9]={}
        after=m.row();name='component/%d/%d/%s'%(ack,n,op);interval(name,before,after,'POSSIBLE')
        if op=='none':
            bad=deepcopy(after);bad['stream_ack']=1 if after['stream_ack']==-1 else after['stream_ack']+1;interval(name+'/no-C-ACK',before,bad,'INVALID')
            if n<120:bad=deepcopy(after);bad['queue_count']+=1;interval(name+'/no-call-growth',before,bad,'INVALID')
            if n:bad=deepcopy(after);bad['queue_count']-=1;interval(name+'/no-call-loss',before,bad,'INVALID')
        if op=='own-pop':
            bad=deepcopy(after);bad['stream_ack']+=1;interval(name+'/latest-pop',before,bad,'INVALID')
            if after['queue_count']:bad=deepcopy(after);bad['queue_count']-=1;interval(name+'/removal-lower',before,bad,'INVALID')
        if op=='batch12' and after['queue_count']<120:
            bad=deepcopy(after);bad['queue_count']+=1;interval(name+'/addition-upper',before,bad,'INVALID')
        if op=='other-pop' and ack:
            bad=deepcopy(after);bad['stream_ack']-=1;interval(name+'/other-owner-ACK-regress',before,bad,'INVALID')
    def whole(name,m,expected=('UNKNOWN',),rows=None,module=r):
        rows=m.rows if rows is None else rows
        for x in rows:r.record_valid(x)
        original=deepcopy(rows);result=module.analyze(client,text(rows));assert rows==original
        record(name,list(expected),result['transition_status'],rows,result)
        return result
    for seq,phase,switch in itertools.product((2,3,61,121),(0,1),(False,True)):
        m=mixed(seed,seq,phase,switch);name='complete/%d/%d/%s'%(seq,phase,switch);whole(name,m)
        for field,value in [('stream_ack',-1),('stream_ack',seq-1),('stream_ack',seq+1),('queue_count',1)]:
            bad=deepcopy(m.rows);bad[-1][field]=value;whole(name+'/'+field+'/'+str(value),m,('INVALID',),bad)
    baseline=mixed(seed);whole('complete/epoch-before',baseline)
    epoch=deepcopy(baseline);epoch.epoch+=1;epoch.ack.clear();epoch.queue={p:{} for p in epoch.entries};epoch.finish(18000);whole('complete/bound-epoch-reset',epoch)
    dup=deepcopy(baseline);dup.rpc(3,False,16200,0);dup.rpc(3,True,16300,1);dup.finish(18000);dup.finish(19500);whole('complete/queued-duplicate-immutable',dup)
    pending=deepcopy(baseline);pending.rpc(3,False,16200,0);pending.hook('input_received',16300,9,dict(epoch=1,count=1,first=4,last=4,fire=1,reload=0,moving=0));whole('complete/pending-RX-cut',pending)
    lower=deepcopy(pending.rows);lower[-1]['queue_count']=0;whole('complete/pending-RX-lower',pending,('INVALID',),lower)
    replacement=deepcopy(baseline);replacement.disconnect(9,16200);replacement.disconnect(10,16300);replacement.epoch+=2;replacement.ack.clear();replacement.queue.clear();replacement.rejections=replacement.skips=0;replacement.finish(18000);replacement.connect(9,18100);replacement.admit(9,3,18200);replacement.rpc(1,False,18300,0);replacement.finish(20000);replacement.finish(21500);whole('complete/replacement-new-generation',replacement)
    mono=deepcopy(baseline);mono.rpc(2,True,16200,0,peer=10);mono.finish(18000);mono.select(9,18100);mono.finish(19500);badmono=deepcopy(mono.rows);badmono[-1]['stream_ack']=1
    latest=deepcopy(baseline);latest.rpc(3,True,16200,0);latest.finish(18000);latest.finish(19500);badlatest=deepcopy(latest.rows);badlatest[-1]['stream_ack']=4
    badnoc=deepcopy(baseline.rows);badnoc[-1]['stream_ack']=3;badgrowth=deepcopy(baseline.rows);badgrowth[-1]['queue_count']=1
    cases={'integration':(baseline,badgrowth),'monotonic':(mono,badmono),'zero-C':(baseline,badnoc),'latest':(latest,badlatest),'queue':(pending,lower)}
    messages={'monotonic':'stream ACK regressed/cleared without reset','zero-C':'stream ACK changed without a consumed call','latest':'stream ACK differs from its latest immutable pop','queue':'queue cardinality has no accepted/pop/skipped transition'}
    mutations=[]
    for name,(m,bad) in cases.items():
        whole('mutation-baseline/'+name,m,('INVALID',),bad)
        tree=ast.parse(source)
        if name=='integration':
            class RemoveCall(ast.NodeTransformer):
                def visit_Expr(self,n):
                    if isinstance(n.value,ast.Call) and ast.unparse(n.value.func)=='stream_intervals.observe':return ast.Pass()
                    return self.generic_visit(n)
            tree=RemoveCall().visit(tree)
        else:
            cls=next(x for x in tree.body if isinstance(x,ast.ClassDef) and x.name=='StreamObservationIntervals')
            class RemoveGate(ast.NodeTransformer):
                def visit_Expr(self,n):
                    if isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='need' and len(n.value.args)>1 and isinstance(n.value.args[1],ast.Constant) and n.value.args[1].value==messages[name]:return ast.Pass()
                    return self.generic_visit(n)
            RemoveGate().visit(cls)
        mutant=ast.unparse(ast.fix_missing_locations(tree))+'\n';(a.output/('mutant-'+name+'.py')).write_text(mutant);module=types.ModuleType('mutant_'+name);module.__file__=str(a.source/'scripts/analyze_input_consumption.py');exec(compile(mutant,name,'exec'),module.__dict__);actual=module.analyze(client,text(bad));killed=actual['transition_status']!='INVALID';mutations.append(dict(name=name,killed=killed,result=actual,sha256=hashlib.sha256(mutant.encode()).hexdigest()))
    (a.output/'CASES.json').write_text(json.dumps(outcomes,indent=2)+'\n');summary=dict(expectations=len(outcomes),matches=len(outcomes)-len(failures),failures=failures,mutations=mutations,meaningful_kills=sum(x['killed'] for x in mutations));(a.output/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(dict(expectations=summary['expectations'],matches=summary['matches'],meaningful_kills=summary['meaningful_kills'])))
    return bool(failures) or not all(x['killed'] for x in mutations)

if __name__=='__main__':raise SystemExit(main())
