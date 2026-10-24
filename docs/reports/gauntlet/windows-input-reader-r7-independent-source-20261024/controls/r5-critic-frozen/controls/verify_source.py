#!/usr/bin/env python3
"""Independent complete source/fixture identity and preserved assertion audit."""
import ast,copy,difflib,hashlib,importlib.util,json,os,stat,subprocess,sys
from pathlib import Path
BASE='642dd0e0543698cae5d90b9046d5875beabed111';SOURCE='7d8ec7dda37764e0f45fd2ea1e8d330f84bc2508'
ROOT=Path(__file__).resolve().parents[5];DEPTH=ROOT.parent/'windows-input-reader-r5-independent-depth-one-20261024'
REPORT='docs/reports/gauntlet/windows-input-consumption-r5-20261024'
assert sorted(os.sched_getaffinity(0))==[4]
def git(*args):return subprocess.check_output(['git','-C',str(ROOT),*args])
def table(commit):
 result={}
 for item in git('ls-tree','-rz',commit).split(b'\0'):
  if not item:continue
  meta,path=item.split(b'\t');mode,kind,oid=meta.decode().split();result[path.decode()]={'mode':mode,'kind':kind,'blob':oid}
 return result
old=table(BASE);new=table(SOURCE);a={p:v for p,v in old.items() if not p.startswith('docs/')};b={p:v for p,v in new.items() if not p.startswith('docs/')}
assert len(a)==512 and len(b)==513 and set(a)<=set(b)
changed=[p for p in b if a.get(p)!=b[p]];assert sorted(changed)==['scripts/analyze_input_consumption.py','scripts/test_input_consumption_identity.py','scripts/test_input_consumption_lifecycle.py','scripts/test_input_consumption_stream.py']
views=[]
for label,root in [('own',ROOT),('depth-one',DEPTH)]:
 for path,wanted in b.items():
  f=root/path;data=f.read_bytes();oid=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest();assert oid==wanted['blob'],path
  mode='100755' if f.stat().st_mode & stat.S_IXUSR else '100644';assert mode==wanted['mode'],path
 index={}
 for item in subprocess.check_output(['git','-C',str(root),'ls-files','-sz']).split(b'\0'):
  if not item:continue
  meta,path=item.split(b'\t');mode,blob,stage=meta.decode().split();path=path.decode()
  if not path.startswith('docs/'):assert stage=='0';index[path]={'mode':mode,'kind':'blob','blob':blob}
 assert index==b
 delta=subprocess.check_output(['git','-C',str(root),'diff','--name-only',SOURCE]).decode().splitlines();assert all(p.startswith('docs/') for p in delta)
 views.append({'label':label,'root':str(root),'head':subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip(),'physical_source_paths':len(b),'all_index_paths_modes_blobs_and_working_bytes_exact':True,'source_delta':[]})
additions={}
for path in changed:
 if path not in a:continue
 before=git('show',BASE+':'+path).decode();after=git('show',SOURCE+':'+path).decode();delta=list(difflib.ndiff(before.splitlines(keepends=True),after.splitlines(keepends=True)))
 assert not any(x.startswith('- ') for x in delta),path
 assert ''.join(x[2:] for x in delta if x.startswith('  '))==before
 additions[path]=sum(x.startswith('+ ') for x in delta)
assert additions=={'scripts/analyze_input_consumption.py':24,'scripts/test_input_consumption_identity.py':1,'scripts/test_input_consumption_lifecycle.py':4}
files=['scripts/test_input_consumption_'+n+'.py' for n in ('observation','identity','lifecycle','state')]
def tests(source):
 names=[];assertions=[]
 for path in files:
  tree=ast.parse(git('show',source+':'+path).decode())
  for node in ast.walk(tree):
   if isinstance(node,ast.FunctionDef) and node.name.startswith('test_'):names.append((path,node.name))
   if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr.startswith('assert'):assertions.append((path,ast.dump(node,include_attributes=False)))
 return sorted(names),sorted(assertions)
old_methods,old_asserts=tests(BASE);new_methods,new_asserts=tests(SOURCE)
assert old_methods==new_methods and old_asserts==new_asserts and len(old_methods)==45 and len(old_asserts)==79
historical=[]
for name in ('analyze_input_consumption.py','test_input_consumption_identity.py','test_input_consumption_lifecycle.py'):
 path=REPORT+'/historical-source/'+name;assert new[path]['blob']==old['scripts/'+name]['blob'];assert (ROOT/path).read_bytes()==git('show',BASE+':scripts/'+name);historical.append(path)
critic=table('ad12f7ae08ca9cf1eaf05807ea41c44104544fdc');critic_prefix='docs/reports/gauntlet/windows-input-reader-r4-independent-source-20261024/'
builder=table('d139124e8c663c3951eb6c7aaff99d49f2ce9712');builder_prefix='docs/reports/gauntlet/windows-input-consumption-r4-20261024/'
provenance=[]
for prefix,origin,original_prefix,commit in [(REPORT+'/r4-critic-frozen/',critic,critic_prefix,'ad12f7ae'),(REPORT+'/r4-builder-frozen/',builder,builder_prefix,'d139124e')]:
 for path,value in new.items():
  if not path.startswith(prefix):continue
  mapped=original_prefix+path[len(prefix):];assert mapped in origin,(path,mapped);assert value['blob']==origin[mapped]['blob'],path
  raw=(ROOT/path).read_bytes();assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==value['blob']
  provenance.append({'copy':path,'source_commit':commit,'source_path':mapped,'mode':value['mode'],'blob':value['blob']})
# Independently construct the unchanged failed-attempt fixture and inspect first cache transition.
sys.path.insert(0,str(ROOT/'scripts'))
import test_input_consumption_observation as fixture
import test_input_consumption_lifecycle as lifecycle
rows=fixture.declared_rows('client');failed=copy.deepcopy(rows[1]);failed['reason']='client_connection_failed';rows[2:2]=[failed,copy.deepcopy(rows[1])]
for row in rows[3:]:row['local_attempt']=2
current=lifecycle.restamp(copy.deepcopy(rows))
first=next(i for i,row in enumerate(current) if row['counters'].get('snapshot_applied',0))
previous=current[first-1];snapshot=current[first]
assert previous['wall_msec']==6000 and previous['counters'].get('snapshot_applied',0)==0 and not previous['snapshot']
assert snapshot['wall_msec']==7000 and snapshot['counters']['snapshot_applied']==1 and snapshot['snapshot']['wall_msec']==6000
assert all(row['snapshot']==row['latest']['snapshot_applied'] and row['snapshot']['wall_msec']==6000 for row in current[first:])
report={'base':BASE,'candidate':SOURCE,'non_doc_union_paths':513,'protected_paths':509,'changed_paths':changed,'all_existing_modes_preserved':all(a[p]['mode']==b[p]['mode'] for p in a),'additive_existing_source_lines':additions,'inherited_methods':45,'inherited_assertion_calls':79,'methods_and_assertion_asts_unchanged':True,'historical_source_files_exact':historical,'frozen_copies_verified':len(provenance),'provenance':provenance,'first_snapshot_fixture':{'previous_wall':6000,'previous_applied_count':0,'first_counted_wall':7000,'first_applied_count':1,'cached_timestamp':6000,'persists':True},'views':views,'files':b,'cpu_affinity':[4],'native_executed':False}
print(json.dumps(report,indent=2))
