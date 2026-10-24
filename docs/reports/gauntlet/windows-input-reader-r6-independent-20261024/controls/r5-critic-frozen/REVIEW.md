# Independent R5 input-reader verdict: REJECT

Frozen `7d8ec7dda37764e0f45fd2ea1e8d330f84bc2508`, analyzer SHA-256
`c0fe4d9f078a28043a7c89eaef2b0402ca03c486fb3a8c781040a5e6e517f7e0`, accepts
15 new source-impossible receipts in five invariant groups. Own and initialized
depth-one views reproduce all fifteen with `diagnostic_complete=true`, errors=[].
All ten paired invariant-compatible synthetic positives pass; no false reject
was observed. These fixtures are parser/source counterexamples, not engine models
or acquired observations.

R5 wins the limited source comparison with rejected R4: it meets all108 explicit
retained regression requirements, including the six prior false accepts, and
improves the new corpus from R4's11/30 to15/30. It still fails the registered
source bar. The largest gap is agreement among coalesced stage metadata, actual
stream state and the persistent snapshot cache. Passing direct-row checks does
not constrain all later coalesced observations or state transitions.

## Independence and registration

Root explicitly reused this existing critic thread after new thread creation
hit the supported limit. This is independent of the R5 builder, with no claim of
a newly created thread or fresh-context isolation. Initial registration was
saved before reading R5 implementation, builder registration/handoff or R4
review, SHA-256
`d030c78cca9acc6fa71f7d44adbab259c3e3232fa3028ca010be1402b7da223a`.
Commit57f5d40d records it unchanged in this new own review checkout;
9fcf3159 registers concrete controls before execution; 9c8aa97e retains the rig.
Sealed builder handoff eb2dbc7cc97b337fb8e0bbf601fcb0bbfd984701 preceded all tests.

Own branch `codex/critic-windows-input-reader-r5-20261024` and worktree
`/workspace/reviews/windows-input-reader-r5-independent-20261024` start at exact
7d8ec7dd. Index initialization with read-tree preceded sparse materialization;
explicit restore populated only this new own checkout. Other source/report
worktrees and canonical documents were not edited. A guessed R4 snapshot
adjudication filename was absent; that lookup failure is retained in SETUP_NOTES.
The real source/fixture transition was independently checked below.

## Exact fresh failures

Each named directory exists under both `own-fresh-controls/` and
`depth-fresh-controls/`, with exact `client.txt`, `authority.txt` and `RESULT.json`.
The result names its paired positive, input hashes, expected/actual verdict and
source basis. Each negative changes real serialized input from that control.
All own/depth inputs and per-case metadata are byte-identical.

