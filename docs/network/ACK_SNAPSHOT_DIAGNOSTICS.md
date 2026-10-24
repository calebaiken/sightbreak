# Local ACK snapshot observability

This additive diagnostic follows PR21's preserved gate-evidence checkpoint
`6a6d18ac295d43bea3be657b0f4575e282e813c0`. That checkpoint showed identical
gameplay outputs and did **not** establish a candidate improvement. The new
declared improvement is observation coverage, not movement accuracy.

The shared interface was declared before editing on
[PR17](https://github.com/calebaiken/sightbreak/pull/17#issuecomment-6275595648)
and [PR21](https://github.com/calebaiken/sightbreak/pull/21#issuecomment-6275595589).
Sol's refreshed head was `7e46e0a2d6c3750c94d59f9be4e1229cac7b06fc`.

## Interface and semantics

`SBMovementPrediction.snapshot_diagnostics` is a local RefCounted helper. Its
`samples` window contains at most 120 dictionaries, each with exactly these fields:

| Field | Meaning |
| --- | --- |
| `epoch` | Round epoch supplied to reconciliation |
| `observation` | Accepted reconciliation-observation ordinal within this epoch; not a server tick or wall time |
| `ack` | Snapshot's `move_ack`, including zero |
| `prediction_enabled` | Whether movement prediction was enabled for that reconciliation |
| `repeated_ack` | Whether the ACK equals the previous accepted observation's ACK |
| `anchor_kind` | Always `first_observed_snapshot_not_consumption` |
| `position` | Own actor's received authoritative snapshot position |
| `first_snapshot_position` | First position observed with this ACK in this epoch |
| `previous_snapshot_delta_m` | Distance from the preceding same-ACK observed snapshot; null on a new ACK |
| `first_snapshot_drift_m` | Distance from the first observed snapshot of this ACK; zero on a new ACK |

The first observed snapshot **may already contain authority held-input steps**.
Neither its position nor its ordinal identifies command-consumption time. A
repeated-ACK delta therefore measures observed snapshot-to-snapshot displacement,
not consumption-time prediction error or hidden authority ticks. An identical
duplicate has zero delta. A new ACK starts a fresh anchor even if positions jump.

Existing `error_samples`, `large_corrections`, correction counts, pending command
history and movement/replay execution retain their current semantics. This helper
does not read them or receive an actor reference. It stores only copied own-position
values and the allowlisted metadata above; no combat/private dictionaries, inputs,
remote actor poses or wire fields are retained or added.

Only snapshots actually passed to `reconcile` are observed. The Match may coalesce
multiple network snapshots before the next physics callback. This diagnostic does
not claim coverage of those un-reconciled packets or change their processing.

## Bounds and lifecycle

One ACK anchor and two position values are retained independently of the 120-entry
window. Appending after capacity evicts the oldest sample. Per-epoch scalar
`observations`, `repeats`, `ignored` and `evicted` counters support coverage checks.
No dictionary grows with distinct ACKs. Valid higher epochs, predict-side epoch
changes and explicit resets clear samples, anchors and counters. Connection reset
allows the epoch space to restart from a smaller number. Regressed ACKs and stale
epochs are ignored by the diagnostic only; invalid/missing/nonfinite/out-of-bounds
positions and invalid ACKs cannot erase the active history.

The existing outer `SBSnapshotBuffer` rejects duplicate or out-of-order server
ticks before reconciliation. The helper does not infer packet order from positions
or ACK identity: same-ACK packets without an outer tick cannot be ordered here.
The protocol and caller signatures remain unchanged.

## Declared validation bar

Under the **same six deterministic packet schedules** retained in PR21:

1. The five formerly unscored repeated-ACK held-state snapshots per burst condition
   gain explicit samples. Coverage of the ten held-state snapshots rises from
   5/10 (existing command-error observations) to 10/10 using the separate series.
2. Every reconciled snapshot has a correctly named observation; an external
   position-based oracle verifies both deltas and the first-snapshot anchor.
3. All pre-existing authority/predicted trajectories, ACK-error samples,
   pending/skip counts and correction outputs compare exactly across sources.
4. Lifecycle controls cover duplicate/reordered outer ticks, direct regressed
   ACK/epoch observations, malformed future-epoch data, round and connection resets,
   copied/allowlisted values, independent predictor instances and 481 observations
   against the 120-sample bound.
5. Maintained movement/input/privacy/snapshot/peer/hit-history tests pass on both
   frozen sources. Default-off prediction, protocol6, disabled live rewind and all
   authority/graphics/bot contracts remain preserved.

The old source lacks the new series and lifecycle interface; its observability
gate must fail rather than being reported as an observability pass. Lifecycle
controls are explicitly unavailable there. Existing native assertions still run.
The new packet-schedule fixture adds read-only observation hooks to the retained
probe; the six conditions, packet schedule and authority methods are unchanged.

## Cached serial reproduction

Freeze the runtime and external workload first. The new driver requires a clean
checkout and a previously imported **frozen-baseline** game whose shipping bytes
match the archived baseline. It archives exact game sources into new directories,
copies the existing import cache, overlays the identical external fixtures and
uses Python capture/wait for one official Godot child at a time. It launches no
editor and no ENet/multiprocess campaign. Shipping hashes are checked before/after;
the permitted baseline/candidate runtime delta is exactly the helper and predictor.

```powershell
python scripts/measure_ack_snapshot_diagnostics.py `
  --candidate <frozen-workload-commit> `
  --godot C:\Users\blith\AppData\Local\Temp\opencode\godot\Godot_v4.7.2-stable_win64.exe `
  --cache-game C:\Users\blith\AppData\Local\Temp\opencode\prediction-timeline-stages-r1\sample-Q\game `
  --stage C:\Users\blith\AppData\Local\Temp\opencode\ack-observability-stage-new `
  --out C:\Users\blith\AppData\Local\Temp\opencode\ack-observability-evidence-new
```

The output includes raw native logs/traces, exact source/cache/engine/workload
receipts, author-run geometric/coverage checks and a fresh `blind/` packet with a
separate mapping. Earlier PR21 raw failures, report and neutral ZIP remain intact.
This is an observability acceptance bar, not an ENet, real-map, performance,
gameplay-accuracy or prediction-activation claim.
