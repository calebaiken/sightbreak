#!/usr/bin/env python3
"""Exact one-commit local source transfer; no ancestor, remote or alternate."""
import argparse,hashlib,json,os,subprocess
from pathlib import Path
SOURCE='7d8ec7dda37764e0f45fd2ea1e8d330f84bc2508'
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--dest',type=Path,required=True);a=p.parse_args()
root=a.root.resolve();dest=a.dest.resolve();assert not dest.exists() and sorted(os.sched_getaffinity(0))==[4]
def src(*args):return subprocess.check_output(['git','-C',str(root),*args])
objects={SOURCE,src('rev-parse',SOURCE+'^{tree}').decode().strip()};paths=[]
for item in src('ls-tree','-rtz',SOURCE).split(b'\0'):
 if not item:continue
 meta,path=item.split(b'\t');mode,kind,blob=meta.decode().split();path=path.decode()
 if kind=='tree':objects.add(blob)
 elif not path.startswith('docs/') or path.startswith(('docs/engineering/','docs/roadmap/','docs/reports/gauntlet/windows-input-consumption-r5-20261024/')):objects.add(blob);paths.append(path)
pack=subprocess.run(['git','-C',str(root),'pack-objects','--stdout','--threads=1'],input=('\n'.join(sorted(objects))+'\n').encode(),capture_output=True,check=True).stdout
subprocess.run(['git','init','--quiet','--initial-branch=review',str(dest)],check=True)
subprocess.run(['git','-C',str(dest),'index-pack','--stdin'],input=pack,capture_output=True,check=True)
(dest/'.git/shallow').write_text(SOURCE+'\n')
def run(*args):return subprocess.check_output(['git','-C',str(dest),*args])
run('update-ref','refs/heads/review',SOURCE)
run('config','core.sparseCheckout','true');run('config','core.sparseCheckoutCone','false')
(dest/'.git/info/sparse-checkout').write_text('\n'.join('/'+path for path in paths)+'\n')
run('read-tree','-mu','HEAD');run('restore','--source=HEAD','--worktree','--','.')
parent=subprocess.run(['git','-C',str(dest),'cat-file','-e','09b476ae79c2d6158b811d7e743f814078f81036^{commit}'],capture_output=True)
assert run('rev-parse','HEAD').decode().strip()==SOURCE and run('rev-parse','--is-shallow-repository').decode().strip()=='true' and run('rev-list','--count','HEAD').decode().strip()=='1'
assert not run('status','--short') and not run('remote','-v') and parent.returncode==128 and not (dest/'.git/objects/info/alternates').exists() and not os.environ.get('GIT_ALTERNATE_OBJECT_DIRECTORIES')
print(json.dumps({'source':SOURCE,'path':str(dest),'clean':True,'shallow':True,'reachable_commits':1,'parent_exit':parent.returncode,'parent_stderr':parent.stderr.decode(),'remotes':[],'alternates_present':False,'alternate_environment_set':False,'tracked_index_paths':len(run('ls-files','-z').split(b'\0'))-1,'pack_bytes':len(pack),'pack_sha256':hashlib.sha256(pack).hexdigest(),'local_object_transfer':True,'network_clone':False,'cpu_affinity':[4],'native_executed':False},indent=2))
