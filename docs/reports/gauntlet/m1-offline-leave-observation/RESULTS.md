# Visible offline LEAVE MATCH lookup

Candidate: `4a9ee7b` → `fc4e609` → `85d6101`, based on integrated `e38ec3c`.
Criteria were committed first as [3a37b4d](CRITERIA.md). No game files changed.
The exact Windows full journey remains unverified.

## Actual failure and supporting reproduction

Windows [CI39723283770](https://github.com/calebaiken/sightbreak/actions/runs/39723283770),
frozen `dc2a198`, passes the previously corrected settings/resume transaction,
then fails `Native UI text not found: LEAVE` at driver 87.375 seconds. The player
is alive with 100 health and SMG 30/120, focused and paused. Restart and focus
recovery are not reached in this attempt.

The actual final lookup input, `ocr-current.png`, visibly shows FIELD MENU and
LEAVE MATCH. Its SHA-256 is
`e62116a4c42c7b09ca947a7eb1cb3551865c4d6f4ffecff36066f8e7d4bee635`.
The independent CI reviewer established its provenance from the official ZIP and
source ordering. Native Windows OCR exits zero, but the old controller does not
save its stdout/TSV. The exact Windows tokens remain unknown.

An unchanged production-function replay on those same pixels, using local Linux
Tesseract, reads `LEAYE MATCH`. Thus the old exact `LEAVE` lookup also fails in the
supporting replay. This is not a reconstruction of the missing Windows TSV.

## Correction

The UI observer now enlarges grayscale pixels before the existing threshold of
145. Thresholding the small native glyph first discarded detail that the local
reader needed to distinguish V from Y. The saved native screenshot is unchanged.
The same final pixels now yield the exact words `LEAVE MATCH`; no misspelling or
fuzzy match is accepted.

The final native click additionally requires one complete, unique `LEAVE MATCH`
line and a complete, unique `FIELD MENU` heading. Incomplete, reordered, misread,
ambiguous or unidentified lines fail. The original living actor, round, focus,
weapon, ammunition and time-scale guard runs before and after this OCR, with
pause required. Native input, the existing 30-second rendered return check and
main-menu capture remain in place.

The 300-second whole-flow deadline, 20-second OCR ceiling and other stage
budgets are unchanged. The repair adds no OCR invocation. The newer workflow
lanes, original-PNG packaging and layout OCR resource behavior are preserved;
one pure caption test step is added to maintained validation and desktop CI.

Raw OCR stdout is now saved before decoding, including any partial timeout
output. Each retained file is capped at 2 MiB, with length, SHA-256 and completion
metadata. Excess output fails rather than authorizing a click from a truncated
receipt. This bounds retained files; subprocess capture still uses its existing
stdout pipe. The existing QA packer selects these `.log` files.

## Saved-pixel controls

All four shared query sites are covered: VECTORLINE requisition, SETTINGS,
MOUSE and LEAVE. The comparison applies each preprocessing function under the
same new strict heading/caption predicate for LEAVE; it is not a complete replay
of the old baseline click authorization.

| Comparison | Passed | Failed |
| --- | ---: | --- |
| Baseline transform under that common predicate | 9/11 | Both actual Windows FIELD MENU images |
| Candidate transform under that common predicate | 11/11 | None |

The other cases include actual settings, gameplay and main-menu negatives, plus
explicitly altered copies with the full caption, MATCH or heading removed. The
separate original-function final-image replay establishes the old exact-LEAVE
failure. All raw TSV, transformed analysis copies, original identities and
arguments are retained. Replay used one OCR thread and the original timeout.

Five maintained pure caption tests pass, including rejection of `LEAYE MATCH`,
missing MATCH, words from separate lines and duplicate complete captions. The
native-observation Python suite passes four checks and skips three Windows-only
checks on Linux. A new full maintained validation is pending central integration.

The pixel comparison used full controller bytes from `4a9ee7b`, SHA-256
`6dd1e0273e14c41e104b2c2539aa8e5198339e3f5b6c8baab3a07988ee566c2c`.
`fc4e609` changes comments/spacing and test registration; `85d6101` adds stdout
receipts. Their `ocr_words` AST is identical:
`a7b37e36ba550b0a0fcccf75dc7a3bbca085b84069cf7f197a937382d4ea2151`.
The packet retains these source versions and the reconciliation.

## Actual Linux native slice

A clean export of **`85d6101bb049d41368cac2921c6479afe420a242`** passes the
existing settings-only driver in **61.955 seconds**, normal exit 0, empty cleanup
errors. It executes the exact production settings/LEAVE block in the first
ordinary stock live match with the stock sidearm. It injects no state and changes
no game rules or speed. llvmpipe output is correctness evidence, not hardware
performance qualification.

- Settings remain at tick 912, elapsed 15.20 and health 100 while rendered frames
  advance from 119 to 132.
- Explicit native resume is acknowledged at tick 916; the two-frame fence reaches
  tick 929, frames 136, with the same living player.
- The final OCR/click context is paused at tick 936, elapsed 15.60, health 100.
- The exact-caption native LEAVE click occurs at driver 59.712 seconds; the
  rendered return wait completes at 60.729 seconds.
- `08-return-menu.png` shows the actual SIGHTBREAK main menu and DEPLOY button.

All seven raw stdout files match their recorded byte counts and SHA-256 values;
all are complete and untruncated with exit zero. Final `ocr-stdout/007.log`
contains the exact FIELD MENU and LEAVE MATCH lines used by the click.

The driver SHA-256 is
`3172f3f76fb8a2eb806e7bea3a1aba58c5f1c910d4112136b959b57b388bef85`;
its exact extracted settings block is
`f48aa60a7aab71f61d2b91809b377b0da1432e5442842219cfa1ed03c4effc4b`.
Runtime content remains
`f8a849b90df3ff214037cace7bc32c0c7b5e184911558b424b0a6c0f798db781`.
The receipt retains the complete source, export and executed-text identities.

This probe omits purchases, natural second-round setup, settings restart and
focus recovery. It proves the changed leave transaction only. It cannot pass the
full Linux journey or substitute for native Windows input.

## Evidence and remaining gate

`evidence-r1.tar.gz` retains the actual failed Windows journey, originals, action
and observation receipts, supporting comparisons, alternative transform outputs,
unit results, clean native export metadata and complete focused native output.
Generated caches/config and export binaries are omitted. Every retained file has
a byte count and SHA-256 in the manifest. A setup syntax error before exploratory
image processing is recorded; no native failure was discarded or reclassified.

The independent critic reviewed the source, original PNGs, strict negatives and
actual native click/return receipts, and accepted the bounded correction and
Linux leave slice. Its separate review does not grant Windows/full-journey
acceptance. The builder supplies this packet and does not approve its own work.

Next required result: an exact Windows full journey, retaining the new native
TSV through settings, LEAVE, restart and living focus recovery, under all original
budgets. Central maintained validation remains a separate check.
