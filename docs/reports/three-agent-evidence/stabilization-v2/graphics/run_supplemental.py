import os,pathlib,subprocess,time,json
out=pathlib.Path('/workspace/reviews/stabilization-v2-20261016/graphics');new=pathlib.Path('/workspace/sightbreak-stab2-graphics');old=pathlib.Path('/workspace/sightbreak-stab2-graphics-before');rows=[]
# Keep software-rendered comparisons sequential and wait until the other reviewer renderer has stopped.
limit=time.monotonic()+900
while pathlib.Path('/tmp/.X11-unix/X102').exists():
 if time.monotonic()>limit:raise TimeoutError('renderer102 did not finish')
 time.sleep(1)
assert not pathlib.Path('/tmp/.X11-unix/X104').exists()
env=dict(os.environ,DISPLAY=':104',LIBGL_ALWAYS_SOFTWARE='1',LP_NUM_THREADS='2',SIGHTBREAK_STATE_DIR=str(out/'state-supplemental'))
def run(label,root,args,timeout=240):
 cmd=[str(root/'scripts/godot.sh'),*args];start=time.monotonic()
 with (out/(label+'.log')).open('w') as f:p=subprocess.run(cmd,cwd=root,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
 rows.append({'name':label,'source':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),'command':cmd,'exit':p.returncode,'seconds':time.monotonic()-start});(out/'supplemental-runs.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows[-1]),flush=True)
with (out/'xvfb104.log').open('w') as log:
 x=subprocess.Popen(['/workspace/tools/xvfb/usr/bin/Xvfb',':104','-screen','0','1280x720x24','-nolisten','tcp'],stdout=log,stderr=subprocess.STDOUT,env=env)
 try:
  for _ in range(50):
   if pathlib.Path('/tmp/.X11-unix/X104').exists():break
   time.sleep(.1)
  dest=out/'snapshot-correct';dest.mkdir(exist_ok=True);only='0,14,28,34,44,52,58,66,69,72,74,78,80,82,84,90,98,104,110,118,126,134,137,141,146'
  run('snapshot-correct',new,['--audio-driver','Dummy','--rendering-method','gl_compatibility','--script','res://tests/reload_sequence_capture.gd','--','--out='+str(dest),'--authority=snapshot','--tail=0.55','--only='+only])
  subprocess.run(['python3',str(new/'tools/art/motion_sheet.py'),str(dest),str(out/'snapshot-correct.jpg'),'snapshot correct (20Hz replica timer)',*only.split(',')],stdout=subprocess.DEVNULL,check=True)
  for label,root in [('perf-before-shader',old),('perf-after-shader',new)]:
   run(label,root,['--audio-driver','Dummy','--rendering-method','gl_compatibility','--script','res://tests/reload_perf_probe.gd','--','--samples=10'],180)
 finally:
  x.terminate();x.wait(timeout=5)
