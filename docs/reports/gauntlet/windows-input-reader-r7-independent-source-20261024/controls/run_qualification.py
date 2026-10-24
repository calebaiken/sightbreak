#!/usr/bin/env python3
import argparse,hashlib,json,os,subprocess,sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert sorted(os.sched_getaffinity(0))==[4];root=a.source.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False);controls=Path(__file__).resolve().parent;model=controls/'model-assessment/controls';reader=root/'scripts/analyze_input_consumption.py';assert hashlib.sha256(reader.read_bytes()).hexdigest()=='d2cab3af7e441615a37caedb259b1311eb0b5b1cde46719c1000181223facba1'
groups=[('projected',model/'projected_oracle.py',['--prototype',str(reader)]),('history',model/'replay_history_db912.py',['--prototype',str(reader)]),('deadline',model/'deadline_histories.py',['--prototype',str(reader),'--schema-source',str(root)]),('source-clocks',model/'source_clock_calls.py',['--prototype',str(reader)]),('coincident',model/'coincident_cuts.py',['--prototype',str(reader)]),('preforget',model/'preforget_pairs.py',['--prototype',str(reader)]),('selected-pure',controls/'run_selected_pure.py',['--source',str(root)]),('retained139',controls/'replay_controls.py',['--source',str(root)])];records=[]
for name,script,extra in groups:
 cmd=[sys.executable,str(script),*extra,'--output',str(out/name)]
 with (out/(name+'.stdout')).open('wb') as stdout,(out/(name+'.stderr')).open('wb') as stderr:r=subprocess.run(cmd,stdout=stdout,stderr=stderr,cwd=root)
 records.append(dict(group=name,command=cmd,exit=r.returncode));print(name,r.returncode,flush=True)
for f in sorted((root/'scripts').glob('*.sh')):
 r=subprocess.run(['bash','-n',str(f)],capture_output=True);records.append(dict(group='shell-syntax',command=['bash','-n',str(f)],exit=r.returncode,stdout=r.stdout.decode(),stderr=r.stderr.decode()))
summary=dict(source=str(root),records=records,all_exit_zero=all(r['exit']==0 for r in records),cpu_affinity=[4],native_executed=False);(out/'RUNS.json').write_text(json.dumps(summary,indent=2)+'\n');raise SystemExit(not summary['all_exit_zero'])
