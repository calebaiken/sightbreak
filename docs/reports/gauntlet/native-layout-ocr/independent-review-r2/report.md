# Independent letterboxed HUD OCR revision review

Candidate `afe7b5454572b3f14f8b9dbdbc47c5bfa7bc8331` wins against `3a847afa0903827dfa510f9c3c343061797c6457` for the declared rendered-observer correction. I accept the revised footer crop across the four declared saved-image sizes and independently verify the completed four-size native generation run. The previous crop still rejects the real 1280×800 HUD because it reads MENU as `EN`; the revised crop reads every required word from the same unmodified PNG and preserves the actual wrong-screen and missing-footer rejections.

This is a nonblind tooling comparison. Game pixels and the game tree are unchanged. No CS2 presentation comparison, human readability acceptance, whole-product acceptance or physical-device performance claim follows from this review.

## Independent work

Read `AGENTS.md`, the installed original `.claude/skills/gauntlet-loop/SKILL.md`, `.claude/skills/no-ai-slop/SKILL.md` and its `eval.md`, the project gauntlet, mission records, `ITERATION_2.md`, the preceding independent report, fixture manifest and tests. A separate fresh-context source auditor checked the exact diff and preserved contracts; its report and fixture-integrity results are in `source-audit/`. No builder worktree file was changed, and neither critic launched a native renderer.

I inspected the original HUD PNGs at 960×540, 1280×720, 1920×1080 and the 1280×800 counterexample. I also inspected fresh native 1280×800 HUD, roster and settings PNGs; 1280×720 touch and restored-keyboard PNGs; a fresh 960×540 menu; and a fresh 1920×1080 field menu. The 1280×800 frame visibly has 40-pixel top/bottom letterboxing, HEALTH and the complete keyboard footer. The old broad analysis includes status text, gun and world edges below the footer. The new strip retains the hint row and removes that lower region; actual analysis images and TSVs were inspected directly.

Independently ran:

```sh
PYTHONDONTWRITEBYTECODE=1 \
SIGHTBREAK_OCR_TEST_OUTPUT=/workspace/reviews/layout-ocr-revision-critic/saved-image-tests \
python3 scripts/test_rendered_layout_hud.py -v

PYTHONDONTWRITEBYTECODE=1 \
python3 /workspace/reviews/layout-ocr-revision-critic/probe_fresh_images.py

PYTHONDONTWRITEBYTECODE=1 \
python3 /workspace/reviews/layout-ocr-revision-critic/verify_receipts.py
```

The first run passed all seven tests in 14.071 seconds using actual Tesseract 5.5.0, with 46 OCR calls over the 22 byte-bound original native fixtures and the erased-footer control. Each declared size has a real HUD positive and actual menu, roster, field-menu and settings negatives. Actual touch passes touch classification and fails desktop classification even when supplied a desktop footer. Erasing the identifying footer still fails desktop classification. The slowest OCR call took 0.501 seconds. These measurements describe saved-image OCR, not live confirmation time or hardware performance.

My additional probes classified all 22 newly generated native capture PNGs, including touch opt-in and keyboard restoration. I also erased the footer on a separate analysis copy of each size's HUD; all four copies failed desktop classification. All 26 probes passed. The 59 real Tesseract calls include direct old/new crop comparisons and a repeat of the original 1280×800 counterexample; the slowest took 0.614 seconds. All original hashes were rechecked after analysis. The fresh initial live HUD PNGs have the same bytes as the corresponding retained fixtures, so these captures add native generation evidence without adding a new world composition for those four positives.

| Native size | Revised footer rectangle | Previous crop | Revised crop |
| --- | --- | --- | --- |
| 960×540 | `[240,493,720,518]` | Desktop | Desktop |
| 1280×720 | `[320,658,960,690]` | Desktop | Desktop |
| 1920×1080 | `[480,987,1440,1035]` | Desktop | Desktop |
| 1280×800 | `[320,698,960,730]` | Rejected: MENU read as `EN` | Desktop: `TAB ROSTER ESC MENU` |

