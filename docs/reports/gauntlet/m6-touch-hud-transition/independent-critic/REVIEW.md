# Independent live touch HUD transition review

Status: source review accepted; native comparison and regression execution pending.
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

Both independent source readers found no concrete production counterexample.
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

## Open evidence

The root owns the shared CPU lane. This critic has run no Godot, rendering or OCR.
The candidate must still pass execution with retained baseline-negative failures,
fresh exact-source export/capture receipts, direct original on/off PNG review,
and the maintained suite on the integrated source. Source inspection alone does
not pass the presentation gate. The largest remaining gap is that fresh native
transition evidence has not yet been produced.
