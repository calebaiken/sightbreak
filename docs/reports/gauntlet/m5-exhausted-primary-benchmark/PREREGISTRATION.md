# Exhausted active-primary benchmark, source stage

Base source is `b2e0293a546961230afbd73e5cd2a1a307d69e94`. The accepted
known-dry primary-return correction is present. Its bot, actor and weapon
definition bytes match tested `8e8d13e`. This is a new component; the previous
84-case fixture and all earlier evidence remain unchanged.

The named, inspected comparison bar is this exact SIGHTBREAK implementation:
`SBBotAI.compute_bot_input`, `SBActor.tick_authority_actions`, `_equip`,
`start_reload`, `_fire` and `SBWeapons.DATA`. The common diagnostic fixture is
`game/tests/bot_exhausted_primary_probe.gd`. It will run unchanged on the
baseline and any later candidate. It compares actual decision and action
outputs, not a description of a shipped title. No CS2 balance value or parity
claim is involved.

No engine, import, fixture, export, OCR, service or native runtime has run in
this worktree. No product source, maintained test registration or canonical
mission document has changed. A fresh critic must review this source freeze
before root releases any engine run. The new probe has no generated UID yet;
that setup must also wait for root's engine-lane authorization.

## Source findings and boundary

The current normal/hard combat fallback checks empty clip, an owned sidearm,
acquired target distance below 20 m and no interaction. It does not inspect
primary reserve or holstered sidearm ammo. Easy disables this fallback. The
final input dictionary can request reload whenever clip is empty, even if
reserve is zero. Authority rejects a reload with zero reserve and cannot fire
an empty clip. These source facts justify measuring repeated commands and real
resource outcomes. They do not by themselves select a new tactical policy.

The source-stage correctness boundary is resource accounting and observation.
The probe must preserve player-equivalent input consumption, profile/vision and
objective guards, reload/equip timing, ammo conservation and normal kill rewards.
It must log inefficient commands as observations rather than classify every
unused alternative as a defect. Range, difficulty and objective policy remain
unchanged.

Any later product proposal is limited initially to handling an active primary
whose authoritative clip AND reserve are zero. Loaded and reloadable primaries
are controls. Owned sidearm state must distinguish loaded, reserve-only, dry
and unknown. A missing holstered entry retains legitimate `_equip` defaults;
it is not evidence of known usable or known dry resources. Easy, interaction,
20 m fallback and weapon/vision range boundaries cannot be removed without a
separate root decision and exact candidate preregistration after baseline.
No product edit is authorized by this diagnostic registration.

## Inspected weapon and profile facts

Values below come from `SBWeapons.DATA`, not another game's balance.

| Weapon | Trace range | Cycle interval | Base random-cone half-angle | Reload | Clip / reserve |
| --- | ---: | ---: | ---: | ---: | ---: |
| Kestrel 9 sidearm | 45 m | 0.23 s, semiautomatic | 0.003 rad | 1.45 s | 15 / 60 |
| Vectorline SMG | 35 m | 0.085 s, automatic | 0.009 rad | 1.85 s | 30 / 120 |
| Relay AR rifle | 70 m | 0.105 s, automatic | 0.002 rad | 2.25 s | 30 / 90 |
| Longwatch marksman | 100 m | 0.82 s, semiautomatic | 0.001 rad | 2.8 s | 8 / 32 |

Easy/normal/hard vision ranges are 28/38/46 m, reaction delays are
0.60/0.35/0.18 s, and sidearm fallback flags are false/true/true. Weapon trace
range, acquisition range and the 20 m fallback policy are separate facts.
Base spread does not establish hit probability: `current_spread` adds movement
and airborne spread, applies crouch scaling, and the shot also uses recoil.
The actions-only fixture logs actual floor contact and action spread. It does
not claim grounded accuracy, native cadence, damage effectiveness or aim quality.

## Fixed matrix and logging contract

