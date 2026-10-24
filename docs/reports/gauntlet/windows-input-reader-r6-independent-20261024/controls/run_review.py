#!/usr/bin/env python3
import argparse,hashlib,json,os,subprocess,sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert sorted(os.sched_getaffinity(0))==[4];root=a.source.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False);controls=Path(__file__).resolve().parent
assert hashlib.sha256((root/'scripts/analyze_input_consumption.py').read_bytes()).hexdigest()=='c53b1ced5743c7440d0530874115d474da2a70f2416c7515e098109837182be8'
groups=[('queue-models','queue_oracle.py',['--prototype',str(root/'scripts/analyze_input_consumption.py')]),('aggregate-models','aggregate_oracle.py',['--prototype',str(root/'scripts/analyze_input_consumption.py')]),('generated-histories','generated_histories.py',['--prototype',str(root/'scripts/analyze_input_consumption.py')]),('causal-cases','causal_cases.py',['--source',str(root)]),('retained-controls','replay_controls.py',['--source',str(root)]),('selected-pure','run_selected_pure.py',['--source',str(root)])]
records=[]
for name,script,extra in groups:
 cmd=[sys.executable,str(controls/script),*extra,'--output',str(out/name)]
 with (out/(name+'.stdout')).open('wb') as stdout,(out/(name+'.stderr')).open('wb') as stderr:
  result=subprocess.run(cmd,stdout=stdout,stderr=stderr,cwd=root)
 records.append(dict(group=name,command=cmd,exit=result.returncode));print(name,result.returncode,flush=True)
for f in sorted((root/'scripts').glob('*.sh')):
 result=subprocess.run(['bash','-n',str(f)],capture_output=True);records.append(dict(group='shell-syntax',command=['bash','-n',str(f)],exit=result.returncode,stdout=result.stdout.decode(),stderr=result.stderr.decode()))
summary=dict(source=str(root),output=str(out),cpu_affinity=[4],records=records,all_exit_zero=all(r['exit']==0 for r in records),native_executed=False)
(out/'RUNS.json').write_text(json.dumps(summary,indent=2)+'\n');raise SystemExit(not summary['all_exit_zero'])
