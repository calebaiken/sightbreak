import ast,hashlib,json,os,stat,subprocess
from pathlib import Path
ROOT=Path.cwd();OUT=ROOT/'.local/frozen-evidence-completeness';BASE='1add0f828b26b86b9bc2ec9e02c4208e31bb2e5a';SOURCE='0f478a078277fdb0d711837bef67cf14262d9d8f'
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def sha(b):return hashlib.sha256(b).hexdigest()
def tree(rev):
 result={}
 for line in git('ls-tree','-rz',rev).split(b'\0'):
  if line:
   identity,path=line.split(b'\t',1);result[path.decode()]=identity.decode()
 return result
old,new=tree(BASE),tree(SOURCE);delta=sorted(p for p in set(old)|set(new) if not p.startswith('docs/') and old.get(p)!=new.get(p))
expected=['scripts/shutdown_evidence_fixtures.py','scripts/shutdown_study_evidence.py','scripts/test_shutdown_study_evidence.py','scripts/test_windows_shutdown_study.py','scripts/windows_shutdown_study.py'];assert delta==expected,delta
files=[]
for name,identity in new.items():
 if name.startswith('docs/'):continue
 mode,kind,blob=identity.split();p=ROOT/name;need=p.lstat();assert stat.S_ISREG(need.st_mode) and not p.is_symlink(),name
 b=p.read_bytes();assert b==git('cat-file','blob',blob),name
 actual_mode='100755' if need.st_mode&stat.S_IXUSR else '100644';assert mode==actual_mode,name
 files.append(dict(path=name,identity=identity,bytes=len(b),sha256=sha(b),physical_mode=actual_mode))
assert len(files)==516
protected=[name for name in old if not name.startswith('docs/') and name not in expected];assert len(protected)==511 and all(old[name]==new[name] for name in protected)
allprotected=[name for name in old if name not in expected];assert all(old[name]==new[name] for name in allprotected)
assert git('rev-parse',BASE+':game')==git('rev-parse',SOURCE+':game')
def section(source,name):
 lines=source.splitlines(keepends=True);node=next(n for n in ast.parse(source).body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name==name);return ''.join(lines[node.lineno-1:node.end_lineno])
a=git('show',BASE+':scripts/windows_shutdown_study.py').decode();b=(ROOT/'scripts/windows_shutdown_study.py').read_text()
unchanged=['WindowsOwner','driver_arguments','typed_leak_rows','embedded_pck_identity','runtime_identity','main'];assert all(section(a,name)==section(b,name) for name in unchanged)
a=git('show',BASE+':scripts/test_windows_shutdown_study.py').decode();b=(ROOT/'scripts/test_windows_shutdown_study.py').read_text()
def tests(source):return {n.name:ast.dump(n,include_attributes=False) for n in ast.walk(ast.parse(source)) if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')}
assert len(tests(a))==28 and tests(a)==tests(b) and section(a,'Owner')==section(b,'Owner')
count=sum(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr.startswith('assert') for m in ast.walk(ast.parse(a)) if isinstance(m,ast.FunctionDef) and m.name.startswith('test_') for n in ast.walk(m));assert count==113
proposal=(ROOT/'docs/reports/gauntlet/windows-shutdown-evidence-completeness-20261024/OLD28_HELPER_PROPOSAL_V3.py').read_text()
original_helper=next(n for n in ast.walk(ast.parse(b)) if isinstance(n,ast.FunctionDef) and n.name=='run_generated');proposed=next(n for n in ast.parse(proposal).body if isinstance(n,ast.FunctionDef));assert ast.dump(original_helper,include_attributes=False)==ast.dump(proposed,include_attributes=False)
summary=dict(source=SOURCE,base=BASE,delta=delta,non_doc_paths=len(files),physical=files,protected_original_non_doc=len(protected),protected_all_original_paths=len(allprotected),game_tree_exact=True,default_driver_bindingR3_workflow_exact=True,unchanged_study_sections=unchanged,old_test_methods=28,old_assertions=113,all_old_test_method_asts_exact=True,old_owner_bytes_exact=True,helper_matches_independently_adjudicated_v3=True,construction_adjudication='f76df6387834dfd791b7686d63f1576ad008bfe4',native_invocations=0,cpu=sorted(os.sched_getaffinity(0)),view=str(ROOT))
assert not git('status','--porcelain','--untracked-files=all')
(OUT/'SOURCE_UNION.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({k:v for k,v in summary.items() if k!='physical'},indent=2))
