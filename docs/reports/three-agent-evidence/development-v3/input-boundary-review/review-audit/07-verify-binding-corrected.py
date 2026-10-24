import pathlib,sys,json,hashlib,subprocess,datetime,time,struct,re
sys.stdout.reconfigure(encoding='utf-8')
ROOT=pathlib.Path(r'C:\Users\blith\AppData\Local\Temp\opencode\sol-input-boundary-controls-20261022')
OUT=pathlib.Path(r'C:\Users\blith\AppData\Local\Temp\opencode\sol-input-component-sourcebinding-20261023T011730421928Z')
REPO=pathlib.Path(r'C:\Users\blith\AppData\Local\Temp\opencode\sightbreak-v3')
(OUT/'07-verify-binding-corrected.py').write_text(pathlib.Path(__file__).read_text(encoding='utf-8'),encoding='utf-8')
commands=json.loads((OUT/'actual-git-commands.json').read_bytes())
def sha(b):return hashlib.sha256(b).hexdigest()
def git(*args):
 argv=['git','-C',str(REPO),*args];started=datetime.datetime.now(datetime.timezone.utc).isoformat();t=time.perf_counter()
 p=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)
 commands.append({'argv':argv,'started_utc_local':started,'elapsed_seconds':time.perf_counter()-t,'exit':p.returncode,'stdout_bytes':len(p.stdout),'stdout_sha256':sha(p.stdout),'stderr':p.stderr.decode('utf-8',errors='replace')})
 (OUT/'actual-git-commands.json').write_text(json.dumps(commands,indent=2)+'\n',encoding='utf-8')
 if p.returncode:raise RuntimeError(commands[-1])
 return p.stdout
expected={'sample-bd249c':'f3ceaad98e089aa393c7f5fa650a52695094d979','sample-05ec6c':'701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd'}
r3=json.loads((ROOT/'attempt-r3/private/SOURCE_FROZEN_BEFORE_EXECUTION.json').read_bytes())
assert {label:meta['source_commit'] for label,meta in r3['samples'].items()}==expected
cache={};proof=[]
for attempt,driver in [('attempt','attempt/private/driver-before-api-fix.py'),('attempt-r2','attempt-r2/private/driver-before-log-fix.py'),('attempt-r3','run.py')]:
 key=json.loads((ROOT/attempt/'private/SOURCE_FROZEN_BEFORE_EXECUTION.json').read_bytes())
 assert sha((ROOT/driver).read_bytes())==key['driver_sha256']
 for label,meta in key['samples'].items():
  project=ROOT/attempt/'private'/label
  assert sha((project/'probe.gd').read_bytes())==key['probe_sha256']
  assert sha((project/'project.godot').read_bytes())==meta['config_sha256']
  for path,record in meta['files'].items():
   ident=(meta['source_commit'],path)
   if ident not in cache:
    b=git('show',meta['source_commit']+':'+path)
    oid=git('rev-parse',meta['source_commit']+':'+path).decode().strip()
    calc=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
    assert oid==calc==record['blob']
    cache[ident]=(b,oid)
    dest=OUT/'git-objects'/meta['source_commit']/path;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b)
   b,oid=cache[ident];retained=(project/pathlib.Path(path).name).read_bytes()
   assert b==retained and oid==record['blob'] and sha(b)==record['sha256']
   proof.append({'attempt':attempt,'label':label,'commit':meta['source_commit'],'source_path':path,'git_blob':oid,'bytes':len(b),'sha256':sha(b),'git_object_retained_recorded_exact_match':True,'probe_sha256_verified':key['probe_sha256'],'driver_sha256_verified':key['driver_sha256'],'config_sha256_verified':meta['config_sha256']})
match=[]
for commit in expected.values():
 path='game/scripts/gameplay/match.gd';b=git('show',commit+':'+path);oid=git('rev-parse',commit+':'+path).decode().strip()
 assert oid==hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
 lines=b.splitlines(keepends=True);snippet=b''.join(lines[985:1011]);text=snippet.decode('utf-8')
 dest=OUT/'match-rpc-excerpts'/(commit+'.lines-986-1011.gd.txt');dest.parent.mkdir(exist_ok=True);dest.write_bytes(snippet)
 match.append({'commit':commit,'path':path,'git_blob':oid,'full_file_bytes':len(b),'full_file_sha256':sha(b),'retained_excerpt_lines':[986,1011],'excerpt_sha256':sha(snippet),'excerpt':text})
 print('MATCH_RPC',commit,oid,'\n'+''.join(f'{i+986}: {line}' for i,line in enumerate(text.splitlines(keepends=True))))
assert match[0]['git_blob']==match[1]['git_blob'] and match[0]['full_file_sha256']==match[1]['full_file_sha256']
engine=pathlib.Path(r'C:\Users\blith\AppData\Local\Temp\opencode\godot\Godot_v4.7.2-stable_win64.exe')
digest=hashlib.sha256();n=0
with engine.open('rb') as f:
 for block in iter(lambda:f.read(1024*1024),b''):digest.update(block);n+=len(block)
