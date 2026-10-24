"""Synthetic receipt validation only; never runs a native driver."""
import json,os,sys,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=Path(os.environ.get('STUDY_REVIEW_SOURCE_ROOT','/workspace/reviews/windows-shutdown-study-independent-source-20261024'))
LABEL=os.environ.get('STUDY_REVIEW_RUN_LABEL','own-receipt-propagation')
sys.path.insert(0,str(ROOT/'scripts'))
import windows_shutdown_study as study
assert sorted(os.sched_getaffinity(0))==[4]
class Owner:
 def __init__(self):self.queries=[];self.cleaned=0
 def query(self,label):
  r=dict(label=label,verified=True,active_processes=1,process_ids=[99]);self.queries.append(r);return r
 def baseline_only(self,r):return r['verified'] and r['active_processes']==1 and r['process_ids']==[99]
 def safety_cleanup(self):self.cleaned+=1;raise AssertionError('missing receipts must not require process cleanup')
with tempfile.TemporaryDirectory() as td:
 calls=[];owner=Owner()
 def driver(args,callback,path):
  calls.append(args);path.mkdir();(path/'results.json').write_text('{"passed":true}\n')
 report=study.collect_trials(Path(td)/'out',{},owner,driver,identity_reader=lambda:{})
 result=dict(source='0f478a078277fdb0d711837bef67cf14262d9d8f',cpu=[4],native_invocations=0,
  input={'each_trial_files':{'results.json':'{"passed":true}\n'},'all_other_receipts_absent':True,'owner':'synthetic controller-only rows','identity':{}},
  expected_passed=False,actual_passed=report['passed'],calls=len(calls),cleanup_calls=owner.cleaned,report=report,
  interpretation='Synthetic missing-receipt trust-boundary false success; no source-emitted/native outcome claim')
 (HERE/(LABEL+'.json')).write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({k:v for k,v in result.items() if k not in ('report','input')}))
