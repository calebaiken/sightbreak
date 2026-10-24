import contextlib,importlib,inspect,json,os,sys,time,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=Path(os.environ.get('MATH_REVIEW_ROOT','/workspace/reviews/windows-fov-math-acquisition-runtime-20261024'));OUT=HERE/os.environ.get('MATH_SELECTED_LABEL','own-selected');OUT.mkdir(exist_ok=True)
sys.path.insert(0,str(ROOT/'scripts'));assert sorted(os.sched_getaffinity(0))==[4]
selected=[];omitted=[];suite=unittest.TestSuite()
for name in ('test_windows_fov_math','test_fov_math_reference','test_fov_binary_input','test_native_log'):
 module=importlib.import_module(name)
 for _,cls in inspect.getmembers(module,inspect.isclass):
  if not issubclass(cls,unittest.TestCase) or cls.__module__!=name:continue
  for method in unittest.defaultTestLoader.getTestCaseNames(cls):
   identity=name+'.'+cls.__name__+'.'+method
   if cls.__name__=='ProcInterfaceControls' or method=='test_authenticated_generated_sdk_fixture_extracts_only_gui_and_records_measured_member':omitted.append(identity)
   else:selected.append(identity);suite.addTest(cls(method))
assert len(selected)==80 and len(omitted)==5,(len(selected),len(omitted))
start=time.monotonic()
with (OUT/'stdout').open('w') as stdout,(OUT/'stderr').open('w') as stderr,contextlib.redirect_stdout(stdout):result=unittest.TextTestRunner(stream=stderr,verbosity=2).run(suite)
summary=dict(source='b16b012d720c0981cfc28146a651b3ba5f8a9caa',runtime='25603855ad7029b10c6c4109a4d47b949d72c1d2',scope='Selected source/pure controls; not full85 builder replay, no SDK/API/proc/pidfd/native',selected=selected,omitted=omitted,methods=result.testsRun,errors=len(result.errors),failures=len(result.failures),skips=len(result.skipped),passed=result.wasSuccessful(),seconds=time.monotonic()-start,cpu=[4],actual_native_invocations=0)
(OUT/'RESULTS.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({k:v for k,v in summary.items() if k not in ('selected','omitted')}));assert result.wasSuccessful()
