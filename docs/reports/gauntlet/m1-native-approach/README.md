# M1 native objective approach

Builder: `/root/gameplay_recon`, branch `codex/native-approach-control`, based on
`561d0cb`. Scope: the exported-objective validator's native WASD approach only.
Game code, physics, observation cadence, fixtures and authority remain unchanged.

## Benchmark and criteria, declared before implementation

The inspected engineering reference is SIGHTBREAK's pinned
`game/scripts/network/movement_step.gd`: 60 Hz physics, 5.1 m/s walking and
28 m/s² ground acceleration. Actual baseline traces are retained under
`docs/reports/evidence/desktop-playability-2026-10-21/linux/ci-s14/offline-plant/`;
their identities are in `baseline-sha256.json`. The player remains alive at 100
health while full-speed steering oscillates around requested z=8. Release at
z=7.607 coasts to 6.760; release at 8.293 coasts to 8.800. The 15-second approach
expires without a settled endpoint. This is a native-controller regression bar,
not a comparison with CS2 presentation or physical input feel.

The root reproduced the failure on a fresh exported client at `561d0cb`, source
game tree `45b6c6e`, in `builds/mission-m1/plant-baseline/`: movement deadline
failure, 68.384 wall seconds overall, living 100-health player at z=7.6983 moving
at −5.1 m/s. Root retains its original actions, screenshots and native recording.

Required outcomes:

- Reach the same requested floor point within the original 15 wall seconds and
  strictly less than 0.45 m, at horizontal speed at most 0.05 m/s.
- Accept only after two distinct newer authoritative neutral-input observations;
  repeated/stale snapshots and moving arrivals cannot satisfy settling.
- Use ordinary native WASD events only. Preserve physics, positions, game rules,
  live scenario state and all objective checks; release controls on every exit.
- Dynamics tests cover sampled observations, native delivery delay, slow simulated
  progress, high-speed arrivals, blocked movement and observation failure. They
  measure endpoint, elapsed wall time and consumed neutral samples.
- Existing observation/tool regressions remain passing. Actual exported plant and
  defuse runs and independent fresh-context critique are required before accepting
  the native milestone. A model pass alone cannot close it.

## Candidate and targeted results

The controller releases movement before its final approach, then sends short
ordinary WASD pulses from rest. Pulse length uses the inspected ground acceleration
and recent observed simulation/wall ratios. It accepts the endpoint only from
later actual neutral, stopped snapshots. Duplicate snapshots cannot add settling
ticks. Every exit attempts all movement key releases, including observation and
deadline failures. No Ctrl mapping or other platform adapter changed.

Commands run in this worktree:

```sh
python3 scripts/test_native_approach.py -v
python3 scripts/test_native_observation.py -v
python3 scripts/test_build_manifest.py -v
python3 -m py_compile scripts/native_approach.py scripts/verify_offline_match.py scripts/test_native_approach.py
git diff --check
```

The nine approach tests pass. The ground-motion model exercises 27 combinations
of objective/diagonal routes, simulation rates 0.4/0.7/1.0 per wall second and
native delivery delays 0/0.1/0.2 simulation seconds, plus delayed-publication and
moving-arrival cases. All 29 successful cases meet the original criteria; maximum
wall time is **11.937015 seconds**, maximum endpoint error **0.408889 m**. Negative
cases retain failure for blocked motion, duplicated stopped snapshots, unreadable
observation, changed round, non-finite velocity and reads finishing after deadline.

Raw output is in `targeted-tests.txt`; per-case measurements are in
`dynamics-results.json`. Existing native-observation tests pass four applicable
Linux cases, with three Windows-only checks skipped. All 24 build-manifest/log
tests pass. Their original outputs are retained beside this record. Python
compilation and diff whitespace checks also pass.

This simulation uses sampled 60 Hz ground dynamics and explicit delivery delay;
it does not model collisions, native scheduling, varying hardware, arbitrary
publication delays or all routes. Native exported plant/defuse evaluation and the
root's separate fresh-context critic remain pending. No game-quality category or
release gate is accepted by these builder results.
