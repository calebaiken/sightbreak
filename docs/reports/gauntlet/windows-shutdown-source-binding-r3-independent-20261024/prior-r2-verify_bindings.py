import hashlib,json,os,stat,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=Path(os.environ.get('BINDING_REVIEW_ROOT','/workspace/reviews/windows-shutdown-source-binding-r2-exact-20261024'))
BUILDER=Path('/workspace/sightbreak-windows-shutdown-source-binding-r2');PREFIX='docs/reports/gauntlet/windows-shutdown-source-binding-r2-20261024/'
SOURCE='b6da3aecfc2d88443c5e0757a9bd9320122a1d4d';HANDOFF='b69213b13a4503a330d283bf72565096e152f9d5';BASE='c90fedfd56a09bd0ba13cce5565ccd160891c3fb'
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def sha(b):return hashlib.sha256(b).hexdigest()
def tree(rev):
 result={}
 for line in git('ls-tree','-rz',rev).split(b'\0'):
  if line:
   identity,path=line.split(b'\t',1);result[path.decode()]=identity.decode()
 return result
m=json.loads(git('show',HANDOFF+':'+PREFIX+'MANIFEST.json'));outputs=[]
for name,rec in m['files'].items():
 b=git('show',HANDOFF+':'+PREFIX+name);actual=(BUILDER/PREFIX/name).read_bytes()
 assert len(b)==rec['bytes'] and sha(b)==rec['sha256'] and b==actual,name
 p=HERE/'builder-evidence-exact'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b);outputs.append(dict(path=name,**rec))
(HERE/'builder-evidence-exact/MANIFEST.json').write_bytes(git('show',HANDOFF+':'+PREFIX+'MANIFEST.json'))
old,new=tree(BASE),tree(SOURCE);delta=sorted(p for p in set(old)|set(new) if not p.startswith('docs/') and old.get(p)!=new.get(p))
assert delta==['scripts/shutdown_study_retention.py','scripts/test_shutdown_source_binding.py'],delta
physical=[]
for path,identity in new.items():
 if path.startswith('docs/'):continue
 p=ROOT/path;mode,kind,blob=identity.split();assert p.is_file() and not p.is_symlink();b=p.read_bytes();assert b==git('cat-file','blob',blob),path
 actual_mode='100755' if p.stat().st_mode&stat.S_IXUSR else '100644';assert actual_mode==mode,path
 physical.append(dict(path=path,identity=identity,bytes=len(b),sha256=sha(b),owner_exec_mode=actual_mode))
assert len(physical)==513
protected=[p for p in old if not p.startswith('docs/') and p!='scripts/shutdown_study_retention.py'];assert len(protected)==511 and all(new[p]==old[p] for p in protected)
all_protected=[p for p in old if p!='scripts/shutdown_study_retention.py'];assert all(new[p]==old[p] for p in all_protected)
assert git('rev-parse',BASE+':game')==git('rev-parse',SOURCE+':game')
assert not git('status','--porcelain','--untracked-files=all')
x=dict(source=SOURCE,handoff=HANDOFF,base=BASE,source_view=str(ROOT),source_status='clean',builder_outputs=outputs,physical_non_doc_count=len(physical),physical=physical,delta=delta,protected_non_doc_original=511,protected_all_original_path_identities=len(all_protected),game_default_driver_old_receipt_reader_workflow_exact=True,native_invocations=0)
(HERE/os.environ.get('BINDING_REVIEW_BINDINGS','BINDINGS.json')).write_text(json.dumps(x,indent=2)+'\n')
print(json.dumps({k:v for k,v in x.items() if k not in ('physical','builder_outputs')}))
