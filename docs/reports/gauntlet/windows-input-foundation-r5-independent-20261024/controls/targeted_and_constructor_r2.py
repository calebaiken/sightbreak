#!/usr/bin/env python3
import argparse
import ast
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import types
import unittest
from independent_models import Forward


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def leaves(a, b, path=''):
    if isinstance(a, dict) and isinstance(b, dict):
        out=[]
        for key in sorted(a.keys()|b.keys()):
            out += leaves(a.get(key,'<absent>'), b.get(key,'<absent>'), path+'.'+key)
        return out
    if isinstance(a,list) and isinstance(b,list) and len(a)==len(b):
        return sum((leaves(x,y,path+'[%d]'%(i+1)) for i,(x,y) in enumerate(zip(a,b))),[])
    return [] if a==b and type(a)==type(b) else [dict(path=path,original=a,versioned=b)]


def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    a.output.mkdir(parents=True,exist_ok=False)
    home=Path(__file__).resolve().parents[1];proposal=home/'frozen-builder/constructor-proposal'
    sys.path.insert(0,str(a.source.resolve()/'scripts'))
    import analyze_input_consumption as r
    from test_input_consumption_observation import declared_rows,text
    source=(a.source/'scripts/analyze_input_consumption.py').read_text()
    assert sha(source.encode())=='104d998dc504e30fb6702426025b611aa5ee86390a1734f06142d92a3473e4d4'
    seed=declared_rows('authority');client=text(declared_rows('client'))
    m=Forward(seed);m.rpc(2,True,11200,0);m.tick(12500)
    cases={}
    early=Forward(seed);early.connect(10,11200);early.admit(10,2,11300)
    early.rpc(2,True,11400,0);early.rpc(1,True,11500,0,peer=10);early.tick(13000);early.tick(14500)
    bad=deepcopy(early.rows);bad[-1]['stream_ack']=0;cases['ack-zero']=bad
    bad=deepcopy(m.rows);bad[-1]['latest']['input_received']['fire']=0;cases['proved-header']=bad
    bad=deepcopy(m.rows);bad[-1]['latest']['input_received']['wall_msec']=12100;bad[-1]['latest']['input_accepted']['wall_msec']=12000;cases['proved-time']=bad
    results=[]
    for name,rows in cases.items():
        for row in rows:r.record_valid(row)
        actual=r.analyze(client,text(rows));assert actual['transition_status']=='INVALID',(name,actual)
        results.append(dict(name=name,expected='INVALID',actual=actual))
        (a.output/(name+'.json')).write_text(json.dumps(dict(authority=rows,result=actual),indent=2)+'\n')
    mutations={
        'helper-noop':('helper','ack-zero'),
        'packet-noop':('packet','proved-header'),
        'foundation-early':('foundation','ack-zero'),
        'queue-early':('queue','ack-zero'),
        'packet-equality-erased':('equality','proved-header'),
        'packet-time-erased':('time','proved-time')}
    mutation_results=[]
    for name,(kind,case) in mutations.items():
        tree=ast.parse(source)
        fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='analyze_role')
        if kind=='helper':
            next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='deterministic_stream_constraints').body=[ast.Pass()]
        elif kind=='packet':
            cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='PacketProjectionHistory')
            next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='observe').body=[ast.Pass()]
        elif kind=='foundation':
            i=next(i for i,n in enumerate(fn.body) if isinstance(n,ast.For) and ast.unparse(n.iter)=='rows')
            # First rows loop is schema validation. Put the early call after existing prefix validation.
            i=next(i for i,n in enumerate(fn.body) if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and ast.unparse(n.value.func)=='observation_prefix_invariants')
            fn.body[i+1:i+1]=ast.parse("if role == 'authority':\n    authority_lifecycle_foundation(rows)").body
        elif kind=='queue':
            loop=next(n for n in fn.body if isinstance(n,ast.For) and any(isinstance(x,ast.Assign) and ast.unparse(x.targets[0])=='owners_before' for x in n.body))
            i=next(i for i,n in enumerate(loop.body) if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and ast.unparse(n.value.func)=='deterministic_stream_constraints')
            loop.body[i:i]=ast.parse('transitions.observe(row, owners_before)').body
        else:
            class Remove(ast.NodeTransformer):
                def visit_Expr(self,node):
                    if isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Name) and node.value.func.id=='need' and len(node.value.args)>1 and isinstance(node.value.args[1],ast.Constant):
                        message=node.value.args[1].value
                        if kind=='equality' and message=='input outcome differs from its proven synchronous receive':return ast.Pass()
                        if kind=='time' and message=='input outcome predates its proven synchronous receive':return ast.Pass()
                    return self.generic_visit(node)
            tree=Remove().visit(tree)
        mutant=ast.unparse(ast.fix_missing_locations(tree))+'\n'
        (a.output/(name+'.py')).write_text(mutant)
        mod=types.ModuleType('controlled_'+name);mod.__file__=str(a.source/'scripts/analyze_input_consumption.py');exec(compile(mutant,name,'exec'),mod.__dict__)
        actual=mod.analyze(client,text(cases[case]))
        killed=actual['transition_status']!='INVALID'
        mutation_results.append(dict(name=name,case=case,killed=killed,source_sha256=sha(mutant.encode()),actual=actual))
    # Independent constructor comparison and forward source projection.
    before=json.loads((proposal/'original-rows.json').read_text());after=json.loads((proposal/'versioned-rows.json').read_text());claim=json.loads((proposal/'PROPOSAL.json').read_text())
    differences=leaves(before,after)
    assert differences==claim['leaf_changes'] and len(differences)==23
    oldtree=ast.parse((proposal/'original-test-source.py').read_text());newtree=ast.parse((proposal/'proposal-only-adapter.py').read_text())
    method='test_definite_prefix_faults_are_not_hidden_by_unknown_lifecycle'
    old=next(n for n in ast.walk(oldtree) if isinstance(n,ast.FunctionDef) and n.name==method)
    new=next(n for n in ast.walk(newtree) if isinstance(n,ast.FunctionDef) and n.name==method)
    def tail(n):
        i=next(i for i,x in enumerate(n.body) if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='control' for t in x.targets))
        return ast.dump(ast.Module(body=n.body[i:],type_ignores=[]))
    assert tail(old)==tail(new)
    raw=''.join((proposal/'original-test-source.py').read_text().splitlines(keepends=True)[old.lineno-1:old.end_lineno])
    # Builder's field is the whole original module hash despite its method label.
    assert sha((proposal/'original-test-source.py').read_bytes())==claim['original_method_source_sha256']
    original=r.analyze(client,text(before));versioned=r.analyze(client,text(after));assert original['transition_status']=='INVALID' and versioned['transition_status']=='UNKNOWN'
    w=Forward(seed)
    w.rows=deepcopy(seed[:5]);w.prototype=deepcopy(seed[4]);w.count=Counter(seed[4]['counters']);w.latest=deepcopy(seed[4]['latest']);w.queue={9:{1:w.command(1,True)}};w.ack={};w.actor={1:deepcopy(seed[4]['actor'])};w.now=w.last_emit=9000;w.sim=seed[4]['simulation_tick'];w.edges.pop('input_consumed',None);w.trace=[]
    w.pop(9999,1);w.rpc(2,True,10500,0);w.tick(11000)
    command=w.queue[9].pop(2);w.ack[9]=2;w.actor[1]['input']=deepcopy(command);w.hook('input_consumed',11000,9,dict(command,peer=9,actor=1,generation=1));w.tick(12000)
    keys=['reason','wall_msec','counters','latest','queue_count','stream_ack','input_age_msec','deadline_remaining_msec']
    assert len(w.rows)==len(after)
    for n,(actual,expected) in enumerate(zip(w.rows,after),1):
        for key in keys:assert actual[key]==expected[key],(n,key,actual[key],expected[key])
        assert actual['actor'].get('input')==expected['actor'].get('input'),(n,'actorinput')
    spec=importlib.util.spec_from_file_location('proposal_control',proposal/'proposal-only-adapter.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    with (a.output/'proposal-method.stderr').open('w') as stream:test=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(module))
    result=dict(targeted=results,mutations=mutation_results,meaningful_kills=sum(x['killed'] for x in mutation_results),
                proposal=dict(leaf_changes=differences,tail_AST_exact=True,original_method_literal_sha256=sha(raw.encode()),original_module_sha256=claim['original_method_source_sha256'],builder_hash_label_is_module=True,original_status=original['transition_status'],versioned_status=versioned['transition_status'],forward_projection_keys=keys,forward_trace=w.trace,methods=test.testsRun,failures=len(test.failures),errors=len(test.errors),maintained_credit=0))
    (a.output/'SUMMARY.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(targeted=len(results),meaningful_kills=result['meaningful_kills'],proposal=result['proposal']['methods']),indent=2))
    return not(all(x['killed'] for x in mutation_results) and test.wasSuccessful())


if __name__=='__main__':raise SystemExit(main())
