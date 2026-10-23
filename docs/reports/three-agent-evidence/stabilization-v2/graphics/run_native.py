import json,os,pathlib,subprocess,time
ROOT=pathlib.Path('/workspace/sightbreak-stab2-graphics'); OUT=pathlib.Path('/workspace/reviews/stabilization-v2-20261016/graphics'); DISPLAY=':102'
assert not pathlib.Path('/tmp/.X11-unix/X102').exists()
env=dict(os.environ,DISPLAY=DISPLAY,LIBGL_ALWAYS_SOFTWARE='1',LP_NUM_THREADS='2',SIGHTBREAK_STATE_DIR=str(OUT/'state-native'))
rows=[]
def run(name,args,timeout=240):
 command=[str(ROOT/'scripts/godot.sh'),*args];start=time.monotonic()
 with (OUT/(name+'.log')).open('w') as f:
  p=subprocess.run(command,cwd=ROOT,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
 row={'name':name,'source':'5357329fa06136ac0d81b58ace97f872f37bebfa','command':command,'exit':p.returncode,'seconds':time.monotonic()-start};rows.append(row);(OUT/'native-runs.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(row),flush=True)
 return p.returncode
with (OUT/'xvfb102.log').open('w') as log:
 x=subprocess.Popen(['/workspace/tools/xvfb/usr/bin/Xvfb',DISPLAY,'-screen','0','1280x720x24','-nolisten','tcp'],stdout=log,stderr=subprocess.STDOUT,env=env)
 try:
  for _ in range(50):
   if pathlib.Path('/tmp/.X11-unix/X102').exists():break
   time.sleep(.1)
  run('import-network-enabled',['--headless','--editor','--import','--quit'],120)
  run('weapon-art-native',['--audio-driver','Dummy','--rendering-method','gl_compatibility','--script','res://tests/weapon_art_test.gd'],120)
  run('reload-sequence-headless',['--headless','--script','res://tests/reload_sequence_test.gd'],120)
  only='0,14,28,34,44,52,58,66,69,72,74,78,80,82,84,90,98,104,110,118,126,134,137,141,146'
  for name,args in [('sunlit',[]),('shade',['--view=shade']),('backlight',['--view=backlight']),('dark',['--view=dark']),('reduced-current',['--reduced']),('reduced-calm',['--reduced','--variant=calm']),('reduced-still',['--reduced','--variant=still']),('snapshot20hz',['--authority=snapshot20hz'])]:
   dest=OUT/name;dest.mkdir(exist_ok=True)
   run(name,['--audio-driver','Dummy','--rendering-method','gl_compatibility','--script','res://tests/reload_sequence_capture.gd','--','--out='+str(dest),'--fire','--tail=0.55','--only='+only,*args])
   subprocess.run(['python3',str(ROOT/'tools/art/motion_sheet.py'),str(dest),str(OUT/(name+'.jpg')),name,*only.split(',')],stdout=subprocess.DEVNULL,check=True)
  dest=OUT/'weapon-art-capture';dest.mkdir(exist_ok=True)
  run('weapon-art-capture',['--audio-driver','Dummy','--rendering-method','gl_compatibility','--script','res://tests/weapon_art_capture.gd','--','--capture-dir='+str(dest)],180)
  run('perf-new',['--audio-driver','Dummy','--rendering-method','gl_compatibility','--script','res://tests/reload_perf_probe.gd','--','--samples=10'],180)
 finally:
  x.terminate()
  try:x.wait(timeout=5)
  except subprocess.TimeoutExpired:x.kill()
