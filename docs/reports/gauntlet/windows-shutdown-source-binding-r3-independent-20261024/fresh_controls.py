"""Preregistered physical-binding controls only; no native/API process runs."""
import json,os,subprocess,sys,tempfile
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
ROOT=Path(os.environ.get('BINDING_REVIEW_ROOT','/workspace/reviews/windows-shutdown-source-binding-r3-exact-20261024'))
OUT=HERE/os.environ.get('BINDING_REVIEW_OUTPUT','own-controls');OUT.mkdir(exist_ok=True)
SOURCE='ebc1a94133d4d73c3a553d528986c8fc40c740a9'
sys.path.insert(0,str(ROOT/'scripts'))
import shutdown_study_retention as r
import windows_shutdown_study as study
assert sorted(os.sched_getaffinity(0))==[4]
rows=[]
def save(name,expected,actual,**details):
 x=dict(name=name,expected=expected,actual=actual,matched=expected==actual,**details);rows.append(x)
 (OUT/(name+'.json')).write_text(json.dumps(x,indent=2)+'\n')
def git(root,*args):return subprocess.check_output(['git',*args],cwd=root,stderr=subprocess.PIPE)
def rejected(call):
 try:return False,call(),None
 except (ValueError,UnicodeError,OSError) as e:return True,None,type(e).__name__+': '+str(e)
base=r.source_binding(SOURCE,ROOT);save('clean_exact_source','BIND','BIND' if len(base['physical_sources'])==513 else 'WRONG_COUNT',binding=base)
pre=r.preflight(SOURCE,ROOT);save('fixed_preflight','BLOCKED',pre['status'],execution_authorized=pre['execution_authorized'])
with patch.object(study,'WindowsOwner') as owner,patch.object(study,'runtime_identity') as identity,patch.object(study,'real_driver') as driver,patch.object(sys,'argv',['study','collect','--expected-source',SOURCE,'--output',str(OUT/'unreached')]):
 try:study.main();error=None
 except RuntimeError as e:error=str(e)
 owner.assert_not_called();identity.assert_not_called();driver.assert_not_called()
 save('public_collect','BLOCKED','BLOCKED' if error and 'BLOCKED' in error else str(error),owner_calls=owner.call_count,identity_calls=identity.call_count,driver_calls=driver.call_count)
# Exact original supported marker, now applied to the candidate's file.
p=ROOT/'scripts/shutdown_study_retention.py';old=p.read_bytes();new=old+b'\n# Independent source-binding witness: materialized bytes differ.\n'
for flag in ('assume-unchanged','skip-worktree'):
 try:
  git(ROOT,'update-index','--'+flag,'scripts/shutdown_study_retention.py');p.write_bytes(new)
  status=git(ROOT,'status','--porcelain','--untracked-files=all').decode();bad,receipt,error=rejected(lambda:r.source_binding(SOURCE,ROOT))
  save('original_marker_'+flag,'REJECT','REJECT' if bad else 'BIND',git_status=status,original_sha256=r.sha(old),altered_sha256=r.sha(new),appended_bytes_hex=new[len(old):].hex(),error=error,receipt=receipt)
 finally:p.write_bytes(old);git(ROOT,'update-index','--no-'+flag,'scripts/shutdown_study_retention.py')
