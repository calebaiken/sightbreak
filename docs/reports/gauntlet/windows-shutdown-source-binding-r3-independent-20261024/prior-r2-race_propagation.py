import json,os,subprocess,sys,tempfile
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;ROOT=Path(os.environ.get('BINDING_REVIEW_ROOT','/workspace/reviews/windows-shutdown-source-binding-r2-exact-20261024'))
sys.path.insert(0,str(ROOT/'scripts'))
import shutdown_study_retention as r
assert sorted(os.sched_getaffinity(0))==[4]
def git(root,*args):return subprocess.check_output(['git',*args],cwd=root,stderr=subprocess.PIPE)
with tempfile.TemporaryDirectory() as td:
 root=Path(td);git(root,'init','-q');git(root,'config','core.autocrlf','false')
 expected=b'original bytes\n';changed=b'changed! bytes\n';files={p:b'fixture\n' for p in r.MODEL_PATHS};files['runtime/race.txt']=expected
 for name,data in files.items():p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data);p.chmod(0o644)
 git(root,'add','.');git(root,'-c','user.name=Independent Reviewer','-c','user.email=review@example.invalid','commit','-qm','registered full binding race fixture');rev=git(root,'rev-parse','HEAD').decode().strip()
 q=root/'runtime/race.txt';before=q.stat();real_read=Path.read_bytes
 def raced(p):
  data=real_read(p)
  if p==q:p.write_bytes(changed);os.utime(p,ns=(before.st_atime_ns,before.st_mtime_ns))
  return data
 with patch.object(Path,'read_bytes',raced):
  try:binding=r.source_binding(rev,root);error=None
  except (ValueError,OSError,UnicodeError) as e:binding=None;error=type(e).__name__+': '+str(e)
 after=q.stat();current=q.read_bytes()
 result=dict(source='b6da3aecfc2d88443c5e0757a9bd9320122a1d4d',cpu=[4],native_invocations=0,expected='REJECT',actual='BIND' if binding else 'REJECT',error=error,
  input={name:data.hex() for name,data in files.items()},changed_bytes_hex=changed.hex(),current_bytes_hex=current.hex(),
  before=dict(inode=before.st_ino,size=before.st_size,mtime_ns=before.st_mtime_ns,ctime_ns=before.st_ctime_ns),after=dict(inode=after.st_ino,size=after.st_size,mtime_ns=after.st_mtime_ns,ctime_ns=after.st_ctime_ns),
  returned_binding=binding,git_status_after=git(root,'status','--porcelain','--untracked-files=all').decode(),scope='Mutation within physical helper read call; not whole-filesystem atomicity')
 (HERE/os.environ.get('BINDING_REVIEW_RACE','own-race-propagation.json')).write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({k:v for k,v in result.items() if k not in ('input','returned_binding')}))
