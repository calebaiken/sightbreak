# Independent R3 source verdict: ACCEPTED for the narrow correction

Frozen source `4854aed946d25d27482af66c332f84aa51cea8fb` wins against control
`d6cb78aa4b0bc5a8265d9b82a0d379b4ee386e53` within the preregistered source/API
scope. The control fails on an auxiliary AXButton whose title copy returns
NoValue with a null output. The candidate records an empty noncandidate title,
continues the complete bounded traversal and still requires one exact enabled
Deploy button with matching owned-window/native geometry. No source blocker was
found. This verdict approves no native attempt, actual macOS behavior or shipping
feature.

The largest remaining gap is actual exported-tree evidence after that first
untitled button. Run 39939989024 stopped before it could establish whether the
required Deploy semantics exist. Synthetic success cannot answer that question.

## Independent comparison and tests

[Preregistration](PREREGISTRATION.md), commit
`57c790689a3570d4aea254931d2b3099399ce6d5`, preceded my detailed source and output
inspection. I retrieved and read actual HIServices API headers before inspecting
the implementation. AXError.h distinguishes NoValue -25212 from unsupported
attribute -25205 and failed messaging -25204. AXUIElement.h documents NoValue for
CopyAttributeValue and its retained output. AXAttributeConstants.h says AXTitle
is required if the element draws a string, and its value is a CFStringRef. The
header URL, hashes and limits are in registration; this is a source/API
comparison without a blind visual claim. Builder self-reports were excluded
from acceptance evidence.

[challenge.py](challenge.py) independently constructs typed native-ABI outputs
and executes the actual adapter, its call/window/PID guards, CF conversion,
ownership cleanup, traversal and collection validator. It never constructs the
native libraries. Only the existing synthetic capture fixture supplies the
corroborating image metadata.

| Check | Independent result |
| --- | --- |
| Original control, same eight challenge methods | Two positive methods error with exact `AXTitle code=-25212`; six groups pass. Original output retained. |
| Frozen candidate, eight challenge methods | PASS in source and exact depth-one checkout. |
| Maintained controls, 14 commands / 131 top-level methods | PASS in source and exact depth-one checkout, including six byte-identical original R1 native-boundary falsifiers. |
| Original R2 independent controls, eight methods | PASS in source and exact depth-one checkout; copied original is byte-identical to `114f2224`. |
| Actual original failed receipt | Request binding passes; collection still rejects with `AX traversal did not complete`. No synthetic repair to native evidence. |

The independent cases cover all ten nonzero error codes tested, success with
null, success with a real title, contradictory error pointers, wrong CF type,
empty/whitespace titles, embedded/trailing NUL, non-BMP Unicode, required window
titles, roles and geometry attributes. Unsupported attribute remains a failure.
Sensitive/group/static-text titles are never copied. A missing Deploy title,
wrong text, disabled target, duplicate target, out-of-window geometry and foreign
PID reject with the untitled sibling present. Geometry/PID/role changes after the
title call and returns at 0.25 or 5.001 seconds reject. The full ABI tree checks
all copied/created/borrowed-reference releases, including repeated copies of the
same native element. Retained original R1/R2 cases cover cleanup after late
returns, reference limits, strict Unicode/count boundaries and deadline/window
failures. Existing trust, cap, input/privacy, controller and path controls pass.

All pure test and provenance-audit processes were pinned to CPU 4. The maintained
AX path test also replays its child suites under an aliased temporary root; the
131 count includes their two enclosing methods without double-counting children.
The exact logs distinguish expected mocked FAILED output from suite failures.

## Exact source and retained evidence

The entire executable-source delta from the control is:

| Path | Frozen SHA-256 |
| --- | --- |
| `scripts/probe_macos_ax.py` | `298bf62dbb60d324b006ab970683e6278464005b9af30917460fc8f49de8097e` |
| `scripts/test_macos_ax_untitled.py` | `10b48e29b379fab923d1d1a24bdba25ac0dbac7dc9b2b7b8a14efed31218aa3b` |

