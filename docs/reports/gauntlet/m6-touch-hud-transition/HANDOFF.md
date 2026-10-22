# Touch HUD transition handoff

Final product source is `589a52a4c621503d76383d411b6d3ed07c5e267c`, built from
`e7718ee42fd67a65bcb83061c868b34bd9a2c3d2` in the isolated sparse worktree
`/workspace/sightbreak-touch-transition`. Integrate these commits in order:

1. `e9ee49b`: preregister the real native benchmark and gates.
2. `bc01a06`: synchronize the existing HUD margin and keyboard footer when the
   selected touch mode changes; add live settings transition coverage.
3. `a048049`: preregister the independently reproduced retained-feed regression.
4. `589a52a`: refit existing feed rows from their stored names when the frame
   resizes; strengthen the transition test with row/text bounds and restoration.

This file and `builder-evidence/` are a later documentation-only follow-up.
Root owns canonical progress, NEXT_SESSION and worklog updates. The independent
critic retains its own [review](independent-critic/REVIEW.md) and counterexample.

## What changed

`main.gd` retains the active HUD, overlay, touch instance, feed rows and their ages.
A selected-mode change updates the existing device margin and keyboard-footer
visibility. The footer always contains the keyboard bindings so a HUD constructed
in touch mode can later return to desktop mode. Temporary pause/focus input
disablement does not change the selected presentation mode. A real frame resize
refits retained feed rows from existing full-name metadata, preserving headshot
meaning and restoring text when room returns.

`input_mode_test.gd` uses the real desktop-touch CheckButton signal through both
directions while FIELD SETTINGS is open. It checks initial desktop/touch and
forced-mobile behavior, 960/1280 by 720 at 100/130% text, saved custom controls,
maximum button size, preserved nodes, row age, complete feed bounds and safe
focus/resume input. Existing art, touch positions, saved-layout policy, bots,
arena, gameplay timing, protocol and economy are unchanged.

## Retained results

| Evidence | Actual result |
| --- | --- |
| Actual `872a576` native benchmark | MENU overlaps DEVICE / CARRIED; keyboard hints remain after opt-in. [Original pixels](../m1-native-ci-39725980732/local/06-touch-hud-opt-in-original.png). |
| First source oracle, identical test | `bc01a06`: 336 checks, zero failures. `e7718ee` production baseline: 336 checks, 20 expected failures on the margin/footer transition. |
| First frozen native iteration | `bc01a06`: seven original PNGs, on/off flow passes generation in 72.252 s; native menu/live exit 0; source unchanged; cleanup errors empty. |
| First blind still comparison | Root's fresh judge chooses B, revealed as `bc01a06`, for the device/Menu gap and removed misleading keyboard hints. This visual win does not accept the whole first candidate. |
| Independent first-candidate counterexample | All four long-feed cases fail on `bc01a06`. At 1280/100%, a 435 px retained row sits in a 375 px frame and victim text extends 52 px beyond its right edge. First candidate rejected on this supported regression. |
| Revised source oracle, identical test | Revised source: 462 checks, zero failures. `bc01a06` production source: 462 checks, 16 expected failures on row/text clipping. |
| Maintained focused regressions | Touch 34/0, HUD overflow 2,435/0, objective HUD 33/0 and input lifecycle 3/0. All runner source/copy guards and owned namespace/project cleanup pass. |
| Revised frozen native iteration | `589a52a`: seven original PNGs, on/off flow passes generation in 71.891 s; menu/live exit 0; source unchanged; cleanup errors empty. Touch resume has pointer mode 0; restored desktop has mode 2, each after at least two drawn frames. |
| Independent unchanged long-feed probe | `589a52a` passes all four cases with the same row retained, versus all four failing on `bc01a06`. Source/copy guards and owned cleanup pass. |
| Final source/native review | Separate critic confirms the revised source, original native PNGs and source/input/pointer receipts pass this bounded correction. Root is arranging a fresh blind comparison of the final originals separately. |

The first source oracle ran concurrently with root's larger headless layout
regression, explicitly authorized for correctness only. Both native captures ran
in the released lane under the unchanged 120-second case / 520-second whole-flow
limits. These software-rendered durations are functional capture receipts, not
device performance evidence.

## Evidence and exact reproduction

[The evidence index](builder-evidence/index.json) hashes 14 verbatim original PNGs
and raw source/native JSON, log and TSV receipts. TSV/log files are losslessly
gzip-compressed, with original-byte hashes in the index. It preserves both negative
controls and the failed first candidate. OCR working-image copies, fixture user
data and exported binaries remain at the raw workspace paths recorded in the
receipts. No retained original image was cropped or altered.

[Source binding](builder-evidence/source-binding.json) proves that the focused
checks' actual production and test hashes match frozen `589a52a`; those checks ran
after implementation, before the source commit. The fresh export/capture and
independent long-feed follow-up use the clean frozen commit directly.

One attempted focused driver stopped at the native runner's ten-suite allowlist
before executing the requested extra suite. Its original failure and cleanup
receipt are retained under `source-r2-harness-attempt`. The successful
[explicit driver](builder-evidence/drivers/run_focused_hud.py) adds the three
existing maintained suite IDs only in its process, retaining the existing
120-second timeout, native namespaces, source guards and cleanup. No source
runner or shipping behavior changed.

From the clean frozen worktree:

```sh
SIGHTBREAK_TOOLS_DIR=/workspace/tools SIGHTBREAK_STATE_DIR=/workspace/sightbreak/.local SIGHTBREAK_BUILDS_DIR="$PWD/builds/native-589a52a" python3 scripts/export.py linux
SIGHTBREAK_TOOLS_DIR=/workspace/tools SIGHTBREAK_STATE_DIR=/workspace/sightbreak/.local SIGHTBREAK_BUILDS_DIR="$PWD/builds/native-589a52a" XVFB_BIN=/workspace/tools/xvfb/usr/bin/Xvfb LIBGL_ALWAYS_SOFTWARE=1 LP_NUM_THREADS=2 python3 scripts/capture_desktop_layouts.py --sizes 1280x720 --touch-toggle --display-base 211 --case-timeout 120 --timeout 520 --output builds/layout-589a52a
```

Those output folders already exist and must be preserved. For a repeat, use fresh
output folders and a free display number. Raw root paths are `builds/layout-bc01a06`,
`builds/layout-589a52a`, `builds/native-bc01a06` and `builds/native-589a52a`.
The original and revised negative controls remain in
`/workspace/sightbreak-touch-transition-baseline` and
`/workspace/sightbreak-touch-feed-baseline` respectively; only their test file is
deliberately replaced by the identical corresponding candidate test.

## Remaining work

Root must run the complete aggregate on the integrated frozen source with its
tracked CSV/hash fixture directory restored. The prior aggregate stopped on a
sparse-checkout omission, so it does not establish a full regression pass. The
existing full landscape matrix remains part of that aggregate; this new actual
native transition capture covers 1280 by 720 only.

The first fresh blind judge's largest remaining visual gap is thin touch-control
outlines and small labels over pale pavement/weapon pixels, particularly USE and
JUMP. This correction does not qualify full accessibility, custom-layout
readability, physical touch/controller input, human play, device performance,
CS2 parity, an 8.5 quality score or whole G7/G10 acceptance.
