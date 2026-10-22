# Letterboxed footer observation

Independent critic `/root/layout_ocr_critic` accepted candidate `3a847af` for the
bounded 1280×720 correction and found an additional actual 1280×800 false
negative. Its unchanged native image visibly contains the keyboard footer and
health. The broad crop OCR reads `TAB ROSTER’ ESC EN`, missing `MENU`. The
critic report and original TSVs are retained in `independent-review-r1/`; the
native image is now a byte-bound regression fixture. This is an additional
observer limit; the current touch-toggle workflow invokes that check only at
1280×720.

Before implementation, read-only analysis located the error: the broad crop
includes gun/world edges beneath the hint row, merging them into MENU's OCR
box. An aspect-correct strip at reference content coordinates y658–690 reads
all four required words from each declared size's original live HUD, including
the 1280×800 letterbox. No acceptance words or negative controls will be removed.

Required outcomes for this iteration:

- Classify the original live HUD at all four declared sizes as desktop, including
  the independently found 1280×800 counterexample.
- Reject each size's actual menu, roster, field menu and settings as either HUD.
- Preserve real touch rejection, erased-footer rejection, same-frame binding,
  health/eliminated requirement and all existing wall/frame fences.
- Preserve raw original bytes and analysis transforms/results. Saved images
  establish detector correctness; fresh full-size native generation remains a
  separate gate and must not be claimed from these tests.

The candidate maps the hint strip through the fixed 1280×720 content area using
the native dimensions and aspect ratio. The horizontal bounds remain the middle
half of that content; the vertical bounds are y658–690. This avoids interpreting
world geometry below the actual text as part of a glyph. Every required word,
full-frame exclusion, same-PNG binding and native timing/frame fence is unchanged.

`python3 scripts/test_rendered_layout_hud.py -v` now passes seven tests in
14.707 seconds with actual Tesseract 5.5.0. The suite covers 22 unchanged native
PNGs and 46 OCR calls. Each declared size has a real desktop positive and real
menu, roster, field-menu and settings negatives. Existing touch and erased-footer
counterexamples still fail desktop classification. The narrowest declared size
uses production's full-frame three-times scale; other full-frame images use
two-times scale, while all footer analyses use four-times scale.

The independently found 1280×800 image now reads `TAB ROSTER ESC MENU` in 0.170
seconds from `[320,698,960,730]`; full-frame OCR takes 0.383 seconds. The slowest
saved-image OCR call in this run takes 0.568 seconds. These are saved-image
measurements, not native-run timing or hardware performance acceptance. Original
PNG hashes remain unchanged. Exact raw test output is in `iteration-2-tests.txt.gz`;
all TSVs and transform/timing receipts are in `saved-image-r2/`. Compilation and
whitespace checks pass.

The earlier 3a847af native result remains bound to its own source; it does not
attest this later crop. The following exact-source run verifies this revision.

## Exact-source four-size generation and independent review

Clean commit `afe7b5454572b3f14f8b9dbdbc47c5bfa7bc8331` exported with pinned
Godot 4.7.2 and unchanged game tree `13079ab8a3de9b18252a652ed57157e0776cf394`.
Validation digest is
`2b9d7ee068e9b12e0444bed6e33db16545074eb62654d122c1519412e0813883`;
the actual exported ELF SHA-256 is
`2187c9c316ab6e45b17f64028c7345e3efab3f4ebfbffc9fbd2ebb7e09af998f`.

With the same pinned-tool environment recorded in `native-four-size-r1/evidence.json`,
the fresh export used `SIGHTBREAK_BUILDS_DIR="$PWD/builds/native-candidate-r2"`.
The native controller command was:

```sh
python3 scripts/capture_desktop_layouts.py \
  --output builds/native-layout-four-size-r1 --display-base 232 --touch-toggle
```

It requested all default sizes with the original 120-second case and 520-second
whole-flow limits. Full generation passed in 304.692 seconds; source and ELF
identities remained unchanged. All eight menu/live exits were zero and cleanup
errors were empty.

| Native size | Case wall seconds | Result |
| --- | ---: | --- |
| 960×540 | 49.220 | Passed |
| 1280×720 | 78.299 | Passed, including real touch opt-in/off |
| 1920×1080 | 113.278 | Passed |
| 1280×800 | 63.723 | Passed, native letterboxing retained |

`native-four-size-r1/` retains all 22 original capture PNGs, all 85 distinct raw
OCR-original PNGs, complete results/logs, export receipts and every raw TSV in
lossless per-size archives. The evidence manifest binds each retained artifact
to its original bytes; all 218 artifact receipts were checked during retention.
This later documentation commit does not re-attest the export as its own build.

Fresh critic `/root/gameplay_recon/layout_revision_critic` independently accepts
`afe7b54` over `3a847af` for the declared four-size observer correction and
verifies the exact-source native generation. Its verbatim report, separate
source-audit report, scripts, raw TSVs, logs and result receipts are retained in
`independent-review-r2/`. It independently ran all seven tests, checked original
pixels across all four sizes and verified source/ELF/payload hashes, all native
capture and OCR-receipt hashes, exits and all 16 two-drawn-frame fences. It also
classified all 22 fresh capture PNGs and four analysis-only erased-footer
counterexamples: all 26 probes passed using 59 actual Tesseract calls. The
previous crop still reproduces the 1280×800 MENU failure on the same raw input.
The four fresh initial HUD captures have the same bytes as the corresponding
baseline fixtures; they establish new native generation without adding new
world compositions.

No blocking correction was found within that scope. The largest remaining
coverage limit is explicit: native HUD classification inside its frame fence
runs only for the 1280×720 touch-toggle case. Other sizes have actual native
captures and independent saved-pixel checks, not four-size live classifier
execution. The 1920 case has 6.722 seconds left under its existing cap. Physical
hardware performance, human readability, external presentation comparison,
accessibility, full matches and other platforms retain separate acceptance
gates. The original failures remain retained; this pass does not erase them.
