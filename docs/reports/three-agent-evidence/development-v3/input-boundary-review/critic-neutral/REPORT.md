# Independent neutral component-packet verdict

## Outcome

**The component traces are not behaviorally tied despite both reporting 21 checks and zero failures.** At this boundary, **sample-bd249c** better distinguishes a fully ACKed replay from a queued/unACKed duplicate: it returns false and increments the rejected counter for both fully ACKed replay variants, while **sample-05ec6c** returns true. Both preserve legitimate queued retries and the later mixed acknowledged/new packet in the recorded sequence.

This is a narrow **accept-return/counter distinction**, not an observed Match/lifecycle/timeout/UDP/actor improvement. All captured queue, ACK and rate-bucket transitions match between samples, and neither resurrects consumed commands. Whether an outside caller uses the accept return to refresh live-input activity is absent from this packet and was not inferred.

No source identity, key, parent run/probe/private directory, main component verdict, source module, GitHub comment or owner claim was consulted. No connection between these labels and previous neutral labels or source identities is proposed. The previous large-packet freeze was not opened or modified.

## Evidence and independent audit

The allowed input was only:

`C:\Users\blith\AppData\Local\Temp\opencode\sol-input-boundary-controls-20261022\attempt-r3\neutral\`

I copied its 15 files into a newly isolated external directory and hashed every byte. A final read-only recheck of exactly that input directory matched all original intake paths, sizes and hashes. `RESULTS.json` was only copied/hashed, not read for aggregate verdicts or owner claims. Actual evidence used was each sample's raw `result.json`, `probe.engine.log`, `import.engine.log`, process receipts and empty stdout log files.

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

## Assessor-local failure retained

An initial freeze finalizer incorrectly expected 16 input files; the actual full inventory has 15 (seven per sample plus RESULTS.json). It stopped at that count assertion before creating a report, ledger or FROZEN record. The input byte inventories had already matched. That partial external attempt is retained untouched, and its exact script/error are included under `review-attempts/`. The corrected new finalizer rechecked all 15 files. This is an assessor bookkeeping error, not a hidden native-test or packet failure.

## Frozen audit layout

- `packet/`: byte-exact copies of all 15 permitted input files, including the aggregate file retained only for hashing.
- `audit/sample-*-evidence.json`: every raw event/log/process receipt and independently derived classification/delta.
- `audit/comparison.json`: all cross-sample differences and clock evidence.
- `audit/packet-decodes.json` and `audit/packets/*.bin`: original serialized payloads, complete typed parses and byte hashes.
- `audit/independent-checks.json`: 326 consistency checks, no failures.
- `FINDINGS.json`: bounded machine verdict, preserved controls and explicit limits.
- Intake/audit/finalization scripts and read-boundary receipts document this offline analysis.
- `SHA256SUMS.txt`, `FROZEN_UTC.txt`, `FROZEN.json` and `FROZEN.sha256` bind the frozen content. This freeze is not signed attestation or trusted timestamping.
