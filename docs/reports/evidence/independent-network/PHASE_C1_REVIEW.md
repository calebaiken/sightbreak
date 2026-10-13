# Independent Phase C1 interpolation review

Base: PhaseB `acfa7041ea61ae835a158d324e276472d8dfdd22`; branch`codex/network-movement`. Reviewed uncommitted production files captured by `c1-source.sha256`; frozen project `c1/game/`. No tracked source edits by reviewer. Godot4.7.2 official, Linux cloud, headless process callbacks. This is not phone rendering/FPS evidence or an external security audit.

## Verdict

**No unresolved blocker found for a scoped C1 development commit after the two corrections below.** Require the lead's full network/privacy/gameplay/protocol regression matrix before integration. Local prediction, adverse-network acceptance, production security and the initiative-wide8.5gates are not established by this limited review.

## Corrected findings

1. **First-visible actors briefly moved backward.** Original buffer returned the latest pose whenever delayed brackets lacked an actor. A2m/s actor revealed at1.000s was shown atx2.0, thenx2.1 at1.050s, then jumped backward tox2.0 at1.083s when the delayed cursor reached its first buffered pose. External Godot probe measured one−0.10m step. Corrected sampler considers only frames containing the actor and holds its first known pose during warmup. Same probe now measures zero backward steps.
2. **Permanent interpolation starvation after a latency increase.** Original clock used`max(clock,server_time)` and could never recover downward relative to packet arrivals. With a simulated arrival-delay step0→250ms,119settled render intervals contained79holds and40moves, each move reaching0.10m at2m/s. The render cursor stayed167ms ahead of the newest snapshot. Corrected monotonic clock slewing yields119continuous moves,0holds, maximum0.033334m/frame, and cursor83ms behind the latest snapshot. This test manipulates arrival timing in the actual buffer; it is not a cellular measurement or a real UDP test.

Evidence: `buffer_adversarial.gd`, frozen module `snapshot_buffer_c1.gd` (only class_name removed to avoid duplicate global registration), `buffer-adversarial.log`, `buffer-adversarial-recheck.log`, and`buffer-reveal.csv`. The CSV was regenerated on the corrected version; original failure values remain in the initial log and review record.

## Independent verification

- Maintained snapshot-buffer suite:13checks,0failures (`c1-maintained-buffer.log`). Covers stale/duplicate ticks, bounded extrapolation, revocation, relevance restoration, epoch reset, yaw wrap, buffer bound, reconnection and first-pose warmup.
- Ideal20Hz stream at2m/s preserves a modeled100ms interpolation delay.
- Actual `TacticalMatch._process` integration probe ran51snapshots over2.505s, observed269process callbacks and200position changes on callbacks where no new snapshot arrived. This directly establishes continuous transform updates between packet arrivals. It is a headless callback test, not graphics throughput. Evidence: `continuous_render_probe.gd`, `continuous-render.log`, `continuous-render.csv`.
- Read-path review: authority-only metadata remains immediate; no damage/ammunition interpolation. Revocation removes all historical poses before sampling. New actors/epochs snap appropriately. Teleport gaps over3m clear prior actor poses. Client reconnect clears tick/epoch history. Rotation uses shortest-path yaw interpolation. Server's integer tick%3 scheduling matches the configured60Hz physics rate and fixes the prior15Hz countdown defect.

## Remaining limits

- Up to50ms velocity extrapolation is not collision-aware. It can overshoot stops or enter thin cover by up to speed×0.05s (approximately0.3m at6m/s) before correction. Treat this as an explicit bounded presentation tradeoff; collision scenarios still need measured fixtures.
- Client replica bodies use delayed render positions while crouch/collision dimensions are current metadata. Local prediction will collide with approximate remote state; its reconciliation/correction limits must be independently tested.
- Clock slewing intentionally changes presentation speed while restoring buffer occupancy. Long server stalls, irregular game time, long-duration clock drift and discontinuities need further real-process tests.
- A first-visible actor holds its first available pose until the delayed cursor catches up. Conservative privacy prefetch reduces this warmup cost but cannot provide unknown historical poses.
- Test harness's authoritative comparison originally sampled server poses only at the20Hz replication cadence, then compared against linear interpolation of those same samples. That is interpolation self-consistency, not an independent60Hz trajectory-error measurement. Reviewer requested every authoritative tick be recorded. Hidden enemy replicas must also be excluded/count-tracked in trajectory comparisons, especially at ten clients.
- The lead owns the real UDP impairment matrix. This report does not claim those runs were independently executed by this reviewer.

## Regression recommendations

Keep explicit tests for monotonic first-visibility movement and recovery after a sustained delay step; single steady-latency tests do not expose these failures. Retain all privacy revocation and round/reset cases when prediction is integrated.