| Case | Deterministic source contradiction |
| --- | --- |
| `coalesced_single_already_acknowledged` | A hidden count1 acceptance claims sequence1 after the same stream has ACK1. InputStream24-38 stages only sequences above ACK and rejects an empty stage. The paired hidden sequence2 accepts. |
| `coalesced_single_above_window` | The same hidden count1 acceptance claims122 at ACK1; every command must be at most121. |
| `coalesced_accepted_wrong_epoch` | The hidden accepted projection claims epoch2 while the unchanged authority stream is epoch1. InputStream19 rejects that packet before staging. |
| `coalesced_accepted_over_batch_cap` | A hidden accepted batch claims13 commands. InputStream19 rejects more than MAX_BATCH12 before staging. |
| `direct_single_command_inflates_queue_2` | Direct receive observes queue0; its synchronous count1 acceptance claims queue2. One staged unique command can create at most one entry. |
| `direct_single_command_inflates_queue_120` | The same local count1 transition claims queue120. A legitimate full queue is possible after many batches; this one-command transition cannot create it. |
| `ack_advances_without_consumption` | Same peer/generation/epoch advances ACK1 to2 without any new consumed call. Pop alone stores ACK and Match271-281 observes each nonempty pop synchronously. |
| `ack_zero_without_consumption` | ACK1 becomes0 in the same lifetime with unchanged consumption. Observer ACK is absent-1 or a positive popped sequence; forget/reset does not store0. |
| `ack_clears_without_reset` | ACK1 becomes absent-1 without disconnect, stream/epoch reset or identity change. All lifecycle counters and the live binding persist. |
| `queue_appears_without_acceptance` | An empty queue gains an entry while receive/accept counters/latest stay unchanged in the same stream. No source operation adds queued input without acceptance. |
| `cached_snapshot_disappears` | Cached client snapshot becomes empty although the applied counter remains1 and persistent latest header remains present. Only a counted snapshot call writes the cache. |
| `cached_snapshot_restamped` | Cached wall time changes while applied counter/latest remain unchanged; age is recomputed so the existing freshness check passes. |
| `cached_snapshot_header_changes` | Cached own_ack changes while the actual latest snapshot header/counter stay unchanged. |
| `cache_precedes_first_applied_counter` | A nonempty cached snapshot appears with no applied counter or latest header. Match1271,1283-1289 increments the counter before writing the cache and latest from the same header. |
| `partial_rejected_state_survives_replacement` | Rejected state2 becomes1 across a zero-peer epoch change with no new rejection calls. The old stream retains2; replacement creates a new stream at0. There is no decrement-to1 operation. The paired full-reset0 and no-replacement2 controls both pass. |

The first four cases keep action aggregates unchanged, so Match1295-1300 may
legitimately coalesce their receive/accept calls into a later authority tick.
The reader's epoch/count/ACK acceptance checks execute only on direct
`input_accepted` rows. The count1 projection exposes its sole command, making
these contradictions observable without reconstructing a packet. The positive
count3/first1/last1 can hide a fresh middle2 with unchanged fire aggregate1; it
passes and must remain allowed. Endpoints do not establish whole packet identity.

Queue/ACK cases retain one observed bound generation and complete lifecycle
history. Direct lifecycle events exclude an unobserved second binding or forget
narrative. Match1066-1078 has no await between receive and accepted observations;
InputStream39-47 adds only staged unique keys. Match271-281 calls pop, assigns the
actor input and observes consumption; InputStream83 stores ACK, while forget and
reset_epoch clear it. The reader binds ACK to direct consumption but leaves later
unchanged-counter state transitions unchecked.

Snapshot cases use the actual cache aliasing: Match1283-1289 assigns the same
header to diagnostic.snapshot and latest.snapshot_applied before adding its wall
time; later records duplicate those values. Neither welcome nor reconnect clears
this diagnostic cache. An unchanged applied counter cannot produce a different
cache. The current reader checks cache shape/age and persistent latest separately,
so internally plausible ages can hide the contradiction.

For stream rejection, the existing reset allowance is too broad. With new reject
count dJ, no replacement requires Cnew=Cprevious+dJ; a possible replacement permits
Cnew in[0,dJ]. It does not permit every value up to Cprevious+dJ. Match1468-1479
constructs a new InputStream whose rejected value starts0, and its only other
writes increment it. Forget and ordinary epoch reset do not decrement it.

## Positive coverage and retained regressions

Fresh corpus:30 cases, ten admitted positives and20 negatives. Five negatives
are correctly rejected;15 falsely accept. Positive coverage includes ordinary
coalesced fresh input, hidden fresh middle commands behind stale endpoints,
unchanged ACK/queue, two coalesced rejections, a legitimate full stream reset,
no-replacement state persistence, inclusive latest-time boundaries and a cached
first snapshot inside its observed interval. There are no failed constructions,
contradictory duplicate expectations or adapted negative expectations.

Both views reproduce108/108 retained requirements: exact prior92, final R4
critic13 and three separately state-corrected versions. This is regression
evidence, not the new independent corpus. The three newly obsolete state0/J1
positives retain their original bytes, assertions, expectations and old R4
outcomes. Their source-consistent replacements remain separate. The replay
wrapper changes only the fixture-home path from the sealed builder script;
its verdict logic and transformations are unchanged.