actual=digest.hexdigest();assert actual==r3['engine_sha256']
def pe_version(path):
 with path.open('rb') as f:
  def at(offset,size):f.seek(offset);b=f.read(size);assert len(b)==size;return b
  assert at(0,2)==b'MZ';pe=struct.unpack('<I',at(0x3c,4))[0];assert at(pe,4)==b'PE\0\0'
  coff=at(pe+4,20);sections=struct.unpack_from('<H',coff,2)[0];opt_size=struct.unpack_from('<H',coff,16)[0];opt=at(pe+24,opt_size);magic=struct.unpack_from('<H',opt,0)[0];dstart=112 if magic==0x20b else 96
  resource_rva,resource_size=struct.unpack_from('<II',opt,dstart+2*8)
  table=at(pe+24+opt_size,sections*40);maps=[]
  for i in range(sections):
   vs,va,rawsize,rawptr=struct.unpack_from('<IIII',table,i*40+8);maps.append((va,max(vs,rawsize),rawptr))
  def offset(rva):
   for va,size,pointer in maps:
    if va<=rva<va+size:return pointer+rva-va
   raise ValueError('RVA not mapped')
  resource_base=offset(resource_rva)
  def children(rel):
   h=at(resource_base+rel,16);count=sum(struct.unpack_from('<HH',h,12));entries=at(resource_base+rel+16,8*count)
   return [struct.unpack_from('<II',entries,8*i) for i in range(count)]
  node=next(v for name,v in children(0) if name==16)
  while node&0x80000000:node=children(node&0x7fffffff)[0][1]
  data_rva,size,codepage,reserved=struct.unpack('<IIII',at(resource_base+node,16));blob=at(offset(data_rva),size)
  pos=6
  while blob[pos:pos+2]!=b'\0\0':pos+=2
  key=blob[6:pos].decode('utf-16-le');pos=(pos+2+3)&~3
  fixed=struct.unpack_from('<13I',blob,pos);assert key=='VS_VERSION_INFO' and fixed[0]==0xfeef04bd
  version=lambda ms,ls:[ms>>16,ms&0xffff,ls>>16,ls&0xffff]
  return {'fixed_file_version':version(fixed[2],fixed[3]),'fixed_product_version':version(fixed[4],fixed[5]),'resource_bytes':size}
pev=pe_version(engine)
assert pev['fixed_file_version'][:3]==[4,7,2]
engineproof={'path':str(engine),'bytes_streamed':n,'sha256':actual,'recorded_sha256':r3['engine_sha256'],'recorded_version':r3['engine_version'],'pe_version_resource':pev,'independently_executed_for_version':False,'version_limit':'PE numeric version independently read; full stable/official/build suffix corroborated by recorded version and retained banners only, not a new --version execution.'}
rawproof=[]
for label in expected:
 native=ROOT/'attempt-r3/neutral'/label;project=ROOT/'attempt-r3/private'/label
 r=json.loads((native/'result.json').read_bytes());core={k:v for k,v in r.items() if k not in ['label','actual_exit']}
 persisted=json.loads((project/'probe-result.json').read_bytes())
 lines=[line for line in (native/'probe.engine.log').read_text(encoding='utf-8').splitlines() if line.startswith('INPUT_BOUNDARY_RESULT ')]
 assert len(lines)==1 and json.loads(lines[0].split(' ',1)[1])==core==persisted
 for phase in ['import','probe']:
  proc=json.loads((native/(phase+'.process.json')).read_bytes());log=(native/(phase+'.engine.log')).read_text(encoding='utf-8')
  assert proc=={'complete':True,'exit':0,'errors':[]} and r3['engine_version'] in log
  assert log.strip()
 assert r['checks']==21 and r['failures']==0 and r['actual_exit']==0
 rawproof.append({'sample':label,'source_commit':expected[label],'neutral_core_equals_engine_line_and_persisted_project_result':True,'checks':21,'failures':0,'probe_actual_exit_recorded':0,'import_actual_exit_recorded':0,'persisted_sha256':sha((project/'probe-result.json').read_bytes()),'engine_version_banner_matches_record':True})
summary={'source_binding':proof,'r3_mapping_verified':expected,'exact_module_comparisons':len(proof),'match_rpc_source_only':match,'match_file_identical_across_refs':True,'engine_streamhash_static_version':engineproof,'r3_native_receipt_consistency':rawproof,'no_new_native_execution':True,'source_postunchanged_limit':'Current retained production/probe/config bytes match pre-execution recorded hashes and exact Git objects; driver has explicit post checks for modules and probe, not configuration; not trusted historical attestation.'}
(OUT/'source-binding-verification.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
print('BINDING_SUMMARY',json.dumps({k:v for k,v in summary.items() if k!='match_rpc_source_only'},indent=2))