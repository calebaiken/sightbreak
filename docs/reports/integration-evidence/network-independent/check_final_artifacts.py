from pathlib import Path
import hashlib, json, struct, subprocess, zipfile
ROOT=Path('/workspace/sightbreak-integration'); OUT=Path(__file__).resolve().parent/'final-artifacts'; OUT.mkdir(exist_ok=True)
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()
def sha(path):
 with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pack(path,embedded=False):
 data=path.read_bytes(); start=0
 if embedded:
  size,magic=struct.unpack_from('<QI',data,len(data)-12);assert magic==0x43504447
  start=len(data)-12-size
 magic,version,major,minor,patch,flags,base,directory=struct.unpack_from('<6IQQ',data,start)
 assert magic==0x43504447 and version in (3,4) and not flags&1
 count,=struct.unpack_from('<I',data,start+directory);at=start+directory+4; records={}
 for i in range(count):
  length,=struct.unpack_from('<I',data,at);at+=4
  name=data[at:at+length].rstrip(b'\0').decode();at+=length
  offset,size=struct.unpack_from('<QQ',data,at);expected_md5=data[at+16:at+32];fileflags,=struct.unpack_from('<I',data,at+32);at+=36
  assert not fileflags&1
  content=data[start+base+offset:start+base+offset+size]
  assert len(content)==size and hashlib.md5(content).digest()==expected_md5,(name,offset,base)
  records[name]=hashlib.sha256(content).hexdigest()
 return records
runtime=hashlib.sha256()
for p in sorted((ROOT/'game').rglob('*')):
 rel=p.relative_to(ROOT/'game')
 if p.is_file() and '.godot' not in rel.parts and 'tests' not in rel.parts:runtime.update(rel.as_posix().encode()+b'\0'+p.read_bytes()+b'\0')
content=runtime.hexdigest(); current=git('rev-parse','HEAD');tree=git('rev-parse','HEAD:game'); assert not git('status','--porcelain','--','game')
report={'inspection_commit':current,'game_tree':tree,'source_content_sha256':content,'artifacts':{}}
packs={}
for target in ('linux','android','ios'):
 record=json.loads((ROOT/'builds'/target/'source.json').read_text());assert record['source_game_tree']==tree and record['source_content_sha256']==content and record['export_completed'] and not record['source_game_dirty']
 for entry in record['payload']:
  p=ROOT/'builds'/entry['path'];assert p.stat().st_size==entry['bytes'] and sha(p)==entry['sha256']
 artifact=ROOT/'builds'/record['artifact']['path'];assert sha(artifact)==record['artifact']['sha256']
 if target=='linux':paths=pack(artifact,True)
 elif target=='ios':paths=pack(ROOT/'builds/ios/sightbreak.pck')
 else:
  with zipfile.ZipFile(artifact) as z:
   assert z.testzip() is None
   paths={p.removeprefix('assets/'):hashlib.sha256(z.read(p)).hexdigest() for p in z.namelist() if p.startswith('assets/') and not p.endswith('/')}
 assert paths and not any('tests/' in p or p.endswith('_test.gdc') for p in paths)
 prior=json.loads((OUT.parent/(target+'-pack-content.json')).read_text())
 prior_scripts={p:h for p,h in prior.items() if p.endswith('.gdc')};scripts={p:h for p,h in paths.items() if p.endswith('.gdc')}
 changed_scripts=sorted(p for p in set(prior_scripts)|set(scripts) if prior_scripts.get(p)!=scripts.get(p))
 assert all(p.endswith('/main.gdc') for p in changed_scripts),(target,'unapproved compiled runtime change',changed_scripts)
 for fragment in ('relay_ar.glb-','relay_ar_arms.glb-','relay_ar_hands.glb-'):assert any(fragment in p and p.endswith('.scn') for p in paths)
 for module in ('state_privacy','snapshot_buffer','movement_prediction','peer_lifecycle','result_outbox'):assert any(p.endswith('/'+module+'.gdc') for p in paths)
 packs[target]=scripts
 report['artifacts'][target]={'build_commit':record['source_commit'],'artifact':record['artifact'],'payload_files_hashed':len(record['payload']),'resources':len(paths),'compiled_scripts':len(scripts),'compiled_scripts_unchanged_from_d084':len(scripts)-len(changed_scripts),'changed_compiled_scripts':changed_scripts}
 (OUT/(target+'-pack-content.json')).write_text(json.dumps(paths,indent=2)+'\n')
assert packs['linux']==packs['android']==packs['ios']
report['cross_target_compiled_scripts_identical']=len(packs['linux'])
report['scope']='Independent payload SHA256, PCK per-resource MD5/SHA256, APK CRC, runtime source content, required art/network resources; mobile installation and Xcode compilation UNVERIFIED'
(OUT/'results.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
