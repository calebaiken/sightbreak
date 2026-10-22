# Independent live touch HUD transition review

Status: final source, regression and native transaction review accepted at
`589a52a`; root owns the fresh blind pixel verdict and integrated suite gate.
This does not close G7, G10 or a platform gate.

Reviewer: `/root/touch_transition_critic`, with a separate read-only source
adversary `/root/touch_transition_critic/source_adversary`. Builder:
`/root/touch_transition_builder`. First candidate: `bc01a069fb600b7e10fe9310a5a97f08c726a60b`.
Final frozen candidate: `589a52a4c621503d76383d411b6d3ed07c5e267c`.
Preregistered criteria: `e9ee49b9fcfb7cabac5621e972a71156771186b2`.
Baseline source: `e7718ee42fd67a65bcb83061c868b34bd9a2c3d2`.
The full source hashes and candidate patch are retained beside this report.

## Actual benchmark

I opened the original native 1280 by 720 frame from exported source
`872a57618c079c5854dea47d361cc7da732378ec`:
`/workspace/sightbreak-linux-872a576/builds/layouts-872a576/1280x720/06-touch-hud-opt-in.png`.
Its SHA-256 is `2bd9a745dcf07ab6dc8b8c91f6a1ef0ac9980992bd81706242a3838cbcbc046f`.
The MENU circle intersects the DEVICE / CARRIED text in the upper-right corner.
The keyboard B / E / TAB / ESC hint strip remains visible along the bottom.
The production main and touch-control sources match the pre-change source
baseline, so that actual image is a valid regression bar for this correction.
No shipped-game comparison or numerical quality score is claimed.

## Source judgment

The initial static pass found no concrete production counterexample. A later
source trace identified the existing-row clipping path below and an independent
engine probe reproduced it; that failure supersedes the initial source acceptance.
`sync_hud_input_mode` reads the selected mode through `uses_touch_controls`,
separately from temporary touch input enablement. It changes only the existing
right margin and footer visibility. Calling it from pointer-policy updates and
ordinary HUD processing covers initial creation, real settings changes while
paused, and explicit resume. `clear_ui` clears its references and invalidates the
cached selection before a later HUD is built.

The change keeps the old initial-touch geometry: an 80-pixel right inset. It
leaves touch positions, button scale, layout persistence, protocol and gameplay
unchanged. The focused regression uses the actual CheckButton toggle signal in
both directions, retains overlay/touch/action/status/feed identities, and checks
saved positions and scale. It includes 960/1280 widths at 100/130 percent text,
initial explicit desktop touch, mobile-forced touch, and focus input clearing.
Existing landscape, touch, lifecycle and pointer-policy tests remain required.

The new transition helper does not directly assert pointer mode or every HUD
node identity. The production mutation is narrow, existing source pointer checks
remain, and native transition receipts expose `mouse_mode` for independent
inspection. This is a coverage limit rather than a demonstrated regression.

## Executed focused regression

I inspected the builder's original headless logs and isolation receipts, then
recomputed their correspondence to frozen Git source. The candidate passes
336 checks with zero failures. The negative control runs the identical candidate
test against the original production source and fails 20 of 336 checks. Every
failure names stale footer/margin presentation or the original initial-touch to
desktop hint restoration defect. No unrelated error is mixed into that control.

Both source inventories match their declared main.gd bytes. The test hashes are
identical, and main.gd is the sole differing resource between the two private
projects. Both runs retain unchanged source/copied resources, removed private
native user-data namespaces, removed temporary projects and no finalization
failure. Their raw logs, JSON receipts, SHA-256 inventory and independent checks
are retained under `focused/` and `focused-review.json`.

These are capability/input simulations with `graphical_pointer=false`. They
verify the settings signal, geometry and lifecycle regression in the real main
controller; they do not verify native rendering or physical touch behavior.

## Rejected first candidate: existing feed clips after opt-in

The original `bc01a06` native run completed and its on/off originals show the
intended primary correction: MENU clears DEVICE / CARRIED, the keyboard footer
is absent with touch selected, and that footer returns with touch disabled.
Those images contain ordinary short feed rows. They cannot resolve the separate
long-name transition defect.

