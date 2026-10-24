#!/usr/bin/env python3
import argparse,ast,hashlib,json,os,stat,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--depth',type=Path);a=p.parse_args();assert sorted(os.sched_getaffinity(0))==[4]
BASE='c8827e7d158431097a5413273b5a1e93715961b0';SOURCE='2d4214c4d3314df568796f0a6f3a38fc357db318';HANDOFF='2fd161e4536911d0d86280b2a53444376534259c'
def git(*words):return subprocess.check_output(['git','-C',str(a.source),*words])
def tree(commit):
 d={}
 for item in git('ls-tree','-rz',commit).split(b'\0'):
  if item:
   info,path=item.split(b'\t');mode,kind,blob=info.decode().split();d[path.decode()]={'mode':mode,'kind':kind,'blob':blob}
 return d
old=tree(BASE);new=tree(SOURCE);handoff=tree(HANDOFF);left={p:v for p,v in old.items() if not p.startswith('docs/')};right={p:v for p,v in new.items() if not p.startswith('docs/')};h={p:v for p,v in handoff.items() if not p.startswith('docs/')};assert right==h and set(left)<=set(right)
changed=sorted(p for p in right if left.get(p)!=right[p]);assert changed==['scripts/analyze_input_consumption.py','scripts/test_input_consumption_absorbing.py','scripts/test_input_consumption_expiry.py'] and len(right)==517
views=[]
for root in [a.source]+([a.depth] if a.depth else []):
 for path,want in right.items():
  f=root/path;raw=f.read_bytes();assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==want['blob'],path;mode='100755' if f.stat().st_mode&stat.S_IXUSR else '100644';assert mode==want['mode'],path
 index={}
 for item in subprocess.check_output(['git','-C',str(root),'ls-files','-sz']).split(b'\0'):
  if item:
   info,path=item.split(b'\t');mode,blob,stage=info.decode().split();path=path.decode()
   if not path.startswith('docs/'):assert stage=='0';index[path]={'mode':mode,'kind':'blob','blob':blob}
 assert index==right
 views.append(dict(root=str(root),head=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip(),physical_non_doc_paths=len(right),index_modes_blobs_and_physical_bytes_exact=True))
files=[p for p in left if p.startswith('scripts/test_input_consumption_') and p.endswith('.py')]
def signatures(commit):
 methods=[];calls=[]
 for path in files:
  for node in ast.walk(ast.parse(git('show',commit+':'+path).decode())):
   if isinstance(node,ast.FunctionDef) and node.name.startswith('test_'):methods.append((path,node.name))
   if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr.startswith('assert'):calls.append((path,ast.dump(node,include_attributes=False)))
 return sorted(methods),sorted(calls)
methods,asserts=signatures(BASE);assert (methods,asserts)==signatures(SOURCE) and len(methods)==75
prior_expiry=git('show','fdab9461:scripts/test_input_consumption_expiry.py');current_expiry=git('show',SOURCE+':scripts/test_input_consumption_expiry.py');assert prior_expiry==current_expiry
expiry_tests=sum(isinstance(n,ast.FunctionDef) and n.name.startswith('test_') for n in ast.walk(ast.parse(current_expiry.decode())));assert expiry_tests==20
before=ast.parse(git('show',BASE+':scripts/analyze_input_consumption.py').decode());after=ast.parse(git('show',SOURCE+':scripts/analyze_input_consumption.py').decode());defs=lambda t:{n.name:ast.dump(n,include_attributes=False) for n in t.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))};bdefs,adefs=defs(before),defs(after);protected_defs=sorted(n for n in bdefs if n!='analyze_role');assert all(bdefs[n]==adefs[n] for n in protected_defs)
print(json.dumps(dict(base=BASE,source=SOURCE,handoff=HANDOFF,handoff_non_doc_identical=True,non_doc_union=517,protected_paths=514,changed_paths=changed,all_existing_modes_preserved=all(left[p]['mode']==right[p]['mode'] for p in left),unique_union_blobs=len({v['blob'] for v in list(left.values())+list(right.values())}),inherited_methods=75,inherited_assertions=len(asserts),inherited_methods_assertion_asts_exact=True,prior_expiry_methods=20,prior_expiry_file_exact=True,prior_expiry_sha256=hashlib.sha256(prior_expiry).hexdigest(),protected_analyzer_definitions=protected_defs,protected_definitions_ast_exact=True,views=views,files=right,cpu_affinity=[4],native_executed=False),indent=2))