The adapter adds seven lines: four executable lines and three comments. It
accepts only `AXTitle`, error -25212, null output and a freshly rechecked AXButton
role. The title wrapper maps only that absent result to an empty string. All
other errors, success/null and error/non-null cases retain failure behavior.
The existing guarded `call` secures every non-null Copy output before post-call
timing/window checks. The new path creates no reference for a null output; its
extra role copies pass the same ownership, PID, window and original-deadline
guards. Closing the adapter releases them.

[source-provenance.json](source-provenance.json) binds the complete ten-path
source/report delta, Git blobs, SHA-256 values and unchanged trees. No existing
file except the adapter changed; there are no deletions. Game tree
`55691684d31d44f1680141954bbe530443de9d1f`, workflow, capture helper, OCR/ordinary
selectors, AX contract/controller/AppKit, timing budgets, launch flags, maintained
R1/R2 tests and tracked fixtures are byte-identical to the control. All 14 AX
report files present at the control remain identical. No action API, input post,
permission prompt, target relaxation or new text/value attribute read was added.

All 53 members of actual-review commit
`e1221ba2ab391810005f63a3e43b58bc26d06e21` were compared against its existing
isolated checkout and matched their Git bytes; sizes and SHA-256 values are in
the provenance JSON. This includes the original failure, ZIPs, job log, negative
receipts, original PNG/JSON, metadata and retained review-setup error. The original
2,083-byte AX receipt remains SHA-256
`f795b8f263668b7e4e6960969fd9f23dc57fbbf97c7b88e541999f75919c8be8`.
Its first AXButton's identity remains unknown. This source review did not reopen
or requalify native visual, binary, timing or packaging claims.

## Depth-one, remote and setup proof

Exact replay checkout:
`/workspace/reviews/mac-ax-untitled-r3-independent-exact-depth1`. It was cloned
with `--no-checkout --depth 1 --no-local`, selected from an own immutable local
ref at the frozen candidate, then sparsely initialized and explicitly checked
out. The remote was removed before tests. Audit proves shallow=true, one
reachable commit, exactly one commit object, HEAD equal to the full frozen hash,
clean status and no configured remote. Candidate parent `90f77959`, control d6,
historical c088 and both old critic commits are absent. Tests use frozen tracked
fixtures without historical Git. The corrected maintained replay and both
independent replay groups pass there with no source mutations.

Live `git ls-remote` independently advertised
`115ecbc07821815b30fdb1f82ed8d133c15495c8` on the builder's own remote branch.
Its exact delta from the frozen source is documentation only: the handoff,
evidence index, two retained depth-one logs and `docs/engineering/NEXT_SESSION.md`.
No runtime/test/workflow bytes differ. This remote handoff is distinct from the
tested frozen source.

Retained setup and review errors are explicit:

- Initial root instruction-file reads failed because the existing root checkout
  is sparse; Git reads resolved them without changing that checkout.
- [maintained-initial.log](maintained-initial.log) retains three failed commands:
  missing screen-identity fixtures, two original OCR JSON fixtures and the legacy
  boundary script. Selecting their exact frozen tracked sparse directories
  resolved setup; [maintained-corrected.log](maintained-corrected.log) passes all
  14 commands without edits or skips.
- An initial depth-one clone followed the builder's moving branch and resolved
  to documentation handoff `115ecbc0`. No tests ran or pass was claimed there.
  I retained that checkout and made the separate exact-hash clone used above.
- [source-audit-initial.log](source-audit-initial.log) retains my overly narrow
  assertion that the remote handoff changed only the report directory. The
  actual delta also includes NEXT_SESSION. Enumerating that documentation path
  corrected the review assumption; [source-audit-final.log](source-audit-final.log)
  passes without changing candidate bytes.
- [original-control.log](original-control.log) retains both independently
  reproduced original positive-case errors. The final challenge only renames
  the foreign-PID case label from `untrusted` to its precise name; case behavior
  and all assertions are unchanged. Both initial and final candidate outputs
  remain attached.

No engine, native client, Swift compile, CI, dispatch, nested agent or target
input was run. Actual ARM semantics, call timing, native CF lifetimes, gameplay,
Intel, device performance, broad accessibility and shipping qualification remain
unverified here. This critic changed only this exact report directory.
