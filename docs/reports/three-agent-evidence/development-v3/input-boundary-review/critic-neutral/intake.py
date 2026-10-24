import pathlib,sys,json,hashlib,datetime,stat
sys.stdout.reconfigure(encoding='utf-8')
source=pathlib.Path(r'C:\Users\blith\AppData\Local\Temp\opencode\sol-input-boundary-controls-20261022\attempt-r3\neutral')
base=pathlib.Path(r'C:\Users\blith\AppData\Local\Temp\opencode')
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
root=base/('sol-input-component-neutral-'+stamp)
root.mkdir(exist_ok=False)
(root/'intake.py').write_text(sys.orig_argv[sys.orig_argv.index('-c')+1],encoding='utf-8')
inventory=[]
for file in sorted(source.rglob('*')):
 assert not file.is_symlink(), str(file)
 if not file.is_file(): continue
 rel=file.relative_to(source);data=file.read_bytes();target=root/'packet'/rel
 target.parent.mkdir(parents=True,exist_ok=True)
 with target.open('xb') as f:f.write(data)
 inventory.append({'path':rel.as_posix(),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
(root/'intake-inventory.json').write_text(json.dumps({'source_directory_only':str(source),'python_executable':sys.executable,'python_version':sys.version,'copied_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':inventory},indent=2)+'\n',encoding='utf-8')
print('ISOLATED_ROOT',root)
print('INVENTORY',json.dumps(inventory,indent=2))
for name in ['README.md','MANIFEST.json','manifest.json']:
 file=root/'packet'/name
 if file.is_file(): print('FILE',name,'\n'+file.read_text(encoding='utf-8'))