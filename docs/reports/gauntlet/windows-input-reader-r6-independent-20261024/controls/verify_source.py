#!/usr/bin/env python3
import argparse,ast,hashlib,json,os,stat,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--depth',type=Path);a=p.parse_args();assert sorted(os.sched_getaffinity(0))==[4]
BASE='7d8ec7dda37764e0f45fd2ea1e8d330f84bc2508';SOURCE='c8827e7d158431097a5413273b5a1e93715961b0';HANDOFF='abd5a57223ffe8c4481271f06884eb5fe883b96f'
def git(*words):return subprocess.check_output(['git','-C',str(a.source),*words])
def tree(commit):
 d={}
 for item in git('ls-tree','-rz',commit).split(b'\0'):
  if item:
   info,path=item.split(b'\t');mode,kind,blob=info.decode().split();d[path.decode()]={'mode':mode,'kind':kind,'blob':blob}
 return d
old=tree(BASE);new=tree(SOURCE);handoff=tree(HANDOFF)
a1={p:v for p,v in old.items() if not p.startswith('docs/')};b={p:v for p,v in new.items() if not p.startswith('docs/')};h={p:v for p,v in handoff.items() if not p.startswith('docs/')}
assert b==h and set(a1)<=set(b)
changed=sorted(p for p in b if a1.get(p)!=b[p]);assert changed==['scripts/analyze_input_consumption.py','scripts/test_input_consumption_receipts.py','scripts/test_input_consumption_state.py','scripts/test_input_consumption_transitions.py']
assert len(b)==515 and len(b)-len(changed)==511
views=[]
for root in [a.source]+([a.depth] if a.depth else []):
 for path,want in b.items():
  f=root/path;raw=f.read_bytes();assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==want['blob'],path
  mode='100755' if f.stat().st_mode & stat.S_IXUSR else '100644';assert mode==want['mode'],path
 index={}
 for item in subprocess.check_output(['git','-C',str(root),'ls-files','-sz']).split(b'\0'):
  if item:
   info,path=item.split(b'\t');mode,blob,stage=info.decode().split();path=path.decode()
   if not path.startswith('docs/'):assert stage=='0';index[path]={'mode':mode,'kind':'blob','blob':blob}
 assert index==b
 views.append({'root':str(root),'head':subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip(),'physical_non_doc_paths':len(b),'index_modes_blobs_and_physical_bytes_exact':True})
files=[p for p in a1 if p.startswith('scripts/test_input_consumption_') and p.endswith('.py')]
def assertions(commit):
 methods=[];calls=[]
 for path in files:
  for node in ast.walk(ast.parse(git('show',commit+':'+path).decode())):
   if isinstance(node,ast.FunctionDef) and node.name.startswith('test_'):methods.append((path,node.name))
   if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr.startswith('assert'):calls.append((path,ast.dump(node,include_attributes=False)))
 return sorted(methods),sorted(calls)
m0,c0=assertions(BASE);m1,c1=assertions(SOURCE);assert m0==m1 and c0==c1 and len(m0)==55 and len(c0)==100
before=git('show',BASE+':scripts/test_input_consumption_state.py');after=git('show',SOURCE+':scripts/test_input_consumption_state.py');assert after.replace(b'        duplicate[0][\'queue_count\'] = 1\n',b'')==before
print(json.dumps({'base':BASE,'source':SOURCE,'handoff':HANDOFF,'handoff_non_doc_identical':True,'non_doc_union':len(b),'protected':511,'changed':changed,'all_modes_preserved':all(a1[p]['mode']==b[p]['mode'] for p in a1),'unique_union_blobs':len({v['blob'] for v in list(a1.values())+list(b.values())}),'inherited_methods':len(m0),'inherited_assertion_calls':len(c0),'inherited_asts_exact':True,'duplicate_fixture_only_registered_line':True,'views':views,'files':b,'cpu_affinity':[4],'native_executed':False},indent=2))
