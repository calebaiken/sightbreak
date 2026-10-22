# M4 stock weapon benchmark

Status: initial harness rejected by independent source review; revised harness
awaiting source review and the shared engine lane. No native result exists.

The comparison source is `317410aff6f1a85b4f8c1b5b344c7ec50dd363d2`, game tree
`fb6be859e05812d8707be1ef5c6f747d2588c1e9`. The benchmark uses the actual
`SBActor.tick_authority_actions` path and all four definitions in `SBWeapons.DATA`.
It measures simulation ticks, not physical input latency, listening quality,
animation quality or device performance. External-title and human comparisons
remain blocked by unavailable reference media and people/hardware.

Source inspection found existing all-four sustained cadence coverage, but reload
conservation, switch interruption and numerical damage/feedback coverage are
mostly rifle-specific. No supported high-impact product defect has been found.
No weapon rule or feel parameter will change without a baseline counterexample.

## Components and declared gates

1. Cadence: record every emitted shot tick over 1,800 authority ticks at 60 Hz,
   with an explicitly oversized measurement magazine. Automatic weapons use a
   held trigger; semi-automatic weapons use alternating press/release ticks.
   Automatic cumulative shot phase stays within one tick of the data interval.
   Semi-automatic intervals respect the data interval and the sampled trigger
   edges. Require the complete stock schedule, its count and final eligible shot;
   a partial run cannot pass. A continuously held semi-automatic trigger emits
   one shot.
2. Reload and ammunition: for every weapon, reload from five missing rounds and
   three reserve rounds. The sum of magazine and reserve stays constant on every
   tick; no transfer occurs before completion; the final magazine has two missing
   rounds and zero reserve. Completion is no earlier than the configured reload
   and no later than one physics tick beyond it. Record exact completion ticks.
3. Switch interruption: cancel a reload halfway through with an ordinary owned
   weapon request, return to the original weapon, and verify that magazine and
   reserve are preserved and the cancelled reload does not complete. A ready
   alternate weapon cannot emit a shot before its 0.3-second deploy delay. Include
   the initial switch/fire action and every forbidden deploy tick in the retained
   events. The original weapon's cycle time is retained while holstered. Shorter
   stock cycles are masked by deploy; the marksman case distinguishes cycle
   preservation from the deploy delay.
4. Damage and feedback: fire real rays at isolated enemy body and head volumes,
   recording produced contact distance, damage, shot/ammunition change and
   confirmation flags for every weapon. The recorded distance and stock damage,
   falloff and head multiplier determine expected damage. One accepted hit emits
   one confirmation; misses, friendly obstruction, dry fire, reload and deploy
   cannot emit a damage confirmation. Record and check health loss and alive
   state, actual feedback startup/flags, and an actual low-health lethal ray for
   every weapon. Friendly obstruction requires a produced impact at the friendly
   front volume, with an enemy on the same ray behind it. Feedback expiry cannot
   change either actor's authority.

Each component must retain its raw measurements and any failure. A source change
requires a baseline failure, candidate pass, and controls against weakening the
invariant. A fresh critic must inspect frozen source and actual outputs; the
builder cannot approve this work. Whole G4/G5/G6/G9/G18 remain open.

## Execution boundary

The root reserves the local engine/render/CPU lane for the combined aggregate
and account qualification. No Godot, native capture, renderer or OCR process has
been started for this increment. The root must explicitly release that lane
before native execution.

## Inspected rules and coverage

The stock definitions are in `game/scripts/gameplay/weapons.gd`. These are source
values, not measured output:

| Weapon | Trigger | Interval (s) | Magazine / reserve | Reload (s) | Body / head multiplier | Range / terminal falloff |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Kestrel 9 | Semi | 0.23 | 15 / 60 | 1.45 | 27 / 3.3 | 45 / 0.55 |
| Vectorline | Auto | 0.085 | 30 / 120 | 1.85 | 22 / 3.1 | 35 / 0.5 |
| Relay AR | Auto | 0.105 | 30 / 90 | 2.25 | 35 / 3.5 | 70 / 0.72 |
| Longwatch | Semi | 0.82 | 8 / 32 | 2.8 | 74 / 2.2 | 100 / 0.86 |

