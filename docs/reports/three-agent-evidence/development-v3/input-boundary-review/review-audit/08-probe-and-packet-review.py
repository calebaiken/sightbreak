import pathlib,sys,json,hashlib,re,ast,struct,os,datetime
sys.stdout.reconfigure(encoding='utf-8')
ROOT=pathlib.Path(r'C:\Users\blith\AppData\Local\Temp\opencode\sol-input-boundary-controls-20261022')
OUT=pathlib.Path(r'C:\Users\blith\AppData\Local\Temp\opencode\sol-input-component-sourcebinding-20261023T011730421928Z')
CRITIC=pathlib.Path(r'C:\Users\blith\AppData\Local\Temp\opencode\sol-input-component-neutral-verdict-20261023T011249700925Z')
(OUT/'08-probe-and-packet-review.py').write_text(sys.orig_argv[sys.orig_argv.index('-c')+1],encoding='utf-8')
def sha(b):return hashlib.sha256(b).hexdigest()
probe=(ROOT/'probe.gd').read_text(encoding='utf-8').splitlines()
assertions=[]
for line_no,line in enumerate(probe,1):
 m=re.match(r'\tcheck\((.*), "([^"]+)"\)',line)
 if m:assertions.append({'number':len(assertions)+1,'probe_line':line_no,'predicate':m.group(1),'label':m.group(2)})
assert len(assertions)==21
for label in ['sample-bd249c','sample-05ec6c']:
 r=json.loads((ROOT/'attempt-r3/neutral'/label/'result.json').read_bytes());e=r['events'];q=e[0]['after']['queue']
 predicates=[e[0]['accepted'],e[1]['accepted'],e[1]['after']['queue']==q and e[1]['after']['ack']==0,e[2]['accepted'],e[2]['after']['queue']==q,e[3]['popped']['sequence']==1 and e[3]['popped']['move']==[1.,0.] and e[3]['popped']['fire'] is True and e[3]['after']['ack']==1,e[4]['accepted'],len(e[4]['after']['queue'])==1,e[5]['popped']['sequence']==2 and e[5]['popped']['move']==[1.,0.] and e[5]['popped']['fire'] is False and e[5]['after']['ack']==2,not e[5]['after']['queue'],e[6]['after']['ack']==2 and not e[6]['after']['queue'],e[7]['after']['ack']==2 and not e[7]['after']['queue'],e[8]['accepted'],e[9]['accepted'],e[10]['popped']['sequence']==3 and e[10]['popped']['move']==[-1.,0.] and e[10]['popped']['fire'] is True,not e[11]['popped'],not e[12]['accepted'],not e[13]['accepted'],not e[14]['accepted'],not e[14]['after']['queue'] and e[14]['after']['ack']==3,None]
 assert len(predicates)==21 and all(v is True for v in predicates[:-1])
 for item,value in zip(assertions,predicates):item[label]={'raw_event_predicate_verified':value,'status':'independently matches recorded event values' if value is not None else 'No post-forget state event retained; recorded aggregate 21/0 and source direct forget/three-map assertion only.'}
