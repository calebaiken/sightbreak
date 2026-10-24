#!/usr/bin/env python3
"""Initialize one-commit local source view without remotes, parents or alternates."""
import argparse, hashlib, json, os, subprocess
from pathlib import Path
SOURCE='4cf6ac8e744603ed6af122a362036d276754cc76'
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--dest',type=Path,required=True);a=p.parse_args()
assert sorted(os.sched_getaffinity(0))==[4]
root=a.root.resolve();dest=a.dest.resolve();assert not dest.exists()
def git(*args,**kwargs):return subprocess.check_output(['git','-C',str(root),*args],**kwargs)
objects={SOURCE,git('rev-parse',SOURCE+'^{tree}').decode().strip()};paths=[]
for entry in git('ls-tree','-rtz',SOURCE).split(b'\0'):
 if not entry:continue
 meta,path=entry.split(b'\t');mode,kind,oid=meta.decode().split();path=path.decode()
 if kind=='tree':objects.add(oid)
 elif not path.startswith('docs/') or path.startswith(('docs/engineering/','docs/roadmap/','docs/reports/gauntlet/windows-route-clock-boundary-20261024/')):
  objects.add(oid);paths.append(path)
pack=subprocess.run(['git','-C',str(root),'pack-objects','--stdout'],input=('\n'.join(sorted(objects))+'\n').encode(),capture_output=True,check=True).stdout
dest.mkdir();subprocess.run(['git','init','--quiet',str(dest)],check=True)
subprocess.run(['git','-C',str(dest),'index-pack','--stdin'],input=pack,capture_output=True,check=True)
(dest/'.git/shallow').write_text(SOURCE+'\n')
subprocess.run(['git','-C',str(dest),'update-ref','refs/heads/review',SOURCE],check=True)
subprocess.run(['git','-C',str(dest),'symbolic-ref','HEAD','refs/heads/review'],check=True)
subprocess.run(['git','-C',str(dest),'read-tree','HEAD'],check=True)
subprocess.run(['git','-C',str(dest),'sparse-checkout','init','--cone'],check=True)
subprocess.run(['git','-C',str(dest),'sparse-checkout','set','.claude','.github','backend','game','scripts','server','tools','docs/engineering','docs/roadmap','docs/reports/gauntlet/windows-route-clock-boundary-20261024'],check=True)
subprocess.run(['git','-C',str(dest),'restore','--source=HEAD','--worktree','--','.'],check=True)
print(json.dumps({'source':SOURCE,'destination':str(dest),'objects':len(objects),'materialization_paths':len(paths),'pack_bytes':len(pack),'pack_sha256':hashlib.sha256(pack).hexdigest(),'local_object_transfer':True,'network_clone':False,'native_executed':False},indent=2))
