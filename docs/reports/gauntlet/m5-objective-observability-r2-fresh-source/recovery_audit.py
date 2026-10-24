#!/usr/bin/env python3
"""Independent recovery identity and retained-evidence audit; no engine calls."""
import difflib, hashlib, json, os, re, stat, subprocess
from pathlib import Path
assert sorted(os.sched_getaffinity(0)) == [4]
ROOT=Path(__file__).resolve().parents[4]
REPORT=Path(__file__).resolve().parent
SOURCE='dce89495d04c9d3fefece0f8c7929e2e01b8e7df'
DEPTH=ROOT.parent/'m5-objective-observability-r2-fresh-depth-one'
def git(root,*args,check=True):
 return subprocess.run(['git',*args],cwd=root,capture_output=True,check=check)
def digest(b):return hashlib.sha256(b).hexdigest()
def decode_many(s):
 d=json.JSONDecoder();result=[];i=0
 while i<len(s):
  if s[i].isspace():i+=1;continue
  v,n=d.raw_decode(s[i:]);i+=n;result.append(v)
 return result
inventory=json.loads((ROOT/'docs/reports/gauntlet/m5-objective-observability/correction-r2/acquisition-inventory.json').read_text())['files']
expected={}
for line in git(ROOT,'ls-tree','-rz',SOURCE,'--','game','scripts').stdout.split(b'\0'):
 if not line:continue
 meta,path=line.split(b'\t');mode,kind,blob=meta.decode().split();expected[path.decode()]={'mode':mode,'blob':blob}
assert set(expected)==set(inventory)
views=[]
for label,root in [('own',ROOT),('depth-one',DEPTH)]:
 tracked={}
 for line in git(root,'ls-files','-sz','--','game','scripts').stdout.split(b'\0'):
  if not line:continue
  meta,path=line.split(b'\t');mode,blob,stage=meta.decode().split();assert stage=='0';tracked[path.decode()]={'mode':mode,'blob':blob}
 assert tracked==expected
 changed=[]
 for path,sha in inventory.items():
  p=root/path; data=p.read_bytes()
  actual_mode='100755' if p.stat().st_mode & stat.S_IXUSR else '100644'
  if digest(data)!=sha or actual_mode!=expected[path]['mode']:changed.append(path)
 assert not changed
 assert not git(root,'diff',SOURCE,'--','game','scripts').stdout
 assert not git(root,'ls-files','--others','--exclude-standard','--','game','scripts').stdout
 gitdir=Path(git(root,'rev-parse','--absolute-git-dir').stdout.decode().strip())
 parent=git(root,'cat-file','-e','41aa040dd04a624cefd74dfef74c10bbcf95b44d^{commit}',check=False)
 views.append({'label':label,'path':str(root),'head':git(root,'rev-parse','HEAD').stdout.decode().strip(),
  'shallow':git(root,'rev-parse','--is-shallow-repository').stdout.decode().strip(),
  'reachable_commits':int(git(root,'rev-list','--count','HEAD').stdout),
  'remotes':git(root,'remote','-v').stdout.decode(),
  'alternates_present':(gitdir/'objects/info/alternates').exists(),
  'git_alternate_object_directories_set':bool(os.environ.get('GIT_ALTERNATE_OBJECT_DIRECTORIES')),
  'parent_object_exit':parent.returncode,'parent_object_stderr':parent.stderr.decode(),
  'source_paths':len(expected),'source_paths_modes_blobs_equal':True,'working_source_files_equal':True,
  'source_tree':{p:git(root,'rev-parse','HEAD:'+p).stdout.decode().strip() for p in ('game','scripts')},
  'source_untracked':[]})
