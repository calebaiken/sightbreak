# Independent bounded PNG packaging review

Reviewed `a9961a6d8566dbc7aa3f11a8900b72b60ffa0662` against `021e493` in a
separate worktree. The PNG artifact component is accepted for its declared local
packaging scope. It improves the previous workflow by retaining each Linux
native size in a separate bounded archive while leaving the complete QA artifact
and receipt artifact intact. This is a tooling comparison, so a blind visual
A/B would not answer the acceptance question.

`python3 scripts/test_package_qa_receipts.py -v` independently passes all eight
controls. The separate `recompute_packaging.py` script verifies every original
PNG against the ZIP member, per-file index, original retained native manifest and
source bytes. It checks duplicate paths/members, archive CRCs, final archive
size, archive SHA-256, complete file selection and exact deterministic rebuilds.
All 107 images pass: 15 at 960×540, 39 at 1280×720, 24 at 1920×1080 and 29 at
1280×800. Those images remain bound to original capture source `afe7b54`, not the
current CI source. Actual output is in `packaging-recomputation.json`.

The four ZIP sizes are 2,190,326, 7,107,089, 6,672,673 and 3,650,760 bytes.
The original failed OCR frames are included. The default hard limit remains
31,457,280 bytes, with both streamed payload and final ZIP overhead checked.
Overflow raises before the temporary archive can become an upload target;
source files are read without transformation or truncation. The existing
symlink rejection, fresh output requirement and deterministic unique relative
entry construction remain in use.

The workflow diff only adds a Linux packaging step and four unconditional-on-
completion uploads. Every successful size can upload even when another size
fails packaging. The four upload names bind to `github.sha`, the original full
artifacts remain, and all retention periods remain 14 days. Matrix selection,
permissions and gameplay/test commands are unchanged. Root integration must
preserve the later Windows lane commit `47b142d`; it is outside this candidate's
base and was not tested by this review.

All five new retained `39719407304` gzip JSON receipts independently reconstruct
the original downloaded receipts and their declared SHA-256 values. Their Linux
menu/settings failures remain failures of source `0ca125d`.

The largest remaining deficiency is the lack of an actual CI upload/download
trial using these new artifacts. The current `39719407304` Linux PNGs remain
unavailable because the complete archive exceeds the transfer limit. No visual
quality, new native-generation, hardware-performance or release gate passes
follow from byte-fidelity packaging. Existing filesystem behavior is a stable-
evidence packager, not an atomic defense against a concurrent malicious writer.
