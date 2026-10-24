"""Registered independent pure controls; no native driver or Windows API runs."""
import copy,hashlib,json,os,subprocess,sys,tempfile,zipfile
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;ROOT=Path(os.environ.get('STUDY_REVIEW_SOURCE_ROOT','/workspace/reviews/windows-shutdown-study-independent-source-20261024'))
SOURCE='c90fedfd56a09bd0ba13cce5565ccd160891c3fb'
sys.path.insert(0,str(ROOT/'scripts'))
import shutdown_study_retention as retention
import windows_shutdown_study as study
assert sorted(os.sched_getaffinity(0))==[4]
OUT=HERE/os.environ.get('STUDY_REVIEW_RUN_LABEL','own-fresh-controls-r2');OUT.mkdir(exist_ok=True)
records=[]
def save(name,value):
 (OUT/(name+'.json')).write_text(json.dumps(value,indent=2)+'\n');records.append(dict(name=name,**value))
def sha(b):return hashlib.sha256(b).hexdigest()
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
base=retention.source_binding(SOURCE,ROOT)
check=retention.preflight(SOURCE,ROOT)
save('clean_source_fixed_preflight',dict(expected_status='BLOCKED',actual=check,matched=check['status']=='BLOCKED' and check['execution_authorized'] is False))
# Actual public check; sentinels are independent of the fixed status return.
with patch.object(study,'WindowsOwner') as owner,patch.object(study,'real_driver') as driver,patch.object(study,'runtime_identity') as identity,patch.object(sys,'argv',['study','collect','--expected-source',SOURCE,'--output',str(OUT/'must-not-exist')]):
 try:study.main();error=None
 except RuntimeError as e:error=str(e)
 assert error and 'BLOCKED' in error
 owner.assert_not_called();driver.assert_not_called();identity.assert_not_called()
 save('public_collect_real_blocker',dict(expected='BLOCKED before owner/identity/driver',actual_error=error,owner_calls=owner.call_count,identity_calls=identity.call_count,driver_calls=driver.call_count,matched=True))
with patch.object(sys,'argv',['study','preflight','--expected-source',SOURCE,'--output',str(OUT/'real-preflight.json')]):
 try:study.main();code=0
 except SystemExit as e:code=e.code
save('public_preflight_exit',dict(expected_exit=2,actual_exit=code,matched=code==2))
# A physical file change hidden from ordinary Git status. Preserve both bytes.
p=ROOT/'scripts/shutdown_study_retention.py';original=p.read_bytes();flag_before=git('ls-files','-v','--',str(p.relative_to(ROOT))).decode()
changed=original+b'\n# Independent source-binding witness: materialized bytes differ.\n'
(OUT/'source-binding-original.py').write_bytes(original);(OUT/'source-binding-altered.py').write_bytes(changed)
for flag in ('skip-worktree','assume-unchanged'):
 try:
  git('update-index','--'+flag,'scripts/shutdown_study_retention.py');p.write_bytes(changed)
  status=git('status','--porcelain','--untracked-files=all').decode();flags=git('ls-files','-v','--','scripts/shutdown_study_retention.py').decode()
  try:actual=retention.source_binding(SOURCE,ROOT);error=None
  except ValueError as e:actual=None;error=str(e)
  save(flag+'_materialized_source_mismatch',dict(expected='REJECT materialized model-source byte mismatch',actual='ACCEPTED unchanged source identity' if actual else 'REJECTED',binding_equal_baseline=actual==base,git_status=status,index_flags=flags,original_bytes=len(original),altered_bytes=len(changed),original_sha256=sha(original),altered_sha256=sha(changed),binding=actual,error=error,matched=actual is None))
 finally:
  p.write_bytes(original);git('update-index','--no-'+flag,'scripts/shutdown_study_retention.py')
