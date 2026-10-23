# Independent revised M4 source review

Verdict: **source accepted for a bounded native measurement after root releases
the engine lane**. No native acceptance or product improvement is established.

Reviewed frozen `d1e89edfbd474a04d6759300141880566b1559e3`, game tree
`20b03e37fef28a601b4488971b9a022d4e8109f1`, against rejected `68587d0` and
the unchanged stock actor, weapons and match rules. The original review and
counterexamples remain unchanged in this directory. The builder's retained
original probe and source-controls JSON are byte-identical to the reviewed
artifacts. Only the test and report paths changed; no shipping source defect or
correction was found.

Root's account trial2 owns the local engine/CPU lane. This review started no
Godot, renderer, OCR or runtime process. Python controls and source inspection
cannot establish GDScript compilation, signal behavior, actual ray contacts or
native test results.

The revision closes the prior source-level acceptance gaps:

| Prior gap | Revised control inspected |
| --- | --- |
| Truncated cadence could pass | Full expected schedule, count and final eligible tick are all required. |
| Expected damage event could accompany unchanged health | Target health delta, expected remaining health, alive state and intended recipient are checked. |
| Sidearm/SMG never exercised lethal confirmation | Each weapon also fires an actual body ray at a five-health victim. |
| Initial switch/fire action was discarded | Its shot and alternate ammunition state are checked and retained; subsequent forbidden deploy ticks are checked individually. |
| Conservation/cancellation could not be recomputed | Started reload, every advancing tick, cancellation, holstered deploy and return/idle samples retain ammo, reserve, timers and shot count. |
| Friendly control could pass without contact | The emitted ray must intersect both actors, with the actual impact distance at the friendly front volume and neither actor damaged. |
| Missing feedback startup could pass expiry | Actual timer and head/lethal flags are checked before visual expiry; both actor snapshots must remain equal afterward. |

`revision_controls.py` independently reads immutable Git blobs and retains
`revision-source-controls.json`. Forty pure controls pass across the four
weapons, including rejection of every retained truncated cadence and event-only
damage example, missing middle/final shots, incorrect alive state and missing
feedback startup. Fourteen source anchors and preservation of the initial deploy
events were also checked. These are source checks, not native test assertions.

The expected cadence schedule was recomputed with exact rational intervals and
separately with the current actor's float64 timer/carry rules. The schedules agree
completely, and agree with the builder's committed predictions:

| Weapon | Predicted count | Predicted final shot tick |
| --- | ---: | ---: |
| Kestrel 9 | 129 | 1792 |
| Vectorline | 353 | 1796 |
| Relay AR | 286 | 1796 |
| Longwatch | 36 | 1750 |

The revised assertions do not weaken the declared reload bounds, ammunition
conservation, 0.3-second deploy delay or original-cycle preservation. The latter
is distinguishable from deploy using the marksman's 0.82-second cycle; the other
three stock cycles remain masked by deploy. The low-health fixture changes only
the victim's test starting health and still uses `_fire` and actual tracing.
The friendly case now aims downward through the front body and the lower body
behind; the pinned engine must show both intersections rather than assuming them.

The largest remaining deficiency is the absence of actual native output. There
is no evidence yet that the revised GDScript compiles, the fixtures settle as
expected, all 52 case records exist, the strict tick schedules match engine
execution, or the existing controls still pass. Keep any native failure and the
exact failed source. An import-generated UID must be stabilized and included in
the frozen identity before measured runs.

When the lane is released, record engine 4.7.2, source/game-tree identity before
and after, commands, exit statuses and complete stdout/stderr for the probe and
existing actor/weapon/feedback/phased-authority tests. Independently recompute the
four cadence schedules; all reload and cancellation samples; initial and later
deploy events and ammunition; switch gaps; real contact distances and stock
damage; health loss, alive/lethal state and feedback fields. Timeline samples use
the post-action counter, while shot ticks are captured before `advance` increments
it; align a sample at tick N with an action/shot tick N−1. Feedback noninterference
is currently an inline snapshot assertion plus a recorded comparison boolean,
rather than separate post-visual raw snapshots, which limits independent
reconstruction of that one comparison.

This measurement does not replace match phased-combat tests or verify network
recipients, state privacy, economy, opt-in prediction or disabled live rewind.
No CS2 comparison, human play/listening, device latency, gunfeel, rendered
presentation, 8.5 score or whole G4/G5/G6/G9/G18 acceptance follows from source
review. Actual results still require a separate independent verdict.
