# Route-only bounded native pulse, source-only preregistration

Registered before implementation on 2026-10-23. Base
`e28c8e90b9ef2d0c766bd9152c194e3197ceba9a`, own branch
`codex/windows-route-pulse-e28-20261023`. No runtime retry is approved.

The inspected engineering bar is final actual review
`2020cfa9082fd68a46282a4e25b2f82549a2812d`, run 39926044462 / job 120322557935,
and original `offline-input/results.json` / `actions.json`. Last accepted stopped
x is -6.2700005 at tick 3159; rejected x is -8.6911116 with vx -3.7 at tick 3211.
Health remains 100 with the same actor/life/round/SMG ammunition. Corridor x>=-8.5
and endpoint <.45 m remain binding. Settings/reopen/focus are unreached. The
separate legacy reload timeout remains failed under its original deadline.

Actual pulse requests are 0.154589 and 0.125769 seconds; selected A/D after-call
down/up brackets are .500 and .515 seconds. These are driver action brackets,
not physical hold intervals or proof of cause. Source inspection finds that
WinUI uses in-process ctypes/SendInput, not a subprocess per key. Fine pulses
currently trace four WASD steering calls and four releases, including OS queries
and actions.json rewrites. This known work occurs between selected key edges.

Add one route-only Windows pulse operation: selected ordinary key-down calls,
bounded sleep, then every attempted key-up in `finally`, within one controller
method call and without trace/file I/O or unrelated key calls between the edges.
Retain monotonic before/after API brackets, requested hold/deadline, and all WASD
OS key/focus snapshots in memory, then persist the receipt after release. Do not
label SendInput return or OS bitmaps as game consumption/physical latency proof.
Anchor the requested hold to the earliest down-call boundary; API cost consumes
that budget rather than creating a new hold window. Late returns must fail,
while release remains mandatory after the original cap.

Expose an optional fine-pulse hook in `approach_floor`, defaulting to the exact
old path. Only the ordinary Windows settings route supplies it. Coarse route
motion, Linux/default approaches, all other input schedules, capture/graphics,
game/AI/rules/seed and original 35-second/whole caps remain unchanged. Do not
loosen corridor, target, .45 m endpoint, .05 m/s settle, two later neutral states,
identity, life or health checks. Raw controller state gates remain authoritative.

Pure controls must exercise mocked native exceptions, down/up release attempts,
sleep failure, pre-edge expiry, late successful calls/reads, OS state receipts,
foreground loss, original cap sharing, default-path behavior and actual source
scope. Retain raw failed-run facts with hashes and meaningful declared pulse
model comparisons. No engine/import/native/CI/OCR/service/Apple compile/heavy
work or nested agents. The builder cannot approve its own freeze; require fresh
source review and exact combined approval before any actual acquisition.
