#!/usr/bin/env python3
import argparse,gzip,hashlib,json,os,sys,unittest
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert sorted(os.sched_getaffinity(0))==[4];root=a.source.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False);os.chdir(root);sys.path.insert(0,str(root/'scripts'))
reader=root/'scripts/analyze_input_consumption.py';assert hashlib.sha256(reader.read_bytes()).hexdigest()=='104d998dc504e30fb6702426025b611aa5ee86390a1734f06142d92a3473e4d4';suite=unittest.defaultTestLoader.discover(str(root/'scripts'),pattern='test_input_consumption*.py');index=[];by_test={};failures=[];digest=hashlib.sha256();stream=gzip.GzipFile(filename=str(out/'CALLS.jsonl.gz'),mode='wb',mtime=0)
def profile(frame,event,arg):
 if event!='return' or frame.f_code.co_filename!=str(reader) or frame.f_code.co_name not in {'analyze','analyze_role','authority_lifecycle_foundation'}:return
 test_id=None;parent=frame.f_back
 while parent:
  value=parent.f_locals.get('self')
  if parent.f_code.co_name.startswith('test_') and isinstance(value,unittest.TestCase):
   test=getattr(value,'_subtest',None) or value;test_id=test.id();break
  parent=parent.f_back
 local=frame.f_locals;name=frame.f_code.co_name;record=dict(id=len(index)+1,test=test_id,entry=name,result=arg)
 if name=='analyze':record.update(client_text=local['client_text'],authority_text=local['authority_text'])
 else:record.update(rows=local['rows'],role=local.get('role','authority'))
 data=(json.dumps(record,separators=(',',':'))+'\n').encode();stream.write(data);digest.update(data);index.append(dict(id=record['id'],test=test_id,entry=name,status=arg.get('transition_status') if isinstance(arg,dict) else None));by_test.setdefault(test_id,[]).append(record['id'])
class Result(unittest.TextTestResult):
 def addFailure(self,test,err):
  failures.append(dict(kind='failure',test=test.id(),calls=by_test.get(test.id(),[]),traceback=self._exc_info_to_string(err,test)));super().addFailure(test,err)
 def addError(self,test,err):
  failures.append(dict(kind='error',test=test.id(),calls=by_test.get(test.id(),[]),traceback=self._exc_info_to_string(err,test)));super().addError(test,err)
sys.setprofile(profile)
try:r=unittest.TextTestRunner(verbosity=2,resultclass=Result).run(suite)
finally:sys.setprofile(None);stream.close()
failures=[dict(kind='failure',test=t.id(),calls=by_test.get(t.id(),[]),traceback=trace) for t,trace in r.failures]+[dict(kind='error',test=t.id(),calls=by_test.get(t.id(),[]),traceback=trace) for t,trace in r.errors]
(out/'INDEX.json').write_text(json.dumps(index,indent=2)+'\n');(out/'FAILURES.json').write_text(json.dumps(failures,indent=2)+'\n');summary=dict(source=str(root),reader_sha256=hashlib.sha256(reader.read_bytes()).hexdigest(),methods=r.testsRun,failure_events=len(r.failures),errors=len(r.errors),skips=len(r.skipped),captured_calls=len(index),raw_jsonl_sha256=digest.hexdigest(),gzip_sha256=hashlib.sha256((out/'CALLS.jsonl.gz').read_bytes()).hexdigest(),candidate_functions_or_test_assertions_replaced=False,cpu_affinity=[4],native_executed=False,new207_replay_executed=False);(out/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2));raise SystemExit(not r.wasSuccessful())
