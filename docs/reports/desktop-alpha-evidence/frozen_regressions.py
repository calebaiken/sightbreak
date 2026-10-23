from pathlib import Path
import subprocess,os,time,json,platform,sys
sys.path.insert(0,'scripts')
import build_manifest as m,toolchain
out=Path('/workspace/desktop-evidence');before=m.source();receipt={'source_before':before,'engine':toolchain.verify_engine(),'host':platform.platform(),'command':['bash','scripts/validate.sh','--backend']}
(out/'frozen-regressions.json').write_text(json.dumps(receipt,indent=2)+'\n')
log=(out/'frozen-display.log').open('w');display=subprocess.Popen(['/workspace/tools/xvfb/usr/bin/Xvfb',':117','-screen','0','1280x720x24','-nolisten','tcp'],stdout=log,stderr=subprocess.STDOUT)
try:
 time.sleep(.7)
 env=dict(os.environ,DISPLAY=':117',LIBGL_ALWAYS_SOFTWARE='1',LP_NUM_THREADS='2',DBUS_SESSION_BUS_ADDRESS='unix:path=/workspace/desktop-evidence/unavailable-regression-bus',SIGHTBREAK_STATE_DIR='/workspace/desktop-evidence/frozen-regression-state')
 with (out/'frozen-regressions.log').open('w') as stream:
  result=subprocess.run(receipt['command'],env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=1100)
 receipt.update(exit_code=result.returncode,source_after=m.source())
 receipt['exact_source_unchanged']=receipt['source_after']==before
 (out/'frozen-regressions.json').write_text(json.dumps(receipt,indent=2)+'\n')
 print(json.dumps({'exit':result.returncode,'exact_source_unchanged':receipt['exact_source_unchanged']}),flush=True)
 if result.returncode or not receipt['exact_source_unchanged']:raise SystemExit(1)
finally:
 display.terminate();display.wait(timeout=5);log.close()
