# Exhausted-primary selection candidate

This source-only component starts at root
`c7c95521200490305ff035e01951215b5980e4bb` on the new own branch
`codex/m5-exhausted-primary-selection-20261023`. No engine, import, compile,
native run, service or audio change is released. Root owns the canonical docs
and the later runtime decision. A fresh critic must review the final source
and comparison method before root releases an attempt.

The concrete bar is the unchanged `b87afb7` diagnostic, actual package
`700abf8c9d43279518c5257edfdbaee513569cea`, independently audited by
`b5fa18a1`. Its 1,239 real decision/action rows, positive shot/kill/reload
witnesses and repeated impossible commands are retrievable in the existing
benchmark report. At 24 m and with no target, an exhausted active primary
repeatedly receives reload commands while a known loaded sidearm stays unused.
This bar measures a selection correction; it does not establish shipped-game
parity, balance, aim quality or full match reliability.

## Registered policy

Keep the existing visible-target `<20 m` fallback exactly, including its
empty-clip behavior with primary reserve and its handling of unknown or dry
sidearm cache. Keep easy's `sidearm_fallback=false`. Extend only enabled
normal/hard behavior when all of these conditions hold:

1. The active weapon is a stock primary: SMG, rifle or marksman.
2. Its active `ammo` and `reserve` fields are both zero.
3. The actor owns a sidearm, the sidearm is holstered, and a recorded sidearm
   cache entry has positive clip or positive reserve. An absent entry is
   unknown and does not qualify for the extension.
4. The bot is not interacting.
5. Either it has no acquired target, or the acquired target's center distance
   is at most `SBWeapons.get_weapon("sidearm").range`, currently 45 m.

The center-distance boundary is explicitly inclusive. It uses the existing
weapon definition, without increasing trace range or changing acquisition.
The active primary's potentially stale `_ammo_store` entry is never used to
decide exhaustion. The sidearm cache is consulted only while a primary is
active. The extension requests normal equip input; authority consumes draw,
reload, fire, damage and reward through the stock paths.

Loaded/reloadable primaries, easy, unowned/known-dry/unknown sidearms outside
the old close fallback, beyond-range targets and interaction guards retain
their behavior. Hidden targets qualify through the no-acquired-target branch;
this does not expose or aim at their live coordinates. The previous known-dry
primary-return priority and guards remain unchanged. No difficulty, objective,
perception, movement, aim, cadence, accuracy, magazine, economy or protocol
value changes.

## Common fixture and expected changes

Copy `game/tests/bot_exhausted_primary_probe.gd` from `b87afb7` byte-for-byte,
SHA-256 `540d24dda8e58f4685030e81b55ac3778ccbf31a89f76f9873ac598c32770731`.
Its matrix remains 567 cells, 72 eight-step sequences / 576 steps, and five
mandatory controls / 96 steps. It retains settled physical lanes, full enemy
phases, event/reward snapshots and stock callbacks. The original prepared UID
may be copied from the baseline preparation receipt; no new UID generation
or import runs in this stage. No pose, health, resource, visibility, seed,
timestep, timing budget or terminal assertion is changed in the common probe.

A separate derived native test will add policy assertions to the common
probe's real rows. It will not mutate production or scenario state to force a
win. Register that test in the existing shell and cross-platform native
registries; retain the common probe separately for the exact diagnostic
comparison. Any wrapper UID remains ungenerated until a later released import.

Add a pure raw-output comparator that determines every expected changed
matrix request from the frozen baseline inputs and the registered rule.
All unqualified matrix requests and first-step controls must remain equal.
Changed weapon requests should be accompanied only by the normal suppression
of a simultaneous reload request and stock action consequences. Later sequence
commands may legitimately change because the sidearm's semi-automatic trigger,
draw/reload state, damage and death differ from the baseline. Do not demand
byte-identical downstream planning after different real shots. Separately
recompute resources and action authority on every candidate row, then compare
sequence identities, no-reset continuity, actual sidearm use and unchanged
control output. Never infer correct resources from a requested equip alone.

The three normal and three hard `far_loaded` sequences should each draw once
and consume sidearm ammunition, replacing their 0/0-primary command loop.
The corresponding six `idle_loaded` sequences should each draw once without
firing; their usable sidearm remains available. Easy and the dry/unknown/beyond
range sequence controls remain unchanged. Reloadable primaries still begin a
legal stock reload. All five mandatory positive controls should retain their
observed actual shot/kill/reward or completed reload outputs.

The current common matrix has no acquired target exactly at 45 m or just
inside that range, no 24 m reserve-only repeated sequence, and no new-policy
guard first entered during an existing primary reload. Keep those coverage
limits explicit. The registered predicate itself will receive pure positive
and negative boundary examples, but synthetic examples do not qualify native
selection/action at unmeasured distances. A source critic can require a
separate common supplement before any new baseline/candidate runtime; the
old fixture and receipts must remain untouched.

## Source boundaries and acceptance limits

Planned edits are confined to `game/scripts/gameplay/bot_ai.gd`, the exact
imported common probe/retained UID, a new derived policy test, its existing
registries `scripts/validate.sh` and `scripts/run_native_regressions.py`, and
this own report's comparison/audit code and receipts. Do not edit actor,
weapon, arena, match, audio, canonical mission or prior evidence files.

Pure checks may verify source identity, policy examples, predicted first-step
deltas and meaningful corruptions of raw inputs. They do not execute or
compile GDScript. Later runtime, if released, uses the same pinned Godot,
private staged copy and explicit bounds. An actual-output critic must bind
the exact source, common fixture, all commands, resources, full authority
transitions, action witnesses and cleanup receipts. The builder cannot accept
its own work.

The original baseline strictly failed shutdown with two unidentified leaked
ObjectDB instances. A separate verbose diagnostic also leaked typed WAV
playback/stream objects; common owner and cause remain unproved. This candidate
does not fix, suppress or reclassify either failure. Selection evidence may be
reviewed as a bounded component while strict shutdown stays failed. Broader
risks remain stationary action-only coverage, injected visibility, unlogged
intermediate planning event counters, representative full matches and human
playtesting. Root will decide policy integration only after independent review.
