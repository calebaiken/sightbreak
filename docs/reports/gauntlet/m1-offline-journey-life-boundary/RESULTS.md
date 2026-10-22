# Offline journey pause boundaries

Candidate code: `5c11a5b` then `171169e`, based on `4418161`. Independent review
and an exact Windows native rerun are required. The game tree is unchanged.
[Criteria](CRITERIA.md) were committed as `c30f5a3` before implementation.

The actual Windows failure in CI [39719407304](https://github.com/calebaiken/sightbreak/actions/runs/39719407304),
frozen `0ca125d`, is a dead player after settings resume. The life guard correctly
rejected it. This is distinct from the earlier ammunition OCR failure.

## Observed failure and correction

The last primary-HUD analysis paused a living player with 70.28 health, then
resumed merely to reopen FIELD MENU immediately. The later actual settings image
shows 40 health. The final generic Escape tap spent 0.3 seconds held plus one
second idle before capturing play; `07d-explicit-resume.png` shows
`ELIMINATED · SPECTATING`, with ammunition 30/120. Native death is recorded at
simulation tick 3272, elapsed 54.533333. Driver and native clocks are separate;
this packet establishes ordering, not a calibrated clock join.

The correction retains the existing ordinary native pause from primary HUD OCR
through field settings. It replaces the final blind delay with physical Escape,
fresh unpaused authority acknowledgment and two drawn frames under a shared
10-second ceiling. The original actor, round, life, focus, weapon, ammunition and
time scale must remain valid before capture, after capture and through saved-HUD
analysis. The final saved-HUD pause remains open for LEAVE MATCH.

A fresh critic identified a context race in `5c11a5b`: the HUD reader could adopt
a new context after capture. `171169e` adds the original-context guard at that
handoff and across analysis, including the already-paused reader branch. Both
iterations are retained. Death during any required same-life transaction still
fails; this run did not justify introducing a new life or round retry.

No game source, spawns, seeds, damage, rules, movement, invulnerability, input
safety or simulation speed changed. The existing 300-second whole-flow,
35-second second-live-round, 160-second natural-round and 20-second OCR ceilings
remain unchanged. The added paused-state observation has a five-second ceiling;
resume acknowledgment and its frame fence share ten seconds within the original
whole-flow deadline.

## Native Linux evidence

All runs used pinned Godot 4.7.2, actual X11 input and native exported clients
under llvmpipe. This is observer correctness evidence, not hardware performance.

| Source / run | Result | Scope and limit |
| --- | --- | --- |
| `c30f5a3`, baseline full journey | FAILED, 149.273 s | Original 35-second second-live wait; actual final status still buy, 0.433333 simulation seconds remaining. Changed block not reached. |
| `5c11a5b`, candidate full journey | FAILED, 162.449 s | Same unchanged wait; actual final status buy, 1.0 simulation second remaining. Changed block not reached. |
| `171169e`, first settings probe | FAILED, 72.112 s | First health OCR exceeded its original 20-second ceiling before settings. Cleanup complete. |
| `171169e`, repeated settings probe | PASSED, 62.373 s | Exact production settings block in the first ordinary stock live match with its stock sidearm. Normal close, exit 0, cleanup complete. |

The successful probe omits purchases, second-round setup, settings restart and
focus recovery. It cannot establish full-journey acceptance. Its driver extracts
the settings block verbatim and records the production controller, exact block,
driver and executed-text hashes. No state is injected.

Retained authority sequence from that successful probe:

| Observation | Simulation tick | Elapsed | Health | Paused | Drawn frames |
| --- | ---: | ---: | ---: | --- | ---: |
| Before field settings | 912 | 15.200000 | 100 | true | 119 |
| After settings changed | 912 | 15.200000 | 100 | true | 132 |
| Actual explicit resume | 924 | 15.400000 | 100 | false | 134 |
| Capture ready / after capture | 937 | 15.616667 | 100 | false | 136 |

The native resumed image shows `100 HEALTH` and `SIDEARM 15 / 60`; the production
pixel reader returns those values. The primary and resumed OCR pauses preserve
elapsed time and health during external analysis. Settings sensitivity changed
through the actual slider and the ordinary offline profile file was saved.

The failed OCR attempt overlapped the critic's separate saved-pixel replay,
which also timed out. That timing is retained; it does not prove the timeout's
cause. The repeat ran after both agents stopped other OCR. A missing-template
export attempt and an external probe path error before client launch are also
retained. Neither was converted to a pass or hidden by a longer deadline.

## Windows controls and supporting checks

Local replay used the unchanged Windows CI pixels with both the frozen and
candidate production pixel readers. Each preserves eight living ammunition
pairs. Both reject the actual menu, both actual eliminated frames (including the
new failure), and copies of a living frame with health or ammunition removed.
The two pixel-reader AST hashes are identical; the correction changes scheduling.

The combined replay passes 41 checks: 26 pixel cases, actual dead-state and
paused-dead HUD guards, original-context boundary mutations and the paused OCR
handoff control. The mutations and extracted-function execution are explicitly
supporting controls, not native gameplay. Replay used `OMP_THREAD_LIMIT=1` and
kept each OCR call's original 20-second ceiling. Raw OCR output is retained.

Python compilation and the maintained native-observation tests pass: four
checks pass, three Windows-only checks skip on Linux. An initial module-style
invocation used the wrong import path; the direct documented test invocation
passed. No new full maintained validation or Windows gameplay pass is claimed.

## Reproduce and review

`evidence-r1.tar.gz` contains 139 individually hashed files plus its manifest:
all native receipts, actions, traces, untouched captures, saved offline profiles,
export metadata, supporting controls and failed command outputs. Export binaries
and generated cache/config are omitted. Source identity remains the exact commit
recorded in each run; this later report does not relabel a binary.

```sh
# Inspect every file against MANIFEST.json after extracting the archive.
OMP_THREAD_LIMIT=1 python3 verify_boundary_controls.py \
  --candidate /extracted/controllers/candidate-171.py \
  --baseline /extracted/controllers/windows-frozen-0ca.py \
  --receipts /extracted/windows-ci-0ca-native \
  --captures /extracted/windows-ci-0ca-native --output /new/windows-replay

# From a clean checkout containing this candidate, use new build/output paths.
SIGHTBREAK_BUILDS_DIR="$PWD/builds/new-pauses" python3 scripts/export.py linux
SIGHTBREAK_BUILDS_DIR="$PWD/builds/new-pauses" \
  XVFB_BIN=/workspace/tools/xvfb/usr/bin/Xvfb \
  python3 docs/reports/gauntlet/m1-offline-journey-life-boundary/verify_native_settings_only.py \
  --target linux --display :193 --output builds/new-pauses-probe
```

The builder has not approved this candidate. The remaining acceptance gap is an
exact Windows full journey, including settings restart and living focus recovery,
plus a Linux full journey that clears all original stage budgets. The scoped
first-round probe proves the corrected transaction only.
