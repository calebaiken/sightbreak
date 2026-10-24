from pathlib import Path
import json,subprocess,sys,time
out=Path(sys.argv[sys.argv.index('--output')+1])
child=subprocess.Popen([sys.executable,'-B','-c',"from pathlib import Path; import json,os,time; Path('C:\\\\Users\\\\blith\\\\AppData\\\\Local\\\\Temp\\\\opencode\\\\critic-after-controller-20261019T193151501897Z\\\\supervisor-descendant-control\\\\child-started.json').write_text(json.dumps({'pid':os.getpid()})); time.sleep(1.5); print('ERROR: escaped exported-flow descendant',flush=True); Path('C:\\\\Users\\\\blith\\\\AppData\\\\Local\\\\Temp\\\\opencode\\\\critic-after-controller-20261019T193151501897Z\\\\supervisor-descendant-control\\\\child-finished.json').write_text('finished'); raise SystemExit(7)"])
marker=Path('C:\\Users\\blith\\AppData\\Local\\Temp\\opencode\\critic-after-controller-20261019T193151501897Z\\supervisor-descendant-control\\child-started.json')
while not marker.exists(): time.sleep(.005)
print('synthetic worker exiting zero',flush=True)
(out/'results.json').write_text(json.dumps({'passed':True,'synthetic_control_not_native_evidence':True}))
