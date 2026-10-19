# ACK snapshot observability — diagnostic-only follow-up

This follow-up has a declared **observation-coverage** bar. It does not claim a
gameplay accuracy, movement, performance or prediction-activation improvement.
The earlier gate-evidence checkpoint, including its unsuccessful preflights and
neutral ZIP, remains unchanged at `6a6d18ac295d43bea3be657b0f4575e282e813c0`.

## Frozen inputs

| Input | Exact revision |
| --- | --- |
| Frozen baseline | `701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd` |
| Prior PR21 gate evidence | `6a6d18ac295d43bea3be657b0f4575e282e813c0` |
| Diagnostic runtime | `0fbce120d8c17db58596d280f7d8401ab2aa0937` |
| External probe/driver freeze | `06034326b7b005340453383cf7c25909f34253f3` |

Interface ownership was refreshed and declared on
[PR17](https://github.com/calebaiken/sightbreak/pull/17#issuecomment-6275595648)
and [PR21](https://github.com/calebaiken/sightbreak/pull/21#issuecomment-6275595589)
before editing. [Exact-source freeze handoff](https://github.com/calebaiken/sightbreak/pull/17#issuecomment-6275752939).

## Runtime change and metric definition

`ack_snapshot_diagnostics.gd` is a local RefCounted observer with no actor reference
and no simulation or network calls. Five additive lines in `movement_prediction.gd`
instantiate it and observe/reset it. The existing command-error append/removal,
movement replay, correction and presentation statements are unchanged.

The observer records every **reconciled** own-actor snapshot, separately identifying
repeated ACKs and measuring drift from the previous and first observed snapshot
with that ACK. It retains one ACK anchor and at most 120 samples. New epochs and
explicit resets clear the diagnostic history; stale epochs, regressed ACKs and
invalid data cannot contaminate its anchors. Metadata is allowlisted and copied.

**Snapshot time is not command-consumption time.** The first observation may already
contain held-input steps. The explicit anchor label is
`first_observed_snapshot_not_consumption`; new-ACK delta is null, not an invented
zero-time measurement. Existing `error_samples` remains the consumed-command
comparison series with its old limitations. No new wire field or caller argument
is introduced. [Complete interface and validation bar](../network/ACK_SNAPSHOT_DIAGNOSTICS.md).

The prior fixture contained ten delivered held-state snapshots per loss condition.
Five had an old command-error sample; the other five repeated an ACK removed from
history. The new bar requires 10/10 observable held snapshots, including explicit
samples and correct snapshot-relative drift for all five formerly missing cases,
while every recorded legacy output stays identical.

## Matched source-bound result

The frozen cached serial native run is in progress. No follow-up candidate win is
asserted until the completed raw receipt and coverage/equality checks are added.

## Scope and remaining limits

- The same six deterministic 9-second schedules use inherited native authority
  ticks, real actors and replay. Packet timing is in-process; this is not ENet,
  Relay Yard, rendering or human-feel evidence.
- The observer sees reconciliations, not every received packet: Match can coalesce
  multiple network snapshots before its next physics callback.
- Existing outer snapshot tick filtering supplies order. Without outer ticks,
  the helper cannot identify an out-of-order same-ACK pose or distinguish an
  identical repeated snapshot from a transport duplicate.
- The 120-entry window is intentionally lossy after saturation. Scalar counters
  retain observation/repeat/eviction totals for the current epoch only.
- Consumption time and the earlier unobserved portion of held-input drift remain
  unknown. This is an observability improvement, not a replacement prediction-error
  estimate or a claim to solve historical 0.4–0.6 m p95 gameplay divergence.
- `input_stream.gd`, match/actor, UI/backend, bot/art and Sol's shared Python
  harnesses are unchanged. Protocol6, prediction default-off and live rewind off
  remain in force. Independent acceptance is pending.

The next real-ENet out-of-band consumption-tick experiment remains useful for the
unknown anchor, but is not needed to validate this narrower observation-coverage
bar. The host run reuses prior imported caches and launches one native child at a
time; no editor imports or multiprocess network campaign are launched.
