import os,json,hashlib,zipfile,stat,subprocess,sys,time
from pathlib import Path
sys.path.insert(0,'/workspace/sightbreak/scripts')
import build_manifest as m, verify_builds as v
from native_log import failed
root=Path(os.environ['SIGHTBREAK_BUILDS_DIR']);receipt=json.loads((root/'manifest.json').read_text());out=Path(sys.argv[1]);out.mkdir(parents=True)
unpacked=out/'unpacked';unpacked.mkdir()
checks=[]
def check(condition,message):
 if not condition: raise RuntimeError(message)
 checks.append(message)
for descriptor in receipt['artifacts']:
 path=root/descriptor['path']
 with path.open('rb') as stream: digest=hashlib.file_digest(stream,'sha256').hexdigest()
 check(digest==descriptor['sha256'] and path.stat().st_size==descriptor['bytes'],'artifact '+descriptor['path'])
for record in receipt['exports']:
 target=record['target'];archive=root/f"sightbreak-{target}-{'xcode-project' if target=='ios' else 'debug'}.zip"
 with zipfile.ZipFile(archive) as z:
  names=z.namelist();expected={row['path'] for row in record['payload']}|{target+'/source.json'}
  check(len(names)==len(set(names)) and set(names)==expected,'exact archive inventory '+target)
  check(json.loads(z.read(target+'/source.json'))==record,'receipt bytes '+target)
  for row in record['payload']:
   info=z.getinfo(row['path']);mode=info.external_attr>>16
   check(stat.S_ISREG(mode) and mode&0o777==row['archive_mode'],'archive mode '+row['path'])
   data=z.read(info)
   check(hashlib.sha256(data).hexdigest()==row['sha256'] and len(data)==row['bytes'],'payload '+row['path'])
   dest=unpacked/row['path'];check(dest.resolve().is_relative_to(unpacked.resolve()),'safe path '+row['path'])
   dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data);dest.chmod(mode&0o777)
   check(stat.S_IMODE(dest.stat().st_mode)==row['archive_mode'],'extracted mode '+row['path'])
v.BUILDS=unpacked
for target in ('linux','windows','macos'):
 if target in receipt['targets']:check(v.desktop_resources(target)>0,'extracted runtime content '+target)
state=out/'native-state';env=dict(os.environ)
for key,part in [('XDG_DATA_HOME','data'),('XDG_CONFIG_HOME','config'),('XDG_CACHE_HOME','cache')]:
 (state/part).mkdir(parents=True);env[key]=str(state/part)
command=[str(unpacked/'linux/sightbreak.sh'),'--headless','--','--smoke']
with (out/'linux-launcher.log').open('w') as f:r=subprocess.run(command,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=60)
log=(out/'linux-launcher.log').read_text();check(r.returncode==0 and 'SIGHTBREAK_MAIN_READY screen=menu' in log and not failed(log),'extracted Linux launcher native startup')
(out/'results.json').write_text(json.dumps({'passed':True,'source_commit':receipt['source_commit'],'checks':len(checks),'targets':receipt['targets'],'command':command,'exit':r.returncode,'limitations':'Other native hosts and graphical input verified separately.'},indent=2)+'\n')
print('Verified',len(checks),'delivery checks; native extracted launcher exit',r.returncode)
