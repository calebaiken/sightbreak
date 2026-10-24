"""Actual detached source/manifest preflight; all native preparation forbidden."""
from pathlib import Path
import json,os,sys,hashlib
from unittest.mock import patch
ROOT=Path(os.environ['MATH_REVIEW_ROOT']);sys.path.insert(0,str(ROOT/'scripts'))
import windows_fov_math as w
OUT=Path(__file__).resolve().parent/os.environ['MATH_REVIEW_LABEL'];OUT.mkdir(exist_ok=True)
manifest=ROOT/'docs/reports/gauntlet/windows-fov-math-finalization-20261024/RUNTIME_COMPONENT_MANIFEST.json'
expected='cb5a22fa2d0317a861eca3653cedb7fa9f98572a61d4e8c952b7c02ffb921c72'
assert hashlib.sha256(manifest.read_bytes()).hexdigest()==expected
calls={key:0 for key in ('sdk','job','execute')}
def blocked(name):
    def invoke(*a,**k):
        calls[name]+=1
        raise AssertionError('forbidden native preparation '+name)
    return invoke
with patch.object(w,'sdk_member',blocked('sdk')),patch.object(w,'WindowsJob',blocked('job')),patch.object(w,'execute_prepared',blocked('execute')):
    result=w.collect((OUT/'preflight').resolve(),OUT/'absent-sdk.zip',manifest,expected,
                     'bede80b8dbfa5a276c9468b492cbd2fcc54d8e67',root=ROOT)
assert result['source']['runtime_commit']=='bede80b8dbfa5a276c9468b492cbd2fcc54d8e67'
assert result['source']['code_commit']=='ab864ab9dd1a620ff86ca27bad0f59031c734555'
assert result['preflight']['status']=='BLOCKED' and result['preflight']['execution_admitted'] is False
assert result['native_invocations']==0 and result['passed'] is False
assert calls==dict.fromkeys(calls,0),calls
(OUT/'PUBLIC_GUARD_RESULT.json').write_text(json.dumps(dict(source=result['source'],artifact_preflight=result['preflight'],calls=calls,actual_native_invocations=0,complete_generated_preflight_evidence=result['evidence_complete'],scope='Generated source-only blocked preflight, no native acquisition originals'),indent=2)+'\n')
print(json.dumps(dict(status='BLOCKED',native=0,calls=calls,source_components=len(result['source']['files']))))
