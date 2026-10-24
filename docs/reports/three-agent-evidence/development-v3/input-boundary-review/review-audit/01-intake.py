import pathlib,sys,json,hashlib,datetime
sys.stdout.reconfigure(encoding='utf-8')
base=pathlib.Path(r'C:\Users\blith\AppData\Local\Temp\opencode')
producer=base/'sol-input-boundary-controls-20261022'
critic=base/'sol-input-component-neutral-verdict-20261023T011249700925Z'
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
out=base/('sol-input-component-sourcebinding-'+stamp);out.mkdir(exist_ok=False)
(out/'01-intake.py').write_text(sys.orig_argv[sys.orig_argv.index('-c')+1],encoding='utf-8')
pins={'FROZEN.json':'d9c883f4e60ccbda05bd02191421d2acccf5d336bbaa9927b2f83748eb333c78','REPORT.md':'cff57e331635ec0c3d2f65398f6fd4bf83ee339090211c3a2df75c19e3b0c51a','SHA256SUMS.txt':'446cbfd2dc80ab913212776b6f4024b425cb8669f55c891be03f8397f39ac2db'}
verified=[]
for name,h in pins.items():
 b=(critic/name).read_bytes();actual=hashlib.sha256(b).hexdigest();assert actual==h,(name,actual)
 verified.append({'path':str(critic/name),'sha256':actual,'bytes':len(b)})
ledger=(critic/'SHA256SUMS.txt').read_text(encoding='utf-8');count=0
for line in ledger.splitlines():
 h,rel=line.split('  ',1);parts=pathlib.PurePosixPath(rel).parts
 assert not pathlib.PurePosixPath(rel).is_absolute() and '..' not in parts
 assert hashlib.sha256(critic.joinpath(*parts).read_bytes()).hexdigest()==h,rel
 count+=1
assert count==37
print('NEW_EXTERNAL_SOURCEBINDING_ROOT',out)
print('CRITIC_REHASH',json.dumps({'pins':verified,'all_37_ledger_payloads_verified':True}))
listing=[]
for p in producer.iterdir():
 if 'private' not in p.name.casefold() and 'source_frozen' not in p.name.casefold() and 'key' not in p.name.casefold():
  listing.append({'name':p.name,'directory':p.is_dir(),'bytes':None if p.is_dir() else p.stat().st_size})
print('PERMITTED_PRODUCER_TOPLEVEL_NONPRIVATE',json.dumps(listing,indent=2))
for attempt in ['attempt-r1','attempt-r2','attempt-r3']:
 p=producer/attempt
 if p.is_dir():
  print('ATTEMPT_NONPRIVATE_TOPLEVEL',attempt,json.dumps([{'name':f.name,'directory':f.is_dir(),'bytes':None if f.is_dir() else f.stat().st_size} for f in p.iterdir() if not any(k in f.name.casefold() for k in ['private','key','source_frozen'])],indent=2))
(out/'critic-rehash.json').write_text(json.dumps({'verified_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pins':verified,'ledger_payloads_verified':count},indent=2)+'\n',encoding='utf-8')
for path in [pathlib.Path(r'C:\Users\blith\AppData\Local\Temp\opencode\sightbreak-v3\AGENTS.md'),pathlib.Path(r'C:\Users\blith\AppData\Local\Temp\opencode\sightbreak-v3\docs\AGENTS.md'),pathlib.Path(r'C:\Users\blith\AppData\Local\Temp\opencode\sightbreak-v3\docs\reports\AGENTS.md'),pathlib.Path(r'C:\Users\blith\AppData\Local\Temp\opencode\sightbreak-v3\docs\reports\three-agent-evidence\AGENTS.md'),pathlib.Path(r'C:\Users\blith\AppData\Local\Temp\opencode\sightbreak-v3\docs\reports\three-agent-evidence\development-v3\AGENTS.md')]:
 if path.is_file(): print('APPLICABLE_ROUTER',str(path),'\n'+path.read_text(encoding='utf-8'))