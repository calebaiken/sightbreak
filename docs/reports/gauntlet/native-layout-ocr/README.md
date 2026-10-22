# Rendered desktop HUD observation

Builder: `/root/gameplay_recon`, branch `codex/v1-layout-ocr`, based on `6a0d8d5`.
Scope: the native layout validator's rendered keyboard-HUD check. No game or
platform input code changes are planned.

## Inspected benchmark and criteria, before implementation

The real failed 1280×720 capture `keyboard-hud-check-35-ocr-original.png` visibly
contains `B BUY E OBJECTIVE TAB ROSTER ESC MENU`, health and ammunition, with no
touch buttons. The existing full-frame grayscale threshold at 145 removes much
of the small muted footer. Retained preceding TSV34 recognizes `HEALTH` while
missing `TAB`, `ROSTER` and `ESC`; attempt35 exhausts the unchanged five-second
rendered-confirmation budget. Raw PNG, original case result, TSV and source/ELF
identities are retained here. `fixtures.json` identifies each unchanged native
image and its SHA-256.

This is a rendered-observation correctness benchmark. It does not assess the
game's presentation against CS2 or certify text readability for human players.

Required outcomes:

- Recognize the actual failed desktop image from its pixels, including the
  keyboard footer and health/elimination status.
- Recognize the real touch HUD as touch and reject it as desktop. Reject the
  actual main menu, field menu, settings and roster as either active HUD mode.
- Keep a pixel check independent of persisted settings and read-only UI flags;
  preserve the two-drawn-frame fence, native controls and existing timeouts.
- Reject a desktop image whose identifying footer is absent, and reject touch
  buttons even when keyboard words appear elsewhere in the input.
- Preserve original screenshots. Record any crop/scale/threshold applied to OCR
  analysis copies and bind both full/crop analysis to the same captured frame.
- Run the real exported 1280×720 touch opt-in/off case at a clean exact-source
  candidate. A saved-image test alone cannot close native generation acceptance.

An exploratory analysis of the failed PNG's bottom-centre region, without the
hard threshold, reads all eight footer words using Tesseract in 0.188 seconds.
That investigation supports a localized OCR correction; final results and the
root's separate independent critique remain pending.

## Candidate and saved-image verification

The desktop check now analyzes the same captured PNG twice: the existing
full-frame thresholded image supplies health and overlay/touch exclusions; a
bottom-centre grayscale crop preserves muted footer strokes at four-times scale.
Both command receipts retain the original PNG hash, crop, scale and threshold.
The desktop footer requires `TAB ROSTER ESC MENU`. Four rendered `BOT` entries
reject an open roster. Touch mode still requires `FIRE RELOAD USE` from actual
full-frame pixels. No setting, UI flag or generated screenshot substitutes for
these observations.

`python3 scripts/test_rendered_layout_hud.py -v` passes six tests using actual
Tesseract 5.5.0 and the retained native PNGs. Real desktop/touch images receive
their expected classifications; main menu, field menu, settings and roster fail
both active-HUD classifications. An explicit analysis-only erased-footer copy
fails desktop recognition, and touch labels still reject desktop mode even when
desktop footer tokens are supplied as a counterexample. All original PNG byte
hashes remain unchanged.

Raw test output is in `targeted-tests.txt`; OCR TSVs and per-call timing/transform
receipts are in `saved-image-r1/`. Existing native-observation regressions pass
four Linux cases, with three Windows-only skips; all 24 build/log tests pass.
Compilation and whitespace checks pass. These are validator results only; actual
native opt-in/off execution and independent review remain pending.
