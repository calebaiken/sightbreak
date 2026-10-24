# Request changes: late owned-window ambiguity

Frozen source `01464976ab77bd446265a848e9f3b56560af27d1` is rejected for another
native attempt. This independent review used its own sparse branch/worktree,
based on builder evidence commit `8799bbc`. No engine, native API/input, OCR,
export, CI dispatch or platform process was run.

The blocking finding is in `scripts/macos_ordinary_input.py:276`. Startup discovery
requires exactly one visible owned window, but the fresh capture and input guard
then filter the current rows to the selected ID. A second visible layer-zero
window belonging to the same PID is ignored. `pin_for_input()` calls that guard
and accepts the ambiguous window set. The foreground PID cannot distinguish the
two windows, so subsequent global pointer input has no unique owned-window target.

The retained actual-method counterexample selects PID 123 / window 34 /
`[40,32,960,568]`, supplies current rows for windows 34 and 35 with that same PID
and bounds, and calls the real `pin_for_input()`. It returns with
`input_geometry_pinned=true`, `cg_event_post_attempts=0`, and no error. The real
post-pin `require_target()` also accepts those two rows. A full synthetic driver
case starts with one window, introduces the second during its first capture,
uses the real guard and pin methods, reaches mocked Deploy, and reports a
synthetic pass. These are source counterexamples, never native gameplay evidence.

Required correction: apply the same exact unique owned-visible-window predicate
at fresh post-focus validation/pin and every later input guard. Retain the actual
rows on rejection. Keep valid one-window startup, one 60-second menu deadline,
one five-second focus budget, the permanent input pin and all gameplay/cleanup
limits. Preserve these counterexamples and rerun them against the new freeze.

Independent validation:

- All 67 maintained pure tests pass after restoring the exact tracked screen
  identity fixtures omitted by the sparse checkout. The initial seven fixture
  errors remain in `test_macos_screen_identity.txt`; the fresh restored-fixture
  run is separate. All four aliased-temp pure commands pass.
- `independent_controls.py` runs 11 tests: eight pass and three fail on the
  blocking ambiguity. It also checks foreign metadata and screen identity,
  mapping/focus rejection, pre-pin event release, permanent pinning, later
  geometry/disappearance, late menu/focus and persistent splash, and unchanged
  gameplay/cleanup/helper source. Run it from the repository root with
  `python docs/reports/gauntlet/m2-mac-journey-recovered/independent-startup-fresh/independent_controls.py`.
- `zero-event-pin-counterexample.json` retains the exact selected/current rows,
  zero-event pinned state and actual guard trace. The full synthetic counterexample
  and raw failed unittest output are retained separately.
- All original evidence-index file sizes/hashes and the builder's frozen tested
  source hashes match. The whole Deploy-through-teardown section, budgets, accepted
  menu adapter/driver, Swift capture helper and game source remain unchanged.

The original run `39906639650` remains failed before any CGEvent. I inspected its
actual PNG: it shows the Godot splash, not the game menu. Receipt PID 14158 /
window 54 / `[0,25,1024,684]` agrees with the original observed window. The later
guard rows were not retained, so no resize or window-replacement cause is proved.
The public failure-close request timed out; SIGTERM removed the client. Neither
that failure nor these pure controls establish native gameplay, 1280x720 rendered
frames, clean ordinary teardown, full Mac journeys or an 8.5 quality gate.

Native execution stays unreleased until the narrow correction receives an
independent review on its new exact source and root binds the combined candidate.
