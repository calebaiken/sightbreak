# Fresh complete-reader causal cases, before execution

Use an independent emitter/stream oracle derived from Match1243–1327,
InputStream.accept/pop/forget/reset_epoch and lifecycle hook ordering. A fixed
schema template can come from declared_rows, but state transitions, packet
staging, immutable payloads, control-edge coalescing and expected results come
from this review's oracle. Baseline first direct receive/accept/pop supplies
required pipeline evidence; subsequent controls use live peers and persistent
observer metadata. No candidate model determines the positive witness.

The following pairs are registered before candidate execution:

- Hidden A count1 accepted while A is sole owner; connection of B exposes that
  call; B then directly accepts a different control aggregate; delayed A selected
  tick must retain A's original count1 payload and queue1. Counterfactual A queue0
  or queue2 is impossible with no A pop/reset/new accept.
- Opaque A count3 [2,3,2], with aggregate matching the old global accepted edge,
  followed by B's different header and delayed A observation. Preserve two actual
  unique keys. Counterfactual queue3 or first pop3/skip0 contradicts the mandatory
  fresh endpoint2, even though the middle packet command is unobserved.
- Old-epoch hidden A acceptance exposed at B connection, then reset before B's
  new-epoch acceptance and delayed A selection: A is empty. Retaining A's old
  queued key is impossible. Conversely reset before hidden A acceptance proves
  a new-epoch receipt that survives and cannot disappear. Do not borrow B's
  later global header for either epoch interpretation.
- Disconnect/reconnect of the same peer using a fresh monotonically allocated
  generation: old queue and receipt origins are gone; an unchanged observer
  accepted count cannot populate its fresh queue. A bound peer's expiry hook
  precedes disconnect and does not itself permit a full observer-state reset.
- Repeat selected ticks with no new local acceptance/pop must preserve ACK/queue;
  earlier cached projections cannot be replayed as new calls.
- Equal versus unequal timestamps around acceptance/reset/selection preserve
  actual source order. A tie does not authorize wrong peer/generation attribution.
- Coalesced A pop exposed by a foreign lifecycle hook, then B's latest pop and
  delayed A selection: retain the earlier proved owner and immutable consumed
  controls. Mutated popped payload/ACK/cardinality must fail.
- Genuine duplicate-accept ownership ambiguity with two live queues is UNKNOWN
  and incomplete. Multiple hidden local accepts can also remain UNKNOWN rather
  than a source-invalid claim. A separate invalid client/schema fact must still
  produce INVALID, not be swallowed by authority UNKNOWN.
- Epoch interval matrix covers acceptance before/after reset, intermediate
  epochs across a larger jump, out-of-range accepted epochs, old metadata with
  unchanged count and repeated epoch ticks. Preserve valid complete source
  witnesses; impossibility mutations change only the claimed projection.

Retain all client/authority input bytes, oracle event witnesses, expected and
actual transition_status/diagnostic_complete/error fields. Assess source-positive
UNKNOWN separately from a false INVALID; either result is incomplete. A true
false complete acceptance is a source rejection. Do not require old contradictory
positive fixtures to pass. Record any helper construction failure and correction
as separate versions, without rewriting raw prior inputs/results.
