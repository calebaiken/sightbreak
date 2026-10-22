# Offline input observer candidate

Status: implemented and component-tested; independent review and new native
full-flow runs pending. Neither platform's original offline-flow failure is
converted to a pass by this record.

## Changes

The HUD reader now OCRs the single ammunition line with PSM 7, excluding grenade
inventory beneath it. A pure function extraction lets the comparison invoke the
same production reader. Health contrast/life exclusions and every controller
deadline remain unchanged.

The opt-in offline diagnostic UI snapshot reports the controller's existing
`waiting_for_input_release` flag. The native controller waits for that flag to
be false and neutral commands before sending its fresh W press. Product input
logic, held-input safety, game rules, networking and persistence are unchanged.
Missing guard data fails the new predicate rather than implying acknowledgment.

## Actual Windows evidence

The original artifact identity and predeclared criteria are in `BENCHMARK.md`.
`evidence-r1.tar.gz` retains the complete extracted `offline-input` directory,
including 16 untouched native PNGs, original failure, commands, actions and
observer state. The manifest records every retained byte/hash.

Local Tesseract 5.5.0 replay on unchanged Windows pixels:

| Check | Original reader | Candidate reader |
|---|---|---|
| Nine living-player captures, exact ammunition/reserve | 8/9 | 9/9 |
| Actual menu and eliminated-player frames rejected | preserved | 2/2 |
| Altered copies with health or ammunition removed rejected | not compared | 2/2 |
| `07d-explicit-resume.png` | no ammunition pair | 30/120 |

Maximum external OCR invocation in the corrected comparison: 1.032 seconds,
within the unchanged 20-second invocation cap. This measures the observer only.

Retained failed iteration `hud-comparison-r1`: the test initially expected an
eliminated `06c-next-round` frame to pass. Both readers correctly rejected its
`ELIMINATED - SPECTATING` text. The corrected experiment treats that actual frame
as a negative control and retains its rejection; no life gate was relaxed.

A new Windows native full-flow run remains required. These unchanged screenshots
prove the observed OCR defect and pixel-reader correction, not Windows settings
restart or focus-recovery acceptance. The failing screenshot reads health 100
while the adjacent authority receipt reports a living actor at about 40 health;
this packet does not establish numeric render/authority synchronization.

## Actual Linux failure and ordering reproduction

The retained timestamped CI-console excerpt and parsed failure are the available
raw evidence. The original Linux QA ZIP is inaccessible here because it exceeds
the tool's 32 MiB transfer cap and its official redirect was denied by network
policy. No Linux native screenshots from this run were inspected.

At the release observation the actor was alive, tick 1015, movement/fire neutral,
and position `[-4.400000095, 0.000156248, -19.640003204]`. The final failed
observation was tick 1379, dead, at the same position with neutral movement/fire.
The old release wait completed approximately 15 ms after it began; W was pressed
again about 60 ms after physical release. The old observer has no guard flag,
so the CI log alone cannot prove when its controller consumed that release.

The real Godot controller source test reproduces the unsafe observer ordering:

1. A physical release before the next controller tick leaves neutral commands
   and the guard engaged; the old release predicate already accepts neutrality.
2. A new physical W press at that point remains safely blocked.
3. Release followed by an actual controller tick clears the observed guard.
4. A subsequent W press reaches the real controller's movement state.

`input_mode_test.gd`: 36 checks, zero failures, five new ordering checks.
`offline_diagnostics_test.gd`: 60 checks, zero failures, including inactive and
network-mode boundaries. Production Python predicate checked against actual
Godot snapshots plus absent/nonneutral controls: nine checks, zero failures.
These are source-level input-state tests, not physical hardware acceptance.

Initial invocation failures are retained: a relative project path was invalid
with the toolchain wrapper, and an unimported worktree lacked Godot class cache.
After the ordinary pinned-editor import, the test passed. An input-event reuse
warning led to duplicating generated unit events; the final run is clean.

## Reproduce

Extract the archive into a new directory, then run:

```sh
python docs/reports/gauntlet/m1-offline-flow-observation/compare_hud_pixels.py \
  --captures /absolute/extracted/windows-ci6a/offline-input \
  --output /new/empty/comparison-output
python docs/reports/gauntlet/m1-offline-flow-observation/verify_focus_trace.py \
  /absolute/extracted/focus-unit-r5.log
```

