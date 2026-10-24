# Independent actual collector facts

Single run40080238905, job120832097220, exact
c32415148db1f110bbc7eadfca3793d4693429ff. This is the delegated collector
schema/privacy/role/source-hook/partial-order review, not overall acceptance.
All shell and pure analysis ran on CPU4. No native run, engine, workflow, input,
signal, cleanup, source edit, retry, commit or push was performed here.

Official original root is
`/workspace/reviews/windows-collector-actual-20261024/.local/windows40080238905/receipts/evidence`.
References below omit that prefix. Full-QA originals used for direct PNG review
are under the sibling `full/` directory. The timestamped job-log wrapper was
excluded from the decoder. Parent owns archive, official digest, complete source,
workflow/run identity, duplicate artifact and overall gate verification.

`analyze_collector.py` independently decoded every exact collector prefix in146
retained log/text streams. The corrected source-bound decode has17,190 passing
predicates, zero failing predicates and zero malformed prefixed JSON lines.
These counts include copied records and do not measure independent events or
coverage. `collector-facts.json` retains log hashes, every predicate class,
role-local gaps, identity segments and latest-slot ages. `collector-rows.csv`
retains original file/line/observation ordinals and projected stage metadata.
`derive_stage_facts.py` and `stage-facts.json` retain current-stage matches,
controller action array indexes, authority effect rows, exact argv and PNG hashes.
The initial audit's290 failures and original decoder/facts/CSV remain in
`initial-*` and `INITIAL_AUDIT_FAILURES.md`; corrections are explained there.

The two canonical process-capture logs contain234 distinct JSON lines:

| Captured stdout | Owner from commands.json | Bytes / SHA256 | Actual collector output |
| --- | --- | --- | --- |
| native-input/client.log | Exported SIGHTBREAK.exe PID9332 | 120975 / c3c1ea9dd74d2a4903b9325a558b8cc436f730d95c857f3ce8530dbacba56582 | 77 rows, indexes1–77, original lines6–84 |
| native-input/server.log | Pinned source Godot fixture PID1684 | 237725 / 211600ebc62e2be7e7ff819c153ed768f172e9b46643aa95f75af0c689ebeaeb | 157 rows, indexes1–157, original lines3–191 |

Every canonical prefixed row parses, output indexes are contiguous, record times
and frame counts are nondecreasing within each captured process, counters do not
decrease, and each entire capture ends with a newline. No canonical duplicate
index, malformed JSON, unknown key, wrong-role hook/counter/latest slot, nonfinite
number or projection/type violation was found. Neither process reaches1024 or
emits observation_limit. This establishes decoding of these recorded lines;
complete event coverage remains UNKNOWN because suppression/coalescing and the
lack of a terminal seal apply even below the cap.

The secondary Godot userdata sink adds150 byte-identical copies and no new
prefixed event. `native-input/state/roaming/Godot/app_userdata/SIGHTBREAK/logs/godot.log`
has149 prefixed rows: all77 client rows followed by72 authority rows, indexes86–157.
Its line85 is a1501-byte markerless fragment, SHA256
943ee4e16b8360feb57fc9b2c10782256125a2097b2f70e6c3534826a169d22f,
exactly the suffix of canonical server.log:113/index85 after55 missing leading
bytes. The rotated godot2026-10-24T09.04.41.log contains one copy of authority
ready/index1. Shared-sink bytes remain untouched. They cannot be used as a single
process trace or certify an untruncated auxiliary log. The canonical stdout
captures provide the full versions of those copied/fragmented records.

Both ordinary processes actually receive `--native-input-observation` after
`--`: server source fixture command includes its explicit output directory and
client command includes the exported EXE, audio Dummy and976×549 resolution.
commands.json records starts at controller0.421s and0.921s and exits0 for
server/client respectively. These are captured owner/argv receipts, not live
PID/start-time identity observations by this subcritic. The exact-source fixture
adds Boolean `_native_input_fixture:true` only for the flagged source server
(`scripts/fixtures/export_integration.gd:56–60`). The source debug/loopback/
account-free admission and fixed projection are detailed in SOURCE_FACTS.md.
Direct02-exported-connect.png shows127.0.0.1, UDP27020 and JOIN GUEST LAN MATCH;
client.log:13 reports LAN practice, and server.log:29 records protocol6.

All observed client traffic is one local attempt1 and transport335231315, local
actor1, prediction epoch1. The server selects peer335231315, actor1, generation1,
authority epoch1. Its peer_connected and peer_bound rows are server.log:26/index22
and:27/index23. Client attempt1 begins at client.log:7/index2 while still showing
offline status and the prior offline transport ID1: the source hook is BEFORE
close/reset, so that row is valid. Initial ready rows precede host/client startup;
authority_epoch0 on server ready becomes1 before guest admission. Client's
unused authority_epoch remains0. Client's generation stays−1 because it has no
server peer-lifecycle entry. These different counters have separate meanings.
There is no observed reconnect, second peer generation, expiry or later epoch.
Source support for those branches does not qualify their actual execution.

