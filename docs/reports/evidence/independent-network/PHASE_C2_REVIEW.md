# Independent Phase C2 review

Reviewed 2026-10-13 by a separate Codex reviewer agent. This is same-model technical review, not an external security audit or human gameplay acceptance. Tracked files were read-only throughout. No merge or PR approval was performed.

## Scope and environment

Reviewed movement prediction and input batching on `codex/network-movement`, initially uncommitted above `05e517e570162942790c5ee33f0c45ae69232daf`. Frozen reviewed sources are `c2/game`, `c2-recheck/game`, and `c2-final/game` in this evidence directory. `c2-final-source.sha256` identifies the final tested movement helper, predictor, input stream and match integration exactly. Implementation may be committed after this freeze; these hashes remain the evidence identity.

Debian GNU/Linux 13.6, Linux 6.18.44, official Godot 4.7.2 `ed1daf0bf`, headless engine. Real CharacterBody3D physics was exercised. No mobile device, mobile GPU, human input-feel assessment, or Internet transport test was performed by this reviewer during C2.

## Recommendation

Accept the repaired code for a development branch with local prediction explicitly opt-in, subject to the complete regression/protocol matrix run by the lead engineer. Keep continuous remote interpolation enabled independently. Do not claim an 8.5 prediction/feel gate or production readiness. Dynamic actor collision, actual visible correction distributions in real-map play, and human movement feel remain UNVERIFIED.

The lead engineer reports real-map acknowledgment-position divergence around 0.6m p95 in an intermediate run. That number was not independently reproduced here and is not the same metric as visible correction amplitude. Nevertheless, the predictor only masks up to 0.35m of correction and calls a correction “hard” only above 2m. Zero hard corrections therefore cannot establish smooth play. Final real-process results must identify their exact tested source and simulated conditions.

## Blocking defects found and repaired

### C2-1: Packet gaps manufactured trigger releases

Original `TacticalMatch._authority_tick` assigned neutral controls on every empty command queue. This reset actor fire/jump/utility edge flags even though no actual release input arrived.

Independent actual-match probe over 180 physics ticks: continuously held sidearm fired 1 shot; identical held controls delivered every other tick fired 13 shots. Both streams were accepted without rejection. `c2_edge_epoch_probe.gd` / `c2-edge-epoch.log` preserve the failure.

Repair: hold previous controls through short gaps; after sustained silence stop actions while preserving fire/jump/grenade/smoke edge latches. Recheck: held continuous and gapped input both fire 1 shot. Sustained silence does not create a new press. `c2-final-lifecycle.log`: 3/3 maintained checks pass.

### C2-2: A stalled old epoch could permanently reject new-round inputs

Original round reset cleared server queues and client pending history but retained incompatible sequence windows. With acknowledgment 1 and 120 old pending commands, every new-epoch packet exceeded the server's ack+120 ceiling. Independent probe: 200 submissions accepted 0, acknowledgment stayed 1, client filled another 120 commands then stopped.

Repair: reset server acknowledgment/queue state and client sequence on epoch transitions, retaining the epoch check against late old packets. Recheck: 200 new-epoch submissions accepted, acknowledgment 200, pending history empty. The maintained test also incorporates acknowledgments, so recovery actually continues.

### C2-3: Temporary loss left permanent combat-input latency

The server popped one queued command per 60 Hz tick while the client generated one per tick. A transient backlog could never drain after normal delivery resumed.

Independent 1200-tick probe used 30 Hz redundant batches, dropped ticks 300–311, then restored immediate delivery. Originally acknowledgment lag stayed 11 ticks (~183ms) at ticks 600 and 1199. `c2_backlog_probe.gd` / `c2-backlog.log` preserve the failure.

Repair: when backlog exceeds six commands, discard stale intent and retain two newest commands. No extra physics or combat ticks run. Recheck: lag returns to 1 tick immediately at tick312 and remains 1 at600/1199 (`c2-final-backlog.log`). Brief actions in discarded commands can be lost; this limitation must be documented, and reliable action-event delivery remains future work.

## Other implementation findings

- Server command batches, client input sequences and acknowledgments do not grant extra simulation time. Authority still advances once per physics tick, with server collision and combat.
- Compressed input has an 1100-byte wire bound and 8192-byte decompressed bound, at most 12 commands, finite vector checks, boolean checks, per-peer rate limiting, and a 120-command sequence window. This is bounded input validation, not comprehensive transport DoS protection.
- Existing queued command identities cannot be rewritten by redundant later packets. Duplicates inside one initial packet currently use its last value; this is not an identified privilege escalation but stricter duplicate rejection would clarify the contract.
- Movement replay does not call weapon fire/reload/damage/economy logic. Actual weapon authority remains separate.
- The implementation correctly moved snapshot replay to the physics callback after the lead engineer found that `move_and_slide()` uses render delta outside physics. This callback diagnosis was independently supported by code inspection; the original timing defect was not separately reprobed after its fix.
- Authoritative grounded/jump state is used for the first replay step, including a no-pending-history path. Remaining Godot collision-contact state is not fully serializable, so this is approximate replay.
- Remote CharacterBody3D transforms follow the interpolation timeline while own prediction replays another timeline. Moving-player collision and dense interactions need dedicated tests and actual gameplay review.
- Backlog discard can skip a brief press/release or jump. It may also leave one to five ticks of input backlog below its correction threshold. This is a documented compromise, not zero-latency or reliable delivery.
- Owner-only grounded/jump/ack fields were added through the privacy projection. No newly exposed enemy-private field was found in this diff.

## Independently executed evidence

| Check | Result | Evidence |
|---|---:|---|
| Initial held-trigger and epoch adversarial probe | Both defects reproduced | `c2-edge-epoch.log` |
| Repaired real-match lifecycle | 3/3 pass | `c2-final-lifecycle.log` |
| Input stream regression | 17/17 pass | `c2-final-input-stream.log` |
| Twin-body delayed physics replay, wall, strafe/diagonal/reversal/jump/landing/crouch | 725/725 pass; max position error 0.075834m in this fixture | `c2-maintained-prediction.log` |
| Transient-loss backlog reproduction and repair | 11-tick persistent lag → 1 tick after repair | `c2-backlog.log`, `c2-final-backlog.log` |
| Adversarial typed input mutation | 247 mutations; 24 accepted, 223 rejected, 0 unsafe outputs | `c2-final-fuzz.log`, `c2_input_fuzz.gd` |

The replay helper and predictor bytes are identical between `c2-recheck` (725-check run) and `c2-final` (final input/lifecycle runs). An intermediate maintained lifecycle test had a GDScript inferred-type parse failure; the explicit Dictionary correction was retested successfully. No test was removed.

The complete baseline regression, real ENet impairment matrix, PostgreSQL/economy suites, build checks and protocol matrix are the lead engineer's separate evidence. This report does not relabel those as independently executed by this reviewer. The existing Claude Unicode HUD failure and previously reported silent admitted-peer issue remain separate upstream/baseline concerns until reviewed against newer upstream fixes.

## Remaining gates

Prediction and movement-feel quality: UNVERIFIED. Physical-device performance: UNVERIFIED. Production transport/security: UNVERIFIED. Human or external security acceptance: not performed. No numerical score substitutes for those gates.
