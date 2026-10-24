#!/usr/bin/env python3
import argparse,json,os,subprocess
from pathlib import Path
SOURCE='4cf6ac8e744603ed6af122a362036d276754cc76'
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--dest',type=Path,required=True);p.add_argument('--evidence',type=Path,required=True);a=p.parse_args()
assert sorted(os.sched_getaffinity(0))==[4]
root=a.root.resolve();dest=a.dest.resolve();ev=a.evidence.resolve()
r=subprocess.run(['git','-C',str(dest),'status','--short'],capture_output=True)
(ev/'depth-setup-initial-status.txt').write_bytes(r.stdout);(ev/'depth-setup-initial-status.stderr').write_bytes(r.stderr)
paths=[]
for entry in subprocess.check_output(['git','-C',str(root),'ls-tree','-rz',SOURCE]).split(b'\0'):
 if not entry:continue
 _,path=entry.split(b'\t');path=path.decode()
 if not path.startswith('docs/') or path.startswith(('docs/engineering/','docs/roadmap/','docs/reports/gauntlet/windows-route-clock-boundary-20261024/')):paths.append(path)
subprocess.run(['git','-C',str(dest),'config','--worktree','core.sparseCheckout','true'],check=True)
subprocess.run(['git','-C',str(dest),'config','--worktree','core.sparseCheckoutCone','false'],check=True)
(dest/'.git/info/sparse-checkout').write_text('\n'.join('/'+path for path in paths)+'\n')
subprocess.run(['git','-C',str(dest),'read-tree','-mu','HEAD'],check=True)
def git(*args):return subprocess.check_output(['git','-C',str(dest),*args],text=True).strip()
parent=subprocess.run(['git','-C',str(dest),'cat-file','-e','e46680e4acd849c8d8e8125ed4b0a27c9e751320^{commit}'],capture_output=True)
assert git('rev-parse','HEAD')==SOURCE and git('rev-parse','--is-shallow-repository')=='true' and git('rev-list','--count','HEAD')=='1' and not git('status','--short')
print(json.dumps({'source':SOURCE,'destination':str(dest),'head':git('rev-parse','HEAD'),'shallow':True,'reachable_commits':1,'remotes':git('remote','-v'),'alternates_present':(dest/'.git/objects/info/alternates').exists(),'git_alternate_object_directories_set':bool(os.environ.get('GIT_ALTERNATE_OBJECT_DIRECTORIES')),'parent_exit':parent.returncode,'parent_stderr':parent.stderr.decode(),'paths_materialized':len(paths),'pack_bytes':sum(f.stat().st_size for f in (dest/'.git/objects/pack').glob('*.pack')),'status':git('status','--short'),'network_clone':False,'native_executed':False},indent=2))
