# Authority order benchmark, declared before gameplay edits

Source bar: frozen SIGHTBREAK `6a0d8d5`, locally fetchable with `git show`.
Reported trigger: Claude PR26 `5288a69`,
`docs/reports/gauntlet/relay-yard-layout/stats-review.md` and raw archived bot logs.
Those logs identify a squad effect and order-reversal sensitivity. They do not
establish map or role balance. This milestone changes no arena or bot code.

Run the identical real Godot 4.7.2 harness before and after the correction.
`game/tests/authority_order_test.gd` drives the real match authority tick, actor
movement, weapon cadence, trace volumes and elimination handlers. Its fixture
removes bot decisions, networking transport and map/objective distractions; it
keeps ten real actors and native physics on a simple floor. It permutes actor
Dictionary insertion order while preserving actor IDs, positions, RNG seeds and
commands, and mirrors the physical duel. Raw per-case records remain in the logs.

The intended bounded correctness contract is:

1. All actors alive when the tick begins advance their authoritative movement
   and stance once. Shots use the resulting common poses. Actor collision
   resolution remains Godot's existing sequential movement behavior.
2. Every eligible weapon consumes its existing one-tick action and traces before
   this tick's hitscan damage can remove a later actor or its shielding volume.
   Opposing lethal shots accepted in the same tick can trade.
3. Damage resolves once before objectives, elimination checks and snapshots.
   One victim emits at most one elimination, with existing actual-damage caps,
   rewards, privacy and weapon data. A corpse cannot fire on a later tick.
4. `SBActor.tick_authority` remains an immediate standalone wrapper, and shared
   movement/prediction math, trigger edges, reload, deploy and cadence stay intact.

Pass criteria: all mirrored lethal duel cases consume one round per eligible
shooter and eliminate both, independent of insertion order. A target that moves
outside a head ray before this tick's combat must miss in either order. Paired
results must agree on health, ammunition and shot/elimination counts, with paired
positions within 0.0001 m (0.1 mm) for native floor-solver settling. Dead
actors must not produce extra shots or duplicate deaths/rewards on the next tick.
Include a front-target shielding regression and preserve weapon/actor/input,
privacy, movement, match and bot regression suites. Keep any baseline failing
oracle distinct from passing maintained tests.

Measure ten-actor authority CPU time in repeated no-fire and sustained-fire loops
with identical commands and script, before and after. Record raw samples and
median/p95; investigate a median increase above 25%, and report rather than hide
noise. These are same-host headless CPU costs, not hardware frame or input latency.

Unsupported competitive policy remains open: kill/assist attribution when several
same-tick attackers hit one victim, the existing attacker-first simultaneous full
team-wipe result, utility detonation ordering, and contact/collision permutation
invariance. This benchmark cannot prove bot/human match balance, network fairness,
sub-tick ordering or parity with a shipped tactical shooter. Builder cannot approve
this candidate; a separate fresh-context critic must inspect it.

## Review-driven benchmark correction

The critic found that original `fire=true` samples depleted their reserve in the
first sample. They remain evidence of an empty held-trigger loop, not sustained
firing. The reviewed benchmark supplies sufficient ammunition only in its fixture,
compensates actual recovered recoil through authoritative look inputs, and records
shots and damage events per sample. Every active 2,000-tick sample must produce
3,170–3,180 shots with one damage event per shot. Input generation and deferred
presentation/audio frame flushes occur outside timed authority calls. Product
magazine, reload, recoil and cadence code stays unchanged.
