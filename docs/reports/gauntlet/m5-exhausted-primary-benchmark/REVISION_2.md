# R2 source registration after rejected R1

Independent review through `fb9b113` rejected source freeze `114150a` before
runtime. Its ordinary rays crossed a container, its damage/reward tests could
pass without damage, and it lacked target decision-phase snapshots and completed
reload witnesses. The rejected freeze, original registration and hash receipt
remain in Git. No R1 engine result exists or is promoted to qualified evidence.

R2 changes only the diagnostic fixture and this report's pure checker/tests.
Production/game definitions, maintained registrations and canonical mission
documents remain unchanged from `b2e0293`. No engine, import, UID generation,
native, OCR, export or service has run. This source requires fresh review and
an explicit root release before any such setup or measurement.

## Physical observation and decision fences

All 567 independent cells and 72 eight-step diagnostic sequences remain. The
resource/difficulty/target labels are unchanged. Ordinary poses through 45.5 m
are centered along `z=-20`, with shooter and target at negative/positive half
distance. This stays inside the stock yard and avoids the freight at `z=-11`.
The 60 m cell uses in-bounds diagonal endpoints at approximately
`(±21.213, 0, ±21.213)`; it remains an injected acquisition-range diagnostic,
and its line may be obstructed. Objective cells retain their site poses.

After each prepared pose, the fixture awaits two physics-frame signals while
match physics remains disabled. It logs frame counters and requires at least
one complete physics frame between preparation and observation. It then queries
the actual settled world's collision mask 1 and the stock center `trace_shot`.
Every row logs query endpoints, bounds, world hit data and stock trace identity.
The ordinary through-45.5 m cells must have clear nominal lines; living targets
within the active weapon's range must be reached by that stock center trace.
All controlled actor footprints must remain inside the yard walls.

These are runtime requirements, not claims that the new poses have been observed
clear. The center query uses the registered fixed yaw/pitch without shot spread
or recoil. Mandatory fired-shot controls below separately require actual hits.
No wall, collider, trace, damage function or reward path is disabled or mocked.

The replacement shooter now has the same five callback connections as stock
`_spawn_actor`, plus recorders. Target damage and elimination events retain their
serial order and snapshots. Each row logs the full protected shooter and target
state before decision, after decision and after action. The target snapshot also
includes its input dictionary. Objective authority fields have the same three
phases. The fixture requires equality across the decision boundary and no shot,
damage or elimination event during planning. Allowed bot/team memory remains
separate. Damage and reward deltas start from the after-decision snapshots.

## Mandatory positive controls

Five additional controls use the separate 2 m lane from `(-1,0,-20)` to
`(1,0,-20)`. Each requires settled in-bounds poses, a clear actual world ray and
a stock center trace that reaches the living target before action. All use real
bot decisions and the stock action, equip, reload, shot, damage and match reward
callbacks. No resource or health value is restored between a control's steps.

| Control | Initial resources / target | Steps at 0.12 s | Mandatory outcome |
| --- | --- | ---: | --- |
| `kill_rifle` | Normal profile, rifle clip 1 / reserve 0, no sidearm; target starts at an explicitly artificial 10 health | 8 (0.96 s) | Exactly one actual shot, positive target damage totaling 10, one elimination, victim deaths +1, shooter kills +1 and ordinary credits +300; no draw or reload |
| `reload_smg` | Normal profile, hidden target, SMG 0 / 30, no sidearm | 19 (2.28 s) | One accepted stock reload start at 1.85 s, one legal completion, final 30 / 0 |
| `reload_rifle` | Normal profile, hidden target, rifle 0 / 30, no sidearm | 22 (2.64 s) | One accepted stock reload start at 2.25 s, one legal completion, final 30 / 0 |
| `reload_marksman` | Normal profile, hidden target, marksman 0 / 8, no sidearm | 27 (3.24 s) | One accepted stock reload start at 2.8 s, one legal completion, final 8 / 0 |
| `reload_sidearm` | Normal profile, exhausted rifle; holstered sidearm 0 / 15; target visible on step 0 and hidden thereafter | 20 (2.40 s) | One actual fallback/equip with stock 0.3 s draw delay, one accepted 1.45 s reload, one legal completion, final sidearm 15 / 0 |

Every reload start must retain clip/reserve and begin at its full configured
duration. Completion must occur within one action tick after that duration and
transfer exactly `min(magazine - clip, reserve)`, adjusted for actual shots.
Reload controls require zero shots/damage/eliminations and an unchanged target.
Their budgets exceed start and configured reload times; the sidearm budget also
includes the draw delay, without assuming draw and reload cannot overlap.

The existing 567 decisions / 72 sequences / 576 sequence steps keep their old
durations. The new controls add 96 steps, making 1,239 decision/action rows.
The final result emits all five labeled witness summaries and must fail if any
registered positive witness is absent, even when every diagnostic cell passes.
A no-op fire, damage, reward or reload function cannot satisfy those controls.
These short stationary controls are not complete matches, cadence/accuracy
benchmarks, tactical balance evidence or a new sidearm policy.

## Pure falsifiers and next boundary

`witness_oracle.py` independently checks the positive raw control rows without
starting the engine. It checks complete protected snapshots, decision fences,
continuous actor states, actual control positions, settled ray/trace results,
shot/damage/death/reward witnesses, draw count and stock reload start/timing/
transfer/completion. It ignores claimed success counts when deriving witnesses.
The full 567-cell comparison still needs an independent actual-output auditor.

`test_witness_oracle.py` uses one explicitly synthetic legal timeline set and
14 falsifiers: missing control, no fired shot, no damage event, no reward,
decision-time target damage, decision-time objective mutation, missing target
resource field, blocked ray, forged in-bounds flag, unsettled ray, no reload
start, illegal transfer, absent completion transfer and a non-Boolean clear flag.
These are parser/oracle controls, not executed game evidence. Their command and
raw result are retained in `r2-pure-checks`.

Only fresh source acceptance can support root releasing one bounded baseline,
with pinned engine, private state, exact source/hash, raw outputs, real native
PID/start/exit and scoped cleanup receipts. Proposed outer wall bound is 120 s.
The source-stage checker cannot prove parsing/import availability, geometry
registration, runtime leaks or positive witness success. Those remain unverified.
Root chooses any product rule only after supported baseline output; no product
edit or removal of profile/range/objective guards follows from this registration.
