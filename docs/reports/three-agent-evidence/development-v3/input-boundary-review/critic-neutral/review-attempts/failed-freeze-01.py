import pathlib,sys,json,hashlib,datetime,stat
sys.stdout.reconfigure(encoding='utf-8')
BASE=pathlib.Path(r'C:\Users\blith\AppData\Local\Temp\opencode')
ROOT=BASE/'sol-input-component-neutral-20261023T010534385344Z'
P=ROOT/'packet';A=ROOT/'audit'
SOURCE=pathlib.Path(r'C:\Users\blith\AppData\Local\Temp\opencode\sol-input-boundary-controls-20261022\attempt-r3\neutral')
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
V=BASE/('sol-input-component-neutral-verdict-'+stamp);V.mkdir(exist_ok=False)
def sha(b):return hashlib.sha256(b).hexdigest()
def load(p):return json.loads(p.read_bytes())
def save(name,obj):
 path=V/name;path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
(V/'finalize.py').write_text(sys.orig_argv[sys.orig_argv.index('-c')+1],encoding='utf-8')
for folder,prefix in [(P,'packet'),(A,'audit')]:
 for file in sorted(folder.rglob('*')):
  if file.is_file():
   rel=pathlib.Path(prefix)/file.relative_to(folder);target=V/rel;target.parent.mkdir(parents=True,exist_ok=True)
   target.write_bytes(file.read_bytes())
for name in ['intake.py','intake-inventory.json']:(V/name).write_bytes((ROOT/name).read_bytes())
intake=load(ROOT/'intake-inventory.json');expected={e['path']:e for e in intake['files']}
current={}
for file in SOURCE.rglob('*'):
 assert not file.is_symlink()
 if file.is_file():
  rel=file.relative_to(SOURCE).as_posix();b=file.read_bytes();current[rel]={'path':rel,'bytes':len(b),'sha256':sha(b)}
assert current==expected
assert len(expected)==16
for entry in expected.values():
 b=(V/'packet'/entry['path']).read_bytes();assert len(b)==entry['bytes'] and sha(b)==entry['sha256']
