# Independent Phase E review — bounded hit-history diagnostics

Reviewer: separate Codex reviewer agent; read-only tracked source. Automated same-model review does not replace external security review or human gameplay acceptance.

## Recommendation

**Accept as a disabled-by-default diagnostic foundation**, contingent on the aggregate weapon/hit-volume/gameplay regressions. Do not enable historical damage or call this completed lag compensation. No 8.5/10 or production readiness score is established.

Reviewed commit `4c39ccf559d124fe0a12e0584e90b00f2e29f822`; later branch `4401ff81c240b09af5ef6f5870564c89c1a49bf9` only carries outbox fixes in addition. Tested on Linux x86_64 6.18.44 and official Godot 4.7.2 (`ed1daf0bf`), headless.

## Confirmed implementation

- The match hook records only for server mode plus explicit `record_hit_history`; no live firing or damage path consults history. No new RPC or client-trusted hit is introduced.
- Fourteen pose frames bound current-roster history. Exact retained ticks, epochs and per-actor continuity checks reject future/stale/removed/team/death/large-teleport histories.
- Historical trace reuses the live capsule/ellipsoid helpers, captured stance and transform. It never moves live physics nodes or changes ammunition, firing cadence or damage.
- Candidate rewind is capped at 12 fixed 60 Hz ticks / 200 ms and rejects nonfinite/unreasonable timing. Its documented inputs must remain server-observed RTT and server-configured presentation delay.
- Current static-world distance bounds a trace. Smoke remains concealment rather than a ballistic wall, consistent with the live design.

## Independently executed tests

- Maintained history suite: **638 checks passed**, `phasee-unit.log`.
- Independent seeded random parity: **10,000 rays, zero mismatches**, across standing/crouched stances, ten random actor rotations per stance, varied elevation, and ranges from 1 to 140 m. Hit/miss, headshot classification and distance matched live `volume_intersection` within 0.00001 m. `phasee-independent.log`.
- Removed actor IDs and IDs returning after a recorded absent frame could not be hit using the old pose. Four invalid direction inputs were rejected.
- Tests loaded an exact external copy of the commit's history source (global `class_name` removed solely to avoid duplicate registration) and the maintained test with an external preload. Probe source is `phasee/independent_probe.gd`. No tracked files were changed.

## New nonblocking finding / activation requirement

**Slot ownership changes are not continuity events.** `hit_history.gd:29-34` captures team, life and pose but no account/possession generation. A new actor occupying the same ID, same team and alive state, within 3 m, retains continuity without an absent frame. The independent probe confirmed `same_slot_replacement_hits_predecessor=true`. The current server also reuses existing actor slots for bot/human admission, so object-instance identity alone would not cover the actual case.

This does not affect current gameplay because history never awards damage. Before active rewind, add explicit actor/possession generation at join, disconnect/bot substitution and reset boundaries, record it in history, and reject traces across generations. Add actual server lifecycle coverage. Document this activation gate now.

## Other activation gates and unverified areas

- No live RTT estimator, authenticated shot sequence/time mapping or bounded shot/history integration exists yet. The target-tick helper is a candidate policy, not measured fairness.
- Records are end-of-authority-loop samples; future live firing hookup needs explicit phase/ordering semantics. Current state can otherwise be one tick old relative to a shot.
- Existing helper parity does not establish moving-world obstruction correctness, trade-kill policy, animation alignment or defender fairness behind cover. Deliberately inflated RTT remains capped but can still gain allowance.
- Camera/render delay under jitter differs from the nominal 100 ms; it requires measurement before shot-time mapping is accepted.
- Normal fixed roster keeps history bounded. Runtime feature toggling and alternative dynamic rosters need explicit lifecycle handling before exposure.
- No latency-matrix compensated engagements, physical-device timing, recording performance or human acceptance was tested. These remain **UNVERIFIED**.
