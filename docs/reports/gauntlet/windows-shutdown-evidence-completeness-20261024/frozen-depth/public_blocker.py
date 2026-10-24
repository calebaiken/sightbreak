import json,os,sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'scripts'))
import windows_shutdown_study as study
assert sorted(os.sched_getaffinity(0))==[4]
with patch.object(study,'WindowsOwner') as owner,patch.object(study,'runtime_identity') as identity,patch.object(study,'real_driver') as driver,patch.object(sys,'argv',['study','collect','--expected-source','0f478a078277fdb0d711837bef67cf14262d9d8f','--output',str(ROOT/'.local/unreached-collect')]):
 try:study.main();error=None
 except RuntimeError as e:error=str(e)
 owner.assert_not_called();identity.assert_not_called();driver.assert_not_called();assert error and 'BLOCKED' in error
 result=dict(source='0f478a078277fdb0d711837bef67cf14262d9d8f',cpu=[4],scope='Actual fixed preflight, guarded public collect; no actual native action',native_invocations=0,error=error,owner_calls=owner.call_count,identity_calls=identity.call_count,driver_calls=driver.call_count)
 (ROOT/'.local/frozen-evidence-completeness/public-collect-blocked.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
