import ast,contextlib,json,sys,tempfile,types
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
source=(HERE/'historical/windows_shutdown_study-original.py').read_text();node=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='real_driver')
scope=dict(sys=sys,contextlib=contextlib);exec(compile(ast.Module(body=[node],type_ignores=[]),'<frozen real_driver>','exec'),scope)
with tempfile.TemporaryDirectory() as td:
 out=Path(td)/'trial';observed={}
 def fake_main(*,study_observer):
  observed['preexisting_files']=sorted(p.name for p in out.iterdir())
  if out.exists() and any(out.iterdir()):raise RuntimeError('actual frozen empty-output guard rejects')
 with patch.dict(sys.modules,{'verify_offline_export':types.SimpleNamespace(main=fake_main)}):
  try:scope['real_driver'](['scripts/verify_offline_export.py','--output',str(out)],lambda *a,**k:None,out);error=None
  except RuntimeError as e:error=str(e)
 result=dict(scope='pure fake-main source guard, not actual driver/native run',expected_rejection=True,error=error,observed=observed,retained_files={p.name:p.read_bytes().hex() for p in out.iterdir()},native_invocations=0)
 assert error and len(observed['preexisting_files'])==2
 (HERE/'historical/wrapper-guard-failure.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(result))
