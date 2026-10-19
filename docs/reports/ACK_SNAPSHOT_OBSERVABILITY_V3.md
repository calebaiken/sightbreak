# ACK snapshot observability — diagnostic-only follow-up

**Author-run observability bar passed:** held-snapshot coverage rose from **5/10
to 10/10 in each of four burst-loss conditions**. All 1,224 candidate reconciled
snapshots received explicit diagnostic samples; recorded legacy movement/error
outputs matched the baseline exactly. Independent acceptance is pending.

This is an **observation-coverage** improvement. It does not establish a gameplay
accuracy, movement, performance or prediction-activation improvement.
The earlier gate-evidence checkpoint, including its unsuccessful preflights and
neutral ZIP, remains unchanged at `6a6d18ac295d43bea3be657b0f4575e282e813c0`.

## Frozen inputs

| Input | Exact revision |
| --- | --- |
| Frozen baseline | `701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd` |
| Prior PR21 gate evidence | `6a6d18ac295d43bea3be657b0f4575e282e813c0` |
| Diagnostic runtime | `0fbce120d8c17db58596d280f7d8401ab2aa0937` |
| First observability workload | `06034326b7b005340453383cf7c25909f34253f3` |
| Shared lifecycle workload | `f5603d6a362cf195e7f8b68a3dae713af475fafd` |
| Final measured workload/source | `1a941e8fb3041eb7467977d31467824b6cf711eb` |