The last server row, server.log:191/index157, is peer_disconnected but still has
peer_bound=true/joined=true/generation1/actor1/ack593. That is source-correct:
match.gd1029 observes before forgetting lifecycle/stream/binding. Its current
actor is30/86 with neutral controls; the newest consumed slot is sequence593 at
wall36849,72ms older than the row, and accepted/received slots are144ms old.
The later fixture report at server.log:193 records peer_count0/peer_bound=false.
No expiry or post-unbind collector row was emitted.

Actual ordinary fire and reload are supported through the following separate
stages. All `latest` references in this table describe either the named current
reason or the slot's own timestamp. A row's timestamp never refreshes every slot.

| Stage | Original evidence | Supported observation |
| --- | --- | --- |
| Native fire call/state | actions.json items38–39,42–43 | LMB before/after down at controller28.437s; before/after up at29.203s; GetAsyncKeyState records down/then up with the target focused. This proves this OS stage only. |
| Current sampled fire | client.log:34/index27, wall27515 | physical lmb=true and local_input.fire=true; attempt1/transport335231315/epoch1 context. |
| Current fire send call | client.log:35/index28, wall27521 | Packet summary epoch1/count6/first178/last183/fire2; this follows rpc_id invocation, not delivery. Later current sends reach count12/fire12/first182/last193 at:40/index33. |
| Current received and accepted | server.log:71–72/index61–62, wall28075/28078 | Same first fire packet projection, peer335231315/actor1/generation1/epoch1. Receipt precedes accept within this process by source and raw order. |
| Current consumed fire | server.log:75/index65, wall28087/tick1667 | Sequence182, fire=true/reload=false assigned to actor1; actor ammo is still30 at this pre-effect hook. |
| Genuine shot effects | server.log:76–77,:87–88,:90–91,:93–94 | Four shot signals with ammo29,28,27,26 at authoritative ticks1667,1674,1680,1686. The first follows the consumed hook in the same source/process/tick. Later shots can use held intent; four shots do not imply four printed consumed edges. |
| Fire cessation limit | server.log:96–97 | Actor input is neutral by fixture tick1688; collector latest consumed can still be fire=true/sequence193 from wall28227. Source silence gating can neutralize actor input after consumption. No dedicated current fire-release consumed row is recorded; an OS-up→neutral-command link is UNKNOWN. |
| Native reload call/state | actions.json items46–47,52–53 | R before/after down29.781s and before/after up32.328s; observed native R state changes with target focused. |
| Current sampled reload | client.log:41/index34, wall29572 | local/physical fire=false, R/reload=true, prediction_sequence193. The preceding send slot is still old fire12 from wall27656, age1916ms. |
| Current reload send call | client.log:42/index35, wall29574 | Epoch1/count12/first184/last195/fire10/reload2. Old fire history and new reload intent coexist in a redundant packet; the summary does not establish simultaneous buttons on one command. |
| Current received and accepted reload projection | server.log:98–99/index75–76, wall30085 | Same mixed summary under the same peer/generation/epoch. Later packet summary190..201 includes8 reload flags before consumption. |
| Current consumed reload | server.log:106/index83, wall30119/tick1790 | Sequence200, fire=false/reload=true assigned; pre-effect actor ammo26/reserve90/reload0. Source pop skipped6 queued commands between ack193 and200; no contiguous-consumption assumption is valid. |
| Genuine reload start/countdown | server.log:107–111 | Native reload command and start, no --automatic-reload argv; tick1791/ack201, countdown2.23333333333333, ammo26/reserve90. A later collector actor sample at:112/index84 shows countdown1.98333333333333. |
| Current release of reload intent | client.log:73/index66; server.log:176/index148 | Client physical/local R/reload=false. Separately, authority consumes sequence308/reload=false at tick1898 while countdown is still0.46666666666667. This is release of intent, not reload completion. |
| Genuine reload completion | server.log:182–184 | Completion tick1926/ack336 with countdown0, ammo30/reserve86. Total ammunition changes120→116 after four shots and stays116 across reload. Final authority ack593 is later, not the completion ack. |
| Client acknowledgment/state | client.log:42/index35 and:81/index74 | First visible post-shot actor sample is ammo29 but header own_ack183; later rows reach26. At:81 actor30/86/reload0 accompanies snapshot tick1953/epoch1/own_ack363, snapshot age62ms. Current prediction_sequence370/pending10 is a separate pipeline stage. |
| Rendered response | Direct original06 and07 PNGs |06 visibly shows RELOADING1.9s and07 shows rifle30/86.04-fire-input.png and05-after-fire-input.png are byte-identical (SHA256659616d4e8fe548799252902347593964eae83a6f1e62ad2e9cac73554f62934) and show rifle30/90, so they do not qualify rendered firing response or fresh shot-state timing. |

