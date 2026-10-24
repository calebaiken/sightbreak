import pathlib,json,sys,hashlib,datetime
sys.stdout.reconfigure(encoding='utf-8')
base=pathlib.Path(r'C:\Users\blith\AppData\Local\Temp\opencode\sol-input-boundary-controls-20261022')
out=pathlib.Path(r'C:\Users\blith\AppData\Local\Temp\opencode\sol-input-component-sourcebinding-20261023T011730421928Z')
(out/'02-main-freeze.py').write_text(sys.orig_argv[sys.orig_argv.index('-c')+1],encoding='utf-8')
f=base/'MAIN_NEUTRAL_FREEZE.json';b=f.read_bytes();obj=json.loads(b)
print('MAIN_FREEZE_JSON',json.dumps(obj,indent=2))
print('MAIN_FREEZE_SHA256',hashlib.sha256(b).hexdigest())
print('MAIN_VERDICT_SHA256',hashlib.sha256((base/'MAIN_NEUTRAL_COMPONENT_VERDICT.md').read_bytes()).hexdigest())
for rel in ['attempt','attempt-r2/neutral','attempt-r3/neutral']:
 p=base/rel
 print('NONPRIVATE_LIST',rel,json.dumps([{'name':q.name,'directory':q.is_dir(),'bytes':None if q.is_dir() else q.stat().st_size} for q in p.iterdir() if not any(x in q.name.casefold() for x in ['private','key','source_frozen'])],indent=2))
(out/'main-freeze-intake.json').write_text(json.dumps({'freeze_sha256':hashlib.sha256(b).hexdigest(),'record':obj,'verdict_sha256':hashlib.sha256((base/'MAIN_NEUTRAL_COMPONENT_VERDICT.md').read_bytes()).hexdigest()},indent=2)+'\n',encoding='utf-8')