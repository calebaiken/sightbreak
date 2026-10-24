import ast,hashlib,json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path.cwd();OUT=Path(os.environ.get('EVIDENCE_PROOF_OUT',ROOT/'.local/frozen-evidence-completeness'));OUT.mkdir(parents=True,exist_ok=True)
SOURCE='0f478a078277fdb0d711837bef67cf14262d9d8f';assert sorted(os.sched_getaffinity(0))==[4]
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip()==SOURCE
assert not subprocess.check_output(['git','status','--porcelain','--untracked-files=all'],cwd=ROOT)
results=[]
for name,pattern in (('binding','test_shutdown_source_binding.py'),('old28','test_windows_shutdown_study.py'),('evidence','test_shutdown_study_evidence.py')):
 command=[sys.executable,'-m','unittest','discover','-s','scripts','-p',pattern,'-v'];started=time.monotonic();p=subprocess.run(command,cwd=ROOT,capture_output=True)
 (OUT/(name+'.stdout')).write_bytes(p.stdout);(OUT/(name+'.stderr')).write_bytes(p.stderr)
 row=dict(name=name,command=command,exit=p.returncode,seconds=time.monotonic()-started);results.append(row);print(json.dumps(row),flush=True)
command=[sys.executable,'scripts/windows_shutdown_study.py','preflight','--expected-source',SOURCE,'--output',str(OUT/'preflight.json')]
p=subprocess.run(command,cwd=ROOT,capture_output=True);(OUT/'preflight.stdout').write_bytes(p.stdout);(OUT/'preflight.stderr').write_bytes(p.stderr)
pre=json.loads((OUT/'preflight.json').read_text());results.append(dict(name='preflight',command=command,exit=p.returncode,status=pre['status'],physical=len(pre['source']['physical_sources'])))
assert p.returncode==2 and pre['status']=='BLOCKED' and not pre['execution_authorized']
assert all(r['read_observations']==2 for r in pre['source']['physical_sources'].values())
assert not subprocess.check_output(['git','status','--porcelain','--untracked-files=all'],cwd=ROOT)
summary=dict(source=SOURCE,scope='Builder pure/source evidence only; independent critic required; public collect BLOCKED',cpu=[4],native_invocations=0,results=results,source_clean=True)
(OUT/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary),flush=True)
assert all(r['exit']==0 for r in results if r['name']!='preflight')
