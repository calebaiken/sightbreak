# Independent offline boundary review

Reviewed criteria c30f5a3, initial candidate 5c11a5b and correction 171169e.
This review uses the actual frozen Windows 0ca125d receipts and screenshots,
the two local full-journey failures and the corrected native focused probe.
It does not compare presentation quality or establish a release gate.

The initial candidate had a source acceptance gap: its original-context frame
fence ended before capture, then HUD analysis established a new context. A
round or life change during capture could evade the promised same-life check.
The critic reported this before approval. Correction 171169e checks the original
context immediately after capture and at every HUD-analysis observation. The
already-paused path also checks a fresh observation after OCR. The gap is fixed
on source inspection.

The actual baseline Windows death is independently reconstructed in
`windows-recomputed.json`. Primary HUD pause held tick 3244, elapsed
54.0666666666649, health 70.2791296386719. The baseline resumed at tick 3246
before opening settings. Death appears at tick 3272, elapsed
54.5333333333315, frame 748. I viewed the original primary HUD, main menu,
settings and resumed images: settings shows 040 HEALTH and resumed play shows
ELIMINATED / SPECTATING. Native and driver clocks have different origins;
these facts establish order rather than an exact clock join.

Ten independent saved-pixel checks passed: the baseline and first candidate
readers each accept real fire/reload/primary positives and reject the actual
main-menu and eliminated frames. The readers are identical. These checks use
local Tesseract on retained Windows pixels, so they do not prove Windows native
behavior. `source-checks.json` separately records 15 supporting checks, including
the actual dead Windows observation, a paused version of that observation and
individual actor/focus/round/weapon/ammunition/speed changes. Deliberately changed
states and executed source predicates support the source review only. The final
171169e pixel-reader AST is identical to the exercised baseline reader.

The local baseline c30f5a3 full journey failed at 149.27315811200242 seconds and
candidate 5c11a5b failed at 162.44861794100143 seconds. Both hit the unchanged
35-second second-live-round wait while still in round 2 buy, with 0.433333333333009
and 0.999999999999677 simulation seconds remaining. Both report empty cleanup
errors and SIGTERM teardown of the uncompleted client. Neither reached the
changed settings boundary; their different random stock seeds and wall timings
cannot support a relative performance claim.

Only the observer script changes. The game tree is unchanged from 4418161 and
frozen Windows 0ca125d. Native OS controls, stock starts/seeds/rules, protocol 6,
prediction off, time scale 1, 300-second whole flow, 35-second second-live wait,
160-second natural-round wait and 20-second OCR watchdog remain. The explicit
resume acknowledgment and two-frame fence share one 10-second watchdog. A
dead player, changed life/round/context or legitimate damage that kills the
player remains a hard failure.

The corrected 171169e focused native Linux probe passes in 62.37265693399968
seconds with actual client exit 0 and empty cleanup errors. Seventeen independent
checks in `native-recomputed.json` recompute raw provenance, source/block hashes,
stock rules, observation identity, arithmetic and actual control ordering without
calling the production acceptance predicates. Raw files and unmodified PNGs are
in `native-focused-raw.zip`; its digest and every retained file hash are recorded.
The probe runs the production settings block verbatim in the first ordinary
stock live match, with the default sidearm. It omits purchases, the second-round
setup, restart and focus recovery.

Before and after settings, native tick 912, elapsed 15.2000000000003 and health
100 are exactly frozen while drawn frames progress 119 to 132. Physical Escape
produces an actual unpaused observation at tick 924/frame 134; the fence observes
tick 937/frame 136. Escape key-up is sent through the native input API before
the frame fence and capture; the OS diagnostics separately sample r/d/w, not
the Escape bitmap. Acknowledgment plus the two-frame fence takes 1.4199399250028364 wall
seconds within the shared 10-second watchdog. I viewed the original settings
and resumed PNGs: sensitivity 0.0051 persists, and resumed native pixels show
100 HEALTH / SIDEARM 15/60. The original-context guard continues through fresh
paused OCR observations. This is Linux software-rendered observer behavior,
without a device performance claim.

The earlier focused attempt timed out in the original 20-second health OCR
before entering the changed block. Its exact 72.11193678899872-second failure
and cleanup success remain retained. `PIXEL_RERUN_FAILURE.md` also records the
overlapping independent saved-pixel timeout and the uncertain resource cause.

Builder evidence commit 505d94a is also checked independently. Its archive is
SHA256 `a844aec7122faa93d029cae5861c48018aca27126f465b71861a0180d4ac3be1`.
All 139 manifest entries match their retained bytes and all 136 existing original
paths; all 140 archive members are unique regular files with safe relative paths.
See `builder-packet-check.json`. The packet retains failed commands and actual
failed full-journey captures as well as the successful scoped transaction.

**Bounded verdict: accept 171169e for the scoped observer correction.** The
initial source gap was corrected and the actual Linux transaction passes with
its native output independently inspected. There is no blind A/B verdict:
the retained full journeys never reached this boundary, and the focused probe
does not recreate Windows round 2 damage conditions.

The maintained `validate.sh` run on the final code is pending the central native
lane. This review does not close the gauntlet skill's full-validation exit
requirement. The builder's maintained Python observation checks report four
passes and three Windows-only skips; I have not substituted those for the full
suite.

The biggest remaining deficiency is the failed complete Windows journey.
Linux evidence cannot prove Windows settings survival, restart or native focus
recovery. Legitimate bot damage can still kill the player between authority
acknowledgment and capture, which must fail. Run a fresh exact-source Windows
journey before promoting any complete Windows, G1 or release acceptance gate.
