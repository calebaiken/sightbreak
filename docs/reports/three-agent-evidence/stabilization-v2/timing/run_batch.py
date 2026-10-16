from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import argparse,json,subprocess,os
root=Path('/workspace/reviews/stabilization-v2-20261016/timing')
p=argparse.ArgumentParser();p.add_argument('--label',required=True);p.add_argument('--rounds',type=int,default=3);p.add_argument('--pause-ms',type=int,default=0);p.add_argument('--cpu-workers',type=int,default=0);p.add_argument('--probe',default='reload_audio_clock_probe_physics.gd');a=p.parse_args()
workers=[subprocess.Popen(['python3','-c','while True: sum(i*i for i in range(10000))'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL) for _ in range(a.cpu_workers)]
runs=[]
def one(i,s):
 name=f'{a.label}-{i}-{s}'
 cmd=['python3',str(root/'run_probe.py'),'--name',name,'--clock','frames','--scenario',s,'--probe',a.probe,'--pause-ms',str(a.pause_ms)]
 p=subprocess.run(cmd,capture_output=True,text=True);meta=json.loads((root/(name+'-meta.json')).read_text());return {'name':name,**meta}
try:
 for i in range(a.rounds):
  with ThreadPoolExecutor(max_workers=3) as pool:
   runs.extend(pool.map(lambda s:one(i,s),['reload','cancel','shot']))
finally:
 for w in workers:w.terminate()
 for w in workers:w.wait()
summary={'label':a.label,'probe':a.probe,'cpu_workers':a.cpu_workers,'concurrent_captures':3,'runs':runs};(root/(a.label+'-summary.json')).write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({'label':a.label,'results':[(x['name'],x['code']) for x in runs]},indent=2))
