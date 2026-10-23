# Independent source rejection of Windows route pulse

REJECT source `977633e44a61352cbf666273931021ebebfe70d9`, handoff
`9a3d73563e45c720aa0a3cccd48eb7d4ecd8c996`, against base
`e28c8e90b9ef2d0c766bd9152c194e3197ceba9a`. No actual acquisition is approved.
Independent criteria were committed in `9329c472` before test execution.

The helper sends a second down edge after the owned-window/focus precondition
has already been lost. Independent controls retain the real `WinUI.key` and
`_input` implementations and replace only User32, clock and sleep. For an
accepted two-key request `('w', 'd')`, User32 changes focus or ownership when the
first `SendInput` returns. The next `SendInput` still sends D down. The helper
checks context only after the entire down loop, then releases both attempted
keys and reports failure. Those releases work; they cannot undo the extra down.

| Independent adverse condition | First W down | Second D down | Result |
| --- | --- | --- | --- |
| Foreground changes from 34 to 99 after W | owned foreground 34 | foreground 99 at 0.005 mock seconds | FAIL |
| Target owner changes from PID 12 to 99 after W | owned PID 12 | owner PID 99 at 0.005 mock seconds | FAIL |

See `independent-receipts.json`, rows named
`test_two_key_dispatch_stops_when_focus_changes_after_first_down` and
`test_two_key_dispatch_stops_when_owner_changes_after_first_down`, and the full
assertions in `independent-controls.log`. Mock seconds describe declared inputs;
they are not Windows latency measurements. The source location is
`scripts/verify_integration_export.py:503`: each iteration checks only the cap,
and `state('after_down')` at line 508 runs after all requested downs.

The largest source deficiency is the gap between successive down edges without
a fresh check of the pinned target's ownership, focus, visibility and input
preconditions. Recheck those conditions before each later down while recognizing
already owned keys, fail on unknown or changed context, and still release every
attempted owned key. Keep the original hold boundary and absolute cap, retain
all in-memory brackets/errors, and publish only after release attempts. A source
correction needs a new preregistration and independent review; this report does
not approve a particular implementation.

## Separate results

All nine maintained pure groups pass in a fresh genuine depth-one checkout:
93 discovered methods, 90 executed passes and the original three native-Windows
reader skips. They do not expose the two failures above. The builder pulse tests
replace `WinUI.key`; the independent controls exercise its actual mapping,
scancode/flag construction and `_input` call into fake User32.

The independent suite has 23 methods: 21 pass and two fail. Passing cases cover
all WASD/LMB preflight gates; invisible/unowned/unfocused/unknown targets;
partial dispatch, mapping errors, cancellation and interrupts; all attempted
releases despite an up error; pre-read/dispatch/sleep/up/post-read lateness;
early sleep return; post-dispatch rebinding; external keys; full receipt
publication after release; before/after trace errors or lateness; retained held
keys for outer cleanup; and exact original callback/route caps. The after-trace
late route control does not obtain an endpoint or a completion event.

Twenty independent source/original checks pass. Existing WinUI methods are AST
identical after removing the new pulse method. The default/coarse approach,
route guards and other offline-controller behavior are AST identical after
removing only the optional fine-pulse branch, forwarding and Windows route
callback. Game, CI, toolchain and focus-helper Git objects are exact. The
aggregate change adds only the pure pulse command; no aggregate or native suite
was run. `source-and-originals.json` records all source SHA-256 digests.

The candidate is better than the original on the narrow inspectable batching
mechanism: it keeps receipt data in memory through release and removes traced
unrelated WASD edges from that selected interval. It does not win the complete
source bar because the two context-loss controls fail. No actual speed,
performance, input-consumption, survival or route-success improvement is shown.
The best result available here is the passing narrow release/deadline evidence
with the source rejection retained.

## Original Windows failures remain failed

The original result/actions and legacy result bytes match all three recorded
SHA-256 digests and sizes. The retained full route, selected pulse edge rows and
source digests equal the original receipts. Original run 39926044462 / job
120322557935 still fails: last accepted stopped x=-6.2700005 at tick 3159,
rejected x=-8.6911116 / vx=-3.7 at tick 3211, outside x>=-8.5, with the same
living actor at 100 health. Target x=-7.8, endpoint distance <.45 m, speed
<=.05 m/s, two later neutral observations and all identity/life/weapon checks
remain binding. Settings, LEAVE, reopen and focus remain unreached.

The original pulse requests are 0.1545885467 and 0.1257692308 seconds; driver
selected-key after-call brackets are .500 and .515 seconds. Those brackets
include controller work and do not identify physical key edges or game
consumption. Original OS diagnostics have r/d/w and no independent A bitmap.
WinUI was already in-process ctypes/SendInput. No per-key subprocess startup,
missed-input cause or performance cause is established.

The separate original delayed held-fire reload diagnostic still fails its
original completion deadline. Later completed authority state and workflow
success do not change that result. Its full error is preserved in
`source-and-originals.json` and the original binding is unchanged. The prior
independent actual report `2020cfa9082fd68a46282a4e25b2f82549a2812d` remains valid.

## Setup, replay and limits

The independent worktree is `/workspace/reviews/windows-route-pulse-source`,
branch `codex/review-windows-route-pulse-20261023`. Tests also ran against
`/workspace/reviews/windows-route-pulse-depth-one`, exact handoff HEAD,
`--is-shallow-repository=true`, `rev-list --count HEAD=1`, with only scripts and
root files materialized and no `docs/reports` fixture directory. Local clone
reported that blob filtering was not recognized, so no object-transfer saving
is claimed. Depth-one and absence of materialized historical fixtures were
checked directly. No test used a historical report fixture.

Retained independent rounds R1 (22 methods) and R2 (23 methods) show the same two
candidate failures. Final receipts add explicit test names and allow a fresh
output path for replay. The reviewer's first source-audit iteration incorrectly
expected `python` without `-v` in the aggregate script; the real line is
`python3 scripts/test_native_route_pulse.py -v`. The original failed audit,
JSON and script are retained as `*-r1.*`; the corrected exact-line comparison
passes. That reviewer setup failure is separate from the two source failures.

Replay the independent controls from any candidate checkout, preserving prior
receipts with a new destination (expected exit 1 for rejected 977633e4):

```sh
SIGHTBREAK_PULSE_RECEIPTS=/tmp/pulse-review-replay-NEW.json python /workspace/reviews/windows-route-pulse-source/docs/reports/gauntlet/windows-route-pulse-independent-20261023/independent_controls.py /workspace/reviews/windows-route-pulse-depth-one
```

Each maintained command and log digest is in `depth-one-checks.json`.
`audit_source_and_originals.py` is run from this review worktree and requires the
original retained native receipt directory named in its source; it is not a
runtime dependency or a depth-one candidate test.

No product file, contributor branch, game rule or canonical mission record was
edited. No Windows/native/engine/CI/OCR executable, service, Apple compile or
nested agent ran. Native source-bound delivery, living stopped cover completion
under the unchanged corridor/cap and the remaining settings/LEAVE/reopen/focus
journey remain unverified. Whole release gates remain open.
