"""Authorized pure new-loader availability/negative reads; never the input reader."""
import hashlib,json,os,re,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];sys.path.insert(0,str(ROOT/'scripts'))
import windows_shutdown_study as study
assert sorted(os.sched_getaffinity(0))==[4]
original=json.loads((ROOT/'docs/reports/gauntlet/windows-shutdown-study-controller-20261024/OLD_LIVING_INVENTORY.json').read_text())
def inventory(root):
 return [dict(path=p.relative_to(root).as_posix(),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(root.rglob('*')) if p.is_file()]
records=[]
for reference in original:
 root=Path(reference['path']);before=inventory(root)
 assert before==reference['files'],reference['run']
 result=study.trial_evidence(root)
 after=inventory(root);assert after==before
 assert result['strict_passed'] is False and result['evidence_complete'] is False
 warnings={name:[line for line in (root/name).read_text(encoding='utf-8').splitlines() if re.search(r'\bWARNING\b',line,re.I)] for name in ('client.log','reopened.log')}
 record=dict(run=reference['run'],root=str(root),native_invocations=0,scope='Unchanged archived data availability/negative only; no native run or independent acceptance',before=before,after=after,original_bytes_unchanged=True,availability=result['availability'],evidence_complete=result['evidence_complete'],strict_passed=result['strict_passed'],evidence_errors=result['evidence_errors'],strict_errors=result['strict_errors'],original_result_passed=result['result'].get('passed'),original_shutdown_observations_present='shutdown_study_observations' in result['result'],warning_lines=warnings)
 (HERE/'benchmark'/(reference['run']+'-loader-negative.json')).write_text(json.dumps(record,indent=2)+'\n');records.append(record)
print(json.dumps([dict(run=r['run'],availability=r['availability'],strict_passed=r['strict_passed'],evidence_errors=r['evidence_errors'],strict_errors=r['strict_errors'],bytes_unchanged=True) for r in records],indent=2))
