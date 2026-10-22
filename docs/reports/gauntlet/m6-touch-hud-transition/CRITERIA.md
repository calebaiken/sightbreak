# Live touch HUD mode transition

Declared before the source change on `e7718ee42fd67a65bcb83061c868b34bd9a2c3d2`.
Builder: `/root/touch_transition_builder`. A fresh independent critic owns the
comparison verdict. This is one M6 usability correction; G7 and G10 remain open.

## Inspected benchmark

The actual Linux exported source `872a57618c079c5854dea47d361cc7da732378ec`
produced `/workspace/sightbreak-linux-872a576/builds/layouts-872a576/1280x720/06-touch-hud-opt-in.png`.
SHA-256: `2bd9a745dcf07ab6dc8b8c91f6a1ef0ac9980992bd81706242a3838cbcbc046f`.
The builder inspected the original 1280 by 720 pixels. After the real settings
opt-in, the MENU circle overlaps DEVICE / CARRIED, and the keyboard B / E / TAB /
ESC footer remains visible. A separate native CI outcome critic also reported
both defects. The real frame is the regression bar; no shipped-game parity or
quality score is claimed. CS2 comparison remains externally blocked as recorded
in `docs/roadmap/BARS.md`.

## Required result

1. The real exported desktop sequence starts with keyboard hints, opens FIELD
   MENU and FIELD SETTINGS, opts into touch, and explicitly resumes. MENU and the
   device-state text have no overlapping pixels. Keyboard-only hints are absent.
2. The same session opts out through FIELD SETTINGS and explicitly resumes.
   Keyboard hints return, touch targets disappear, and pointer policy is correct.
   Preserve the original native capture timeouts and screen/source/input guards.
3. A focused source regression exercises both directions while paused in settings,
   using the actual setting toggle signal. Selected mode updates the HUD without
   replacing its nodes, active settings overlay, kill-feed rows or touch instance.
   Pausing/focus loss only disables input; it never changes the selected HUD mode.
4. Initial desktop and mobile mode stay correct. Mobile forces touch even if the
   desktop preference is false. Custom saved positions and button scale survive
   all mode transitions. Default targets stay in place; do not relocate controls
   or rewrite saved layouts to conceal stale HUD state.
5. Check default geometry at 1280 by 720 and 960 by 720, at 100% and 130% text.
   Keep the score centered and health/ammunition bounded. Existing landscape,
   touch, input-mode, objective HUD and lifecycle tests remain required. Safe held
   input and explicit resume behavior must remain intact.
6. Freeze source, export it, retain fresh original on/off transition PNGs and raw
   receipts, then obtain a fresh independent comparison. A source test alone
   cannot pass the native presentation gate. Run the maintained validation suite
   on the combined source after integration; retain skips and failures.

## Resource and scope limits

Do not run Godot, native rendering or OCR until the root grants the shared CPU
lane. Shared tools live outside this sparse worktree. No art, bot, arena, protocol,
economy, prediction or rewind change is included. Software-rendered timings are
functional diagnostics, not physical-device performance acceptance. Human feel,
physical touch/controller input and all other release blockers remain open.

## Iteration 2: preserve readable existing feed rows

Declared after independent source-bound probing of frozen `bc01a06`, before its
revision. The first native run passes generation in 72.252 seconds and visibly
fixes the original overlap/footer pair, but a fresh critic reproduces clipped
long-name feed rows in all four 960/1280 by 720, 100/130% text cases. At 1280/100%,
the frame narrows from 455 to 375 pixels while the retained row stays 435 pixels;
the victim text extends past the frame's right edge at 1178 to 1230. At 960/130%,
the frame narrows from 276 to 196 pixels while the row stays 249 pixels. Raw
independent evidence is in `/workspace/reviews/touch-transition-critic/builds/independent-long-feed-bc01a06`.

Keep that failure and the first native outputs. Refit each retained feed row when
its frame changes width, using the stored original name. Preserve row instances,
ages, headshot meaning and explicit ellipses; widening must recover the text that
fits again. Add actual row and drawn-text bounds to the transition oracle, then
repeat the focused source suite, baseline negative control and existing overflow
test. Freeze the revised source and obtain a new native settings on/off capture
under the unchanged limits. The first frozen native pass does not establish the
revised source's result.