assert not git(ROOT,'status','--porcelain','--untracked-files=all')
with tempfile.TemporaryDirectory() as td:
 root=Path(td);files={name:b'canonical model\n' for name in r.MODEL_PATHS}
 files.update({'runtime/space source.txt':b'spaces\n','runtime/tab\tname.txt':b'tab\n','runtime/line\nname.txt':b'newline\n','runtime/Unicode-\u03b1.txt':b'unicode\n','runtime/executable.py':b'executable\n','.gitattributes':b'runtime/space* filter=disabled_optional_filter\n'})
 git(root,'init','-q');git(root,'config','core.autocrlf','false');git(root,'config','core.filemode','true')
 for name,data in files.items():q=root/name;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data);q.chmod(0o755 if name.endswith('executable.py') else 0o644)
 git(root,'add','.');git(root,'-c','user.name=Independent Reviewer','-c','user.email=review@example.invalid','commit','-qm','registered independent fixture')
 rev=git(root,'rev-parse','HEAD').decode().strip();fixture=r.source_binding(rev,root)
 save('nul_path_parser_and_modes','BIND','BIND' if set(fixture['physical_sources'])==set(files) else 'WRONG_PATHS',files={k:v.hex() for k,v in files.items()},binding=fixture)
 for name in ('scripts/shutdown_study_retention.py','runtime/space source.txt'):
  q=root/name
  for flag in ('assume-unchanged','skip-worktree'):
   try:
    git(root,'update-index','--'+flag,name);q.write_bytes(b'changed physical bytes\n');bad,rec,error=rejected(lambda:r.source_binding(rev,root))
    save('hidden_'+str(len(rows)),'REJECT','REJECT' if bad else 'BIND',name_under_test=name,flag=flag,error=error,receipt=rec)
   finally:q.write_bytes(files[name]);git(root,'update-index','--no-'+flag,name)
 name='runtime/space source.txt';q=root/name
 for kind in ('missing','symlink'):
  try:
   git(root,'update-index','--assume-unchanged',name);q.unlink()
   if kind=='symlink':q.symlink_to(root/'scripts/shutdown_study_retention.py')
   bad,rec,error=rejected(lambda:r.source_binding(rev,root));save(kind+'_source','REJECT','REJECT' if bad else 'BIND',error=error,receipt=rec)
  finally:
   if q.is_symlink():q.unlink()
   q.write_bytes(files[name]);git(root,'update-index','--no-assume-unchanged',name)
 for name,mode in (('runtime/space source.txt',0o755),('runtime/executable.py',0o644)):
  q=root/name;prior=q.stat().st_mode
  try:
   git(root,'update-index','--assume-unchanged',name);q.chmod(mode);bad,rec,error=rejected(lambda:r.source_binding(rev,root))
   save('mode_'+str(len(rows)),'REJECT','REJECT' if bad else 'BIND',name_under_test=name,changed_mode=oct(mode),error=error,receipt=rec)
  finally:q.chmod(prior);git(root,'update-index','--no-assume-unchanged',name)
 q=root/'runtime/space source.txt'
 for label,expected,actual,windows,accept in (
  ('windows_crlf',b'alpha\nbeta\n',b'alpha\r\nbeta\r\n',True,True),
  ('equal_binary',b'\0\xff\r\n',b'\0\xff\r\n',True,True),
  ('linux_crlf',b'alpha\nbeta\n',b'alpha\r\nbeta\r\n',False,False),
  ('partial_crlf',b'alpha\nbeta\n',b'alpha\r\nbeta\n',True,False),
  ('nul_conversion',b'\0\n',b'\0\r\n',True,False),
  ('invalid_utf8',b'\xff\n',b'\xff\r\n',True,False),
  ('existing_cr',b'alpha\rbeta\n',b'alpha\rbeta\r\n',True,False)):
  q.write_bytes(actual);bad,rec,error=rejected(lambda:r.physical_source_file(q,expected,'100644',windows=windows))
  save(label,'BIND' if accept else 'REJECT','REJECT' if bad else 'BIND',expected_bytes_hex=expected.hex(),actual_bytes_hex=actual.hex(),windows=windows,receipt=rec,error=error)
 # Same-call actual reads followed by real mutations; no fabricated read bytes.
 expected=b'original bytes\n';changed=b'changed! bytes\n';assert len(expected)==len(changed)
 real_read=Path.read_bytes
 for restore_mtime in (False,True):
  q.write_bytes(expected);before=q.stat()
  def raced(path):
   data=real_read(path)
   if path==q:
    path.write_bytes(changed)
    if restore_mtime:os.utime(path,ns=(before.st_atime_ns,before.st_mtime_ns))
   return data
  with patch.object(Path,'read_bytes',raced):bad,rec,error=rejected(lambda:r.physical_source_file(q,expected,'100644'))
  after=q.stat();actual=q.read_bytes()
  save('read_race_restore_mtime_'+str(restore_mtime),'REJECT','REJECT' if bad else 'BIND',expected_bytes_hex=expected.hex(),current_bytes_hex=actual.hex(),before=dict(size=before.st_size,mtime_ns=before.st_mtime_ns,ctime_ns=before.st_ctime_ns,ino=before.st_ino),after=dict(size=after.st_size,mtime_ns=after.st_mtime_ns,ctime_ns=after.st_ctime_ns,ino=after.st_ino),receipt=rec,error=error,scope='Same-call mutation after an actual read; not a whole-filesystem atomicity claim')
(OUT/'SUMMARY.json').write_text(json.dumps(dict(source=SOURCE,cpu=[4],native_invocations=0,controls=len(rows),unmatched=[x['name'] for x in rows if not x['matched']],results=rows),indent=2)+'\n')
print(json.dumps(dict(controls=len(rows),unmatched=[x['name'] for x in rows if not x['matched']],native_invocations=0)))
