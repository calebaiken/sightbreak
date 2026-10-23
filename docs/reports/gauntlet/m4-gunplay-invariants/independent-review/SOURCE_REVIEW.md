# Independent M4 source review

Review status: **REVISE HARNESS; native rules acceptance pending**.

Reviewed immutable source `68587d006a2f96d9586e5f133c91f23d9cce02d0`,
probe commit `b6c2ccdaec649e2cfab9191d56b3a647f160b2d6`, game tree
`9aee5364ecf87e2ec7bc12d7b7b26c738353317d`. The comparison source is
`317410aff6f1a85b4f8c1b5b344c7ec50dd363d2`. The only changed runtime/game path
is the new probe. No shipping rule defect or product improvement is established.

This independent review used source and Python controls only. Root's frozen
`b09cfe1` aggregate owns the local engine/render/OCR lane; this review started no
Godot or native process. The stock actor, weapons and match files retain their
baseline blobs. Protocol 6, phased match combat, prediction default, rewind,
privacy and economy are outside the modification and remain unchanged.

## Largest remaining gap

The 1,800-tick cadence case does not require a complete run of shots.
`gunplay_rules_probe.gd:116–121` checks the first shot, ammunition accounting and
the intervals or phase of shots that exist. It never checks the expected count
or the final eligible shot. Automatic `[0]` and semi-automatic `[0, 14]` for the
sidearm or `[0, 50]` for the marksman pass those predicates after stopping for
the rest of the run. A separate finite-magazine case does not close this gap in
the oversized-magazine sustained case.

`source_controls.py` extracts the frozen stock definitions, verifies all four
truncated counterexamples against a transcription of the actual acceptance
predicates, and writes `source-controls.json`. Its expected schedule uses
absolute interval phase for held automatic fire and even-tick trigger edges for
semi-automatic fire. These are predictions to check against native output:

| Weapon | Expected shots in ticks 0–1799 | Last predicted shot | Repeated semi gap | Float64 reload completion prediction |
| --- | ---: | ---: | ---: | ---: |
| Kestrel 9 | 129 | 1792 | 14 ticks | 88 ticks |
| Vectorline | 353 | 1796 | — | 112 ticks |
| Relay AR | 286 | 1796 | — | 136 ticks |
| Longwatch | 36 | 1750 | 50 ticks | 169 ticks |

Require the count and full-window liveness, alongside current per-shot cadence
and ammunition checks. Keep the truncated controls as deliberate rejections.
No row in this table is an engine result.

## Other false acceptance risks

1. Positive damage checks at lines 204–215 read `damage_taken`, last-hit state
   and confirmation flags without asserting the victim's health change or
   alive state. A body-hit implementation that emits the expected event while
   leaving health at 100 satisfies those checks. Record and check victim health
   and alive before/after the actual ray. At two metres the sidearm and SMG head
   hits are nonlethal, so those weapons never exercise lethal confirmation.
   Add an actual low-health lethal hit for each weapon or explicitly narrow the
   per-weapon feedback claim. `source-controls.json` retains event-only examples.
2. The deploy test clears `shots` immediately after the switch/fire action at
   line 163. That discards the exact action whose early shot should be rejected.
   Preserve its events and assert no shot throughout the complete forbidden
   window. Check both alternate ammunition consumption and shot count. The
   current source correctly sets deploy before firing; this is a probe gap.
3. The friendly case changes the sole target's team and places it on the ray,
   then checks absence of damage/confirmation. It neither verifies a friendly
   contact nor places an enemy behind it. A trace that skips the friendly and
   misses everything also passes. Require a recorded friendly contact and an
   enemy behind it if claiming friendly obstruction coverage.
4. Reload checks assert conservation each tick but output only completion and
   final ammunition. That output cannot independently reproduce per-tick
   conservation or early-transfer checks. Retain the actual tick/ammo/reserve/
   remaining timer series, including the cancellation window. The final-only
   cancellation check can miss transient changes that are later undone.
5. Feedback expiry checks a zero timer after 0.2 s without first checking that
   the actual hit started the timer and stored the head/lethal flags. A removed
   `show_hit_feedback` call passes that assertion. Record and assert the initial
   presentation flags/timer, expiry and both actors' authority state.

## Independent rule comparison

`actor.gd:638–672` advances deploy and each weapon's cycle, completes reload,
handles owned switch requests, starts requested reload, then evaluates fire.
`_fire` consumes one round and carries only a small held-trigger remainder;
semi-automatic trigger edges restart their interval. `_equip` stores magazine
and reserve, cancels reload and sets a 0.3-second deploy delay while leaving the
per-weapon cycle dictionary intact. The source supports the declared timing
rules; an actual engine run must establish their sampled results.

The 0.3-second deploy window hides shorter stock cycles for the sidearm, SMG and
rifle. The marksman's 0.82-second interval is the stock case that distinguishes
cycle preservation after a quick round trip. The all-four switch case remains
useful, but it cannot establish independent preservation of every short cycle
from shot gaps alone.

`_fire` uses `trace_shot`: world obstruction comes from Godot's physics ray,
while operators use the actor's analytic drawn body/head volumes. Accepted enemy
damage is stock damage times clamped distance falloff and the head multiplier;
`apply_damage` emits actual health lost, capped by existing health. Current
positive expectations match that source at short range. The fixture's floor
settling, transform propagation, actual seeded ray contacts, emitted values and
head classification still require the pinned engine; source inspection cannot
certify those assumptions. Two-metre hits are not a range/falloff boundary test.

The probe calls standalone `tick_authority_actions` without a hit sink, so it
resolves damage immediately. Match combat passes a sink and resolves contacts
after all actors act. Keep `authority_order_test.gd` and existing actor, weapon
integrity and feedback controls; this probe does not replace them or establish
match fairness, recipient privacy, network behavior or client presentation.

## Required next evidence

Retain this frozen original and any changed probe separately. After root releases
the engine lane, stabilize generated UID files, freeze the source, run the new
probe and relevant existing tests sequentially with pinned Godot 4.7.2 and private
state. Save exact commands, stdout/stderr, process exit status, engine identity,
source/game-tree identity before and after, and complete case records. Check all
four weapons and all expected case keys; a zero-failure summary alone is not
sufficient. Recompute shot count/timing, reload conservation and timing, deploy,
cycle and damage from those raw records independently.

A bounded source/rules measurement can be accepted only after those outputs pass
independent review. CS2 comparison, physical input latency, played gunfeel,
animation, audio/listening, human review and whole G4/G5/G6/G9/G18 acceptance
remain unestablished. There is no blind A/B or 8.5 score from this evidence.
