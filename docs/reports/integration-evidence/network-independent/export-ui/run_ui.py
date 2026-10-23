from pathlib import Path
import hashlib,importlib,json,os,subprocess,sys,time
root=Path('/workspace/sightbreak-integration');out=Path(__file__).resolve().parent
(out/'finish').unlink(missing_ok=True)
logs=[];processes=[]
def launch(name,cmd,env=None,cwd=out):
 log=(out/(name+'.log')).open('w');logs.append(log)
 p=subprocess.Popen(cmd,cwd=cwd,env=env,stdout=log,stderr=subprocess.STDOUT);processes.append(p);return p
try:
 xvfb=launch('xvfb101',['/workspace/tools/xvfb/usr/bin/Xvfb',':101','-screen','0','1280x720x24','-nolisten','tcp'])
 time.sleep(.5)
 env=dict(os.environ,DISPLAY=':101',LIBGL_ALWAYS_SOFTWARE='1',LP_NUM_THREADS='2')
 for name,sub in [('XDG_DATA_HOME','data'),('XDG_CONFIG_HOME','config'),('XDG_CACHE_HOME','cache')]:
  d=out/'state'/sub;d.mkdir(parents=True,exist_ok=True);env[name]=str(d)
 server=launch('server',[str(root/'scripts/godot.sh'),'--headless','--script',str(out/'server.gd')],{**env,'SIGHTBREAK_STATE_DIR':str(out/'server-state')},root)
 for i in range(100):
  if 'SIGHTBREAK_SERVER_READY' in (out/'server.log').read_text():break
  if server.poll() is not None:raise RuntimeError((out/'server.log').read_text())
  time.sleep(.1)
 else:raise RuntimeError('Server readiness timeout')
 exe=root/'builds/linux/sightbreak.x86_64'
 client=launch('client',[str(exe),'--audio-driver','Dummy','--quit-after','1500'],env)
 time.sleep(2)
 sys.path.insert(0,str(out))
 for attempt in range(80):
  try:
   import xinput101 as ui
   break
  except RuntimeError:
   if client.poll() is not None:raise RuntimeError((out/"client.log").read_text())
   time.sleep(.25)
 else:raise RuntimeError("SIGHTBREAK window never appeared")
 for attempt in range(240):
  pixel=ui.ImageGrab.grab(xdisplay=':101').getpixel((100,350))
  if pixel[0]>80 and pixel[0]>pixel[1]*1.5:break
  time.sleep(.25)
 else:raise RuntimeError('Native menu never became visible')
 ui=importlib.reload(ui)
 ui.capture(str(out/'01-exported-menu.png'))
 ui.click(250,419);time.sleep(1)
 ui.capture(str(out/'02-exported-connect.png'))
 ui.click(640,305)
 for attempt in range(80):
  if 'EXPORT_UI_ACK_READY' in (out/'server.log').read_text():break
  if client.poll() is not None:raise RuntimeError('Client exited during admission')
  time.sleep(1)
 else:raise RuntimeError('Client never acknowledged applied owner snapshot')
 time.sleep(1)
 ui.capture(str(out/'03-exported-network-rifle.png'))
 if 'EXPORT_UI_JOIN' not in (out/'server.log').read_text():raise RuntimeError('Exported client did not join through native UI')
 ui.t.XTestFakeButtonEvent(ui.d,1,1,0);ui.x.XFlush(ui.d);time.sleep(.7)
 ui.capture(str(out/'04-exported-firing.png'))
 ui.t.XTestFakeButtonEvent(ui.d,1,0,0);ui.x.XFlush(ui.d);time.sleep(.5)
 ui.capture(str(out/'05-exported-ammo-used.png'))
 for attempt in range(100):
  if 'EXPORT_UI_RELOAD_STARTED' in (out/'server.log').read_text():break
  time.sleep(.05)
 else:raise RuntimeError('Fixture reload never started')
 time.sleep(.5)
 ui.capture(str(out/'06-exported-reload.png'))
 for attempt in range(100):
  if 'EXPORT_UI_RELOAD_COMPLETED' in (out/'server.log').read_text():break
  time.sleep(.05)
 else:raise RuntimeError('Fixture reload never completed')
 time.sleep(.25)
 ui.capture(str(out/'07-exported-reloaded.png'))
 client.wait(timeout=120)
 (out/'finish').write_text('finish\n');server.wait(timeout=10)
 report=json.loads((out/'authority.json').read_text())
 assert report['passed']
 assert client.returncode==0 and server.returncode==0
 for name in ('client','server'):
  text=(out/(name+'.log')).read_text()
  assert 'SCRIPT ERROR' not in text and 'ERROR:' not in text and 'leaked' not in text, text
 result={'source_commit':'d084e5003ac915550c368a86176df9063375bb59','elf_sha256':hashlib.file_digest(exe.open('rb'),'sha256').hexdigest(),'authority':report,'client_exit':client.returncode,'server_exit':server.returncode,'capture_dimensions':[1280,720],'capture_method':'raw X11 ImageGrab; no image edits','reload_trigger':'source authority fixture','desktop_R_key_injection':'UNVERIFIED','exit_method':'supported --quit-after1500; no WM-delete claim','scope':'Actual exported Linux client, real native UI inputs, source Godot authority on loopback; software rendering, no physical-device performance claim'}
 (out/'results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
finally:
 for p in reversed(processes):
  if p.poll() is None:p.terminate()
 for p in reversed(processes):
  try:p.wait(timeout=5)
  except subprocess.TimeoutExpired:p.kill();p.wait()
 for log in logs:log.close()
