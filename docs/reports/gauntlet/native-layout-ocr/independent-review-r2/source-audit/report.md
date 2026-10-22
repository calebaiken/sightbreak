# Independent source contract audit

Audited clean worktree `/workspace/sightbreak-layout-ocr` at exact HEAD `afe7b5454572b3f14f8b9dbdbc47c5bfa7bc8331`, against baseline `3a847afa0903827dfa510f9c3c343061797c6457`. Read-only audit; no graphics launched and no builder worktree files changed. Read `AGENTS.md`, the original gauntlet-loop and no-ai-slop skills (including eval), and sightbreak-gauntlet.

## Finding: native four-size generation is not four-size HUD-classifier execution

`capture_desktop_layouts.py:456` saves the initial ordinary live HUD after the read-only live-state check at lines 238–243/454. It does not call `rendered_hud_matches` there. The only native caller path to `rendered_hud` (lines 365–369) is inside `if args.touch_toggle and size == (1280, 720)` at lines 468–480. Thus even a successful four-size `--touch-toggle` invocation checks the HUD classifier only at 1280×720, on touch opt-in and keyboard restoration. Without `--touch-toggle`, it does not execute that classifier at any size. It still checks native menus, rosters, settings, geometry, progression and clean exits at the other sizes. This is an inherited coverage boundary, not a newly introduced regression.

The saved-image suite does call the classifier for every manifest fixture at all four `DEFAULT_SIZES` (test lines 86–98), including a desktop positive and menu/roster/field-menu/settings negative for each size. Its full-frame scale now matches production: three at widths below 1100, otherwise two; footer scale stays four. It therefore supplies actual multi-size classifier coverage from original native pixels, with native interaction acceptance remaining separate.

## Preserved contracts

An AST comparison of every top-level function/class between these exact commits reports only `hud_footer_region` changed in the production script. No game files changed. All nested native controls, deadlines, watchdogs, frame fences, source checks and classifier logic are byte-for-byte unchanged in that diff.

- Desktop requires all four normalized footer words `TAB`, `ROSTER`, `ESC`, `MENU` plus full-frame `HEALTH` or `ELIMINATED`, with no full-frame `FIRE` (lines 74–85). No word was dropped.
- Full-frame `FIELDSETTINGS`, `FIELDMENU`, and four or more `BOT` entries reject either HUD mode. Touch still requires full-frame `FIRE`, `RELOAD`, `USE`. Main-menu rejection is exercised by actual negative fixtures; there is no new explicit title exclusion.
- `lines(..., footer=True)` captures once to a fresh original PNG path and passes the identical path to both full-frame and footer analysis (296–309). Both OCR receipts retain `original_sha256` (287–289). Earlier native-r2 evidence has matching keyboard full/crop hash `0bac4b03b61a10e53d2d6fa578c5738adfb0b39c8bafbb20fa6e3463b8cc3f97`; those receipts use the old crop and attest baseline 3a847af, not this revision.
- The native two-drawn-frame check remains at 371–404, including reset when UI flags mismatch, integer/nonnegative frame validation, backward-frame rejection, and actual pixel inspection only after first frame + 2.
- The case deadline remains min(whole deadline, case start + case timeout), with per-operation `remaining()` checks (173–197). Defaults stay 120 seconds per case and 520 seconds whole flow, with maximum 120/600 (551–560).
- The 5-second progress stall watchdog, bounded 1200 samples, schema/speed/clock validation are unchanged (89–125).
- OCR remains min(12 seconds, remaining case time, active rendered confirmation budget) (274–286). Rendered confirmations remain 5 seconds by default, 8 for roster/settings (371, 459, 466, 476); the shared deadline spans full + crop OCR (397–402).
- Xvfb start remains 5 seconds, focus waits 20, menu 15, standard offline readiness 10, profile persistence 4, native close up to 12, and cleanup TERM/KILL waits 3 + 3 (344, 421, 429, 432, 435, 442, 445, 485, 521–527). No fence was relaxed.

## Crop and fixture integrity

The production change maps the reference strip `[320,658,960,690]` through a centered 1280×720 content rectangle using `min(width/1280,height/720)`, flooring the start and ceiling the end. This yields `[240,493,720,518]` at 960×540, `[320,658,960,690]` at 1280×720, `[480,987,1440,1035]` at 1920×1080, and `[320,698,960,730]` at 1280×800. The game project still declares a 1280×720 viewport and canvas-items stretch. Compared with the prior broad bottom crop, this removes the gun/world region below the hint row without changing required evidence.

All 22 fixture PNGs independently matched the manifest SHA-256 and declared dimensions. Every referenced original path exists; all 22 copied fixture hashes also match those original native files. The erased-footer counterexample and original-before/after hashing remain in the suite (100–107, 117–119).

Committed `native-r1` and `native-r2` runs are explicitly bound to clean baseline 3a847af and requested only 1280×720. The first failed, the unchanged-source retry passed. No committed fresh native result attests afe7b54. `ITERATION_2.md` states this limit accurately and keeps fresh native generation pending. Independent test execution/image inspection is delegated to the parent critic.

## Verdict

No weakened classifier requirement, dropped negative control, mixed-frame path, deadline relaxation, or frame-fence regression found in this revision. The concrete remaining coverage deficiency is that the native four-size capture workflow does not invoke the HUD classifier at three of its four sizes; all-size classifier correctness is currently established by saved native-image tests only. Do not describe a fresh four-size capture pass as a four-size live HUD-classifier pass.
