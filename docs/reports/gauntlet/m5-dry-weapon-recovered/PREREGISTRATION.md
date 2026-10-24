# M5 dry primary return, 2026-10-23

The comparison source is published checkpoint `917b143`, whose game code matches
published mission source `ad6cdc20db2a2f3ac179ba3cf3bed502620b6171`. The interrupted
session's unpublished dry-weapon work is absent from this executor snapshot.
This is a new investigation; no earlier local result is claimed as recovered.

The installed original gauntlet-loop, no-ai-slop and its eval, and the project
gauntlet were read before this registration. The measurable bar is the actual
`SBBotAI.compute_bot_input` and `SBActor.tick_authority_actions` behavior at the
published checkpoint, exercised by one common engine fixture. This can establish
a bounded correctness improvement. It cannot establish CS2 parity, full-match
balance, physical performance or the cause of any historical journey timeout.

## Inspected source and candidate boundary

`game/scripts/gameplay/bot_ai.gd` currently selects the first owned rifle,
marksman or SMG whenever a sidearm holder has no acquired target. Its comment
promises primary ammo availability, but its condition never reads ammunition.
`SBActor._equip`, in `game/scripts/gameplay/actor.gd`, saves the outgoing weapon's
ammo only on equip. Therefore the active weapon's ammo-store entry can be stale.
A missing holstered entry causes equip to use the weapon definition's starting
ammo; it cannot be classified as dry from its absence.

The first candidate will change only that primary-return loop. Skip an owned
primary if its recorded holstered clip and reserve are both zero. Keep an
unrecorded primary eligible, retain rifle > marksman > SMG priority, and retain
clip-positive and reserve-positive primaries. Do not alter combat fallback,
reload policy, interaction policy, difficulty, perception, timers, authority,
economy, networking or actor equip behavior.

In particular, existing close fallback checks active clip `ammo == 0`, regardless
of reserve, on normal/hard with an owned sidearm, visible target under 20 m and
no interaction. Empty clip with positive reserve remains eligible. Easy remains
disabled. The new fixture records these controls without changing that policy.

## Components and fixed gates

1. Primary return decisions: each of rifle, marksman and SMG has known dry,
   clip-positive, reserve-positive and missing holstered-state cases, across all
   three profiles. Dry must produce no primary request; the other three must
   preserve the existing request. Membership, order, all-dry, active stale-cache
   and interaction controls must match their explicit fixture expectations.
2. Existing combat guards: normal/hard empty primary clips with zero or positive
   reserve still request sidearm below 20 m. Easy, distance 20 m, loaded primary,
   missing owned sidearm and interacting defuser controls must remain unchanged.
   These use an injected visibility actor, as the maintained bot regression test
   does; they do not qualify real perception.
3. Repeated decisions and equip authority: for each profile, run eight no-target
   steps and eight alternating hidden/visible steps from a loaded sidearm and a
   recorded dry rifle. Use the actual authority action consumer after every
   decision. Candidate must request zero dry equips, switch zero times and issue
   zero reloads with no reserve. The common baseline must demonstrate at least
   one dry equip and one repeated dry reload or fallback cycle before a product
   change is justified. Preserve ammo totals, credits, inventory and health.
4. Decision authority: every decision must leave actor ammo, reserve, weapon,
   reload/deploy timers, cooldowns, inventory, ammo store, credits, health and
   utility counts untouched. Protocol remains 6 and offline ranked payload stays
   empty. Existing bot AI and squad symmetry regressions must pass on candidate;
   root coordinates the broader maintained suite and any missing sparse fixtures.

The fixture prints every case, every sequence step and a final JSON result. Its
default exit status is nonzero if any registered expectation fails. The same
fixture bytes must run on unchanged baseline and candidate. Preserve baseline
failures and all later failed iterations. Any added control or changed criterion
must be registered as a new iteration before rerunning.

## Run boundary and independent review

No engine, export, CI or service has run in this lane at registration time.
The root coordinates the one native lane. Before runtime, a fresh critic must
inspect the frozen fixture, the proposed one-loop boundary and these gates.
Baseline production remains unchanged for the first run. Only a retained
baseline defect permits the narrow product edit and a candidate freeze.

Requested native commands, with root-assigned private state/output paths:

```sh
./scripts/godot.sh --headless --audio-driver Dummy --script res://tests/bot_dry_weapon_test.gd
./scripts/godot.sh --headless --audio-driver Dummy --script res://tests/bot_ai_regression_test.gd
./scripts/godot.sh --headless --audio-driver Dummy --script res://tests/bot_squad_symmetry_test.gd
```

The largest open gap at registration is lack of actual common-fixture baseline
output. A source-reviewed candidate alone will remain unverified.
