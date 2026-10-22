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

Fresh independent review of this revision and native generation with this new
crop remain pending. The earlier 3a847af native result remains bound to its own
source; it does not attest this later crop. Full four-size workflow acceptance,
physical hardware and visual/readability quality remain separate gates.
