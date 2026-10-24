# R3 untitled AXButton source handoff

Candidate source: `4854aed946d25d27482af66c332f84aa51cea8fb`, own branch
`codex/m2-mac-ax-untitled-r3`, checkout `/workspace/sightbreak-mac-ax-untitled-r3`.
Registration `90f77959de153b7779bc9202de94b6ef79118c17` preceded code edits.
This is a source-review candidate. The builder grants no approval, native release
or gameplay acceptance.

## Exact change and preserved rejection

The runtime delta from `d6cb78aa4b0bc5a8265d9b82a0d379b4ee386e53` is seven
inserted lines in `scripts/probe_macos_ax.py`. Only AXTitle returning exactly
`kAXErrorNoValue (-25212)` with a NULL output and a fresh AXButton role check may
become an empty title. The existing normalization keeps it an empty noncandidate.
Traversal still reads that node's required containing window, enabled flag,
geometry and children; it does not skip an untitled node or its descendants.
Its title cannot satisfy the exact unique Deploy selection.

All other errors and required attributes stay fatal. A non-NULL error output is
still registered and released once. Original actual-call and whole-request timing,
owner/window guards and secure-role pruning run before any missing title can be
accepted. The counted UTF-8/UTF-16 conversion, malformed/control/NUL rejection,
exact words, uniqueness, enabled/frame requirements and original 0.8 OCR gameplay
threshold remain unchanged. An actual later error still leaves a partial failed
tree even if a matching title was seen earlier.

The only other change under `game`, `scripts`, `.github` or `.claude` is the new
standalone pure suite `scripts/test_macos_ax_untitled.py`. The existing R1/R2 test
files, contract, controller, AppKit adapter, workflow and original helper fixtures
are byte-identical. The game tree remains
`55691684d31d44f1680141954bbe530443de9d1f`. The new suite is included in the
declared source replay, with no workflow amendment.

The actual d6 diagnostic run `39939989024` / job `120368768573` remains FAILED.
It stopped at node 2 with `Required AX attribute unavailable: AXTitle code=-25212`.
The partial AXWindow/AXGroup/AXButton sequence does not establish the button's
identity or whether Deploy exists later. Original observation SHA-256 is
`f795b8f263668b7e4e6960969fd9f23dc57fbbf97c7b88e541999f75919c8be8` and original QA
artifact SHA-256 is `09486d7f72e8ca3290ff4a8d395447668f7a7f11bc762c5c635494f6f2208273`.
The independent actual critic owns the native verdict and original bytes.

The unchanged new control against clean exact d6 depth-one source reproduces
that error before implementation: [original-d6-no-value-falsifier.log](receipts/original-d6-no-value-falsifier.log).
Original cf4 source rejection, earlier native/OCR failures and R2 evidence remain
at their original commits/paths; no outcome is relabeled here.

## API evidence and source-only results

[API_RESEARCH.json](API_RESEARCH.json) records retrieved byte hashes and excerpts
from the Apple macOS 11.3 SDK AXError/AXUIElement headers through an immutable
mirror, plus the pinned Godot Button docs/implementation and pinned AccessKit
optional-title implementation. Apple's developer documentation host was blocked
with tunnel HTTP 403; direct official documentation retrieval remains blocked.
The headers explicitly distinguish an absent value from unsupported attributes
and messaging failure. Godot permits empty button text, and AccessKit exports an
optional title. This supports the bounded source rule without identifying the
actual untitled node or proving native success on macOS 15.