All59 printed current send-call projections equal the59 printed current
received and59 printed current accepted projections in their respective local
orders. stage-facts.json retains every corresponding line/index and summary.
This is a match of epoch/count/endpoints/control counts in the single observed
identity context, not proof of packet-body equality, global order, every packet,
network latency or an action effect for each call. Final counters establish278
client send-call hooks through its last row, versus297 server received/accepted
hooks through the later disconnect row. The output horizons differ and most
hooks are coalesced. Server last-row counters include476 consumed hooks,
stream_rejected0 and stream_skipped117; the collector prints only six current
consumed control edges. It cannot enumerate every command, duplicate, dropped
packet, skipped control or effect. Legitimate unordered batches remain allowed
by input_stream.accept; no increasing-endpoint predicate was applied.

Coverage and staleness limits are separate quantities:

| Process / identity interval | First→last monotonic msec | Largest adjacent printed gap | Leading/trailing limit |
| --- | --- | --- | --- |
| Client entire configuration, attempt0 ready then attempt1 |20682→35661, span14979ms |3717ms, client.log:12→15, indexes7→8, physics356→357/process158→159/drawn158→159 | Process clock origin→first row20682ms; no collector before configuration/menu join is claimed. No exact process-exit timestamp or terminal seal; trailing interval UNKNOWN. |
| Client attempt1 only |20683→35661,76 rows |Same3717ms gap; another1916ms gap:40→41/index33→34, physics549→550/process202→203/drawn202→203 | Attempt hook precedes reset. Native fire-up and R-down occur during the latter sparse observation interval by recorded system times; their exact client processing instants are UNKNOWN. |
| Authority before a selected peer |384→20532,21 rows |1029ms, server.log:24→25 |384ms from process clock origin to first ready record; preceding setup is not observed by this collector. |
| Authority selected peer335231315/generation1 |21372→36921,136 rows |1045ms, server.log:188→189/index154→155 | Last row is before unbind; report:193 is later. No process-exit timestamp/terminal seal, so final collector→exit interval UNKNOWN. |

A later target-window capture_end (actions.json item59) is recorded543ms after the
last client collector system timestamp. A later authority report is recorded
238ms after its last collector timestamp. These are lower-bound indications of
remaining unobserved activity under the host system-clock receipts, not measured
shutdown durations or calibrated monotonic intervals. The exact shutdown tail is
not reconstructed from process exit codes. Unix-minus-monotonic offsets range
1792832681003–1792832681005ms for client and1792832680494–1792832680503ms for
server. Their different process origins and uncalibrated call/clock uncertainty
preclude a cross-role latency figure or invented total order. The two long client
gaps advance only one recorded physics/process/drawn frame each; cause, collector
cost and physical input latency remain UNKNOWN without a matched experiment.

Largest observed event ages are client snapshot3566ms (:16/index9), send slot
1916ms (:41/index34), and welcome14790ms (:84/index77); authority accepted1859ms
(:98/index75), consumed1860ms (:105/index82), and received1004ms (:97/index74).
At reload receipt, an old latest-consumed fire value therefore coexists with
neutral current actor input. No actual stale peer/generation mismatch is needed
to demonstrate stale event values. Pending history peaks at23 in retained client
rows; server queue_count peaks14, and source backlog trimming/skipping remains
active. No observed cap exhaustion occurs, but no terminal event-coverage seal
exists and quiet/suppressed updates remain unprinted.

Actual collector privacy predicates pass for all234 distinct canonical records
and their150 copied records. Exact projection keys/types include only primitive
metadata, fixed control/packet/header summaries, physical Boolean controls and
selected own/guest actor1. No collector names, aim/look, packet bodies, ticket,
reconnect/account credentials, arbitrary private fields or second actor appear.
The markerless auxiliary fragment matches an allowed canonical projection suffix.
This scope concerns collector records; other preexisting fixture output such as
join-snapshot.json has its own scope and is not called privacy-minimal here.

There are zero collector prefixes in142 other retained log/text streams:
regressions95, offline-input21, each of offline-plant/offline-defuse/
offline-full-match/reload-release-first/reload-legacy-delayed4, verification3
and windows3. Typed traversal finds113 retained command occurrences; only four
are flagged, the two ordinary commands repeated in commands.json/results.json.
All109 other command occurrences are unflagged. This verifies observed absence
in these retained native, delayed, offline and default-reopen lanes. It does not
qualify negative release-build, remote-address or account execution, which did
not run here.

The enabled ordinary client emits the OpenGL3.3→ANGLE WARNING at client.log:2
(and the shared copy), despite the producer reporting passed=true. Under the
unchanged preregistered strict warning gate, that observed scope is FAIL. Nothing
in the collector projection analysis erases it or attributes its cause to this
collector. The largest collector evidence gap is unmeasured processing/observer
cost with sparse and stale stages: there is no uninterrupted event or rendered
fire-response proof. Authority four-shot/reload effects and later rendered
reload/completion evidence are bounded positive facts; overall acceptance stays
with the parent and every unrelated gate retains its own result.
