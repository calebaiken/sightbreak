import json,os,stat,sys,tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;ROOT=Path(os.environ.get('BINDING_REVIEW_ROOT','/workspace/reviews/windows-shutdown-source-binding-r3-exact-20261024'))
sys.path.insert(0,str(ROOT/'scripts'))
import shutdown_study_retention as r
assert sorted(os.sched_getaffinity(0))==[4]
rows=[]
def record(name,expect,call,details):
 try:receipt=call();actual='BIND';error=None
 except (ValueError,OSError,UnicodeError) as e:receipt=None;actual='REJECT';error=type(e).__name__+': '+str(e)
 rows.append(dict(name=name,expected=expect,actual=actual,matched=expect==actual,receipt=receipt,error=error,**details))
with tempfile.TemporaryDirectory() as td:
 p=Path(td)/'source.py';expected=b'original bytes\n';changed=b'changed! bytes\n';read=Path.read_bytes;lstat=Path.lstat
 for action in ('unchanged','first_edit','second_edit','constant_metadata_edit','second_error','second_delete'):
  p.write_bytes(expected);p.chmod(0o644);before=p.lstat();counts={'reads':0}
  def observed(q):
   if q!=p:return read(q)
   counts['reads']+=1
   if action=='second_error' and counts['reads']==2:raise OSError('injected second read error')
   data=read(q)
   if (action in ('first_edit','constant_metadata_edit') and counts['reads']==1) or (action=='second_edit' and counts['reads']==2):
    q.write_bytes(changed);os.utime(q,ns=(before.st_atime_ns,before.st_mtime_ns))
   if action=='second_delete' and counts['reads']==2:q.unlink()
   return data
  def metadata(q,*args,**kwargs):return before if q==p and action=='constant_metadata_edit' else lstat(q,*args,**kwargs)
  with patch.object(Path,'read_bytes',observed),patch.object(Path,'lstat',metadata):
   record(action,'BIND' if action=='unchanged' else 'REJECT',lambda:r.physical_source_file(p,expected,'100644'),dict(input_hex=expected.hex(),mutated_hex=changed.hex(),counts=counts))
 for field in ('st_ino','st_size','st_mtime_ns','st_ctime_ns','st_mode','st_atime_ns'):
  p.write_bytes(expected);p.chmod(0o644);before=p.lstat();calls={'lstat':0}
  values={key:getattr(before,key) for key in ('st_dev','st_ino','st_size','st_mtime_ns','st_ctime_ns','st_mode','st_atime_ns')}
  changed_meta=values.copy();changed_meta[field]=values[field]^stat.S_IXUSR if field=='st_mode' else values[field]+1
  def metadata(q,*args,**kwargs):
   if q!=p:return lstat(q,*args,**kwargs)
   calls['lstat']+=1
   return SimpleNamespace(**(changed_meta if calls['lstat']>=4 else values))
  with patch.object(Path,'lstat',metadata):
   record('final_'+field,'BIND' if field=='st_atime_ns' else 'REJECT',lambda:r.physical_source_file(p,expected,'100644'),dict(metadata_before=values,metadata_final=changed_meta,calls=calls))
 p.write_bytes(b'alpha\r\nbeta\r\n')
 record('bounded_windows_scope','BIND',lambda:r.physical_source_file(p,b'alpha\nbeta\n','100644',windows=True),dict(input_hex=p.read_bytes().hex()))
for row in rows:
 if row['actual']=='BIND':assert row['receipt']['read_observations']==2
 if row['name']=='bounded_windows_scope':assert row['receipt']['physical_mode'] is None and row['receipt']['change_metadata_scope']=='Windows NTFS ChangeTime unmeasured'
result=dict(source='ebc1a94133d4d73c3a553d528986c8fc40c740a9',cpu=[4],native_invocations=0,controls=len(rows),unmatched=[x['name'] for x in rows if not x['matched']],results=rows)
(HERE/os.environ.get('BINDING_REVIEW_SECOND','own-second-read-controls.json')).write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='results'}))
