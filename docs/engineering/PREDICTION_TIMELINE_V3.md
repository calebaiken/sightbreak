# Prediction timeline audit: bounded slice and reproduction

## Scope fixed before the matched run

Branch `astra/prediction-reconciliation-v3` starts at PR16
`d2439acdd5f73df7bae5ada62ee1e3dec2cf30db`. The comparator is frozen V2
`701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd`. Their gameplay and network source is
identical. PR4, PR11, PR16, PR17 and PR18 handoffs were refreshed before work.
[Ownership handoff](https://github.com/calebaiken/sightbreak/pull/17#issuecomment-6275184071).

This is the requested **gate-evidence fallback**. No bounded shipping accuracy
fix has been established. The only new code is a diagnostic fixture and its
slice-local measurement driver. Prediction stays opt-in/default-off, protocol 6
and live-rewind-off remain intact. The input-freshness worker owns
`input_stream.gd`; Sol owns the shared matrix/network harnesses. No actor/match,
backend, UI, graphics or bot implementation is edited by this slice.

## Source-bound hypothesis

- `match.gd:240–249,259–273`: consume at most one new command per authority tick,
  retain held controls across short gaps, neutralize after 300 ms of input silence.
- `input_stream.gd:61–78`: acknowledgments identify consumed/skipped command
  prefixes, not the number of physical ticks simulated. Backlogs above six retain
  the two newest commands and discard earlier intent without catch-up physics.
- `movement_prediction.gd:58–75`: score only an ACK whose command remains in
  history, remove that prefix, then replay all remaining commands from the received
  state. Subsequent snapshots with the same ACK need not represent the same pose.
- `state_privacy.gd` supplies owner-only ACK/grounded/jump state; the outer snapshot
  has an authority tick. It does not identify the authority tick at which that ACK
  was first consumed. This audit adds no wire field.

A held-input interval therefore changes the authoritative pose associated with an
ACK; a repeated-ACK snapshot may also be absent from `error_samples`. This is a
measurement/timeline concern, not evidence that every historical 0.4–0.6 m p95
error has the same cause. Collision contacts and delayed remote bodies remain
separate known sources of mismatch.

## Matched native design

`prediction_timeline_probe.gd` uses real `SBActor`, `SBMovementPrediction`,
`SBInputStream` and inherited `TacticalMatch._authority_tick` on two equivalent
flat floors separated by 100 m. The test-only Match subclass suppresses scene
startup, objectives and elimination; it does not override authority movement or
the input queue. Automatic Match callbacks are off; the fixture executes one
authority tick per real 60 Hz physics frame. A direct accepted-input timestamp
assignment reproduces the effect of `_input_rpc:1011`; there is no RPC transport.

The schedule produces commands at 60 Hz, submits redundant batches at 30 Hz and
snapshots at 20 Hz. Delays are 0, 3 or 6 physics ticks per direction. Snapshot
application occurs on the next client physics callback (+1 tick). Loss conditions
drop three consecutive upstream batches (six ticks/100 ms), straddling every
90-tick direction edge; retransmissions and native backlog handling are retained.
All six conditions run for 540 ticks (9 simulated seconds): flat/no loss at zero
and 100 ms nominal RTT; flat/loss at 100 and 200 ms; jump/loss at 100 ms; and
prediction-disabled/loss at 100 ms. This is deterministic in-process scheduling,
not an ENet, real-map, multiplayer, display-latency or human-feel campaign.

Each raw physics row retains the two positions, current ACK, pending count,
skip count and last applied snapshot tick. Each delivered snapshot retains its
send/receive ticks, first-consumption pose, held-step count, saved predicted ACK
pose (or null), ACK error (or null), and replay endpoint.

Metrics:

- **ACK error:** current runtime definition; all matching samples, floor-index
  percentile `int((n-1)*0.95)`. Disabled prediction is not scored.
- **Same-ACK drift:** distance from authority pose at first consumption to a later
  authority pose still bearing the same ACK; isolates a nonstationary ACK anchor.
- **Same-time separation:** client/server distance at the end of a paired tick,
  excluding the first 60 ticks. It includes deliberate client prediction lead
  over delayed authority; it is **not a standalone replay-accuracy score**.
- History bound, one authority tick per scheduled frame, resources, protocol,
  default-off prediction, inactive hit history, and actual airborne coverage are
  asserted. Maintained movement/input/privacy/snapshot/peer/history tests run on
  both exact archived sources.

The intended result is attribution and a sensitive retained experiment. It does
not relax a prediction activation threshold or require either label to win.

## Reproduce

Use a clean checkout containing the probe/driver. Run serially on this limited-memory
Windows host; the official engine must be passed explicitly. Example PowerShell:

```powershell
python scripts/measure_prediction_timeline.py `
  --candidate <exact-probe-commit> `
  --godot C:\Users\blith\AppData\Local\Temp\opencode\godot\Godot_v4.7.2-stable_win64.exe `
  --stage C:\Users\blith\AppData\Local\Temp\opencode\prediction-stage-new `
  --out C:\Users\blith\AppData\Local\Temp\opencode\prediction-evidence-new
```

Both locations must be new. The driver archives only `game/` from exact Git
commits, imports first, restores archived import declarations after Windows
line-ending rewrites, applies the identical external probe, captures/waits each
native process using Python, audits error/leak text and hashes shipping files
before/after. `manifest.json` binds source, engine, driver, fixture and raw logs.
`blind/` contains only unlabelled outcomes and review instructions;
`mapping.json` is separate and should be withheld until the critic records its
outcome-only assessment. Evidence publication is a subsequent commit.

## Smallest next experiment

Extend a **test-only** real ENet authority probe to log `(server_tick, move_ack,
first_consumed_tick, held_steps, first_consumed_pose, current_pose)` out of band.
Join those records to client snapshot/replay traces for matched loss-free and
100 ms burst-loss runs on both a flat floor and Relay Yard, including a moving
remote blocker. Compare unchanged live behavior first; never call current-time
client lead pure prediction error. Then replay those recorded traces offline to
test whether a last-consumed-tick anchor can distinguish repeated-held steps from
unconsumed commands without losing direction/jump edges. Require an independent
authority-step/edge oracle and all privacy/epoch/death/reconnect controls before
proposing any protocol or replay change. An additional production snapshot field
would require protocol-owner review and a version decision, not a silent protocol6
semantic change.

Results, unsuccessful preflights and exact source/evidence receipts are appended
in the slice report after the frozen matched run.