assert git('ls-files','-v','--','scripts/shutdown_study_retention.py').decode()==flag_before
assert not git('status','--porcelain','--untracked-files=all')
# Deliberately finite but not partitionable. Model-only is never execution.
m=retention.fixed_model()
for key in retention.BYTE_FAMILIES:m[key]=0
m.update(ocr_stdout_files=0,ocr_stdout_prefix_bytes=0,png_bytes=3*21*1024*1024//4,all_zip_headers_indexes_bytes=4096,largest_member_with_headers_bytes=21*1024*1024+256,complete_ocr_stdout_on_overflow=True)
a=retention.assess(m)
save('three_twenty_one_mib_model',dict(input=m,actual=a,mathematical_two_bin_feasible=False,reason='Three indivisible21MiB members; each bin holds at most one.',execution_authorized=a['execution_authorized'],interpretation='RETENTION_MODEL_ONLY lacks bin proof; not public ADMITTED',matched=a['status']=='RETENTION_MODEL_ONLY' and not a['execution_authorized']))
with tempfile.TemporaryDirectory() as td:
 root=Path(td);source=root/'raw';source.mkdir()
 for i in range(3):(source/str(i)).write_bytes(b'\0'*(21*1024*1024))
 before=retention.inventory(source)
 try:retention.complete_archives(source,root/'archives');error=None
 except ValueError as e:error=str(e)
 save('three_twenty_one_mib_actual_pack',dict(inputs=before,error=error,output_published=(root/'archives').exists(),originals_unchanged=before==retention.inventory(source),matched=error is not None and not(root/'archives').exists()))
with tempfile.TemporaryDirectory() as td:
 root=Path(td);source=root/'raw';source.mkdir();p=source/'boundary.bin';cap=retention.ARCHIVE_BYTES;size=cap-2048
 p.write_bytes(b'\0'*size);first=retention.complete_archives(source,root/'first');actual=max(first,key=lambda r:r['bytes'])['bytes'];size+=cap-1-actual
 p.write_bytes(b'\0'*size);second=retention.complete_archives(source,root/'second');inner=max(second,key=lambda r:r['bytes'])
 with zipfile.ZipFile(root/'outer.zip','w',compression=zipfile.ZIP_STORED) as z:z.write(inner['path'],'evidence-1.zip')
 outer=(root/'outer.zip').stat().st_size
 save('outer_wrapper_boundary',dict(input=dict(path='boundary.bin',bytes=size,repeated_byte_hex='00',sha256=sha(p.read_bytes())),inner_bytes=inner['bytes'],outer_bytes=outer,limit=cap,inner_fits=inner['bytes']<=cap,outer_fits=outer<=cap,wrapper_assumption='Synthetic STORED outer ZIP with one actual inner ZIP; not an observed GitHub artifact',matched=inner['bytes']<=cap and outer>cap))
# Incomplete synthetic evidence and paired strict-failure controls.
with tempfile.TemporaryDirectory() as td:
 root=Path(td);(root/'results.json').write_text('{"passed":true}\n')
 missing=study.trial_evidence(root)
 save('optimistic_result_missing_required_evidence',dict(files={'results.json':'{"passed":true}\n'},actual=missing,expected='incomplete evidence cannot independently substantiate source-faithful success',interpretation='Evidence-reader trust boundary; not claimed source-emittable passed native output',matched=not missing['strict_passed']))
 (root/'reopened.log').write_text('WARNING: ObjectDB instances leaked at exit\n');warn=study.trial_evidence(root)
 save('strict_warning_in_present_log',dict(actual=warn,matched=not warn['strict_passed']))
 (root/'reopened.log').write_text('');(root/'results.json').write_text(json.dumps(dict(passed=True,ocr_commands=[dict(stdout_complete=False,stdout_truncated=True)])))
 trunc=study.trial_evidence(root);save('truncated_ocr_with_passed_result',dict(actual=trunc,matched=not trunc['strict_passed']))
# Actual pure orchestration with driver errors vs optimistic receipts.
class Owner:
 def __init__(self,final_fail=False):self.queries=[];self.cleaned=0;self.final_fail=final_fail
 def query(self,label):
  row=dict(label=label,verified=True,active_processes=1,process_ids=[99]);self.queries.append(row)
  if label=='study/final' and self.final_fail:raise RuntimeError('independent final unknown')
  return row
 def baseline_only(self,row):return row.get('verified') and row.get('active_processes')==1 and row.get('process_ids')==[99]
 def safety_cleanup(self):self.cleaned+=1;return dict(passed=True,failure_only=True)
for final_fail in (False,True):
 with tempfile.TemporaryDirectory() as td:
  owner=Owner(final_fail);calls=[]
  def driver(args,callback,path):calls.append(args);path.mkdir();raise RuntimeError('independent original flow failure')
  r=study.collect_trials(Path(td)/'out',{},owner,driver,identity_reader=lambda:{},load_evidence=lambda _:dict(strict_passed=True))
  save('driver_failure_final_'+str(final_fail),dict(report=r,cleanup_calls=owner.cleaned,matched=not r['passed'] and len(calls)==4 and owner.cleaned==int(final_fail)))
(OUT/'SUMMARY.json').write_text(json.dumps(dict(source=SOURCE,cpu=[4],native_invocations=0,controls=len(records),unmatched=[r['name'] for r in records if not r['matched']],results=records),indent=2)+'\n')
print(json.dumps(dict(controls=len(records),unmatched=[r['name'] for r in records if not r['matched']],native_invocations=0)))