## Exact-source native run

Verified `builds/native-layout-four-size-r1/results.json`, every per-case result, the export source receipt, actual exported ELF/payload bytes, all 22 capture hashes and dimensions, all 86 native OCR original-image hashes, TSV presence, process exits, logs, progress samples and drawn-frame fences. The receipt verifier retains the detailed results in `native-receipt-verification.json`.

The current clean source exactly matches the run and export receipt:

- Commit `afe7b5454572b3f14f8b9dbdbc47c5bfa7bc8331`.
- Validation digest `2b9d7ee068e9b12e0444bed6e33db16545074eb62654d122c1519412e0813883`.
- Game tree `13079ab8a3de9b18252a652ed57157e0776cf394`; no game diff from the comparison source.
- Content digest `954b0a73cff89483a9270434da7902b2d128f1b9a99c30290dfe03862c038873`.
- Actual x86-64 ELF SHA-256 `2187c9c316ab6e45b17f64028c7345e3efab3f4ebfbffc9fbd2ebb7e09af998f`.

All native logs identify Godot `4.7.2.stable.official.ed1daf0bf` and Mesa llvmpipe. The controller requested the exact four sizes with `--touch-toggle`, using the unchanged 120-second case and 520-second whole-flow defaults. It completed in 304.692 seconds. Cases took 49.220, 78.299, 113.278 and 63.723 seconds respectively. All menu/live/Xvfb exits are 0; cleanup errors are empty. All 16 drawn-frame fences advanced at least two frames. The five-second stall watchdog recorded strictly advancing normal simulation clocks.

Touch-on/off actions record focused native clicks with expected values true then false. The native touch resume advances frames 142→144; restored keyboard advances 164→167. Native keyboard full-frame and footer OCR bind to one actual original PNG SHA-256 `c35fd03bf181b1f87ada5fc2f5f14399c90c018f52b85163be6272f07b5316f5`, using full-frame threshold 145 and the four-times, unthresholded `[320,658,960,690]` footer. Parsing the retained native TSVs independently confirms touch/desktop classifications and FIRE rejection.

Only `hud_footer_region` changed among production functions. Desktop still requires all four footer identifiers and full-frame HEALTH or ELIMINATED, with FIRE excluded. Touch still requires FIRE, RELOAD and USE. FIELD MENU, FIELD SETTINGS and the actual roster rejection remain intact. Full and crop analysis share the same captured path/hash, the two-drawn-frame fence is unchanged, and no wall budget was relaxed. All 22 fixture copies also match their still-existing original native files.

## Largest remaining deficiency and follow-up

The native four-size workflow invokes the HUD classifier only at 1280×720 inside its touch-toggle path. The initial live HUD at each other size is captured after a read-only live-state check; it does not pass the new classifier inside a native frame fence. My probes establish that those freshly captured pixels classify correctly, but they cannot turn this workflow into four-size live HUD-classifier execution. This inherited coverage boundary is the largest remaining deficiency.

No blocking fix was found for the declared saved-image observer correction or four-size generation gate. Before claiming four-size live HUD confirmation, invoke the classifier behind the existing two-drawn-frame fence at every declared size, keep the current budgets, and rerun exact-source native captures. The 1920×1080 case has only 6.722 seconds of its existing 120-second allowance left, so added live work must be measured within that limit. Do not weaken the deadline to hide failure.

The retained baseline four-size keyboard-resume timeout and prior candidate settings-OCR timeout remain failures of their own runs. This pass does not erase them or prove reliability under other host loads. The reproduced previous-crop 1280×800 false negative is preserved in `fresh-image-probes/` with raw TSVs and analysis copies. No broad `validate.sh`, native run initiated by this critic, physical-device test, accessibility acceptance, full-match acceptance or external visual-quality comparison was performed.