retained=[]
for view in ('own','depth-one'):
 for name in ('maintained','source-audit','original-rig'):
  receipt=json.loads((REPORT/view/(name+'.json')).read_text())
  for stream in ('stdout','stderr'):
   assert digest((REPORT/view/(name+'.'+stream)).read_bytes())==receipt[stream+'_sha256']
  retained.append({'view':view,'name':name,'exit_code':receipt['exit_code'],'hashes_verified':True})
 original=decode_many((REPORT/view/'original-rig.stdout').read_text())[-1]
 names=original['results']
 actual=[x for x in names if x['expected_rejection'] and x['name']!='forward_rows_have_no_dt_pose_command_objective_or_progress']
 assert len(actual)==18 and all(x['rejected'] for x in actual)
 positive=next(x for x in names if not x['expected_rejection'])
 assert not positive['rejected']
 retained.append({'view':view,'name':'original-rig-adjudication','named_cases':len(names),'distinct_inputs':19,'actual_mutations':18,'actual_rejections':18,'positive_accepted':True,'duplicate_noop_only_failed_expectation':all(x['met_expectation'] for x in names if x['name']!='forward_rows_have_no_dt_pose_command_objective_or_progress')})
 fresh=decode_many((REPORT/view/'fresh-controls.stdout').read_text())[-1]
 assert fresh['positive_accepted'] and fresh['real_mutations']==12 and fresh['mutations_rejected']==0
 assert len({x['input_sha256'] for x in fresh['results']})==13
 retained.append({'view':view,'name':'fresh-controls','distinct_inputs':13,'real_mutations':12,'actual_rejections':0,'false_passes':fresh['false_passes']})
ai=(ROOT/'game/scripts/gameplay/bot_ai.gd').read_text()
erased=re.sub(r'^[\t ]*# OBJECTIVE_OBSERVATION_BEGIN\n.*?^[\t ]*# OBJECTIVE_OBSERVATION_END\n','',ai,flags=re.M|re.S).replace('_acquire_target(','acquire_target(')
for name in ('acquire_target','compute_bot_input'):
 erased=re.sub(rf'(static func {name}\([^\n]*), observation: Dictionary = \{{\}}(\) ->)',r'\1\2',erased)
erased=erased.replace('acquire_target(match_node, actor, state, profile, observation if observing else {})','acquire_target(match_node, actor, state, profile)')
base=git(ROOT,'show','022d60f:game/scripts/gameplay/bot_ai.gd').stdout
assert erased.encode()==base
history=git(ROOT,'show','0527715:game/scripts/gameplay/bot_ai.gd').stdout
assert history==(ROOT/'docs/reports/gauntlet/m5-objective-observability/correction-r2/source-reference/original-0527715-bot_ai.gd.txt').read_bytes()
delta=list(difflib.ndiff(history.decode().splitlines(),erased.splitlines()))
adds=[x for x in delta if x.startswith('+ ')];deletes=[x for x in delta if x.startswith('- ')]
assert len(adds)==13 and not deletes
rig=ROOT/'docs/reports/gauntlet/m5-objective-observability/correction-r2/original-critic/independent_controls.py'
assert digest(rig.read_bytes())=='af4a712cdd9f195203ad4caec4c9351da4a0ebf221d80ef23e54cd2ec3489813'
grammar=[]
try:
 from gdtoolkit.parser import parser
except ImportError as exc:
 grammar.append({'passed':False,'error':str(exc)})
else:
 for label,root in [('own',ROOT),('depth-one',DEPTH)]:
  for path in ('game/scripts/gameplay/bot_ai.gd','game/tests/bot_objective_observation_probe.gd'):
   parser.parse((root/path).read_text());grammar.append({'view':label,'path':path,'sha256':digest((root/path).read_bytes()),'passed':True})
result={'source':SOURCE,'cpu_affinity':sorted(os.sched_getaffinity(0)),'views':views,'retained':retained,
 'baseline_erasure_equals_exact_git':True,'baseline_sha256':digest(base),'historical_equals_exact_git':True,
 'historical_additions':adds,'historical_removals':deletes,'grammar':grammar,'native_executed':False}
print(json.dumps(result,indent=2))
