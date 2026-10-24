import pathlib,sys,json,hashlib,datetime,subprocess,time,stat
sys.stdout.reconfigure(encoding='utf-8')
BASE=pathlib.Path(r'C:\Users\blith\AppData\Local\Temp\opencode')
OUT=BASE/'sol-input-component-sourcebinding-20261023T011730421928Z'
PRODUCER=BASE/'sol-input-boundary-controls-20261022'
CRITIC=BASE/'sol-input-component-neutral-verdict-20261023T011249700925Z'
REPO=BASE/'sightbreak-v3'
REL='docs/reports/three-agent-evidence/development-v3/input-boundary-review'
TARGET=REPO/REL
(OUT/'09-build-publication.py').write_text(sys.orig_argv[sys.orig_argv.index('-c')+1],encoding='utf-8')
def sha(b):return hashlib.sha256(b).hexdigest()
def load(p):return json.loads(p.read_bytes())
assert not TARGET.exists(), 'Refusing to overwrite existing publication/user work'
TARGET.mkdir(parents=True,exist_ok=False)
attrs=b'* -text -filter -ident -working-tree-encoding\n'
(TARGET/'.gitattributes').write_bytes(attrs)
checkpath=REL+'/critic-neutral/audit/packets/b12609d21012ffc55b9388414fae779a98d12320da4e367a3106272dba02bd95.bin'
argv=['git','-C',str(REPO),'check-attr','text','filter','ident','working-tree-encoding','--',checkpath]
t=time.perf_counter();proc=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)
commands=load(OUT/'actual-git-commands.json');commands.append({'argv':argv,'started_utc_local':datetime.datetime.now(datetime.timezone.utc).isoformat(),'elapsed_seconds':time.perf_counter()-t,'exit':proc.returncode,'stdout_bytes':len(proc.stdout),'stdout_sha256':sha(proc.stdout),'stdout_text':proc.stdout.decode(),'stderr':proc.stderr.decode(),'scope':'Read-only attributes check for this exclusively owned new publication; no staging/index modification.'})
(OUT/'actual-git-commands.json').write_text(json.dumps(commands,indent=2)+'\n',encoding='utf-8')
assert proc.returncode==0 and len(proc.stdout.decode().splitlines())==4 and all(line.endswith(': unset') for line in proc.stdout.decode().splitlines())
(OUT/'byte-protection-check.json').write_text(json.dumps({'gitattributes_bytes':attrs.decode(),'git_check_attr_all_four_unset':True,'output':proc.stdout.decode()},indent=2)+'\n',encoding='utf-8')
packet=OUT/'publication-packet';packet.mkdir(exist_ok=False);origins=[]
def put(rel,data,origin,kind='generated-review-artifact'):
 p=packet/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(data)
 origins.append({'path':pathlib.PurePosixPath(rel).as_posix(),'bytes':len(data),'sha256':sha(data),'origin':str(origin),'kind':kind})
def copy(file,rel,kind):put(rel,file.read_bytes(),file,kind)
put('.gitattributes',attrs,'Reviewer byte-preservation rule; verified text/filter/ident/working-tree-encoding unset')
producer_inv=load(OUT/'producer-noncache-inventory.json')['files']
for e in producer_inv:
 file=PRODUCER/e['path'];b=file.read_bytes();assert len(b)==e['bytes'] and sha(b)==e['sha256'];put('producer/'+e['path'],b,file,'byte-exact-producer-origin')
for file in sorted(p for p in CRITIC.rglob('*') if p.is_file()):copy(file,'critic-neutral/'+file.relative_to(CRITIC).as_posix(),'byte-exact-unchanged-component-critic-freeze')
for sub in ['git-objects','match-rpc-excerpts']:
 for file in sorted(p for p in (OUT/sub).rglob('*') if p.is_file()):copy(file,sub+'/'+file.relative_to(OUT/sub).as_posix(),'exact-Git-object' if sub=='git-objects' else 'exact-permitted-RPC-lines-only')
