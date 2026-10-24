#!/usr/bin/env python3
"""Static frozen-byte/AST audit, no candidate execution."""
import ast, hashlib, json, os, subprocess
from pathlib import Path
ROOT=Path.cwd(); P=ROOT/'docs/reports/gauntlet/windows-authority-foundation-r3-independent-20261024'
BASE='9e3b85db1814a7e06c1306da10cce2fcdb9e7984'; TARGET='ca9a04cd5d995e312b1d5b71c9ffd75d428ea77c'; HANDOFF='db954429caa4cb714efad04023379fa3a4f89b5e'
def git(*args):return subprocess.check_output(['git',*args])
def blob(c,p):return git('show',c+':'+p)
def tree(c):
 out={}
 for row in git('ls-tree','-r','-z',c).split(b'\0'):
  if not row:continue
  meta,p=row.split(b'\t'); mode,typ,sha=meta.decode().split();p=p.decode()
  if p.startswith('docs/'):continue
  out[p]=(mode,sha)
 return out
a,b=tree(BASE),tree(TARGET); files=[]
for p in sorted(a.keys()|b.keys()):
 data=(ROOT/p).read_bytes(); mode='100755' if os.stat(ROOT/p).st_mode&0o111 else '100644';sha=hashlib.sha256(data).hexdigest()
 # Batch-free bounded 520 paths: Git blob identity is computed by its documented header.
 rawhash=hashlib.sha1(('blob '+str(len(data))+'\0').encode()+data).hexdigest();assert b[p]==(mode,rawhash),(p,b[p],mode,rawhash)
 files.append(dict(path=p,mode=mode,bytes=len(data),sha256=sha,git_blob=rawhash,protected=a.get(p)==b[p]))
assert len(files)==520 and sum(x['protected'] for x in files)==517
reader='scripts/analyze_input_consumption.py'; old=ast.parse(blob(BASE,reader));new=ast.parse(blob(TARGET,reader));new.body=[n for n in new.body if not(isinstance(n,ast.FunctionDef) and n.name=='authority_lifecycle_foundation')]
fn=next(n for n in new.body if isinstance(n,ast.FunctionDef) and n.name=='analyze_role')
fn.body=[n for n in fn.body if not (isinstance(n,ast.If) and ast.dump(n.test)==ast.dump(ast.Compare(left=ast.Name(id='role',ctx=ast.Load()),ops=[ast.Eq()],comparators=[ast.Constant(value='authority')])) and len(n.body)==1 and isinstance(n.body[0],ast.Expr) and isinstance(n.body[0].value,ast.Call) and getattr(n.body[0].value.func,'id',None)=='authority_lifecycle_foundation')]
assert ast.dump(old)==ast.dump(new)
methods=asserts=0; protected_methods=[]
for p in sorted(x for x in a if x.startswith('scripts/test_input_consumption') and x.endswith('.py')):
 x,y=ast.parse(blob(BASE,p)),ast.parse(blob(TARGET,p))
 for cls in [n for n in x.body if isinstance(n,ast.ClassDef)]:
  now=next(n for n in y.body if isinstance(n,ast.ClassDef) and n.name==cls.name)
  for method in [n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')]:
   newer=next(n for n in now.body if isinstance(n,ast.FunctionDef) and n.name==method.name);assert ast.dump(method)==ast.dump(newer),(p,method.name)
   methods+=1; count=sum(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr.startswith('assert') for n in ast.walk(method));asserts+=count;protected_methods.append(dict(path=p,method=cls.name+'.'+method.name,assertion_calls=count))
assert (methods,asserts)==(123,295)
legacy=[x for x in protected_methods if x['path']!='scripts/test_input_consumption_foundation_model.py'];assert (len(legacy),sum(x['assertion_calls'] for x in legacy))==(105,224)
all_calls=[]
for p in sorted({x['path'] for x in legacy}):
 x,y=ast.parse(blob(BASE,p)),ast.parse(blob(TARGET,p));ax=[ast.dump(n) for n in ast.walk(x) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr.startswith('assert')];ay=[ast.dump(n) for n in ast.walk(y) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr.startswith('assert')];assert ax==ay,p;all_calls.extend(ax)
assert len(all_calls)==226
report='docs/reports/gauntlet/windows-input-foundation-enforcement-20261024';dest=P/'frozen-builder-db954';dest.mkdir(exist_ok=True); members=[]
for path in git('ls-tree','-r','--name-only',HANDOFF,report).decode().splitlines():
 raw=blob(HANDOFF,path);rel=Path(path).relative_to(report);f=dest/rel;f.parent.mkdir(exist_ok=True,parents=True);f.write_bytes(raw);members.append(dict(path=str(rel),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
manifest=json.loads((dest/'MANIFEST.json').read_text())
(P/'SOURCE_AUDIT.json').write_text(json.dumps(dict(base=BASE,target=TARGET,handoff=HANDOFF,physical_non_doc_paths=len(files),protected_paths=517,deltas=[x['path'] for x in files if not x['protected']],all_modes_and_bytes_match=True,old_methods=105,old_assertion_calls=226,additional_preedit_model_methods=18,additional_preedit_model_assertion_calls=71,total_unchanged_methods=methods,total_unchanged_assertion_calls_inside_methods=asserts,legacy_method_assertion_calls=224,legacy_all_file_assertion_calls=226,old_reader_AST_exact_after_only_new_prepass_and_call_erasure=True,files=files,protected_methods=protected_methods,builder_frozen_members=members,scope='Static source/pre-edit layer audit only; no depth/native/full acceptance'),indent=2)+'\n')
print(json.dumps(dict(paths=len(files),protected=517,methods=methods,assertions=asserts,frozen_builder_members=len(members),manifest_type=type(manifest).__name__)))
