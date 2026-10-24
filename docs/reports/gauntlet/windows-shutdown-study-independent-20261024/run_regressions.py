import json,os,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=Path('/workspace/reviews/windows-shutdown-study-independent-source-20261024')
assert sorted(os.sched_getaffinity(0))==[4]
commands=[('dedicated',[sys.executable,'-m','unittest','discover','-s','scripts','-p','test_windows_shutdown_study.py','-v'])]
for row in json.loads((HERE/'builder-evidence-exact/focused/RESULTS.json').read_text())['groups']:
 commands.append((row['name'],[sys.executable,*row['command'][1:]]))
records=[]
for name,command in commands:
 started=time.monotonic();p=subprocess.run(command,cwd=ROOT,capture_output=True)
 out=HERE/'own-regressions';out.mkdir(exist_ok=True)
 (out/(name+'.stdout')).write_bytes(p.stdout);(out/(name+'.stderr')).write_bytes(p.stderr)
 record=dict(name=name,command=command,exit=p.returncode,seconds=time.monotonic()-started)
 records.append(record);print(json.dumps(record),flush=True)
(HERE/'own-regressions/RESULTS.json').write_text(json.dumps(dict(source='c90fedfd56a09bd0ba13cce5565ccd160891c3fb',cpu=[4],native_invocations=0,groups=records),indent=2)+'\n')
assert all(r['exit']==0 for r in records)