The probe starts each independent case from one controlled actor state. It
injects visibility as the maintained bot regression does; production FOV,
vision-range acquisition, reaction and action consumption remain in use.
The actor faces the enemy directly. No movement tick or full objective timer
runs. Other actors are inactive. Decisions are followed by the actual
`tick_authority_actions(0.12)` consumer. Shots and any resulting target damage,
death and ordinary kill reward are not suppressed.

Targets are 6 m, exactly 20 m, 24 m, 45.5 m, 60 m and hidden/no-target at 6 m.
At 24 m all three profiles can acquire the controlled visible target. At
45.5 m only hard can acquire it, while the target center lies beyond the
sidearm trace range. At 60 m none can acquire it. These are geometric labels,
not claims that an available weapon will hit a target.

| Group | Controlled combinations | Cases |
| --- | --- | ---: |
| Core resources | 3 profiles × 3 primaries × 6 target states × exhausted/reloadable active primary × loaded/dry/unknown holstered sidearm | 324 |
| Loaded primary | 3 profiles × 3 primaries × 6 targets, loaded sidearm | 54 |
| Reserve-only sidearm | 3 profiles × 3 primaries × near/far/no-target, exhausted primary | 27 |
| Stale active cache | 3 profiles × 3 primaries × near/far/no-target × exhausted/reloadable/loaded active fields; deliberately contradictory active cache | 81 |
| Objective guards | 3 profiles × 3 primaries × near/far/no-target × carrier/defuser, exhausted primary and loaded sidearm | 54 |
| Unowned sidearm | 3 profiles × 3 primaries × near/far/no-target, exhausted primary | 27 |
| Total independent decisions | | 567 |

Exhausted means `(0, 0)`. Reloadable primary means empty clip and one magazine
in reserve. Loaded primary means `(1, 0)`. Loaded sidearm means `(15, 0)`;
reserve-only means `(0, 15)`; dry means `(0, 0)`; unknown has no store entry.
Stale-active-cache cases use authoritative active fields first, regardless of
the contradictory cache. Each actor is reset through stock round reset before
the declared starting resources are installed.

For each profile/primary pair, eight scenarios then run eight consecutive
decision/action steps without resource resets: idle/loaded sidearm,
far/loaded, near/loaded, 45.5 m/loaded, far/dry, idle/unknown,
far/reloadable-primary and near/reserve-only-sidearm. This is 72 sequences /
576 steps, or 0.96 simulated seconds per sequence. These steps can show
repetition and a reload beginning; they cannot prove unbounded deadlock or
completion of every configured reload.

Every row emits the full initial scenario, inventory/ammo store, protected
snapshot before and after decision, full command, bot state, enemy state,
actual shots, resources and protected snapshot after authority consumption.
This corrects the earlier fixture's missing raw snapshots. The header emits
the actual weapon definitions, profiles, engine identity, seed and timestep.

Resource rows mark `active_fields`, `holstered_store`, `unknown` or `unowned`.
Known availability never comes from a stale active cache or a missing entry.
`equip_semantics_total` projects stock `_equip` defaults for unknown entries
solely to check conservation across an actual equip; it is explicitly not a
known-availability total. Each real shot must account for one projected round.
Commands requesting reload/fire on empty resources, switches and known sidearm
resource steps are counted without declaring a new selection policy.

## Gates and next action

The fixture exits nonzero for an authority or observation invariant failure,
missing rows, protocol drift or nonempty offline ranked payload. Its successful
exit would certify only those diagnostic checks. It does not assert a required
new sidearm choice or call the baseline behavior correct.

Fresh source review must check matrix identity, full raw recomputability,
unknown-state handling, real authority calls, ordinary damage/reward handling
and absence of production edits. After approval, root may release one bounded
baseline with private state, retained raw output/source hashes, exact engine
PID/start/exit and scoped cleanup receipts. No elapsed wait releases that run.
Only then will root choose a supported candidate rule and preserved controls.

Proposed eventual command, not yet run:

```sh
./scripts/godot.sh --headless --audio-driver Dummy --script res://tests/bot_exhausted_primary_probe.gd
```

The largest gap is absence of actual baseline decision/action output. Full-match
reliability, perception/objective correctness, effective range and tactical
balance remain separate gates.