for file in sorted(p for p in OUT.iterdir() if p.is_file()):copy(file,'review-audit/'+file.name,'reviewer-sourcebinding-audit')
sourceproof=load(OUT/'source-binding-verification.json')
put('SOURCE_BINDING.json',(OUT/'source-binding-verification.json').read_bytes(),'review-audit/source-binding-verification.json')
put('OMISSIONS.json',(OUT/'omissions.json').read_bytes(),'review-audit/omissions.json')
put('PROBE_ASSERTIONS.json',(OUT/'probe-assertions-and-limits.json').read_bytes(),'review-audit/probe-assertions-and-limits.json')
python_commands=[]
for file in sorted(OUT.glob('*.py')):
 python_commands.append({'executable':sys.executable,'argv_pattern':[sys.executable,'-I',str(file)] if file.name.startswith('07-') else [sys.executable,'-I','-c','<exact UTF-8 source retained at review-audit/'+file.name+'>'],'script_sha256':sha(file.read_bytes()),'script':file.name,'status':'failed Git path assumption; retained, no source changes' if file.name.startswith('05-') else 'completed or current build invocation','note':'Only offline Python/Git read commands, never producer run.py or probe.gd executed by reviewer.'})
put('ACTUAL_COMMANDS.json',json.dumps({'reviewer_actual_python_invocations':python_commands,'reviewer_actual_git_commands':commands,'producer_command_recipe_file':'review-audit/producer-command-recipes-not-os-attestation.json','producer_argv_limit':'Producer argv reconstructed from exact frozen driver, not captured per-process OS argv; original Python runner/root exit receipt not retained. Reviewer does not run the engine.','future_publication_copy':'Separate offline publish verifier writes only this new directory; post-copy actual invocation/receipt will be externally frozen, not retroactively appended to frozen payloads.'},indent=2).encode()+b'\n','Recorded reviewer commands and source-reconstructed producer recipes')
report=r'''# Input boundary review: post-freeze source binding

## Bounded conclusion

The separately frozen neutral result now binds to exact recorded component sources:

| Neutral label | Verified source commit | Recorded fully ACKed replay return |
| --- | --- | --- |
| sample-bd249c | `f3ceaad98e089aa393c7f5fa650a52695094d979` | false, rejected counter increments |
| sample-05ec6c | `701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd` | true, no rejection increment |

The added empty-staging guard in the former source explains the narrow component distinction while preserving queued/unACKed retries. Both retain original queued movement/fire payloads and later new sequence 3. This does **not** establish a full-network win, actual Match/timer/actor behavior, PR20 integration, gameplay acceptance or release approval. The separate large-network packet key and verdict are outside this follow-up; neither was opened or changed.

The original independent component freeze remains byte-exact under `critic-neutral/`; this document is an explicitly post-freeze addendum, not a rewritten blind verdict. The main-author neutral assessment is separately preserved and is not counted as independent QA.

## Frozen-before-key boundary

Before opening/printing component source-key contents, I rehashed the independent component `FROZEN.json`, report and ledger against the supplied full pins, verified all 37 critic ledger payloads, and verified both files bound by the main-author freeze:

- Main recorded freeze: **2026-10-23 01:05:20.506667 UTC**; `MAIN_NEUTRAL_FREEZE.json` SHA256 `c2c2d24bed297c4166137166b0d13f80dbd279f2ab7b5ee438bb5d36a4a68d21`; its assessment SHA256 `19a195c9661eb958be3968162ec73df130eb04184feb9a76dd9d1e94eca42dfb` and r3 RESULTS hash both match.
- Independent critic recorded freeze: **2026-10-23 01:12:49.902292 UTC**; FROZEN `d9c883f4e60ccbda05bd02191421d2acccf5d336bbaa9927b2f83748eb333c78`; report `cff57e331635ec0c3d2f65398f6fd4bf83ee339090211c3a2df75c19e3b0c51a`; ledger `446cbfd2dc80ab913212776b6f4024b425cb8669f55c891be03f8397f39ac2db`.
- This review's both-freezes rehash receipt records **01:18:07.597537 UTC**, followed by component source-key inspection. The exact receipt is in `review-audit/both-neutral-freezes-verified-before-key.json`.

These are **local unsigned records**, not a trusted timestamp, signed execution attestation or proof of historical human behavior. The source-key JSON itself has hashes but no trusted creation timestamp. The exact driver writes it before its import/probe loops; that is source-order evidence, not cryptographic proof of launch chronology. Source identity blinding ended only for this tiny component after the freeze boundary. Behavioral blinding was never complete: visible return values expose the behavior under comparison, and the critic already had unrelated large-packet neutral outcome context without its identity key.

## Exact source binding and engine custody checks

I verified all **12 module instances** across all six prepared projects in r1/r2/r3. For each, commit:path bytes from Git, Git blob identity (also recomputed as SHA1 over the Git blob header/content), recorded SHA256 and current retained project bytes match exactly. No parent commit, branch source, broader identity map or unprovided controller/release source was read.

| Production module | Ref(s) | Blob | SHA256 |
| --- | --- | --- | --- |
| input_stream.gd | f3ceaad… | `f0516be1ab2416d36ba3b62f37083f371364f3a4` | `b455205d827134830637f03457cc67e4e321721d91a7d840941fc74e1b26c88e` |
| input_stream.gd | 701ce2c… | `7b4cf13453a15988bb1281e49e0b6eb3835461e5` | `60d92e1cacc838867f9241379cbf3bc8b27a025fd1b91ca191effc37354d7ccc` |
| input_gate.gd | both | `bf23a5b8c6e634121fca9f5daeb2a4d731ff6538` | `4717f892f56d0f5e70aeb321454a986c714be74f150b907f77a90ed380e23c77` |

The production paths are `game/scripts/network/input_stream.gd` and `game/scripts/network/input_gate.gd`; exact bytes are included for both refs. Each attempt's retained probe/config and original driver snapshot also match its source-key hashes. R3 root `run.py` is `b1815f26b57d9169067e6e04c06a132a066deda7baf4f310be1632309f2f6162`; r3 probe is `cb03f812bc765ab996a36768915874bc8ce2c64968f15a11850c77c74cb9b563`; configuration is `5fff83ac9be6b9f4aa57d5830a7c9bb43e767028fe61cff56f08c6a041012d7e`.

The retained projects now match the recorded pre-launch hashes. The driver explicitly checks production-module and probe hashes after each completed project. It does not explicitly post-check config; this review independently checked its retained bytes against the recorded config hash. These comparisons support unchanged retained bytes, not absolute authenticated historical execution.

I independently streamhashed **180,858,888 bytes** of the actual recorded engine executable without running it: SHA256 `ab1824f85bfd8e0e4128182c000c4003a3e042245b2967848d089b2a04b22424`, matching all three source records. Static PE version-resource inspection gives file/product version **4.7.2.0**. The full recorded version `4.7.2.stable.official.ed1daf0bf` agrees with retained engine-log banners; the build suffix was not independently obtained by executing `--version`. The executable is excluded from publication.

The producer imports `matrix_process.run_process` and `native_log.failed` from outside the permitted producer root. Those helper sources were not provided for inspection and were not read or included. Their internals, actual OS command-line capture and root-runner exit status are not authenticated by this source binding. Producer command recipes are reconstructed from exact driver source and separately labeled; actual reviewer Python/Git read commands are recorded without pretending the recipe is an OS receipt.

## Why the source explains the two returns

Both InputStream versions stage every sanitized command whose sequence exceeds ACK. They validate/sanitize even ACKed commands before filtering them out, so an old malformed fire string is not silently exempted. They only insert a staged sequence if it is not already in the queue, preserving the first queued original payload.

The f3ceaad version then checks `staged.is_empty()` at lines 38-40, increments rejection and returns false. The 701ce2c version lacks that guard and returns true after an empty insertion loop. Thus:

- Fully ACKed sequences 1/2 at ACK2 have no staged fresh work: false only with the new guard.
- A still-queued sequence above ACK is staged even if already queued: a legitimate queued/unACKed retry remains true and cannot rewrite its first payload.
- A mixed ACKed/new batch stages sequence3, so it remains accepted.

The recorded component data independently show this distinction for identical and altered replays. Both variants have the same queue/ACK/rate transitions in this fixture; only the two replay return values and resulting rejection-counter offset differ. The narrow component signal advantage is not converted into a throughput/latency or gameplay claim.

## Match call-site inference — source only

The actual permitted path is `game/scripts/gameplay/match.gd`. Its full Git blob is **identical across both refs**, `c06f7b4177a40819fa44eee6ee678c3958fce752`. Only exact lines **986-1011** are semantically reviewed/published, with full-file hash/blob identity recorded in `SOURCE_BINDING.json`.

At 997-998, `_input_rpc` returns when `_input_stream.accept(...)` is false. That early return precedes:

- `_peer_lifecycle.active(...)` at 999;
- alias confirmation logic at 1002-1006;
- the **conditional** `_last_activity[id] = _elapsed` at 1009-1010;
- `_last_peer_input[id] = _elapsed` at 1011.

Therefore, if this RPC reaches the accept call and returns false, it skips those subsequent updates on that invocation. `_last_activity` must not be described as an unconditional update on true: its movement/look/interaction predicate still applies. Prior guards, including `_peer_lifecycle.allow_input` at 991, execute before accept; their internal side effects were not reviewed here. This is not proof that no other path can affect lifecycle/activity.

The RPC expects an unreliable-ordered compressed packet, enforces packed-size bounds and performs DEFLATE decompression before accept. The component instead directly calls `var_to_bytes` / `bytes_to_var` and `stream.accept`. **No Match instance, RPC dispatch, timer, lifecycle expiry, network socket, 300 ms silence deadline, 30 s retirement or physical actor was executed in this component.** The call-site link is source inference only.

## The actual 21 checks and 22 serialized instances

The exact r3 probe has 21 check calls. I matched the first 20 predicates independently to each sample's full raw event data. The two fully ACKed accept results at probe lines 68 and 70 are deliberately **not asserted**; checks 11/12 only assert ACK2 plus an empty queue. Consequently both can report 21/0 without equal accept-return behavior. The source comment explicitly describes the compared outcome as recorded rather than prescribed.

The 21st check (83-84) calls `stream.forget(41)` directly and asserts absence of peer41 in queues, ACKs and rates. No after-forget state event was retained, so its runtime evidence is the aggregate 21/0 plus source; it is not an independently traced cleanup event. `forget` erases three stream-owned map entries, not an actor or network session. The earlier neutral limitation “no disconnect evidence” remains correct for live disconnect/timers; this addendum adds the now-visible **component-unit forget assertion** without rewriting the old verdict.

The exact input-gate module is bound, but this probe/InputStream uses its `BOOLEAN_FIELDS` constant; `InputGate.validate` and `allow_buy` are not exercised by these calls. Backlog dropping (>6 commands), rate threshold (>90 calls), bucket rollover (>=1000 supplied ms), exact +120 acceptance and extensive malformed/type/epoch combinations are source policies, not newly proven native boundaries here. The +121 rejection and malformed-old-first packet are useful but do not prove all adjacent limits or general batch atomicity.

I rechecked all **22 serialized packet instances / seven unique byte strings** using only the bounded Python Decoder class from the frozen critic script, isolated with AST so no frozen top-level code runs or rewrites anything. All bytes fully decode, match JSON payloads and roundtrip exactly with preserved types. This is a narrow decoder for observed unflagged types, not a full protocol/compression/fuzz audit.

Both samples consume exactly sequences1/2/3 with movement +1/+1/-1 and fire true/false/true, then an empty pop. Those are payloads, not actor shots/ammo or physical movement. Both charge their rate bucket on all 11 accept attempts, including rejected attempts; final start/count is1000/11. Supplied rate times span600ms, while retained capture timestamps span only2ms per process. These clocks neither test a production inactivity origin nor establish a wall-time performance comparison.

## Failures preserved, not rerun or erased

| Attempt | Retained facts | Interpretation |
| --- | --- | --- |
| r1 (`attempt`) | Original driver snapshot/key/projects; FAILED contains `WindowsPath` has no `fileno`; no import/probe result/log receipts | Driver passed a Path instead of an open log handle and failed at the pre-import process API boundary. No import/probe execution is established. The driver's earlier `--version` preflight is separate; do not claim no native invocation of any kind historically. |
| r2 | Original driver/probe copies; import/probe receipts complete/exit0; stdout logs both zero bytes; FAILED is missing/ambiguous summary | Failed closed despite zero phase exits. A GUI/root exit0 cannot stand in for native summary evidence. No separately retained root-driver OS-exit receipt or full helper stack is available here. |
| r3 | Nonempty explicit `--log-file` engine logs for both phases/two samples; exit0 phase receipts; one summary each; separate project `probe-result.json` matches engine JSON and neutral result core | Successful retained component measurements with substantially better completion evidence. Still unsigned, not an authenticated OS execution attestation. |

No failed attempt is reclassified as an engine defect or silently dropped. The reviewer also retains an initial failed Git path lookup (assumed `game/scripts/match.gd`, exit128); a filename-only tree lookup found the permitted gameplay path, and both refs were reverified. The original critic's own count-assertion failure remains preserved in its unchanged frozen packet. No producer run or native rerun was performed during this follow-up.

## Publication, omissions and remaining gates

This publication copies **all 67 noncache producer files**, including all three attempt source keys, original failure scripts/receipts, exact modules/probes/configs, UID sidecars, r3 raw/persisted results and both main neutral-freeze files. It also preserves the complete 40-file frozen independent component packet. `ORIGINS.json` and the final ledger bind originals to copies. All 19 generated cache files (71,309 bytes) under `.godot`/`.state` are precisely indexed as omissions without inspecting/hashing their contents. The engine, unprovided helpers, full Match body outside the allowed excerpt and broader PR20/large-packet material are excluded with explicit reasons in `OMISSIONS.json`.

All payloads remain below the requested 3MiB limit. Local `.gitattributes` unsets text conversion, filter, ident and working-tree encoding; `git check-attr` confirms all four are unset for a nested binary payload. There is no staging, commit, GitHub action, network, service, database or engine run. Repository writes are exclusively this new `docs/reports/three-agent-evidence/development-v3/input-boundary-review/` subtree. Original evidence and old frozen verdicts are not modified.

The ledger covers every payload; FROZEN binds the ledger and its complete entry list, and the separate checksum binds FROZEN without a self-hash cycle. Exact whole-file-set verification after copying to the repository is externally recorded before handoff. Freeze times/hashes are local custody aids, not trusted time/authenticity claims.

**Protocol6, prediction default-off, rewind-off and all human/device/authority/privacy/full-integration gates remain.** The source-bound conclusion is limited to the two return values, their preservation controls, exact retained source identity and the static RPC early-return link. It does not independently prove PR20 integration or a full-network outcome; the separate large-packet key remains awaited and unopened here.
'''
put('REPORT.md',report.encode('utf-8'),'New post-freeze reviewer source-binding report')
addendum=r'''# Post-freeze addendum — component only

This document adds source binding **after** the independent component freeze `d9c883f4e60ccbda05bd02191421d2acccf5d336bbaa9927b2f83748eb333c78` and main neutral freeze at01:05:20 UTC were rehashed. It does not amend their bytes or reopen their neutral outcome judgment.

- The component mapping is verified against Git-object identities, recorded SHA256 and retained projects: bd249c=f3ceaad98e089aa393c7f5fa650a52695094d979;05ec6c=701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd.
- The former adds an empty-staged-work guard, explaining false for fully ACKed replay while queued/unACKed retries stay valid. Both consume the same original payloads.
- The identical Match RPC source returns before its later lifecycle.active, conditional last_activity and last_peer_input updates on accept=false. This is **source inference, not executed Match/timers**.
- Both21/0 summaries are expected: the two compared return values are deliberately recorded, not asserted. Source also reveals check21 directly calls component forget and tests three map removals; no traced post-forget state or actual disconnect was retained. The old live-disconnect limitation is unchanged.
- Twenty event predicates per sample and all22 serialized instances are independently rechecked offline. Actor fire, movement, lifecycle,30s expiry, DEFLATE/UDP, real client behavior and unprovided helper internals are not proven.
- All historical failures, raw logs and exact source/probe/driver/config snapshots remain published; engine binary and generated caches are omitted/indexed. No native run or staging/commit occurred.

Local-record ordering and matching hashes are not signed execution or trusted timestamps. No large-network identity key or broader PR20 source/controller/release mapping was opened. No full-network win, release approval or PR20 integration follows from this component alone. See REPORT.md, SOURCE_BINDING.json and PROBE_ASSERTIONS.json for exact evidence and limits.
'''
put('POST_FREEZE_ADDENDUM.md',addendum.encode(),'New explicitly post-freeze source-only addendum')
readme='''# Input-boundary review packet\n\nStart with [REPORT.md](REPORT.md) and [POST_FREEZE_ADDENDUM.md](POST_FREEZE_ADDENDUM.md).\n\n- `producer/`: all permitted noncache originals, three attempts and failure snapshots, main neutral freeze.\n- `critic-neutral/`: complete unchanged independent component neutral freeze.\n- `git-objects/`, `match-rpc-excerpts/`, `SOURCE_BINDING.json`: exact module and restricted source binding.\n- `PROBE_ASSERTIONS.json`, `ACTUAL_COMMANDS.json`, `review-audit/`: reproducible offline checks and command/receipt distinctions.\n- `ORIGINS.json`, `OMISSIONS.json`: full payload origin index and precise exclusions.\n- `SHA256SUMS.txt`, `FROZEN.json`, `FROZEN.sha256`: complete payload ledger and non-self-referential hash chain.\n\nAll native receipts are historical and unsigned. No Match/timer/UDP/actor/network victory, PR20 integration or release approval is claimed. Existing neutral verdicts are unmodified. Do not confuse the component key with the separate large-network key.\n'''
put('README.md',readme.encode(),'Reviewer packet navigation')
frozen_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='microseconds').replace('+00:00','Z')
put('FROZEN_UTC.txt',(frozen_utc+'\n').encode(),'Local unsigned sourcebinding/publication freeze record')
origin_index={'scope':'Every payload origin is indexed below; generated hash-chain metadata is explicitly separately accounted to avoid impossible self-hash cycles. Full payload hashes/sizes are bound by SHA256SUMS and FROZEN.','entries':origins.copy(),'generated_metadata_origin':{'ORIGINS.json':'Generated index, self-entry covered by ledger','SHA256SUMS.txt':'Generated final payload hash ledger, hash bound by FROZEN','FROZEN.json':'Generated freeze/ledger binding, hash in FROZEN.sha256 and external handoff','FROZEN.sha256':'Generated final checksum, externally whole-file-set verified'},'precise_omissions_file':'OMISSIONS.json'}
put('ORIGINS.json',json.dumps(origin_index,indent=2).encode()+b'\n','Generated complete origin index; self-hash bound externally by ledger')
entries=[{'path':file.relative_to(packet).as_posix(),'bytes':file.stat().st_size,'sha256':sha(file.read_bytes())} for file in sorted((p for p in packet.rglob('*') if p.is_file()),key=lambda p:p.relative_to(packet).as_posix())]
(packet/'SHA256SUMS.txt').write_text(''.join(e['sha256']+'  '+e['path']+'\n' for e in entries),encoding='utf-8',newline='\n')
frozen={'schema':1,'frozen_utc':frozen_utc,'kind':'post-neutral-freeze sourcebinding component publication','external_packet':str(packet),'exclusive_repository_path':REL,'source_mapping':sourceproof['r3_mapping_verified'],'critic_neutral_freeze_sha256':'d9c883f4e60ccbda05bd02191421d2acccf5d336bbaa9927b2f83748eb333c78','main_neutral_freeze_sha256':'c2c2d24bed297c4166137166b0d13f80dbd279f2ab7b5ee438bb5d36a4a68d21','source_only_match_rpc_inference':True,'new_native_execution':False,'large_network_key_opened':False,'full_network_or_release_approval':False,'ledger_sha256':sha((packet/'SHA256SUMS.txt').read_bytes()),'payload_count':len(entries),'entries':entries,'metadata_chain':'SHA256SUMS covers every payload including ORIGINS and UTC; FROZEN binds ledger; FROZEN.sha256 binds FROZEN. Metadata excluded from self-cycles is externally inventoried/verified after publication.'}
(packet/'FROZEN.json').write_text(json.dumps(frozen,indent=2)+'\n',encoding='utf-8');fhash=sha((packet/'FROZEN.json').read_bytes())
(packet/'FROZEN.sha256').write_text(fhash+'  FROZEN.json\n',encoding='ascii')
files=[p for p in packet.rglob('*') if p.is_file()];size=sum(p.stat().st_size for p in files)
assert size<=3*1024*1024,size
assert all(not any(k in p.relative_to(packet).parts for k in ['.godot','.state']) and p.suffix.lower()!='.exe' for p in files)
assert sha((packet/'critic-neutral/FROZEN.json').read_bytes())=='d9c883f4e60ccbda05bd02191421d2acccf5d336bbaa9927b2f83748eb333c78'
for e in entries:
 b=(packet/e['path']).read_bytes();assert len(b)==e['bytes'] and sha(b)==e['sha256']
for file in files:file.chmod(stat.S_IREAD)
print(json.dumps({'external_packet':str(packet),'repository_target_prepared_attributes_only':str(TARGET),'sourcebinding_frozen_utc':frozen_utc,'FROZEN_sha256':fhash,'ledger_sha256':frozen['ledger_sha256'],'REPORT_sha256':sha((packet/'REPORT.md').read_bytes()),'payload_count':len(entries),'total_file_count':len(files),'total_bytes':size,'below_3MiB':True,'external_payloads_verified':True,'publication_copy_pending':True},indent=2))