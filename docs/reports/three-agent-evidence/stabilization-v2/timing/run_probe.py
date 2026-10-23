import argparse,hashlib,json,os,signal,subprocess,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--name',required=True);p.add_argument('--clock',default='wall');p.add_argument('--probe',default='reload_audio_clock_probe.gd');p.add_argument('--pause-ms',type=int,default=0);p.add_argument('--negative',default='');p.add_argument('--scenario',default='reload');a=p.parse_args()
root=Path('/workspace/reviews/stabilization-v2-20261016/timing');out=root/a.name;out.mkdir(exist_ok=True)
cmd=['scripts/godot.sh','--headless','--audio-driver','Dummy','--script',str(root/a.probe),'--',f'--out={out}',f'--clock={a.clock}',f'--scenario={a.scenario}',f'--negative={a.negative}']
start=time.monotonic();proc=subprocess.Popen(cmd,cwd='/workspace/sightbreak-three-agent-build',stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1);lines=[];pause=None
for line in proc.stdout:
 lines.append(line)
 if 'PROBE_CAPTURE_READY' in line and a.pause_ms and pause is None:
  os.kill(proc.pid,signal.SIGSTOP);paused=time.monotonic();time.sleep(a.pause_ms/1000);os.kill(proc.pid,signal.SIGCONT);pause={'requested_ms':a.pause_ms,'elapsed_ms':(time.monotonic()-paused)*1000}
rc=proc.wait();(root/(a.name+'.txt')).write_text(''.join(lines));meta={'command':cmd,'code':rc,'pause':pause,'elapsed_s':time.monotonic()-start,'baseline_sha':subprocess.check_output(['git','rev-parse','HEAD'],cwd='/workspace/sightbreak-three-agent-build',text=True).strip(),'probe_sha256':hashlib.sha256((root/a.probe).read_bytes()).hexdigest(),'baseline_status':subprocess.check_output(['git','status','--porcelain'],cwd='/workspace/sightbreak-three-agent-build',text=True)};(root/(a.name+'-meta.json')).write_text(json.dumps(meta,indent=2)+'\n');print(json.dumps({'name':a.name,**meta}));print(''.join(lines)[-4000:])
