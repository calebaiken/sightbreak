import json,os,signal,subprocess,time
from pathlib import Path
root=Path('/workspace/reviews/stabilization-v2-20261016/timing');out=root/'unmodified-pause150';out.mkdir(exist_ok=True)
cmd=['scripts/godot.sh','--headless','--audio-driver','Dummy','--script','res://tests/reload_audio_capture.gd','--',f'--out={out}']
with (root/'unmodified-pause150.txt').open('w') as f:
 p=subprocess.Popen(cmd,cwd='/workspace/sightbreak-three-agent-build',stdout=f,stderr=subprocess.STDOUT)
 time.sleep(.45);os.kill(p.pid,signal.SIGSTOP);st=time.monotonic();time.sleep(.15);os.kill(p.pid,signal.SIGCONT);pause=(time.monotonic()-st)*1000;rc=p.wait()
meta={'command':cmd,'pause_ms':pause,'pause_at_s_after_launch':.45,'exit':rc,'baseline_sha':subprocess.check_output(['git','rev-parse','HEAD'],cwd='/workspace/sightbreak-three-agent-build',text=True).strip(),'status':subprocess.check_output(['git','status','--porcelain'],cwd='/workspace/sightbreak-three-agent-build',text=True)};(root/'unmodified-pause150-meta.json').write_text(json.dumps(meta,indent=2)+'\n');print(meta);print((root/'unmodified-pause150.txt').read_text())
