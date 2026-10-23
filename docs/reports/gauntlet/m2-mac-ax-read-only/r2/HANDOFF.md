# R2 source-only handoff

Exact source freeze: `d6cb78aa4b0bc5a8265d9b82a0d379b4ee386e53`, pushed on `codex/m2-mac-ax-read-only-r2`. Registration `302b9354` preceded all R2 code edits. This is a candidate for independent source review, not source approval or permission to execute native code.

The independent rejection remains attached to exact source `cf4de47f5a94e64146dc3f6402da677c41d1b012`: review `12ec93dd3ccfdaab63ab1d16facbfdb725d9c8b5`, preregistration `709264ea78f8b6a34b26566ed63b155ae85a4df0`. [The unchanged review, runnable controls and original raw failure](rejected-independent-review/REVIEW.md) are retained separately, with original Git paths and checksums in [rejected-review-index.json](rejected-review-index.json). Replaying those controls against the clean rejected checkout reproduced five failures out of six; the original NUL counterexample still records `unique_semantic_candidate=True`. Nothing in this handoff relabels that rejected source or any actual native failure.

## Correction and preserved scope

The source delta from rejected `cf4de47f` contains exactly three files under `game`, `scripts`, `.github` and `.claude`: `scripts/probe_macos_ax.py`, `scripts/macos_ax_contract.py`, and `scripts/test_macos_ax_read_only.py`.

- Actual native AX call start and return are measured. Results at or beyond the existing 0.25-second cap are rejected even if the fixed whole-observation deadline remains open. This does not promise interruption of an in-progress native call.
- Every non-null Create/Copy +1 pointer enters exception-safe ownership before post-call guards can fail, including an out-parameter written before a boundary exception. Registry and error paths release owned references once; borrowed references are retained before ownership.
- Conversion inspects the entire bounded UTF-8 buffer and checks its UTF-16 length against the original CFString. Embedded or trailing NUL, Unicode controls, malformed encoding, count disagreement and excess size reject. Valid complete non-ASCII and non-BMP titles survive without truncation or alteration. Shared traversal and validation enforce the same complete-title rule.

Controller, AppKit adapter, workflow, original runtime helpers, product/game, OCR/HUD, exact title words, privacy/own-PID/window restrictions, no-event behavior and every declared budget are unchanged. Both rejected and R2 `game` trees are `55691684d31d44f1680141954bbe530443de9d1f`. This R2 amendment does not change the diagnostic launch flag, semantic observation method, or profile-write disclosure.

## Completed pure evidence

All commands below use fake API boundaries or source checks; no native library construction, Apple compile, engine/import/UID, OCR executable, service or CI was run.

| Receipt | Source and result |
| --- | --- |
| [rejected-cf4-boundary-replay.log](receipts/rejected-cf4-boundary-replay.log) | Unchanged critic script against clean exact rejected `cf4de47f`: six methods, five failures and the retained NUL counterexample. Expected rejected result. |
| [candidate-first-boundary-replay.log](receipts/candidate-first-boundary-replay.log) | Unchanged critic script against the R2 draft after production corrections: six methods pass. Helper and contract bytes are the same production bytes subsequently frozen in `d6cb78aa`; maintained test additions followed this run. This was not a frozen-checkout replay. |
| [maintained-boundary-first.log](receipts/maintained-boundary-first.log) | Initial seven new maintained boundary groups plus existing controls: 24 methods pass. |
| [pre-freeze-maintained.log](receipts/pre-freeze-maintained.log) | Initial complete replay retained as failed evidence. The added string-ownership fixture supplied a zero-argument fake `CFStringGetLength` where the real adapter passes one argument. Four subcases and the aliased-temp child failed; other commands passed. This fixture was corrected before freeze. |
| [maintained-boundary-corrected.log](receipts/maintained-boundary-corrected.log) | Corrected boundary fixture: 25 maintained structural/source methods pass. |
| [exact-depth-one-d6cb78aa-maintained.log](receipts/exact-depth-one-d6cb78aa-maintained.log) | Clean fresh exact `d6cb78aa` depth-one sparse checkout: all 12 maintained commands pass, 118 methods total, including aliased-temp children, original falsifiers and source-preservation checks. Shallow `true`, one reachable commit, final Git status empty. |

The fresh depth-one clone was created from the local common repository using `git clone --depth 1 --filter=blob:none --no-checkout --single-branch --branch codex/m2-mac-ax-read-only-r2 --upload-pack='git -c uploadpack.allowFilter=true upload-pack' file:///workspace/sightbreak /workspace/reviews/mac-ax-read-only-r2-depth1-d6cb78aa`, followed by its own sparse checkout and detached exact source checkout. The raw maintained receipt records the exact HEAD, one reachable commit, every command/exit and final clean status. No historical commit availability was required by the maintained checks.

All 12 commands completed before root reserved the CPU lane for the separate touch comparison. Additional replays are now paused. An additional unchanged-critic replay against the exact frozen checkout has **not** been run; the independent reviewer can reproduce it using the retained unmodified script and source `d6cb78aa` once the lane is released. The six-method candidate result above must not be represented as that missing frozen-checkout replay.

Actual exported AX exposure, TCC, native ABI and string behavior, per-call timing/interruptibility, geometry agreement and gameplay remain unobserved. Original `.8` OCR rejection and failed actual ARM iterations remain failures. No Mac native or CI release is requested or implied; root and the independent critic own the next review and execution decision.