checks=load(A/'independent-checks.json');assert checks['total']==checks['verified']==326 and not checks['failed']
comp=load(A/'comparison.json');packets=load(A/'packet-decodes.json')
assert comp['unique_variant_packets']==7 and comp['serialized_packet_instances_decoded']==22
assert all(e['queue_ack_rate_equivalent'] for e in comp['event_comparison'])
assert comp['behaviorally_equivalent'] is False
limits=[
 'Only source-identity blinding: labels/keys, parent driver/probe/private/main verdict and source modules were not inspected. Behavior is visible in raw accepted/rejected outputs, and the critic has prior large-packet outcome context without its key. No label/source or cross-packet identity guesses are made.',
 'Unsigned historical local receipts/logs, no externally supplied hash pin or signed engine/OS attestation. Native banner, complete/exit0, error arrays, and matching result records are internal corroboration, not authenticated execution or verified production-source custody.',
 'No Match, lifecycle activity timestamps, simulation clock, timer decision, disconnect event, peer binding, UDP datagram, stock-client reconnect, actor movement/fire/ammo, privacy payload, default-prediction or live-rewind evidence exists in the component states.',
 'Captured monotonic values span only two milliseconds per sample. Fixture-supplied rate times span 600 milliseconds. These are distinct clocks, not a 600 ms native wait or a silence/30-second expiry test; cross-process clock origins are not comparable.',
 'Rate bucket shows 11 charges and no reset. No budget threshold, capacity exhaustion, rollover boundary, backward-clock behavior, flood load or disconnect consequence was tested.',
 'Both 21-check/0-failure summaries are retained, but exact underlying assertion code was prohibited and not read. The independent 326 checks are data/byte/state-consistency observations, not authenticated reruns or reconstruction of those 21 assertions.',
 'The byte parser is deliberately narrow for the observed unflagged Variant types. Exact decoded-payload agreement and roundtrip do not prove engine serializer/deserializer correctness for all types, flags, malformed raw bytes or protocol envelopes.',
 'One deterministic short component sequence per sample; no randomization, repeat distribution, latency/CPU/performance benchmark, packet loss/reordering, queue cap exhaustion, peer authorization or reconnect challenge coverage.',
 'A sequence distance of +121 is rejected, but exact +120/nearby acceptance boundary and full limits are not established. Old epoch 6 is rejected against observed valid epoch 7; other epoch/wrap/type cases are untested.',
 'Malformed acknowledged command is first, then valid new command. Its whole recorded packet is rejected without queue change; reversed ordering or later-invalid partial mutation/transactional atomicity is not established.',
 'Fire true/false/true are popped payload values. Two hypothetical rising edges under a simple latch are not shots, ammunition changes, latch survival through silence, or actor behavior.',
 'RESULTS.json was copied and hashed only, not used as owner/aggregate verdict evidence. Hashes pin the permitted local intake snapshot and freeze contents, not withheld source origins.',
 'Component accepted=false for fully ACKed replay offers a better non-fresh signal under the requested distinction. Whether a caller uses this boolean to renew live activity cannot be established from this packet, so no actual stale-stop or disconnect improvement is inferred.',
 'The prior large-packet frozen directory and all identity keys remained unopened and unchanged in this follow-up. This component verdict does not amend or causally explain that verdict or close its open gates.'
]
findings={'schema':1,'verdict':'Not behaviorally equivalent. sample-bd249c distinguishes both fully ACKed replays by returning false/incrementing rejected, while preserving queued-unACKed and mixed-new retries in this recorded component sequence.','component_signal_advantage':'sample-bd249c','tie_on_recorded_queue_ack_rate_and_consumption':True,'full_behavior_tie':False,'global_network_release_winner':None,'authenticated_execution':False,'native_execution_performed_by_critic':False,'sample_identity_guesses':None,'counts':{'neutral_input_files_verified':16,'events_per_sample':15,'total_events':30,'accept_attempts_per_sample':11,'pop_attempts_per_sample':4,'nonempty_pops_per_sample':3,'packet_instances_independently_decoded':22,'unique_packet_bytes':7,'independent_consistency_checks':326,'independent_consistency_check_failures':0},'important_controls':{'fully_acked_identical_replay':{'before_ack':2,'packet_sequences':[1,2],'queue_before_after':{},'bd249c_accepted':False,'05ec6c_accepted':True,'bd249c_rejected_increment':1,'05ec6c_rejected_increment':0},'fully_acked_altered_replay':{'before_ack':2,'packet_sequences':[1,2],'queue_before_after':{},'bd249c_accepted':False,'05ec6c_accepted':True,'bd249c_rejected_increment':1,'05ec6c_rejected_increment':0},'queued_retries':'Identical, altered, partially ACKed and sequence-3 queued retry all return true in both samples; existing queued payloads unchanged.','mutation_control':'Altered queued retry reverses movement and swaps fire values; both retain the first queued original values.','mixed_new_control':'At ACK2, packet with acknowledged sequence2 and new sequence3 queues only sequence3, accepted true in both.','consumption':'Both pop exactly original sequences1,2,3: moves +1,+1,-1; fire true,false,true. Fourth pop empty and ACK stays3.','invalid_controls':'Old epoch6, sequence124 at ACK3 (+121), and malformed acknowledged fire string before valid new sequence4 rejected without ACK/queue changes in both.','rate_clock':'Each of 11 accept attempts charges bucket once, including rejects; four pops do not charge; start1000 count11 in both. Supplied rate time1000..1600 versus recorded capture spans329..331 and327..329.','disconnect_evidence':'Absent; no lifecycle/Match/timer/UDP/actor inference supported.'},'limits':limits,'source_snapshot_unchanged_at_final_recheck':True,'large_packet_freeze_opened_or_modified':False,'freeze_before_any_key_or_source_followup':True}
save('FINDINGS.json',findings)
report=r'''# Independent neutral component-packet verdict

## Outcome

**The component traces are not behaviorally tied despite both reporting 21 checks and zero failures.** At this boundary, **sample-bd249c** better distinguishes a fully ACKed replay from a queued/unACKed duplicate: it returns false and increments the rejected counter for both fully ACKed replay variants, while **sample-05ec6c** returns true. Both preserve legitimate queued retries and the later mixed acknowledged/new packet in the recorded sequence.

This is a narrow **accept-return/counter distinction**, not an observed Match/lifecycle/timeout/UDP/actor improvement. All captured queue, ACK and rate-bucket transitions match between samples, and neither resurrects consumed commands. Whether an outside caller uses the accept return to refresh live-input activity is absent from this packet and was not inferred.

No source identity, key, parent run/probe/private directory, main component verdict, source module, GitHub comment or owner claim was consulted. No connection between these labels and previous neutral labels or source identities is proposed. The previous large-packet freeze was not opened or modified.

## Evidence and independent audit

The allowed input was only:

`C:\Users\blith\AppData\Local\Temp\opencode\sol-input-boundary-controls-20261022\attempt-r3\neutral\`

I copied its 16 files into a newly isolated external directory and hashed every byte. A final read-only recheck of exactly that input directory matched all original intake paths, sizes and hashes. `RESULTS.json` was only copied/hashed, not read for aggregate verdicts or owner claims. Actual evidence used was each sample's raw `result.json`, `probe.engine.log`, `import.engine.log`, process receipts and empty stdout log files.

The sole execution in this review was serial offline Python at the approved CPython 3.13.15 executable. No Godot/native engine, network, service, database, Git operation, source edit, GitHub action or commit occurred. Packet code was not inspected or executed.

### Process/result receipts

Each sample has import and probe process receipts with `complete:true`, `exit:0`, `errors:[]`. Each saved result has `actual_exit:0`, agreeing with its probe receipt. The engine logs identify themselves as `Godot Engine v4.7.2.stable.official.ed1daf0bf`; import logs show completed initialization/class registration, and the probe engine log contains one `INPUT_BOUNDARY_RESULT` JSON line. That JSON equals the saved result's complete checks/events/failures/scope core; `label` and `actual_exit` are additional saved-result metadata. Both samples log `checks:21`, `failures:0`. No unexpected native error/crash line was found. The separate `import.log` and `probe.log` files are empty in both samples, not replacements for the nonempty engine logs.

These are **unsigned historical receipts**, not independent native/OS execution attestations. The available records do not bind the claimed executable to a validated binary hash, exact invocation, PID, trusted process duration, signed capture, or withheld production-source custody. No external manifest/hash pin was supplied for this small packet; the new ledger pins this local snapshot, not its prior origin. The two matching forms of result JSON are duplicate evidence, not independent executions.

### Original serialized packet bytes

I independently decoded every `packet_variant_bytes_hex`: **22 packet instances, 7 unique byte strings**, byte-identical across samples for each matching event. A narrow bounded offline decoder parsed unflagged little-endian Godot Variant dictionaries/arrays, signed int32, strings, booleans and float32 Vector2 values, checked string padding/duplicate keys/full-byte consumption, and re-encoded each typed tree to the **exact original bytes**. Every decoded packet agrees with its raw JSON payload. All 22 instances pass; no trailing bytes were ignored.

This validates the retained serialized dictionary-boundary evidence, **not an intercepted UDP datagram or complete network protocol envelope**. Individual original `.bin` files, full hex, SHA256, decoded values and typed byte-offset traces are retained in `audit/packets/` and `audit/packet-decodes.json`.

The original 256-byte batch is epoch 7 with:

- sequence 1: move `(1,0)`, look `(0,0)`, fire **true**;
- sequence 2: move `(1,0)`, look `(0,0)`, fire **false**.

Its SHA256 is `b12609d21012ffc55b9388414fae779a98d12320da4e367a3106272dba02bd95` and it is byte-identical in the fresh, identical queued, partially ACKed and fully ACKed original replay events. The altered 256-byte batch keeps epoch/sequences/look but changes both moves to `(-1,0)` and swaps fire to **false/true**; its SHA256 is `28511e7fe9203f34e45f61f1f160e8b40ccfe115c570035184113221740fc6e4`. The same altered bytes are used before and after full ACK. The malformed case genuinely serializes fire as a **string**, not a JSON-display rendering of a Boolean.

## Complete event comparison

Event indices are zero-based. `T/F` are the component accept return, not freshness/activity timestamps. Queue and ACK results in this table are shared by both samples.

| Index/event | bd249c | 05ec6c | Recorded queue/ACK consequence |
| --- | --- | --- | --- |
| 0 fresh_batch | T | T | Empty queue becomes original sequences 1 and 2; ACK stays 0 |
| 1 identical_queued_retry | T | T | ACK 0, both sequences already queued/unACKed; no queue change |
| 2 altered_queued_retry | T | T | Changed move/fire payload cannot overwrite either queued original |
| 3 consume_first | pop 1 | pop 1 | Original +1 movement/fire true returned; ACK 0 to 1; only sequence 2 remains |
| 4 partially_acked_retry | T | T | Sequence 1 is ACKed, 2 remains queued/unACKed; neither reinserted nor mutated |
| 5 consume_second | pop 2 | pop 2 | Original +1 movement/fire false returned; ACK 1 to 2; queue empty |
| 6 fully_acked_identical_replay | **F** | **T** | Both sequences <= ACK 2 and queue empty; no queue/ACK change |
| 7 fully_acked_altered_replay | **F** | **T** | Same fully ACKed classification despite changed move/fire; no queue/ACK change |
| 8 mixed_acked_and_new_intent | T | T | ACKed sequence 2 ignored; only new sequence 3, move -1/fire true, queued |
| 9 new_intent_queued_retry | T | T | Sequence 3 still unACKed/queued; retained without mutation |
| 10 consume_new_intent | pop 3 | pop 3 | Original sequence 3 returned; ACK 2 to 3; queue empty |
| 11 no_duplicate_simulation | empty pop | empty pop | No state change; proves no fourth queue item, not Match simulation behavior |
| 12 old_epoch | F | F | Epoch 6/sequence 4 rejected; queue empty/ACK 3 unchanged |
| 13 beyond_ahead_limit | F | F | Epoch 7/sequence 124, distance +121 from ACK 3, rejected; no queue/ACK change |
| 14 malformed_acked_command_with_new_intent | F | F | ACKed sequence 2 has fire string, followed by valid new sequence 4; whole recorded packet rejected, 4 not queued |

Each before-state exactly equals the previous after-state. Accept calls never advance ACK. Each nonempty pop exactly removes its previously stored original payload and advances ACK to that sequence. ACK is nondecreasing. The four recorded queued/retry accept cases succeed in both, including changed-content retries, yet **accepted=true does not necessarily mean new intent was inserted**. Here existing queued/unACKed data is a legitimate remaining work item; that situation is materially different from events 6-7, when every sequence has already been consumed and the queue is empty.

In events 6-7, bd249c increments `rejected` once for each false return; 05ec6c's counter does not increase. From then on, the two-counter offset persists, but no new queue/ACK/rate behavior difference appears. Both reject the same three final invalid-control packets. Overall:

| Component total | bd249c | 05ec6c |
| --- | ---: | ---: |
| Accept attempts | 11 | 11 |
| Accept true / false | 6 / 5 | 8 / 3 |
| Final rejected | 5 | 3 |
| Pop attempts / nonempty | 4 / 3 | 4 / 3 |
| Final ACK / queue | 3 / empty | 3 / empty |
| Final rate count / bucket start | 11 / 1000 | 11 / 1000 |
| Reported checks / failures | 21 / 0 | 21 / 0 |

All original events, unchanged counters and exact cross-sample field differences remain in machine evidence. The independent **326 successful consistency checks** validate the provided states/bytes/receipts; they are **not** 326 new native tests and do not reconstruct or authenticate the author's uninspected 21 assertion bodies. Equal pass totals cannot establish equal behavior or adequate test sensitivity to fully ACKed return semantics.

## Retry mutation, consumption and fire-edge payloads

At the altered queued retry, both existing originals remain first-write-preserved: queued sequence 1 is still move +1/fire true and sequence 2 still move +1/fire false, despite the incoming reversal/swap. Neither the partially ACKed retry nor mixed ACKed/new packet reintroduces consumed sequence 1 or 2. The only three nonempty pops are exactly:

1. sequence 1, move `(1,0)`, fire **true**;
2. sequence 2, move `(1,0)`, fire **false**;
3. sequence 3, move `(-1,0)`, fire **true**.

Under a hypothetical initially-unheld simple fire latch consuming each payload once, these values would supply rising edges at sequences 1 and 3 with a genuine false value between them. **No physical shots, ammo, actor latch execution, simulation ticks, velocity or position were captured.** An empty fourth pop cannot by itself prove an actor never resimulates or fires twice; it only shows the queue has no fourth consumable command in this sequence. Normalized queue records include false utility fields/empty weapon defaults, but no true jump/grenade/smoke/reload/interact/weapon selection case is exercised.

The invalid acknowledged fire string preceding valid new intent is a useful validation-order control: it is not bypassed simply because its sequence is old, and the new sequence 4 is not admitted from this packet. Because the malformed command is **first**, the evidence does not establish general batch atomicity when a valid new command precedes a later invalid command. Similarly, one rejection at +121 does not prove the exact +120 acceptance boundary, and one old epoch does not exhaust epoch handling or authorization.

## Rate bucket, clocks and disconnect evidence

All 11 accept attempts, successful or not, charge the rate bucket exactly once in each sample. The four pops leave rate state and rejection count unchanged. Bucket start remains **1000** and final count **11**. Thus the fully ACKed replays consume quota even where bd249c returns false; “rejected” does not mean rate bookkeeping was bypassed.

The fixture-supplied rate-clock inputs are exactly:

`1000, 1100, 1150, 1200, 1300, 1350, 1400, 1450, 1500, 1550, 1600` ms.

They span **600 ms**, but the recorded monotonic event timestamps span only **329-331 ms** for bd249c and **327-329 ms** for 05ec6c: **two recorded milliseconds each**. Those are separate clocks. This is not evidence of an actual 600 ms wait, an input-silence timeout, or a 30-second idle experiment. Neither absolute capture offset nor the 2 ms ranges establish a cross-process speed comparison, trusted process duration or meaningful native latency measurement.

There is no bucket rollover, threshold/budget exhaustion, flood pressure, backward-clock or disconnect consequence in these data. No Match elapsed time, accepted-input timestamp, lifecycle wall timestamp, peer binding/status, disconnect event, callback timer, UDP send/receive, ENet retry or stock-client reconnect evidence appears in the before/after states. **No live-input activity extension, actual neutralization deadline, physical stop or disconnect outcome can be inferred from this component.** In particular, 05ec6c's true fully ACKed return is not proof its caller renewed a timer, and bd249c's false return is not proof it retired a peer.

## Blinding, authenticity and remaining coverage

This review is **source-identity blinded, not behaviorally blinded**. The visible raw return values and rejection counts directly reveal the behavior under comparison. The critic also previously reviewed a separate large neutral network packet, but its identity key remains unopened; no relation between the two sets of anonymous labels is used or asserted. Label assignment/source provenance cannot be independently verified from unsigned per-sample receipts, and the restrictive no-source rule prevents validating that a production module or original binary was actually the one run. The scope string's word “production” is not treated as an authenticated source claim.

The retained import/probe logs, process completion, zero-exit records and saved/engine result agreement corroborate the supplied historical narrative internally. They cannot exclude fabrication, mislabeling, copied results or harness-specific behavior. The frozen SHA ledger guarantees future comparison to this snapshot, not signed execution authenticity or trusted time.

Only a single deterministic short component sequence per sample is present. No repetition distribution, randomization, network impairment, peer ownership/privacy, client prediction defaults, live rewind, queue exhaustion, serialization fuzz corpus, timer boundary, real device/human or actor integration validation is added. These open limits are explicit in `FINDINGS.json` rather than converted into passes by the two 21-check summaries.

**Final bounded verdict:** bd249c provides the preferable recorded fully-ACKed-replay accept signal without sacrificing the exercised queued/unACKed retry, original payload, mixed-new-intent and consumption controls. Queue/ACK/rate/consumed payload behavior is otherwise tied in this sequence. No full-network winner, release approval, provenance conclusion or source guess follows. The prior large-packet verdict and all its open gates remain untouched.

## Frozen audit layout

- `packet/`: byte-exact copies of all 16 permitted input files, including the aggregate file retained only for hashing.
- `audit/sample-*-evidence.json`: every raw event/log/process receipt and independently derived classification/delta.
- `audit/comparison.json`: all cross-sample differences and clock evidence.
- `audit/packet-decodes.json` and `audit/packets/*.bin`: original serialized payloads, complete typed parses and byte hashes.
- `audit/independent-checks.json`: 326 consistency checks, no failures.
- `FINDINGS.json`: bounded machine verdict, preserved controls and explicit limits.
- Intake/audit/finalization scripts and read-boundary receipts document this offline analysis.
- `SHA256SUMS.txt`, `FROZEN_UTC.txt`, `FROZEN.json` and `FROZEN.sha256` bind the frozen content. This freeze is not signed attestation or trusted timestamping.
'''
(V/'REPORT.md').write_text(report,encoding='utf-8',newline='\n')
save('read-boundary.json',{'approved_input_directory':str(SOURCE),'original_input_file_count':16,'source_snapshot_stable_at_final_recheck':True,'semantically_read_files':['sample-bd249c/result.json','sample-bd249c/probe.engine.log','sample-bd249c/import.engine.log','sample-bd249c/probe.process.json','sample-bd249c/import.process.json','sample-bd249c/probe.log','sample-bd249c/import.log','sample-05ec6c/result.json','sample-05ec6c/probe.engine.log','sample-05ec6c/import.engine.log','sample-05ec6c/probe.process.json','sample-05ec6c/import.process.json','sample-05ec6c/probe.log','sample-05ec6c/import.log'],'aggregate_RESULTS_json_semantically_read':False,'keys_private_parent_source_modules_main_verdict_comments_claims_read':False,'previous_large_freeze_opened_or_modified':False,'source_guesses_made':False,'native_execution_performed':False,'network_services_db_git_source_edits_github_commits':False,'approved_python_executable':sys.executable,'python_version':sys.version,'freeze_precedes_any_key_read':True,'unsigned_execution_limit_acknowledged':True,'source_identity_not_behavior_blinding':True})
frozen_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='microseconds').replace('+00:00','Z')
(V/'FROZEN_UTC.txt').write_text(frozen_utc+'\n',encoding='ascii')
entries=[]
for file in sorted((p for p in V.rglob('*') if p.is_file()),key=lambda p:p.relative_to(V).as_posix()):
 entries.append({'path':file.relative_to(V).as_posix(),'bytes':file.stat().st_size,'sha256':sha(file.read_bytes())})