| Receipt | Observed pure result |
| --- | --- |
| [candidate-first-untitled.log](receipts/candidate-first-untitled.log) | Seven new methods pass on the first candidate. Fake C endpoints exercise the real adapter and call guards; no native libraries are constructed. |
| [pre-freeze-maintained.log](receipts/pre-freeze-maintained.log) | Retained setup failure: two unchanged legacy suites lacked tracked screen/OCR JSON fixtures in the sparse checkout. The other 12 commands passed. |
| [pre-freeze-corrected-sparse-maintained.log](receipts/pre-freeze-corrected-sparse-maintained.log) | Exact tracked fixture directories restored; all 14 commands / 131 top-level methods pass. Production bytes equal the later source freeze. |
| [depth-one-incomplete-root-setup.log](receipts/depth-one-incomplete-root-setup.log) | Initial clone replay: all suites passed, but five tracked top-level files had not materialized after index/sparse setup. This does not meet the clean-checkout gate. No deletion was committed. |
| [exact-depth-one-4854aed9-maintained.log](receipts/exact-depth-one-4854aed9-maintained.log) | Materialized the exact tracked top-level files with `git checkout-index -a`, then replayed from clean frozen source: all 14 commands / 131 top-level methods pass; shallow true, one reachable commit, empty initial/final status, CPU affinity `[4]`. |

The 131 methods are the unchanged 118 maintained Mac methods, seven new untitled
methods and the original six independent boundary controls. The legacy script is
copied byte-for-byte from R2 handoff `5cf2085529bdd0859a81e66248a974175fc5630f`;
its SHA-256 remains `e7e16c77d8529d10cb424d141aefd9d3b6300a6aaf148a2ba9558ae21b6973f6`.
The frozen helper SHA-256 is
`298bf62dbb60d324b006ab970683e6278464005b9af30917460fc8f49de8097e`; new controls
SHA-256 is `10b48e29b379fab923d1d1a24bdba25ac0dbac7dc9b2b7b8a14efed31218aa3b`.

The new controls cover other error codes, success/NULL, error/non-NULL,
non-title/window/secure-role rejection, role changes, late returns, changed
window inventory, exactly-once error-output cleanup, a nested Deploy beyond an
untitled sibling, traversal of that sibling's descendants, missing/wrong/duplicate/
disabled/outside Deploy rejection, and preserved partial failure after Deploy.
The existing original confidence, privacy, Unicode, ownership and timing controls
all pass unchanged. The pure results do not measure native AX timing or ABI.

The packaging whitespace check flags the raw clean-status lines because the
runner prints a space after the colon before an empty Git status. Those two
literal stdout lines remain unchanged. Authored source and prose pass the
whitespace check; this raw-output formatting note is not a test failure.

## Reproduction and remaining gap

The frozen depth-one checkout is `/workspace/reviews/mac-ax-untitled-r3-depth1`.
It was cloned from the local common repository with `--depth 1 --filter=blob:none
--no-checkout --single-branch --branch codex/m2-mac-ax-untitled-r3`, then detached
at exact `4854aed9`. The local server warned that filtering was unsupported;
the observed shallow boundary still has exactly one reachable commit. Initialize
the index with `git read-tree HEAD`, select sparse paths, and materialize files
with `git checkout-index -a` before checking clean status. Required sparse paths:
`scripts`, `.github`, `.claude`, `docs/engineering`, `docs/roadmap`, this `r3`
report directory, `docs/reports/gauntlet/m2-macos-screen-identity/fixtures` and
`docs/reports/gauntlet/m2-mac-derived-ocr/original-native-39912086121/macos-ordinary-input`.

From a clean exact checkout, place output outside that checkout and run:

```sh
taskset -c 4 python3 docs/reports/gauntlet/m2-mac-ax-read-only/r3/run_pure.py \
  --root "$PWD" --output /tmp/mac-ax-r3-independent-pure.log
```

Biggest remaining gap: actual native traversal and semantic Deploy exposure after
this correction are unobserved. Any later required AX attribute may still fail.
No engine/import, native API construction, Apple compile, OCR executable, CI,
service or new dispatch ran in this work. A fresh independent source critic must
review exact `4854aed9`; root owns any later separately preregistered diagnostic
release. Ordinary gameplay, native Mac qualification and the broader mission
remain incomplete.