Fresh isolated state is mandatory for Godot source tests. Use the pinned
`scripts/godot.sh --headless --script res://tests/input_mode_test.gd` and
`res://tests/offline_diagnostics_test.gd`; import a new worktree first.

Largest unresolved gap: actual exported reruns on Linux and Windows, especially
under hosted render contention. Independent evaluation must inspect actual
outputs and assess whether the narrowed HUD crop retains sufficient platform
layout tolerance. No builder approval or overall gameplay-quality score is given.

## First new native Linux full-flow attempt

Exact clean source: `94dc6bb`, pinned Godot 4.7.2; separate new build directory
`builds/native-r2`. Export passed. The full original 300-second controller ran
with its original assertions/deadlines and failed after 161.160 seconds at
`Second active round for weapon switching` (35-second stage budget). This is a
failed native journey, not a pass or a demonstrated product input defect.

The actual run reached living movement, fire decrement, reload, natural first
round completion and purchased-SMG HUD 30/120. At the resumed post-purchase
observation, round 2 had 13.117 simulation seconds of buy phase remaining.
The 35-second wall wait advanced the simulation about 12.783 seconds; the final
status remained in buy at tick 3005 with 0.333333 simulation seconds remaining
(`time_left=0.333333333333009`). No deadline or game rule was changed. The target settings/restart/focus block was not reached.

`evidence-native-r1.tar.gz` preserves the complete failed attempt, source/export
receipts and setup failures. An initial missing-template failure and refusal to
reuse an existing export directory were resolved with the pinned local template
setup and a new output directory. The first launch also correctly rejected a
missing Xvfb path before creating a client. Native observation Python regression:
seven tests, four passed and three native-Windows tests skipped on Linux.

A separate `verify_native_focus_only.py` probe is prepared to execute the exact
production focus block verbatim in the first ordinary stock match. It retains
the original 60-second stock-live wait, ten-second per-observation gates, held
W/LMB safety checks, explicit resume, live actor/round checks and fresh movement.
It performs no settings/restart or full-journey acceptance and injects no match
state. The probe records hashes of its driver, original block and executed text.
New native focus-only output and independent review remain pending.

## Strict native focus-only result

Clean source `ccfba936327c64e531e5230ae56eb934bc353650`, game tree
`82b1d4551913b11995dd3fdcda78fbdc8a6663dc`. The new source-bound Linux export
passed and the separate focus-only run completed in **58.943 seconds**, client
exit 0 and no cleanup errors. It used the real X11 root-window focus loss,
physical W/LMB and an ordinary stock first match, with no seed/spawn/rule edits.

The production focus block was executed verbatim; its SHA-256 is
`da33a9123b5c97ded7424b22afdccb1e6b7fd28dc665969ce3e74281569a91a8`.
The receipt retains the original controller, driver and transformed-execution
hashes. The full source/export identity is in the raw result and build receipt.

- Actual input acknowledged before focus loss: W forward and fire, ammo 14.
- Focus loss paused the match; restored focus stayed paused with visible pointer.
- Explicit resume retained three neutral held-input samples, unchanged ammo 14,
  yaw/pitch and a stable position after ordinary inertia settled.
- Physical release was acknowledged with `waiting_for_input_release=false` at
  tick 989. A fresh W press reached actual movement at tick 1002, with **0.427778
  metres** of observed displacement and 729 ms between those observer samples.
- Actor remained alive in the same live round at time scale 1. The process
  closed normally and no descendants or cleanup errors remained.

`evidence-focus-r1.tar.gz` retains every native capture, action, trace, source
receipt and process log from the focused run. Generated cache/config files are
omitted; the archive manifest describes this selection and hashes every file.
Five untouched native PNGs were available; the builder inspected the neutral and
fresh-movement images. A separate critic must evaluate the packet and source.

This is one software-rendered local Linux focus-only pass. The full Linux
journey remains failed at its unrelated second-round wall deadline. Settings
restart and the Windows full journey still need actual reruns. No platform,
visual-quality or performance acceptance is inferred from this focused result.
