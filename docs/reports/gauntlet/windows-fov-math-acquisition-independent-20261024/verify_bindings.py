import hashlib,json,os,stat,subprocess,sys,tempfile
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;ROOT=Path(os.environ.get('MATH_REVIEW_ROOT','/workspace/reviews/windows-fov-math-acquisition-runtime-20261024'));LABEL=os.environ.get('MATH_BINDING_LABEL','BINDINGS.json')
SOURCE='b16b012d720c0981cfc28146a651b3ba5f8a9caa';RUNTIME='25603855ad7029b10c6c4109a4d47b949d72c1d2';BASE='64afaa4132c1f1e1c1376f5269b46ff9918aa9a6';PREFIX='docs/reports/gauntlet/windows-fov-math-acquisition-20261024/'
BUILDER=Path('/workspace/sightbreak-windows-fov-math-acquisition')
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def sha(b):return hashlib.sha256(b).hexdigest()
def tree(rev):
 result={}
 for line in git('ls-tree','-rz',rev).split(b'\0'):
  if line:
   identity,name=line.split(b'\t',1);result[name.decode()]=identity.decode()
 return result
m=json.loads(git('show',RUNTIME+':'+PREFIX+'EVIDENCE_INVENTORY.json'));members=[]
for row in m['files']:
 name=row['path'];b=git('show',RUNTIME+':'+PREFIX+name);actual=(BUILDER/PREFIX/name).read_bytes()
 assert len(b)==row['bytes'] and sha(b)==row['sha256'] and b==actual,name
 target=HERE/'builder-evidence-exact'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(b);members.append(row)
(HERE/'builder-evidence-exact/EVIDENCE_INVENTORY.json').write_bytes(git('show',RUNTIME+':'+PREFIX+'EVIDENCE_INVENTORY.json'))
old,source,runtime=tree(BASE),tree(SOURCE),tree(RUNTIME);added=sorted(p for p in source if not p.startswith('docs/') and p not in old)
assert added==['.github/workflows/windows-fov-math.yml','scripts/test_windows_fov_math.py','scripts/windows_fov_math.py'],added
protected=[p for p in old if not p.startswith('docs/')];assert len(protected)==523 and all(old[p]==source.get(p)==runtime.get(p) for p in protected)
assert all(old[p]==source.get(p) for p in old)
non_doc=[p for p in source if not p.startswith('docs/')];assert len(non_doc)==526 and all(source[p]==runtime.get(p) for p in non_doc)
physical=[]
for name in non_doc:
 mode,kind,blob=source[name].split();p=ROOT/name;st=p.lstat();b=p.read_bytes()
 assert stat.S_ISREG(st.st_mode) and not p.is_symlink() and b==git('cat-file','blob',blob),name
 actual_mode='100755' if st.st_mode&stat.S_IXUSR else '100644';assert actual_mode==mode,name
 physical.append(dict(path=name,identity=source[name],bytes=len(b),sha256=sha(b),physical_mode=actual_mode))
assert git('rev-parse',BASE+':game')==git('rev-parse',SOURCE+':game')==git('rev-parse',RUNTIME+':game')
sys.path.insert(0,str(ROOT/'scripts'));import windows_fov_math as w
manifest=ROOT/PREFIX/'RUNTIME_COMPONENT_MANIFEST.json';expected=sha(manifest.read_bytes());assert expected=='9eede33699b5851ea8ed8c9a0e451d10e6d667993408d8b884dccba5f67b1d71'
class Clock:
 def __call__(self):return 100.
with tempfile.TemporaryDirectory() as td:
 out=Path(td)/'blocked'
 with patch.object(w,'WindowsJob') as job,patch.object(w,'sdk_member') as sdk,patch.object(w.subprocess,'Popen') as popen,patch.object(w,'execute_prepared') as prepared:
  report=w.collect(out,Path(td)/'absent-sdk.zip',manifest,expected,RUNTIME,root=ROOT,clock=Clock())
  assert not report['passed'] and report['native_invocations']==0 and report['preflight']['status']=='BLOCKED' and not report['preflight']['execution_admitted']
  assert 'artifact feasibility BLOCKED' in report['error'] and report['source']['runtime_commit']==RUNTIME and report['source']['code_commit']==SOURCE
  job.assert_not_called();sdk.assert_not_called();popen.assert_not_called();prepared.assert_not_called()
  public=dict(report=report,job_calls=job.call_count,sdk_calls=sdk.call_count,popen_calls=popen.call_count,prepared_calls=prepared.call_count,retained_manifest_exact=(out/'source-manifest.json').read_bytes()==manifest.read_bytes())
assert not git('status','--porcelain','--untracked-files=all')
result=dict(source=SOURCE,runtime=RUNTIME,base=BASE,builder_members=len(members),builder_manifest=members,non_doc_paths=526,protected_non_doc_paths=523,protected_all_original_paths=len(old),added=added,all_original_path_mode_blob_exact=True,runtime_full_non_doc_exact=True,game_tree_exact=True,physical=physical,public=public,cpu=sorted(os.sched_getaffinity(0)),actual_native_invocations=0,view=str(ROOT))
(HERE/LABEL).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('physical','builder_manifest','public')},indent=2))