source_analysis={'assertions':assertions,'two_fully_acked_return_values_not_asserted':{'probe_lines':[67,68,69,70,71],'checks_11_12_test_only':'ACK2 and empty queue, not accept return or lifecycle activity'},'forget_check':{'probe_lines':[83,84],'native_invocation_claim':'direct stream.forget(PEER), not a disconnect event','input_stream_lines_bd249c':[86,89],'raw_state_after_forget_captured':False,'scope':'Removal of three stream-owned per-peer maps only; no actor, lifecycle, timer, socket or reconnect assertion.'},'runtime_scope':'SceneTree _initialize creates RefCounted SBInputStream and makes direct var_to_bytes/bytes_to_var -> accept/pop calls synchronously. No Match instantiation/physics/network/await/actor/lifecycle timer occurs.','gate_usage':'Both exact input_gate modules loaded as class context; sanitize references BOOLEAN_FIELDS only. validate/allow_buy are not called by this probe or InputStream.accept.','known_source_policies_not_native_boundary_proven':['rate bucket reject when count >90, reset on >=1000ms','MAX_BATCH12, MAX_AHEAD120, MAX_BACKLOG6','backlog dropping retains newest two only when queue size>6','reset_epoch queue/ack clearing','all finite/vector/angle/weapon/boolean combinations','compressed Match packet envelope and 1100-byte/8192-decompression checks'],'driver_scope_limit':'matrix_process.run_process and native_log.failed are imported from outside permitted producer root and were not inspected/published. Exact driver recipe and raw receipts are retained; helper internals are not an independent execution attestation.'}
(OUT/'probe-assertions-and-limits.json').write_text(json.dumps(source_analysis,indent=2)+'\n',encoding='utf-8')
tree=ast.parse((CRITIC/'audit/audit.py').read_text(encoding='utf-8'))
node=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Decoder')
module=ast.Module(body=[node],type_ignores=[]);ast.fix_missing_locations(module)
ns={'struct':struct};exec(compile(module,'<frozen-critic-Decoder-class-only>','exec'),ns);Decoder=ns['Decoder']
packet_checks=[]
for label in ['sample-bd249c','sample-05ec6c']:
 for e in json.loads((ROOT/'attempt-r3/neutral'/label/'result.json').read_bytes())['events']:
  if e['operation']!='accept':continue
  b=bytes.fromhex(e['packet_variant_bytes_hex']);d=Decoder(b);value,typed=d.read()
  assert d.pos==len(b) and value==e['packet'] and d.encode(typed)==b
  packet_checks.append({'sample':label,'event':e['event'],'bytes':len(b),'sha256':sha(b),'full_consumption':True,'type_preserving_roundtrip':True,'json_payload_agrees':True,'native_decoder_not_executed_by_reviewer':True})
assert len(packet_checks)==22 and len({p['sha256'] for p in packet_checks})==7
(OUT/'postfreeze-packet-checks.json').write_text(json.dumps({'decoder_source_sha256':sha((CRITIC/'audit/audit.py').read_bytes()),'executed_only':'Own previously frozen bounded Python Decoder class, isolated with AST; no frozen top-level code or engine run','instances':packet_checks,'limits':'Unflagged bool/int32/UTF8 string/float32 Vector2/dictionary/array only; no DEFLATE wrapper/UDP or adversarial raw-byte corpus.'},indent=2)+'\n',encoding='utf-8')
keys={attempt:json.loads((ROOT/attempt/'private/SOURCE_FROZEN_BEFORE_EXECUTION.json').read_bytes()) for attempt in ['attempt','attempt-r2','attempt-r3']}
recipes=[]
engine=r'C:\Users\blith\AppData\Local\Temp\opencode\godot\Godot_v4.7.2-stable_win64.exe'
for attempt,key in keys.items():
 recipes.append({'attempt':attempt,'role':'preflight version recipe','argv':[engine,'--version'],'evidence':'Driver source plus recorded version string; not argv/OS receipt; not run by reviewer.'})
 for label in key['samples']:
  project=ROOT/attempt/'private'/label;raw=ROOT/attempt/'neutral'/label
  for phase,flags in [('import',['--headless','--editor','--import','--quit']),('probe',['--headless','--script','res://probe.gd'])]:
   argv=[engine,'--path',str(project)]
   if attempt=='attempt-r3':argv+=['--log-file',str(raw/(phase+'.engine.log'))]
   argv+=flags
   receipt=raw/(phase+'.process.json')
   recipes.append({'attempt':attempt,'sample':label,'phase':phase,'argv_reconstructed_from_exact_driver':argv,'cwd':str(project),'isolated_environment_keys':['APPDATA','XDG_DATA_HOME','XDG_CONFIG_HOME','XDG_CACHE_HOME'],'actual_phase_receipt_present':receipt.is_file(),'receipt':json.loads(receipt.read_bytes()) if receipt.is_file() else None,'status':'Recorded phase receipt, source-reconstructed argv (not captured OS command line)' if receipt.is_file() else 'Prepared/not evidenced as launched; first-attempt pre-import API failure or second-sample unrun after failure.'})