`add_kill_feed` fits text only when adding a row. Live opt-in reduces its clipped
frame by 80 pixels without refitting existing rows. The independent external
probe under this report creates real 24-character W/M display names, adds a
headshot feed row, then toggles the actual settings CheckButton and resumes.
All four cases fail, although each preserved row fit before the transition:

| Logical size | Text scale | Frame width before/after | Unchanged row width | Victim text end / frame end |
| --- | --- | --- | --- | --- |
| 1280×720 | 100% | 455 / 375 | 435 | 1230 / 1178 |
| 1280×720 | 130% | 436 / 356 | 417 | 1231 / 1178 |
| 960×720 | 100% | 295 / 215 | 278 | 913 / 858 |
| 960×720 | 130% | 276 / 196 | 249 | 903 / 858 |

The same row instance survives, but its victim label crosses the clipping edge
by 45–55 pixels. This affects both the paused setting change and the resumed
HUD. The expected fix refits existing text in place after actual frame-width
changes, retaining row identity, source names, headshot meaning, age and row cap.
The original failing log, geometry, isolation and source-binding receipts are
retained in `failed-round-1-long-feed/`; the engine used the exact frozen
candidate production main/touch source and reported unchanged resources and
successful temporary/native namespace cleanup. This headless geometry result
does not claim physical or native pixel acceptance.

## Final revision

The revision connects actual kill-feed frame resize to an in-place row refit.
It reads each saved `full_name` again and preserves headshot meaning through
entry metadata, so narrowing fits the names and widening can restore them. Row
instances, birth times and the four-row cap stay intact. I inspected this patch
and found no further source counterexample.

The same independent GDScript probe, with its hash checked against the rejected
run, now passes all four cases. The final fitted row widths are 357, 333, 199 and
182 pixels, inside frame widths 375, 356, 215 and 196 respectively. No name label
crosses the frame, and the original row survives. The actual engine inventory
matches the final frozen main.gd hash; source/copied resources and cleanup checks
pass. Full raw outputs are retained in `passed-round-2-long-feed/`.

I independently inspected the maintained revised test and its controls: final
462/0 versus first-candidate 462/16, with all sixteen negative failures naming
row or text clipping. The identical revised test hashes match on both runs.
Touch 34/0, HUD overflow 2,435/0, objective HUD 33/0 and input lifecycle 3/0 pass
with isolation receipts. Raw logs and JSON are in `round-2-maintained/`. The
builder also retains its initial driver refusal at the maintained-suite
allowlist; no source suite ran during that failed invocation. The successful
driver adds the three maintained suite identifiers only in its own process.

## Final native transaction

I directly viewed the final exported original live, settings, opt-in and opt-out
PNGs, and recomputed all seven original PNG SHA-256 hashes against the raw
receipt. The selected-mode transition is visibly better than the actual
872a576 regression bar: MENU clears DEVICE / CARRIED, the B / E / TAB / ESC
footer disappears in touch mode, and it returns when touch targets disappear.
The score remains centered; health and ammunition remain bounded.

The exact-source export and capture both identify clean `589a52a`, with ELF
SHA-256 `3d28f41d0c5221742a435247bb6d7bcfc6aafc8d97af9de7dbb712e95f176438`.
The unchanged capture command uses the original 120-second case and 520-second
whole limits and completes in 71.987 seconds. Actual native input receipts record
the settings clicks in both directions and explicit resumes. Drawn-frame fences
show mouse mode 0 (visible) while paused and after touch resume, then mode 2
(captured) after keyboard resume. Both native processes exit zero through
WM_DELETE_WINDOW; cleanup reports no errors. Original frames, full transaction
JSON and export source receipt are retained in `native-589a52a/`.

This was a disclosed independent comparison, not a blind verdict: I had already
seen the baseline and source patch. The root arranged a separate fresh blind
pixel judgment, whose result must be recorded separately.

## Remaining limits

The largest evidence gap within this component is native coverage: exported
pixels cover 1280×720 at 100 percent text. The 960×720 and 130 percent text
transition geometry passes headless source checks; these are not additional
exported or physical-device captures. Saved custom positions, mobile behavior
and held-input safety are source simulations. Human feel, physical touch and
controller input, accessibility, performance and CS2 comparison remain open.
The maintained suite must still run on the final integrated source. This
bounded correction does not close G7, G10 or any whole-platform gate.

The root coordinated both short independent headless probe slots. This critic
launched no rendering or OCR process and preserved all observed failed rounds.
