#!/usr/bin/env python3
import argparse,hashlib,json,os,subprocess
from pathlib import Path
SOURCE='2d4214c4d3314df568796f0a6f3a38fc357db318'
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--dest',type=Path,required=True);a=p.parse_args();assert not a.dest.exists() and sorted(os.sched_getaffinity(0))==[4]
def src(*words):return subprocess.check_output(['git','-C',str(a.root),*words])
objects={SOURCE,src('rev-parse',SOURCE+'^{tree}').decode().strip()};paths=[]
for item in src('ls-tree','-rtz',SOURCE).split(b'\0'):
 if item:
  info,path=item.split(b'\t');mode,kind,oid=info.decode().split();path=path.decode()
  if kind=='tree':objects.add(oid)
  elif not path.startswith('docs/') or path.startswith(('docs/reports/media/art-v9/hands/logs/','docs/reports/gauntlet/native-layout-ocr/','docs/reports/gauntlet/windows-input-consumption-r7-expiry-builder-tests-20261024/','docs/reports/gauntlet/windows-input-consumption-r7-absorbing-lifecycle-20261024/')):objects.add(oid);paths.append(path)
pack=subprocess.run(['git','-C',str(a.root),'pack-objects','--stdout','--threads=1'],input=('\n'.join(sorted(objects))+'\n').encode(),capture_output=True,check=True).stdout
subprocess.run(['git','init','--quiet','--initial-branch=review',str(a.dest)],check=True);subprocess.run(['git','-C',str(a.dest),'index-pack','--stdin'],input=pack,capture_output=True,check=True);(a.dest/'.git/shallow').write_text(SOURCE+'\n')
def run(*words):return subprocess.check_output(['git','-C',str(a.dest),*words])
run('update-ref','refs/heads/review',SOURCE);run('config','core.sparseCheckout','true');run('config','core.sparseCheckoutCone','false');(a.dest/'.git/info/sparse-checkout').write_text('\n'.join('/'+path for path in paths)+'\n');run('read-tree','-mu','HEAD');run('restore','--source=HEAD','--worktree','--','.')
parent=src('rev-parse',SOURCE+'^').decode().strip();probe=subprocess.run(['git','-C',str(a.dest),'cat-file','-e',parent+'^{commit}'],capture_output=True)
assert not run('status','--short') and not run('remote','-v') and probe.returncode==128 and not (a.dest/'.git/objects/info/alternates').exists() and not os.environ.get('GIT_ALTERNATE_OBJECT_DIRECTORIES')
assert run('rev-parse','HEAD').decode().strip()==SOURCE and run('rev-parse','--is-shallow-repository').decode().strip()=='true' and run('rev-list','--count','HEAD').decode().strip()=='1'
assert len(run('ls-files','-z').split(b'\0'))-1==16716
print(json.dumps({'source':SOURCE,'depth':str(a.dest),'clean':True,'shallow':True,'reachable_commits':1,'parent':parent,'parent_exit':probe.returncode,'parent_stderr':probe.stderr.decode(),'remotes':[],'alternates_present':False,'alternate_environment_set':False,'tracked_index_paths':16716,'pack_bytes':len(pack),'pack_sha256':hashlib.sha256(pack).hexdigest(),'local_bounded_object_transfer':True,'network_clone':False,'cpu_affinity':[4],'native_executed':False},indent=2))