Selected207 maintained methods run in process in each view:204 pass, the same
three Windows-only skips, zero failures/errors. Focused reader coverage is55
methods. Server11 and Mac11 groups are excluded by this lane's scope; the
builder's full229 is not represented as independently rerun. Shell syntax passes.
The old-reader comparison imports exact R4 analyzer bytes with unchanged shared
fixture code, not a complete retest of an old checkout. It admits19 of the20
fresh negatives; R5 rejects four additional ones but preserves fifteen defects.

## Source and fixture identity

[Independent bindings](source-bindings.json) prove the complete513-path
non-document union: four changed paths and509 protected paths. Every physical
candidate file, executable mode, full index identity and Git blob matches in
both views. All existing modes remain unchanged. The runtime emitter, transport,
RPC, authority, privacy/economy, controller, native and workflow source is exact.
Analyzer changes add24 lines, identity fixture adds1, lifecycle helper adds4,
and the new stream test adds200; all old lines remain byte-exact and in order.

All45 inherited test methods and79 assertion-call ASTs are unchanged. The exact
old analyzer/identity/lifecycle files remain in historical-source and match R4
Git objects. All323 copied historical files in r4-builder-frozen and
r4-critic-frozen match their named d139124e/ad12f7ae Git blobs and working bytes.

The minimum snapshot-helper change is supported independently. Rebuilding the
unchanged failed-attempt fixture gives welcome/preceding row wall6000, applied
count0 and empty cache; the first counted row is wall7000, applied count1, cached
timestamp6000. Subsequent cached/latest copies retain6000 and ages are recomputed.
Welcome is observed before apply_snapshot, and equal millisecond timestamps are
valid. This is a construction-time fixture correction before assertions; it does
not repair post-mutation input or approve the reader's missing cache invariant.

The separate initialized source view is clean at exact7d8ec7dd, shallow with one
reachable commit and a complete12057-path index. Its parent object is absent
(exit128), it has no remote/object alternate/alternate environment, and its local
pack is9,324,696 bytes. This is a local source/object transfer, not a network clone
or exported artifact. Unlike the builder's disclosed alternate-based depth view,
this reviewer view has independent object storage. The ordinary own worktree
shares its original object database and claims no history isolation itself.

## Reproduction and bounds

From this reviewer checkout, use fresh outputs:

```sh
taskset -c 4 env PYTHONDONTWRITEBYTECODE=1 python3 docs/reports/gauntlet/windows-input-reader-r5-independent-20261024/controls/fresh_controls.py --source . --output /tmp/r5-independent-NEW
taskset -c 4 env PYTHONDONTWRITEBYTECODE=1 python3 docs/reports/gauntlet/windows-input-reader-r5-independent-20261024/controls/run_selected_pure.py --source . --output /tmp/r5-selected-pure-NEW
taskset -c 4 env PYTHONDONTWRITEBYTECODE=1 python3 docs/reports/gauntlet/windows-input-reader-r5-independent-20261024/controls/replay_builder_controls.py --source . --output /tmp/r5-retained-NEW
```

The fresh rig exits1 for its fifteen false accepts. To reproduce one exact saved
case, pass its client.txt and authority.txt to the frozen analyzer CLI with a new
output path. Change --source to the recorded depth-one view for the same models
and tests. No product source was edited by the reviewer.

All work is CPU4 Python/static/shell parsing. No Godot, engine API, export,
native application/helper activation, process inspection, OS input, CI, Mac review,
actual rerun or canonical edit occurred. These observations cannot establish
whole packet identity, real delivery, physical latency, terminal capture coverage
or the historical disconnect cause. The source-only verdict is REJECT; retain
all original failures and require a separately frozen correction and independent
review before any native/readiness decision.
