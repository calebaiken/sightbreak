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

Raw test output is in `targeted-tests.txt.gz`; OCR TSVs and per-call timing/transform
receipts are in `saved-image-r1/`. Existing native-observation regressions pass
four Linux cases, with three Windows-only skips; all 24 build/log tests pass.
Compilation and whitespace checks pass. These are validator results only; actual
native opt-in/off execution and independent review remain pending.

The first evidence-staging whitespace check flagged Tesseract's empty final TSV
fields and trailing blank lines in raw unittest output. Those raw artifacts and
the large baseline result are now stored as lossless gzip files; decompressed
bytes were checked against their originals. No OCR row or failure was edited.

## Exact-source native execution

Both native attempts used clean commit
`3a847afa0903827dfa510f9c3c343061797c6457`, Godot
`4.7.2.stable.official.ed1daf0bf`, unchanged game tree
`13079ab8a3de9b18252a652ed57157e0776cf394` and exported ELF SHA-256
`2187c9c316ab6e45b17f64028c7345e3efab3f4ebfbffc9fbd2ebb7e09af998f`.
The source receipt and export commands/logs are in `native-export/`; environment,
original artifact paths and byte hashes are in `native-evidence.json`. The later
documentation commit retains these results; it does not re-attest the earlier
export as a build of that later commit.

Reproduction from this tested source, with the pinned editor/templates installed:

```sh
SIGHTBREAK_TOOLS_DIR=/workspace/tools \
SIGHTBREAK_STATE_DIR="$PWD/.local" \
SIGHTBREAK_BUILDS_DIR="$PWD/builds/native-candidate-r1" \
python3 scripts/export.py linux

SIGHTBREAK_TOOLS_DIR=/workspace/tools \
SIGHTBREAK_STATE_DIR="$PWD/.local" \
SIGHTBREAK_BUILDS_DIR="$PWD/builds/native-candidate-r1" \
XVFB_BIN=/workspace/tools/xvfb/usr/bin/Xvfb \
LIBGL_ALWAYS_SOFTWARE=1 LP_NUM_THREADS=2 \
python3 scripts/capture_desktop_layouts.py \
  --output builds/native-layout-touch-r2 --sizes 1280x720 \
  --display-base 231 --touch-toggle --case-timeout 120 --timeout 180
```

Attempt `native-r1/` failed after capturing the real touch HUD. Tesseract timed
out on the next full-frame settings image at the existing eight-second fence
(7.747 seconds remaining); the new keyboard-footer check was never reached. The
same raw settings PNG completed unchanged standalone OCR in 0.306 seconds after
the client closed. The failure and forced live-client cleanup remain recorded.
This is an unresolved transient OCR timeout; it is not counted as a passing run.

An unchanged-source retry, `native-r2/`, passed in 78.135 wall seconds. It captured
all seven requested layouts, including real touch opt-in and restored desktop
HUD. Native settings clicks persisted both values; both explicit resumes passed
the existing pixel check and two-drawn-frame fence. The restored keyboard gate
advanced from frame 162 to 164 and analyzed the full image and footer crop from
one identical PNG hash. Menu and live-client exit codes were zero, cleanup
errors were empty, and source/ELF identities remained unchanged. The five-second
keyboard/touch fences and 120-second case limit were preserved in both attempts.

Full JSON results, raw TSVs and logs are losslessly compressed in each attempt's
folder. The failing settings PNG and both passing HUD modes remain unmodified.
Only 1280×720 was rerun here. The other layout sizes, actual desktop hardware,
accessibility, full matches and other platforms retain their separate gates.
Independent critic review is pending; this builder result does not grant visual
quality or release acceptance.
