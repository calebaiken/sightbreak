# Living/settings route handoff, unapproved source-only scenario

Source freeze `af13a99`, exact base
`a089473481ced0f2e7b2a7468bbc5d079f92f0ff`, own branch
`codex/windows-settings-exposure-a089-20261023`, worktree
`/workspace/sightbreak-windows-settings-exposure`. Preregistration `e459fdc`;
first route freeze `bc3dccf`, ground-corridor followup `af13a99`. The builder
cannot approve this component. No runtime retry is approved or performed.

## Actual failed boundary and inspected source

Independent actual review `f314385` of run 39916539053 / job 120291226421 remains
failed for the combined living/settings journey. `original-comparison.json`
retains original-byte bindings, selected full native action/state rows and death
events. The auditor recomputes byte-exact from critic-owned originals. Two
byte-identical original PNGs are retained here and were directly inspected:
06g and 07d both show living 100-health SMG 30/120 at the original spawn.

| Boundary | Controller seconds | Game tick | State |
| --- | ---: | ---: | --- |
| Settings paused | 107.985 | 3030 | Living, 100 health |
| Resume key-down begins | 108.047 | Unassigned | Ordinary native Escape |
| Resume ACK | 108.344 | 3034 | Living, unpaused, 100 health |
| Escape-up completed | 108.422 | Unassigned | Native control released |
| Two-frame fence | 108.719 | 3047 | Living, 100 health |
| 07d capture begin/end | 108.813–109.000 | Unassigned | Original PNG shows 100 health |
| Post-capture/pre-analysis state | Not separately action-timestamped | 3060 | Living, 100 health |
| Next analysis Escape-down begins | 109.079 | Unassigned | Native pause request |
| Kestrel › Operator event | Separate native clock | 3066 | Ordinary kill notification |
| Analysis pause observation | 109.485 | 3071 | Same actor, dead, health zero |

The capture action spans 0.187 seconds and the next pause key-down begins 0.079
seconds after capture-end. These spans include controller bookkeeping; they do
not isolate screenshot cost or locate death inside a capture. There is no
known one-second idle sleep at this boundary to remove. This failure is lost
liveness after acknowledged input, not evidence of missed input or a failure to
pause. LEAVE/reopen and the entire accepted focus experiment remain unreached.
The previous b2e0293 failed living trial and elimination-only plant outcome stay
separate; this attempt's objective passes do not relabel those failures.

Static arena/actor/movement source was read before the preregistration. The
ordinary actor is still at (-4.4,-21), on the exposed side of the west container.
That existing container has bounds x[-8.5,-5.5], y[0,3.1], z[-15.5,-6.5]. The
fixed target (-7.8,-21) stays south of it. The source capsule radius is 0.31 m;
the inspected ground corridor is well clear of the container and boundary wall.
Static head-height segments from the three recorded living enemy positions
miss this one container at the original spawn and intersect it at the target.
This is a route rationale, not native LOS, collision or future survival proof.

## Declared scenario change

After the original round-2 LIVE readiness, the controller now walks to the one
fixed target before sidearm/primary switching and settings. It reuses unchanged
`approach_floor`: only native WASD callbacks and read-only observations reach
it. No runtime enemy position, health threshold, seed choice, alternate route,
later life or later round chooses the target. No state setter or synthetic
game input exists in this change.

The 35-second second-LIVE absolute cap begins where the original 35-second
readiness wait began. Readiness, fresh live observation, walking and natural
settling share that same cap. A final checkpoint rejects completion after the
cap; no route budget is reset. The original whole-flow cap remains 300 seconds.
The existing movement helper still requires endpoint error below .45 m,
horizontal speed at most .05 m/s and two later neutral stopped observations.

The route rejects a changed actor/life/round/phase/team, lost focus, invalid or
nonpositive health, changed SMG 30/120, unexpected inputs, non-stock start or
departure from the fixed ground corridor. It retains raw start, unique observed
path states, previous-valid/rejected state on loss, and raw endpoint. The route
does not heal: positive ordinary damage is recorded in a pure control, while
the unchanged settings assertions still require health to freeze during pause.

This changes the test scenario from stationary exposed spawn to ordinary cover.
It is not a product fix, proof of bot behavior, or a promise of completing the
settings/reopen/focus journey. Every original capture and assertion remains.

## Pure evidence and remaining gate

Eight new methods pass, including nine declared rate/delivery combinations,
positive health loss, death/life/actor/round/phase/focus changes, corridor/height
loss, invalid starts, blocked motion, expired budget and readiness consuming
34.95 seconds of the original cap. Movement releases and raw snapshots are
checked. Five full representative model receipts are retained. These use the
existing inspected 60 Hz movement model; they do not prove native delivery,
collision, measured performance or survival.

All eight pure groups pass: 79 discovered methods, with the original three
native-Windows reader skips. Logs and hashes are in `pure-checks.json`.
`source-preservation.json` verifies that removing only the route import/block
restores the entire controller AST to a089473. HUD analysis, settings health/
identity assertions, frame fences, LEAVE/reopen/focus, capture helpers, physical
dispatch and all other controller behavior remain unchanged. `native_approach`,
the focus helper, toolchain, CI and game tree
`55691684d31d44f1680141954bbe530443de9d1f` are unchanged. The local aggregate
script adds one pure test group; the aggregate engine suite was not run.

No engine/import/UID/native input/OCR executable/export/CI/service, nested agent
or canonical root edit occurred. The next step is a fresh independent source
critic, followed by exact combined-source approval before any one fixed-order
native acquisition. Actual route/collision, continuous living settings analysis,
LEAVE, reopen, focus recovery and normal close remain unverified.