`weapon_integrity_test.gd` already measures all-four mean cadence, rifle
held-trigger reload resumption and marksman-to-sidearm cycle/deploy timing.
`actor_test.gd` checks rifle reload transfer, six-metre lethal rifle head hits,
cosmetic noninterference and round refill. `hit_feedback_test.gd` checks authority
and recipient restrictions, feedback flags/expiry and gameplay noninterference.
`authority_order_test.gd` checks phased combat, mutual lethal fire, movement and
shielding; this probe does not replace that match-level test. A separate read-only
source reader found the same matrix gap and no established gameplay defect.

The reload timer repeatedly subtracts a float step and completes on zero. A pure
float64 transcription predicts nominal tick counts plus one tick for all four
weapons. This is a question for native measurement, not a confirmed defect; the
declared policy accepts completion within one step after the data duration.

## Next native commands

Only after the root releases the lane, use pinned Godot 4.7.2 and private state.
Run each command sequentially, retaining stdout/stderr and exit status under a
fresh evidence directory. Check source identity before and after. Import may
create the new probe's UID; stabilize and freeze that file before measured runs.

```sh
SIGHTBREAK_TOOLS_DIR=/workspace/tools SIGHTBREAK_STATE_DIR="$PWD/.local/m4-probe" ./scripts/godot.sh --headless --editor --import --quit
SIGHTBREAK_TOOLS_DIR=/workspace/tools SIGHTBREAK_STATE_DIR="$PWD/.local/m4-probe" ./scripts/godot.sh --headless --audio-driver Dummy --script res://tests/gunplay_rules_probe.gd
```

Relevant existing controls are `weapon_integrity_test.gd`, `actor_test.gd`,
`hit_feedback_test.gd` and `authority_order_test.gd`. The root owns the next
combined-source aggregate. No test pass or product acceptance is claimed here.

## Rejected first harness and source-only revision

Independent review `5606f1ec0c229be6712e51ecc5ce56a0e88e6bf6` rejected probe
`b6c2ccd` / report checkpoint `68587d0`. The original probe and the critic's raw
counterexamples are retained in [round-1-rejected](round-1-rejected/). The review
is retained on branch `review/m4-gunplay-rules`; its report is
`docs/reports/gauntlet/m4-gunplay-invariants/independent-review/SOURCE_REVIEW.md`.
The builder has not rewritten that verdict.

The old cadence predicates accepted automatic `[0]` and semi-automatic `[0,14]`
or `[0,50]` followed by silence. Event-only damage could pass while victim health
stayed at 100. The first switch/fire action was discarded, friendly contact was
not demonstrated, and reload output lacked per-tick records.

The revision requires all stock cadence ticks and their count/final shot,
preserves reload and cancellation timelines, includes the initial deploy action,
and checks every forbidden deploy tick against shots and alternate ammunition.
Real-hit cases record both actors' health/alive states and feedback before and
after visual expiry. Every weapon has a five-health lethal-body fixture. A third
actor supplies the enemy behind the friendly obstruction.

`python3 docs/reports/gauntlet/m4-gunplay-invariants/round-2/source_predictions.py`
uses exact rational arithmetic on unchanged stock intervals. It agrees with the
independent float predictions: 129 / 353 / 286 / 36 shots, ending at ticks
1792 / 1796 / 1796 / 1750 for sidearm / SMG / rifle / marksman. Its 20 pure checks
retain truncated, missing-shot and event-without-health-change counterexamples.
[Raw source predictions](round-2/source-predictions.json) are not Godot output and
do not establish that the revised GDScript compiles or runs. The expected native
case matrix is 13 cases per weapon: cadence, finite magazine, partial reload,
reload switch, switch cycle, three damage cases and five negative cases.
