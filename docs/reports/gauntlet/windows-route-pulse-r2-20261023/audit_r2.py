"""Bind R2 scope, previous rejection and original failures without native work."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[3]
BASE='e28c8e90b9ef2d0c766bd9152c194e3197ceba9a'
REJECTED='977633e44a61352cbf666273931021ebebfe70d9'
HANDOFF='9a3d73563e45c720aa0a3cccd48eb7d4ecd8c996'
CRITIC='bf47f7c9b15a5d8be8aa3dcc0f815fb3c60961f2'
REVIEW=Path('/workspace/reviews/windows-route-pulse-source/docs/reports/gauntlet/windows-route-pulse-independent-20261023')

def git(*args): return subprocess.check_output(['git',*args],cwd=ROOT)
def without_pulse(payload):
    tree=ast.parse(payload)
    winui=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='WinUI')
    winui.body=[n for n in winui.body if getattr(n,'name',None)!='key_pulse']
    return ast.dump(tree)

checks={}
path='scripts/verify_integration_export.py'
checks['R2_changes_no_other_integration_module_AST']=without_pulse((ROOT/path).read_bytes())==without_pulse(git('show',REJECTED+':'+path))
changed=git('diff','--name-only',REJECTED,'HEAD','--','scripts').decode().splitlines()
checks['R2_only_changes_helper_and_its_pure_tests']=set(changed)=={'scripts/verify_integration_export.py','scripts/test_native_route_pulse.py'}
checks['original_builder_report_is_unchanged']=subprocess.run(['git','diff','--quiet',HANDOFF,'HEAD','--','docs/reports/gauntlet/windows-route-pulse-20261023'],cwd=ROOT).returncode==0
checks['original_trace_recomputed_byte_exact']=(OUT/'original-failed-trace.json').read_bytes()==(OUT.parent/'windows-route-pulse-20261023/original-failed-trace.json').read_bytes()
checks['all_base_scope_checks_pass']=all(json.loads((OUT/'source-preservation.json').read_text())['checks'].values())
protected={}
for path in ('game','.github','scripts/toolchain.py','scripts/native_focus_fence.py'):
    protected[path]={ref:git('rev-parse',ref+':'+path).decode().strip() for ref in (BASE,REJECTED,'HEAD')}
checks['game_CI_toolchain_focus_objects_exact']=all(len(set(refs.values()))==1 for refs in protected.values())
critic_bindings={}
for name in ('REPORT.md','independent_controls.py','independent-receipts.json'):
    payload=(REVIEW/name).read_bytes()
    committed=subprocess.check_output(['git','show',CRITIC+':docs/reports/gauntlet/windows-route-pulse-independent-20261023/'+name],cwd=REVIEW)
    checks['critic_committed_bytes_'+name]=payload==committed
    critic_bindings[name]={'commit':CRITIC,'bytes':len(payload),'sha256':hashlib.sha256(payload).hexdigest()}
original=json.loads((REVIEW/'independent-receipts.json').read_text())
replay=json.loads((OUT/'independent-replay-unchanged.json').read_text())
comparisons=[]
for name,field in (('test_two_key_dispatch_stops_when_focus_changes_after_first_down','foreground'),('test_two_key_dispatch_stops_when_owner_changes_after_first_down','owner')):
    before=next(r for r in original if r['test']==name)
    after=next(r for r in replay if r['test']==name)
    old_unsafe=[r for r in before['calls'] if r['down'] and r[field] != (34 if field=='foreground' else 12)]
    new_unsafe=[r for r in after['calls'] if r['down'] and r[field] != (34 if field=='foreground' else 12)]
    checks[name]=bool(old_unsafe) and not new_unsafe and after['receipt']['attempted_keys']==['w'] and after['receipt']['released_keys']==['w'] and not after['remaining_keys']
    comparisons.append({'test':name,'rejected_raw':before,'R2_raw':after})
(OUT/'falsifier-comparison.json').write_text(json.dumps({'scope':'Same independent fake User32 controls, not native delivery evidence','comparisons':comparisons},indent=2)+'\n')
for prefix in ('pure','depth-one'):
    receipt=json.loads((OUT/(prefix+'-checks.json')).read_text())
    checks[prefix+'_all104_methods_with_original3_skips']=receipt['methods']==104 and receipt['skips']==3 and all(row['exit']==0 for row in receipt['checks'])
depth=json.loads((OUT/'depth-one-checks.json').read_text())
checks['depth_one_no_historical_fixture_directory']=depth['is_shallow']=='true' and depth['history_commits']==1 and not depth['reports_materialized']
checks['diff_check_passes']=subprocess.run(['git','diff','--check'],cwd=ROOT).returncode==0
value={'source_freeze':git('rev-parse','HEAD').decode().strip(),'rejected_source':REJECTED,'base':BASE,'checks':checks,'critic_bindings':critic_bindings,'protected_objects':protected,'source_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ('scripts/verify_integration_export.py','scripts/test_native_route_pulse.py','scripts/verify_offline_export.py','scripts/native_approach.py','scripts/native_settings_route.py')}}
(OUT/'r2-audit.json').write_text(json.dumps(value,indent=2)+'\n')
assert all(checks.values()),checks
print(json.dumps({'passed_source_checks':len(checks),'source_freeze':value['source_freeze']}))
