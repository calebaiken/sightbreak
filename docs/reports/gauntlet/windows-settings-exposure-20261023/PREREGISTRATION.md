# Living/settings cover route, source-only test scenario

Registered before implementation, 2026-10-23. Exact base
`a089473481ced0f2e7b2a7468bbc5d079f92f0ff`; own branch
`codex/windows-settings-exposure-a089-20261023`. No native retry is approved.

The inspected bar is actual run 39916539053 / job 120291226421 and independent
review `f314385`, including original actions, results, initial trace and PNGs.
The resumed player has 100 health through tick 3060 after 07d. A kill notification
occurs at tick 3066 and the next pause observation is dead at tick 3071. Capture
spans controller 108.813–109.000; the next pause key-down starts at 109.079.
There is no one-second idle sleep at this boundary to remove. These sparse,
different-origin clocks do not prove a capture cost or source-caused death.
LEAVE, reopen and the entire focus sequence were unreached; no missed input or
focus-experiment result is established.

Inspect static arena, movement and actor source as well as original pixels. The
player remains at the ordinary first attacker spawn (-4.4,-21). Existing west
freight container bounds are x[-8.5,-5.5], y[0,3.1], z[-15.5,-6.5]. A short
ordinary lateral route to (-7.8,-21) stays south of that container and within
the boundary wall. Static head-height segments from the recorded living enemy
positions intersect the container at that destination while missing it at the
spawn. This is a limited geometric rationale, not native LOS, combat survival
or collision proof.

Implement one fixed, ordinary-input route immediately after round-2 LIVE and
before sidearm/primary switching and settings. Reuse unchanged `approach_floor`
to drive real WASD via the existing OS adapter and read-only native observations.
Use only the fixed destination, never enemy positions for runtime steering.
Share the original 35-second second-LIVE absolute cap between phase readiness
and walking/settling; keep the original whole deadline. Add no stage budget.
Fail on changed actor/life/round/phase, lost focus, invalid health or leaving
the declared corridor. Require the existing .45 m endpoint tolerance, .05 m/s
settle limit and two later neutral stopped observations. Retain raw start/path/
endpoint states and source identity. Do not select later lives, rounds or seeds.

All captures, settings-resume/frame fences, existing identity/health assertions,
HUD analysis pause/LEAVE/reopen/focus checks and original caps remain. This
changes the test scenario from stationary spawn to ordinary hard cover. It is
not a product fix and does not make a broader gameplay or quality claim.

Pure controls must include delayed native-style input/readback walking on the
inspected 60 Hz movement model, death/identity/round/phase/corridor loss, an
expired shared cap, blocked motion, mandatory movement releases and raw state
retention. Preserve existing helper tests and compare exact source/trace with
the base. No engine, import, UID, native input, OCR executable, export, CI,
service, synthetic game input, teleport, forced state or nested agent. Game,
health, AI, seed, rules, timers, graphics and canonical root docs stay unchanged.
Freeze and push for a fresh independent critic before any authorized acquisition.
