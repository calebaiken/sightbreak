from pathlib import Path
import hashlib,json,subprocess,time
root=Path('/workspace/reviews/stabilization-v2-20261016/timing/maintained-serial');cwd=Path('/workspace/sightbreak-stabilization-v2-controls');source=subprocess.check_output(['git','rev-parse','HEAD'],cwd=cwd,text=True).strip();filehash=hashlib.sha256((cwd/'game/tests/reload_audio_capture.gd').read_bytes()).hexdigest();runs=[]
for n in range(10):
 out=root/str(n);out.mkdir(exist_ok=True);cmd=['scripts/godot.sh','--headless','--audio-driver','Dummy','--script','res://tests/reload_audio_capture.gd','--','--scenario=cancel',f'--out={out}'];start=time.monotonic()
 with (root/f'{n}.txt').open('w') as log:
  p=subprocess.run(cmd,cwd=cwd,stdout=log,stderr=subprocess.STDOUT,timeout=30)
 text=(root/f'{n}.txt').read_text();r={'run':n,'command':cmd,'exit':p.returncode,'elapsed_seconds':time.monotonic()-start,'source':source,'capture_sha256':filehash,'working_tree_status':subprocess.check_output(['git','status','--porcelain'],cwd=cwd,text=True),'findings':[x for x in text.splitlines() if x.startswith(('FAIL','ERROR','WARNING','RELOAD_AUDIO_CAPTURE'))]};runs.append(r);(root/'summary.json').write_text(json.dumps({'source':source,'capture_sha256':filehash,'concurrency':1,'runs':runs},indent=2)+'\n');print(json.dumps(r),flush=True)
