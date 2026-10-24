# Source facts governing the independent decode

All line citations refer to exactc32415148db1f110bbc7eadfca3793d4693429ff.
These are source semantics, not observed execution or actual acceptance.

* `game/scripts/gameplay/match.gd:1233–1241`: enabled admission requires debug,
  explicit user flag, false require_accounts, empty join_ticket, literal127.0.0.1
  or ::1, and client mode or server mode plus a Boolean true fixture marker.
  Configure clears the dictionary and reinitializes count/index/attempt state.
* `scripts/verify_integration_export.py:803–820`: ordinary authority receives
  the flag after the source script separator and exported client receives it
  after its own `--`. `scripts/fixtures/export_integration.gd:56–60` supplies
  `_native_input_fixture:true` only when the source authority user flag exists.
  Its initial ordinary configure itself is unmarked and therefore disabled.
* `match.gd:1267–1300`: disabled returns immediately; output count>=1024 returns
  before even updating counters/latest. Otherwise each reason increments its
  named hook counter before suppression. Packet, consumed, and header latest
  slots update before suppression, as do per-reason edge signatures. Lifecycle
  calls emit. Changed control calls emit. Client/authority periodic ticks emit
  when at least1000ms has elapsed since the last emitted row. Other reasons may
  never print directly but become visible through a later row. No terminal seal
  is emitted. Index1024 substitutes literal reason observation_limit; the
  underlying triggering reason is not directly named by that substitution.
* `match.gd:1243–1264,1280–1288,1307–1318`: allowed projection is fixed controls
  (sequence/fire/reload/two-number move), packet summaries (epoch/count/first/
  last/fire/reload/moving), header summaries (tick/epoch/own_ack and source-hook wall_msec), own or last
  selected guest actor (id/alive/ammo/reserve/reload/input), physical Boolean
  fields and primitive collector/connection/counter metadata. It copies no
  names, look/aim, packet bodies, account/ticket/token, arbitrary actor fields
  or other actors. Raw decode must still check exact keys/types and finite values.
* `match.gd:652–655`: client_attempt increments and observes BEFORE old transport
  close and prediction reset. The row can retain prior actor, epoch, pending
  commands, snapshot/latest slots and old connection/transport status. Client
  attempt numbers are process/configuration local; they are not server lifecycle
  generation numbers. `peer_lifecycle.gd:11–22` increments a separate generation
  when a new peer entry is connected.
* `match.gd:1028–1041`: peer_disconnected observes BEFORE forgetting lifecycle,
  stream and binding. That row may truthfully still report joined/peer_bound.
  `match.gd:885–890` emits peer_expired after expired() identifies a timed-out
  entry but before disconnect and the explicit _peer_disconnected call.
  `peer_lifecycle.gd:53–64` shows expired() itself does not erase the entry.
* `match.gd:1053–1078`: input_received is after compressed decoding to Dictionary
  and gate checks, before stream.accept; input_accepted follows success and
  activity refresh. Gate/decode rejection need not have a packet projection.
  `input_stream.gd:14–47` accepts each command by identity and sanitization and
  does not require incoming array endpoints to increase. Fully acknowledged
  retransmissions reject; queued unacknowledged duplicates can accept, and an
  existing queued identity cannot be replaced by later conflicting data.
* `input_stream.gd:67–89`: pop sorts queued keys, drops oldest entries until two
  remain when backlog exceeds6, acknowledges only the consumed sequence and
  can skip sequence values. Forget removes a peer's queue/ack/rate state.
  `match.gd:355–356` resets stream epoch; prediction resets pending and sequence
  on connection/epoch transitions (`movement_prediction.gd:15–29,48–64`).
  First/last/count alone cannot reconstruct a contiguous packet body.
* `match.gd:271–281`: input_consumed follows pop and actor input assignment.
  It precedes phase/silence gating, authority movement and action execution at
  lines298–309. It proves intent consumption at that hook, not action effect.
  The stream counter can advance while observable fire/reload effect is absent.
* `match.gd:832–846,869–878`: client_tick precedes this callback's prediction;
  input_send_called follows rpc_id invocation. Neither proves network delivery.
  Snapshot latest/header and age record the last applied snapshot, potentially
  stale across later rows/attempts. `welcome_received` observes before calling
  _apply_snapshot at lines1099–1100. A later snapshot_applied slot is distinct.

Output order is local to an emitting configuration and each process has its own
monotonic time origin. Unix times are useful for approximate overlap but do not
establish cross-role delivery latency or a global happens-before relation.
Nested latest values keep their own wall_msec; row time is not the event time of
each nested slot. A stale consumed value may retain an old peer/generation while
the row describes an unbound or newly selected peer. Observation count, newest
slot and hook counters do not establish uninterrupted coverage or zero cost.

Actual decode corrected one prepared assumption: snapshot and latest-applied
header share a Dictionary before wall_msec is added (lines1286–1289), so snapshot
also includes wall_msec. INITIAL_AUDIT_FAILURES.md retains the first failure.

That shared header exists entirely inside the diagnostic dictionaries; the alias
correction makes no claim about aliasing protected gameplay state.
