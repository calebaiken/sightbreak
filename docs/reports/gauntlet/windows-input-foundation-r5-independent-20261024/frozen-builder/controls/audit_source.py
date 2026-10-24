#!/usr/bin/env python3
"""Audit exact source/AST preservation without executing the reader."""
import ast,hashlib,json,os,subprocess
from pathlib import Path
ROOT=Path.cwd();P=ROOT/'docs/reports/gauntlet/windows-input-foundation-r5-20261024';BASE='52d2fe5e08d5fb2833040a07fb37f7a99bfd90da'
def git(*args):return subprocess.check_output(['git',*args])
def blob(c,p):return git('show',c+':'+p)
def tree(c):
 out={}
 for row in git('ls-tree','-r','-z',c).split(b'\0'):
  if not row:continue
  meta,p=row.split(b'\t');mode,typ,sha=meta.decode().split();p=p.decode()
  if not p.startswith('docs/'):out[p]=(mode,sha)
 return out
TARGET=git('rev-parse','HEAD').decode().strip();base,now=tree(BASE),tree(TARGET);files=[]
for p in sorted(base.keys()|now.keys()):
 raw=(ROOT/p).read_bytes();mode='100755' if os.stat(ROOT/p).st_mode&0o111 else '100644';oid=hashlib.sha1(('blob '+str(len(raw))+'\0').encode()+raw).hexdigest();assert now[p]==(mode,oid),p
 files.append(dict(path=p,mode=mode,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),blob=oid,protected=base.get(p)==now[p]))
deltas=[x['path'] for x in files if not x['protected']];assert deltas==['scripts/analyze_input_consumption.py','scripts/test_input_consumption_deterministic_phase.py'],deltas
protected=sum(x['protected'] for x in files);assert (len(files),protected)==(521,519)
methods=asserts=0
for p in sorted(x for x in base if x.startswith('scripts/test_input_consumption') and x.endswith('.py')):
 assert blob(BASE,p)==blob(TARGET,p),(p,'old test bytes changed')
 t=ast.parse(blob(BASE,p));methods+=sum(isinstance(n,ast.FunctionDef) and n.name.startswith('test_') for n in ast.walk(t));asserts+=sum(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr.startswith('assert') for n in ast.walk(t))
assert methods==135,methods
path='scripts/analyze_input_consumption.py';old=ast.parse(blob(BASE,path));new=ast.parse(blob(TARGET,path));new.body=[n for n in new.body if not(isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in {'deterministic_stream_constraints','PacketProjectionHistory'})]
fn=next(n for n in new.body if isinstance(n,ast.FunctionDef) and n.name=='analyze_role')
def calls(n,name):return isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and ((isinstance(n.value.func,ast.Name) and n.value.func.id==name) or (isinstance(n.value.func,ast.Attribute) and ast.unparse(n.value.func)==name))
fn.body=[n for n in fn.body if not(isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in {'inference_rows','packets','failed_connections'} for t in n.targets))]
loop=next(n for n in fn.body if isinstance(n,ast.For) and any(isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='owners_before' for t in x.targets) for x in n.body))
body=[]
for n in loop.body:
 if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='failed_connection' for t in n.targets):
  continue
 if isinstance(n,ast.If) and isinstance(n.test,ast.Name) and n.test.id=='failed_connection':
  continue
 if isinstance(n,ast.If) and isinstance(n.test,ast.BoolOp) and isinstance(n.test.op,ast.And) and len(n.test.values)==2 and isinstance(n.test.values[1],ast.UnaryOp) and isinstance(n.test.values[1].operand,ast.Name) and n.test.values[1].operand.id=='failed_connection':
  n.test=n.test.values[0]
 if calls(n,'deterministic_stream_constraints'):
  body.extend(ast.parse('transitions.observe(row, owners_before)').body)
 elif calls(n,'packets.observe') or calls(n,'inference_rows.append'):continue
 else:body.append(n)
loop.body=body
fn.body=[n for n in fn.body if not (isinstance(n,ast.If) and n.body and isinstance(n.body[0],ast.Try)) and not (isinstance(n,ast.For) and isinstance(n.iter,ast.Name) and n.iter.id=='inference_rows')]
i=next(i for i,n in enumerate(fn.body) if calls(n,'observation_prefix_invariants'))
fn.body[i+1:i+1]=ast.parse("if role == 'authority':\n    authority_lifecycle_foundation(rows)").body
assert ast.dump(old)==ast.dump(new),'reader differs beyond declared phase transformation and failed-callback success guard/helpers'
result=dict(base=BASE,target=TARGET,physical_non_doc_paths=len(files),protected_paths=protected,deltas=deltas,all_source_modes_and_bytes_exact=True,old_test_methods=methods,old_test_assertion_calls=asserts,all_old_input_test_files_byte_exact=True,old_reader_AST_exact_after_declared_phase_reversal=True,files=files,native_executed=False,approval='requires different critic')
(P/'SOURCE_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='files'},indent=2))