(V/'SHA256SUMS.txt').write_text(''.join(e['sha256']+'  '+e['path']+'\n' for e in entries),encoding='utf-8',newline='\n')
frozen={'schema':1,'frozen_utc':frozen_utc,'freeze_directory':str(V),'identity_keys_not_opened':True,'large_packet_freeze_untouched':True,'component_signal_advantage':'sample-bd249c','full_behavior_tie':False,'global_network_or_release_winner':None,'source_guesses':None,'native_execution_authenticated':False,'native_execution_performed_by_critic':False,'input_files_verified':16,'packet_instances_decoded':22,'unique_serialized_packets':7,'independent_consistency_checks':326,'ledger_file':'SHA256SUMS.txt','ledger_sha256':sha((V/'SHA256SUMS.txt').read_bytes()),'ledger_payload_count':len(entries),'ledger_entries':entries,'hash_chain_note':'Ledger covers every payload before the ledger/FROZEN/checksum files. FROZEN binds ledger; FROZEN.sha256 supplies its external non-self-referential checksum. No signed or trusted-time attestation.'}
save('FROZEN.json',frozen);fhash=sha((V/'FROZEN.json').read_bytes())
(V/'FROZEN.sha256').write_text(fhash+'  FROZEN.json\n',encoding='ascii')
for file in V.rglob('*'):
 if file.is_file():file.chmod(stat.S_IREAD)
for entry in entries:
 data=(V/entry['path']).read_bytes();assert len(data)==entry['bytes'] and sha(data)==entry['sha256']
assert sha((V/'SHA256SUMS.txt').read_bytes())==frozen['ledger_sha256']
assert sha((V/'FROZEN.json').read_bytes())==fhash
print(json.dumps({'frozen_directory':str(V),'REPORT_path':str(V/'REPORT.md'),'REPORT_sha256':sha((V/'REPORT.md').read_bytes()),'FROZEN_path':str(V/'FROZEN.json'),'FROZEN_sha256':fhash,'ledger_path':str(V/'SHA256SUMS.txt'),'ledger_sha256':frozen['ledger_sha256'],'frozen_utc':frozen_utc,'ledger_payloads_verified_after_readonly_freeze':len(entries),'component_signal_advantage':'sample-bd249c','behavioral_equivalence':False,'prior_large_freeze_untouched':True,'identity_keys_not_opened':True},indent=2))