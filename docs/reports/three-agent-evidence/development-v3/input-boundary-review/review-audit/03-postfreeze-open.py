import pathlib,json,sys,hashlib,datetime,os
sys.stdout.reconfigure(encoding='utf-8')
base=pathlib.Path(r'C:\Users\blith\AppData\Local\Temp\opencode\sol-input-boundary-controls-20261022')
out=pathlib.Path(r'C:\Users\blith\AppData\Local\Temp\opencode\sol-input-component-sourcebinding-20261023T011730421928Z')
(out/'03-postfreeze-open.py').write_text(sys.orig_argv[sys.orig_argv.index('-c')+1],encoding='utf-8')
main=json.loads((base/'MAIN_NEUTRAL_FREEZE.json').read_bytes())
verified=[]
for e in main['files']:
 p=base/e['path'];b=p.read_bytes();h=hashlib.sha256(b).hexdigest();assert len(b)==e['bytes'] and h==e['sha256']
 verified.append({'path':e['path'],'bytes':len(b),'sha256':h})
assert json.loads((out/'critic-rehash.json').read_bytes())['ledger_payloads_verified']==37
receipt={'main_frozen_utc_recorded':main['frozen_utc'],'main_freeze_sha256':hashlib.sha256((base/'MAIN_NEUTRAL_FREEZE.json').read_bytes()).hexdigest(),'main_all_listed_bytes_verified':verified,'critic_frozen_utc_recorded':'2026-10-23T01:12:49.902292Z','critic_freeze_sha256':'d9c883f4e60ccbda05bd02191421d2acccf5d336bbaa9927b2f83748eb333c78','critic_all_37_payloads_verified':True,'rehash_completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'chronology_limit':'Local unsigned records only, not trusted clock/attestation; identity inference does not revise frozen neutral outcomes.'}
(out/'both-neutral-freezes-verified-before-key.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
print('BOTH_FREEZE_HASHCHECKS_COMPLETE',json.dumps(receipt,indent=2))
files=[];cache=[]
for parent,dirs,names in os.walk(base):
 path=pathlib.Path(parent)
 for d in list(dirs):
  if d in ['.godot','.state']:
   cache.append(str((path/d).relative_to(base)));dirs.remove(d)
 for name in names:
  p=path/name;files.append({'path':p.relative_to(base).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(out/'producer-noncache-inventory.json').write_text(json.dumps({'files':files,'cache_directories_not_read':cache},indent=2)+'\n',encoding='utf-8')
print('PERMITTED_NONCACHE_INVENTORY',json.dumps(files,indent=2))
print('CACHE_DIRECTORIES_NOT_READ',json.dumps(cache))
keys=[e['path'] for e in files if e['path'].endswith('SOURCE_FROZEN_BEFORE_EXECUTION.json')]
for rel in keys:
 print('POSTFREEZE_SOURCE_RECORD',rel,'\n'+(base/rel).read_text(encoding='utf-8'))