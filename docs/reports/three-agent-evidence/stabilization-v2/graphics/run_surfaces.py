import os,pathlib,subprocess,time,json
out=pathlib.Path('/workspace/reviews/stabilization-v2-20261016/graphics');root=pathlib.Path('/workspace/sightbreak-stab2-graphics')
assert not pathlib.Path('/tmp/.X11-unix/X103').exists()
env=dict(os.environ,DISPLAY=':103',LIBGL_ALWAYS_SOFTWARE='1',LP_NUM_THREADS='2',SIGHTBREAK_STATE_DIR=str(out/'state-surfaces'))
with (out/'xvfb103.log').open('w') as f:
 x=subprocess.Popen(['/workspace/tools/xvfb/usr/bin/Xvfb',':103','-screen','0','1280x720x24','-nolisten','tcp'],stdout=f,stderr=subprocess.STDOUT,env=env)
 try:
  for _ in range(50):
   if pathlib.Path('/tmp/.X11-unix/X103').exists():break
   time.sleep(.1)
  cmd=[str(root/'scripts/godot.sh'),'--audio-driver','Dummy','--rendering-method','gl_compatibility','--script',str(out/'surface_review.gd')]
  with (out/'surface-review.log').open('w') as f:
   p=subprocess.run(cmd,cwd=root,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=180)
  (out/'surface-run.json').write_text(json.dumps({'command':cmd,'source':'5357329fa06136ac0d81b58ace97f872f37bebfa','exit':p.returncode},indent=2)+'\n')
  print((out/'surface-review.log').read_text())
 finally:
  x.terminate();x.wait(timeout=5)
