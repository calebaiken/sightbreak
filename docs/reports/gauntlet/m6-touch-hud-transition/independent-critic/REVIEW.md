# Independent live touch HUD transition review

Status: revision required. The primary visual correction works, but an independent source probe reproduces clipped existing kill-feed text in all four cases.
This does not close G7, G10 or a platform gate.

Reviewer: `/root/touch_transition_critic`, with a separate read-only source
adversary `/root/touch_transition_critic/source_adversary`. Builder:
`/root/touch_transition_builder`. Frozen candidate: `bc01a069fb600b7e10fe9310a5a97f08c726a60b`.
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

## Open evidence

The root coordinates the shared CPU lane. This critic ran only the explicitly
released short headless adversarial probe; no critic render or OCR was launched.
The candidate still requires fresh exact-source export/capture receipts,
direct original on/off PNG review,
and the maintained suite on the integrated source. Source inspection alone does
not pass the presentation gate. The largest remaining gap is the reproduced existing-feed clipping defect.
The final revision requires fresh native transition evidence after that fix.
