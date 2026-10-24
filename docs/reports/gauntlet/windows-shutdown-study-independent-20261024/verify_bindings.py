import hashlib,json,os,stat,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=Path('/workspace/reviews/windows-shutdown-study-independent-source-20261024')
BUILDER=Path('/workspace/sightbreak-windows-shutdown-bounded-study')
BASE='8ee93ac725d519c9f6d7f1ffbb3f7c9ee960baf8';SOURCE='c90fedfd56a09bd0ba13cce5565ccd160891c3fb';HANDOFF='239fa222ab2c34e6f9c640e468f8855e9163594d'
PREFIX='docs/reports/gauntlet/windows-shutdown-study-controller-20261024/'
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def sha(b):return hashlib.sha256(b).hexdigest()
def tree(rev):
 rows={}
 for row in git('ls-tree','-rz',rev).split(b'\0'):
  if row:
   identity,path=row.split(b'\t');rows[path.decode()]=identity.decode()
 return rows
manifest=json.loads(git('show',HANDOFF+':'+PREFIX+'MANIFEST.json'));evidence=[]
for rec in manifest['files']:
 name=rec['path'];b=git('show',HANDOFF+':'+PREFIX+name);actual=(BUILDER/PREFIX/name).read_bytes()
 assert len(b)==rec['bytes'] and sha(b)==rec['sha256'] and b==actual,name
 p=HERE/'builder-evidence-exact'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
 evidence.append(dict(**rec,actual_builder_equal_git=True))
(HERE/'builder-evidence-exact'/'MANIFEST.json').write_bytes(git('show',HANDOFF+':'+PREFIX+'MANIFEST.json'))
old,new=tree(BASE),tree(SOURCE)
changed=[p for p in old if new.get(p)!=old[p]]
assert changed==['scripts/verify_offline_export.py'],changed
assert len([p for p in new if not p.startswith('docs/')])==512
physical=[]
for p,identity in new.items():
 if p.startswith('docs/'):continue
 mode,kind,blob=identity.split();path=ROOT/p;b=path.read_bytes()
 assert b==git('cat-file','blob',blob),p
 actual_mode='100755' if path.stat().st_mode&0o111 else '100644';assert actual_mode==mode,(p,actual_mode,mode)
 physical.append(dict(path=p,identity=identity,physical_sha256=sha(b),physical_bytes=len(b),mode_verified=True))
protected=[p for p in old if p!='scripts/verify_offline_export.py'];assert all(new[p]==old[p] for p in protected)
assert git('rev-parse',BASE+':game')==git('rev-parse',SOURCE+':game')
# Direct physical default-hook erasure, same bounded labels but independent line operation.
b=(ROOT/'scripts/verify_offline_export.py').read_text();b=b.replace('def main(*, study_observer=None):','def main():')
lines=b.splitlines(keepends=True);out=[];i=0
while i<len(lines):
 line=lines[i]
 if '# BEGIN SHUTDOWN STUDY ' not in line:out.append(line);i+=1;continue
 label=line.split('# BEGIN SHUTDOWN STUDY ',1)[1].strip();i+=1
 while '# END SHUTDOWN STUDY '+label not in lines[i]:i+=1
 i+=1
 if label in ('INITIAL CLOSE','REOPENED CLOSE'):
  out.extend(x[4:] for x in lines[i:i+2]);i+=2
assert ''.join(out).encode()==git('show',BASE+':scripts/verify_offline_export.py')
result=dict(source=SOURCE,handoff=HANDOFF,base=BASE,actual_builder_manifest_members=len(evidence),evidence=evidence,
 non_doc_physical_count=len(physical),non_doc_physical=physical,protected_original_paths=len(protected),original_paths=len(old),
 game_tree_exact=True,default_driver_byte_erasure_exact=True,non_doc_delta=sorted(p for p in set(old)|set(new) if not p.startswith('docs/') and old.get(p)!=new.get(p)),
 actual_native_invocations=0)
(HERE/'BINDINGS.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ('evidence','non_doc_physical')},indent=2))