(OUT/'producer-command-recipes-not-os-attestation.json').write_text(json.dumps(recipes,indent=2)+'\n',encoding='utf-8')
cache_entries=[]
for parent,dirs,files in os.walk(ROOT):
 path=pathlib.Path(parent);rel=path.relative_to(ROOT)
 if any(part in ['.godot','.state'] for part in rel.parts):
  for name in files:
   file=path/name;cache_entries.append({'path':file.relative_to(ROOT).as_posix(),'bytes':file.stat().st_size,'sha256':None,'omission':'Generated .godot/.state cache; metadata indexed, contents not inspected/hashed/copied.'})
failures={'attempt_1':{'directory':'attempt','failed_receipt':json.loads((ROOT/'attempt/FAILED.json').read_bytes()),'original_driver':'attempt/private/driver-before-api-fix.py','production_import_probe_receipts':0,'interpretation':'Pre-import driver API mismatch: passes pathlib.Path as log, error WindowsPath has no fileno; no phase launch/result evidence. Version preflight occurs earlier in driver, so do not claim no native process of any kind was attempted historically. Exact helper stack not retained/audited.'},'attempt_2':{'directory':'attempt-r2','failed_receipt':json.loads((ROOT/'attempt-r2/FAILED.json').read_bytes()),'original_driver':'attempt-r2/private/driver-before-log-fix.py','original_probe':'attempt-r2/private/probe-before-file-result.gd','engine_import_probe_receipts':[json.loads((ROOT/'attempt-r2/neutral/sample-ad535c'/(phase+'.process.json')).read_bytes()) for phase in ['import','probe']],'stdout_lengths':[len((ROOT/'attempt-r2/neutral/sample-ad535c'/(phase+'.log')).read_bytes()) for phase in ['import','probe']],'interpretation':'Engine phase receipts record zero exits but stdout is empty; missing/ambiguous summary correctly fails closed. No root-driver OS exit receipt in retained packet; any enclosing/root exit0 is not proof of summary/native assertions.'},'attempt_3':{'directory':'attempt-r3','successful_recorded_samples':2,'required_nonempty_engine_file_logs':4,'independent_persisted_results_match':2,'interpretation':'Driver adds explicit --log-file, requires summary and persisted result agreement, checks recorded exits/errors and >=20 checks/0 failures; module/probe post hashes checked in source. No reruns by reviewer.'},'reviewer_failures_retained':[{'script':'05-verify-binding.py','error':'git show assumed game/scripts/match.gd exit128; correct target located by filename-only ls-tree and reverified in07 script.'}]}
(OUT/'failures-and-attempts.json').write_text(json.dumps(failures,indent=2)+'\n',encoding='utf-8')
omissions={'producer_cache_files':cache_entries,'producer_cache_file_count':len(cache_entries),'producer_cache_total_bytes':sum(e['bytes'] for e in cache_entries),'other_omissions':[{'origin':engine,'bytes':180858888,'sha256':'ab1824f85bfd8e0e4128182c000c4003a3e042245b2967848d089b2a04b22424','reason':'Native executable excluded; independently streamhashed/static PE version read without running.'},{'origin':'both refs:game/scripts/gameplay/match.gd outside lines986-1011','reason':'Only permitted RPC excerpt retained/published; full blob identity/hash recorded without reviewing other logic.'},{'origin':'scripts/matrix_process.py and scripts/native_log.py','reason':'Imported producer helper dependencies outside provided root; not inspected or included.'},{'origin':'broader PR20, old large-network identity map/source controller/release material','reason':'Not provided/authorized for this component follow-up; neither read nor included.'}]}
(OUT/'omissions.json').write_text(json.dumps(omissions,indent=2)+'\n',encoding='utf-8')
inv=json.loads((OUT/'producer-noncache-inventory.json').read_bytes())['files']
print('PROBE_CHECKS',len(assertions),'RAW_SUPPORTED_PER_SAMPLE',20,'FORGET_SUMMARY_ONLY',1)
print('POSTFREEZE_PACKET_INSTANCES',len(packet_checks),'UNIQUE',7)
print('PRODUCER_NONCACHE',len(inv),'BYTES',sum(e['bytes'] for e in inv))
print('CRITIC_FILES',sum(1 for p in CRITIC.rglob('*') if p.is_file()),'BYTES',sum(p.stat().st_size for p in CRITIC.rglob('*') if p.is_file()))
print('CACHE_OMISSION',len(cache_entries),'BYTES',omissions['producer_cache_total_bytes'])