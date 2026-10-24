#!/usr/bin/env python3
"""Independent 508-path Git/working-byte composition proof, no native calls."""
import ast,difflib,hashlib,json,os,stat,subprocess
from pathlib import Path
BASE='7101350e5d0a2f6e4afb9a913b5b1bcf2107857a';SOURCE='4cf6ac8e744603ed6af122a362036d276754cc76'
ROOT=Path(__file__).resolve().parents[5];DEPTH=ROOT.parent/'windows-route-clock-independent-depth-one-20261024'
assert sorted(os.sched_getaffinity(0))==[4]
def git(root,*args):return subprocess.check_output(['git','-C',str(root),*args])
def table(commit):
 result={}
 for entry in git(ROOT,'ls-tree','-rz',commit).split(b'\0'):
  if not entry:continue
  meta,path=entry.split(b'\t');mode,kind,blob=meta.decode().split();path=path.decode()
  if not path.startswith('docs/'):result[path]={'mode':mode,'kind':kind,'blob':blob}
 return result
base=table(BASE);candidate=table(SOURCE);assert len(base)==len(candidate)==508 and set(base)==set(candidate)
changed=[p for p in base if base[p]!=candidate[p]]
assert sorted(changed)==['scripts/test_native_route_pulse.py','scripts/verify_integration_export.py']
assert all(base[p]['mode']==candidate[p]['mode'] for p in base)
views=[]
for label,root in [('own',ROOT),('depth-one',DEPTH)]:
 assert git(root,'rev-parse','--show-object-format').strip()==b'sha1'
 for path,meta in candidate.items():
  p=root/path;data=p.read_bytes();blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
  assert blob==meta['blob'],path
  mode='100755' if p.stat().st_mode & stat.S_IXUSR else '100644';assert mode==meta['mode'],path
 index={}
 for entry in git(root,'ls-files','-sz').split(b'\0'):
  if not entry:continue
  meta,path=entry.split(b'\t');mode,blob,stage=meta.decode().split();path=path.decode()
  if not path.startswith('docs/'):assert stage=='0';index[path]={'mode':mode,'kind':'blob','blob':blob}
 assert index==candidate
 changes=git(root,'diff','--name-only',SOURCE).decode().splitlines();assert all(p.startswith('docs/') for p in changes)
 views.append({'label':label,'path':str(root),'head':git(root,'rev-parse','HEAD').decode().strip(),'source_paths':508,'all_paths_modes_blobs_and_working_bytes_exact':True,'non_doc_changes':[],'shallow':git(root,'rev-parse','--is-shallow-repository').decode().strip(),'reachable_commits':int(git(root,'rev-list','--count','HEAD'))})
def module_at(commit,path):return git(ROOT,'show',commit+':'+path).decode()
path='scripts/verify_integration_export.py';old=module_at(BASE,path);new=module_at(SOURCE,path)
def method(s):
 cls=next(n for n in ast.parse(s).body if isinstance(n,ast.ClassDef) and n.name=='WinUI')
 return next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='key_pulse')
a,b=method(old),method(new);old_lines=old.splitlines(keepends=True);new_lines=new.splitlines(keepends=True)
erased=''.join(new_lines[:b.lineno-1]+old_lines[a.lineno-1:a.end_lineno]+new_lines[b.end_lineno:]);assert erased==old
path='scripts/test_native_route_pulse.py';oldtests=module_at(BASE,path);newtests=module_at(SOURCE,path)
delta=list(difflib.ndiff(oldtests.splitlines(keepends=True),newtests.splitlines(keepends=True)))
assert not any(x.startswith('- ') for x in delta)
assert ''.join(x[2:] for x in delta if x.startswith('  '))==oldtests
old_ast=ast.parse(oldtests);new_ast=ast.parse(newtests)
new_ast.body=[n for n in new_ast.body if not (isinstance(n,ast.ClassDef) and n.name in ('IndependentClockPulse','RouteClockBoundaryControls')) and not (isinstance(n,ast.Import) and len(n.names)==1 and n.names[0].name=='math')]
assert ast.dump(new_ast,include_attributes=False)==ast.dump(old_ast,include_attributes=False)
report={'base':BASE,'candidate':SOURCE,'paths':508,'unchanged_paths':506,'changed_paths':changed,'all_modes_unchanged':True,'exact_helper_erasure_recovers_old_file':True,'test_changes_additions_only':True,'removing_two_added_classes_and_math_import_recovers_original_ast':True,'views':views,'files':candidate,'cpu_affinity':sorted(os.sched_getaffinity(0)),'native_executed':False}
print(json.dumps(report,indent=2))
