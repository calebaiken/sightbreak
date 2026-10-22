# Native layout observer timing correction

Builder worktree: `/workspace/sightbreak-layout-timeout`, branch
`codex/v1-layout-timeout`, based on `7d46d2e`.

## Inspected evidence and bounded bar

Frozen native CI [39719407304](https://github.com/calebaiken/sightbreak/actions/runs/39719407304)
ran source `0ca125dfba637868e6e8e9772ff9c40400413e32`. Original Linux layout
receipts are retained under `/workspace/reviews/native-ci-39719407304/linux-receipts/evidence/layouts`.
960×540 and 1920×1080 failed main-menu confirmation (case elapsed 16.422956 and
22.561216 seconds). 1280×720 timed out a Tesseract child after 7.020930 seconds
remaining in the eight-second settings confirmation. 1280×800 passed in
59.912499 seconds. These results remain failures/passes of that exact run.
The complete QA artifact is 36,909,293 bytes, beyond the download tool's 32 MiB
single-file limit, so those native PNGs were unavailable for independent review.
No pixel-quality conclusion follows from the OCR receipts.

The comparison bar is the unchanged `capture_desktop_layouts.py` observer,
actual Tesseract and the byte-bound native PNG fixtures in
`docs/reports/gauntlet/native-layout-ocr/fixtures.json`. Prior actual four-size
captures are also retained there; they do not substitute for the missing new CI
pixels. Measure identical analysis bytes in alternating serial trials with
inherited OpenMP behavior and child-only `OMP_THREAD_LIMIT=1`. Record child wall,
CPU, maximum observed threads, output/word hashes and raw TSVs. Coordinate the
shared CPU lane; run no OCR benchmark or native render until the account-match
builder releases it.

## Required outcomes declared before implementation

- A supported change must reduce measured observer cost over the original on
  the same saved pixels without removing any recognition requirement or negative.
- All 22 native fixtures retain their original hashes. Four-size keyboard HUDs,
  touch HUD, wrong screens, FIRE exclusion, same-frame footer binding and erased
  footer counterexamples must retain their existing classification outcomes.
- Original Tesseract PSM 11 TSV, threshold/scale, all native actions, source/ELF
  fences, two drawn frames, and wall budgets remain unchanged: per-call cap 12 s
  with the remaining confirmation cap (including the observed 7.020930 s),
  5/8 s drawn-UI confirmations, 15 s main-menu confirmation, 120 s cases and
  default 520 s aggregate. No shipping graphics change is in scope.
- Child-local resource policy must not change the parent or Godot environment.
  Preserve timeout failures and record failed OCR invocations as well as success.
- A saved-image improvement proves only saved-image observer behavior. New
  native generation remains unverified until an exact-source rerun completes
  under the original budgets and independent review inspects the original PNGs.
- Keep the full artifacts, 14-day retention, permissions and existing gates.
  Add separately downloadable per-size original-PNG archives, each with a hard
  30 MiB limit below the 32 MiB transfer cap, per-file hashes and no lossy changes.
  Oversize groups must fail rather than publish a partial archive.

The builder cannot approve either component. A fresh critic must review the
actual changes and retained measurements before root integration.
