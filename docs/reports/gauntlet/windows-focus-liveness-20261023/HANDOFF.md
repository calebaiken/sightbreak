# Source-only handoff: Windows focus liveness fence

Unapproved candidate. Source freeze `19304d5d736b09326d5d2503da09dc8cf7b45129`,
base `b2e0293a546961230afbd73e5cd2a1a307d69e94`, branch
`codex/windows-focus-liveness-fence-20261023`, worktree
`/workspace/sightbreak-windows-focus-liveness`. The builder cannot approve this
component. No native rerun is authorized or performed by this handoff.

## Original failed attempt

Run 39907358390 / job 120262263075 remains failed. Recomputed original file
hashes, full selected action rows and raw before/after states are in
`original-timeline.json`; `recompute_timeline.py` reads the original transferred
`offline-input` directory. The independent critic owns the original archives at
`/workspace/reviews/windows-combined-recovered/docs/reports/gauntlet/windows-combined-recovered-20261023/archives`.

| Retained observation | Controller seconds | Game tick | Health |
| --- | ---: | ---: | ---: |
| Focus trial starts living | 132.406 | 909 | 100 |
| Held W/LMB consumed | 133.594 | 961 | 100 |
| Native focus lost, paused | 135.281 | 1031 | 81.3571 |
| Native focus restored, still paused | 136.140 | 1031 | 81.3571 |
| Explicit resume, held commands neutral | 139.297 | 1088 | 43.1994 |
| Fresh held-input sample 1 | 139.765 | 1127 | 24.1383 |
| Fresh held-input sample 2 | 140.094 | 1140 | 24.1383 |
| Original native dead `alive` event | Separate game clock, wall_msec 29247 | 1166 | 0 |
| Release acknowledged, guard false | 141.390 | 1192 | 0 |

I inspected both original PNGs without OCR. 11a shows FIELD MENU and 081 HEALTH;
11b shows 005 HEALTH and ordinary gameplay. Their controller capture spans are
0.469 and 0.297 seconds. These spans include trace/file work and do not isolate
screenshot cost. Full source-bound dimensions/hashes and raw states before/after
each capture are retained. The clocks have different origins, and sparse rows
cannot locate the exact death instant within a screenshot operation.

Fresh W-down begins at controller 141.515 seconds after the dead release ACK;
the movement wait begins at 141.922 with budget 10, and key release begins at
152.078. The original result fails at 152.703 seconds with clean recorded
cleanup. This does not qualify living fresh-input response. No matched control
supports attributing the failure to bots, diagnostics, capture overhead or a
source change. The separate plant trace records plant/guidance followed by all
defenders eliminated; this component changes no objective rule and qualifies
no device resolution, next buy or plant-flow restart.

## Candidate behavior

`native_focus_fence.py` rejects lost liveness, positive finite health, actor/life
identity, original round/live phase, schema/scope/scenario, speed or required UI
context before movement can count. Fresh W-down rechecks the latest snapshot
and released input guard. Every fresh state considered by the focus wait is
checked before its response predicate. A rejected state records
`FOCUS_PRECONDITION_LOST`, its reason/stage, baseline, previous valid state and
rejected raw state. An unavailable immediate snapshot also fails closed; there
is no additional retry or publication-gap grace period.

Partial focus receipts now survive failure, including capture context before
and after 11a/11b/11c. A response timeout records only
`RESPONSE_NOT_OBSERVED_BEFORE_ORIGINAL_DEADLINE`; it does not declare an input
defect. A new actor or later round cannot substitute for the original actor.
The stock death counter is also fenced to reject an observed replacement life.

`source-preservation.json` compares the actual source AST with b2e0293: every
original named capture call and literal stage budget is preserved, including
the fresh-response 10 seconds. The whole-flow deadline, transition budget,
wait loop, input dispatch, tap delays, captures, HUD pause analysis and original
held-neutrality function are unchanged. The game tree is exactly
`55691684d31d44f1680141954bbe530443de9d1f`; CI files are unchanged. The local
aggregate script gains one pure-test command. No aggregate engine suite was run.

## Pure verification

`pure-checks.json` binds six zero-exit commands and their original logs to the
source freeze. The new fence group has 11 test methods; existing capture fences
have 15, Mac menu controls 11, reader controls 7 and OCR token controls 5.
That is 49 discovered methods, with the reader's original three native-Windows
checks skipped on Linux. No OCR executable, engine, import, UID, native input,
export, CI or service was started. AST parsing and diff whitespace checks pass.

The declared controls cover original dead release, death between release and
key, death during wait with simultaneous displacement, moved actor/life/round/
phase replacement, invalid health/identity/counters/UI, valid living movement,
pre-key displacement, stale/absent observations, key release and immutable raw
receipt values. Declared mutations establish controller behavior only.

## Smallest proposed living-input retry route

Keep the current fence-only freeze separate from any timing change. The smallest
supported scheduling proposal is to replace only the focus-stage
`tap('Escape')` with the same explicit Escape-down, 0.3-second hold and Escape-up,
then immediately use the existing resume acknowledgment and original 10-second
wait. The generic tap adds a deliberate one-second sleep after key-up while
the match has already resumed. Removing that idle second would leave the full
inertia check, two fresh living neutrality samples, held 11b capture, physical
release ACK, fresh-key fence, 11c capture and original whole/stage deadlines.

The observed living-to-dead interval is small enough to justify reviewing this
one ordinary-input scheduling change before a single fixed-order attempt. It
does not guarantee survival. Require a separate source freeze and independent
review before acquisition. Do not disable bots, change health, select a seed,
skip a capture, extend a deadline or automatically search later lives/rounds for
a passing trial. A lost precondition remains a failed qualification attempt.

The largest remaining gap is actual candidate native evidence of a living
actor consuming and moving on fresh W after the full held-input focus sequence.
G1/G6/G7/G12 and the broader mission remain open.