Interface ownership was refreshed and declared on
[PR17](https://github.com/calebaiken/sightbreak/pull/17#issuecomment-6275595648)
and [PR21](https://github.com/calebaiken/sightbreak/pull/21#issuecomment-6275595589)
before editing. [Final exact-source freeze handoff](https://github.com/calebaiken/sightbreak/pull/17#issuecomment-6276048635).

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

The official Godot `4.7.2.stable.official.ed1daf0bf` executed the same external
fixture against exact game archives on one Windows host, using a previously
imported frozen-baseline cache. The manifest records its complete file hashes,
the engine hash, source trees, fixture/driver hashes, commands and captured logs.
Only one native child ran at a time, captured/waited by Python; all have finished.

| Condition | Held snapshots | Old command-error coverage, both sources | Candidate explicit held observations | All candidate observations |
| --- | ---: | ---: | ---: | ---: |
| Flat, zero delay | 0 | — | — | 202/202 |
| Flat, 100 ms RTT | 0 | — | — | 204/204 |
| Flat, 100 ms RTT + bursts | 10 | 5/10 | 10/10 | 204/204 |
| Jump, 100 ms RTT + bursts | 10 | 5/10 | 10/10 | 204/204 |
| Flat, 200 ms RTT + bursts | 10 | 5/10 | 10/10 | 206/206 |
| Prediction disabled, 100 ms RTT + bursts | 10 | 5/10 | 10/10 | 204/204 |
| **Total** | **40** | **20/40** | **40/40** | **1,224/1,224** |

The old command-error series still covers 20/40 held snapshots on both sources.
The additive series closes the other 20 gaps without changing that metric's
meaning. Baseline has no new diagnostic samples and **fails** the declared new
observability gate; candidate passes. This is not an identical-outcomes tie.

### Concrete anchor check

In the flat 100 ms burst trace, ACK 82 was consumed at authority tick 86. The first
observed ACK-82 snapshot was sent at tick 87 and received at tick 91, already
0.085000038 m beyond consumption. The snapshot sent at tick 90 and received at
tick 94 has no saved ACK pose or old error sample. The new sample records:

- `repeated_ack = true`;
- `previous_snapshot_delta_m = first_snapshot_drift_m = 0.255000114` m;
- `anchor_kind = first_observed_snapshot_not_consumption`.

The out-of-band fixture measures 0.340000153 m from consumption to that second
snapshot. The new diagnostic correctly measures only the 0.255000114 m between
observed snapshots. It cannot recover the initial unobserved 0.085000038 m.
The known-offset control independently separates a 0.399999976 m observed snapshot
delta from the old 0.299999952 m consumed-command error.

### Equality, recovery and lifecycle

- All recorded pre-existing condition outputs compare exactly: per-tick authority
  and predicted positions, per-snapshot ACK errors/saved poses/replay results,
  pending and skipped-command counts, error arrays, correction counts/records,
  visual offsets and the shared 14-event lifecycle trace.
- The original ticks 1–540 and snapshots received through tick 540 are identical
  to the prior r2 trace on both sources. The added tail changes only recovery.
  Same-time P95 uses inclusive ticks 61–540; ACK P95 uses samples received through
  tick 540. Both use `sorted[int((n-1)*0.95)]`.
- The 90-tick recovery tail generates neutral commands through tick 600, then
  stops generation. All six conditions on both sources finish at tick 630 with
  sequence/ACK **600/600**, pending history **0**, upstream/downstream packets
  **0/0**, and authority queue **0**. Of the 1,224 observed snapshots, 1,068 are in
  the measured receive window and 156 arrive during recovery.
- The retained ledger pairs every delivered input/snapshot with its send, checks
  drop schedules, ACKs, timestamps and full drain. It is deterministic fixture
  delivery evidence, not a network capture.
- Both sources execute the same 14 duplicate/reordered/round/reconnect events.
  Candidate adds 25 helper-specific checks covering stale ACK/epoch rejection,
  malformed future-epoch data, reset/ACK-zero behavior, copied allowlisted
  metadata, isolated instances and saturation. The 481-observation control retains
  exactly **120** samples, evicts **361**, and preserves its single-ACK anchor.

### Native and offline checks

| Native gate | Baseline checks | Candidate checks | Failures |
| --- | ---: | ---: | ---: |
| Matched probe | 7,620 | 7,645 | 0 |
| Movement prediction | 725 | 725 | 0 |
| Input stream | 17 | 17 | 0 |
| State privacy | 55 | 55 | 0 |
| Snapshot buffer | 15 | 15 | 0 |
| Peer lifecycle | 16 | 16 | 0 |
| Hit history | 638 | 638 | 0 |

Every final native exit was zero; captured logs contain no script/resource-leak
errors. The archive audit passes **46 top-level receipt checks**, including the
per-position coverage/drift, metric-window and transport-ledger recomputation.
It confirms exact legacy equality and the baseline-fail/candidate-pass result.
These are author-run checks; they do not stand in for a fresh independent critic.

Git-blob auditing proves that removing exactly five additive predictor lines
restores the baseline predictor byte-for-byte. The helper and predictor are the
only differing shipping paths. No runtime change occurred after `0fbce120`.

## Evidence and critic handoff

[Evidence index](ack-snapshot-observability-v3/README.md) ·
[manifest](ack-snapshot-observability-v3/manifest-r3.json) ·
[offline audit](ack-snapshot-observability-v3/offline-audit.json) ·
[checksums](ack-snapshot-observability-v3/checksums.json).

Give the fresh critic **only
[`blind-outcomes.zip`](ack-snapshot-observability-v3/blind-outcomes.zip)** first.
SHA256: `612f1a4974d086b17b3dde7654fc34c3d2a4558b53661be6d90cf61a90e37c69`.
It contains neutral outcomes, metric-window instructions and all 14 named native
logs. Withhold the separate mapping, manifest, raw archive and this report until
the outcome-only verdict is recorded. All source/capture receipts are author-run;
an independently captured run remains an integrator/critic task.

```powershell
python scripts/audit_ack_snapshot_evidence.py docs/reports/ack-snapshot-observability-v3/matched-r3.zip
```

The original fallback's fresh blind critic returned
[**TIE**](https://github.com/calebaiken/sightbreak/pull/21#issuecomment-6275674040).
That verdict and its immutable raw packet remain the prior checkpoint. The new
packet incorporates the requested named logs, explicit percentile windows,
known-offset control, packet ledger and full recovery. Earlier successful-but-
less-complete r1/r2 outputs and the initial parse failure are retained separately.

## Scope and remaining limits

- The same six deterministic 9-second measurement schedules plus 1.5-second
  recovery tails use inherited native authority ticks, real actors and replay.
  Packet timing is in-process; this is not ENet,
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
bar. Independent acceptance and aggregate integration remain pending. Keep PR21
draft and prediction default-off.
