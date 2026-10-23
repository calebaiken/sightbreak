# Independent R3 source critique registration

Registered before detailed candidate source, tests, builder results or actual-run
output inspection. The task briefing supplied the original failure and candidate
intent. The builder supplied its frozen hash and reported pure-suite summary;
neither is accepted as independent evidence.

Candidate: `4854aed946d25d27482af66c332f84aa51cea8fb`.
Control: `d6cb78aa4b0bc5a8265d9b82a0d379b4ee386e53`.
Own worktree: `/workspace/reviews/mac-ax-untitled-r3-fresh-source`.
Own branch: `review/mac-ax-untitled-r3-fresh-source`.
Owned output: this exact `r3/independent-source` directory only.

## Retrieved comparison

The accessible benchmark is the actual macOS 11.3 SDK HIServices public API
headers, mirrored in `phracker/MacOSX-SDKs` on GitHub. Retrieved 2026-10-23 before
source inspection. Base URL:
`https://raw.githubusercontent.com/phracker/MacOSX-SDKs/master/MacOSX11.3.sdk/System/Library/Frameworks/ApplicationServices.framework/Versions/A/Frameworks/HIServices.framework/Versions/A/Headers/`.

| Header | SHA-256 |
| --- | --- |
| AXError.h | `2e34038d1cc0c2251693223e0f911b89c0548be5731e09ab89fbf3f26ccd220a` |
| AXUIElement.h | `23c4ea4f15015ac00e2e07f369228345fa82512446b9216a47dd3d95d3df4de8` |
| AXAttributeConstants.h | `9f24baa4b5a5dc0d0b831ce9c83a56902c6c8d593176deb63b1df2feb7143e82` |

Headers remain outside the repository in
`/workspace/review-cache/mac-ax-r3-source-api`. AXError.h defines NoValue -25212
separately from AttributeUnsupported -25205. AXUIElement.h documents both for
CopyAttributeValue and annotates its returned value CF_RETURNS_RETAINED.
This is a source/API comparison, with no blind labels or native-equivalence claim.

## Criteria fixed before inspection

1. Reproduce the old no-value AXButton failure using independently constructed
   API results. The candidate must accept a valid untitled auxiliary button while
   still finding one exact Deploy button. Exact Deploy text, enabled state,
   geometry, unique target, application/window PID, trust and identity gates stay
   fail-closed.
2. Challenge the optional-title boundary: success with null, wrong CF type,
   empty/whitespace title, title errors -25205/-25212/-25204/-25202/-25211,
   unexpected output pointers on error, required title/role/children failures,
   mixed titled/untitled buttons and duplicate or disabled Deploy controls.
   Derive expected outcomes from the retrieved API and the narrow task contract.
3. Run the preserved R1/R2/R3 pure tests at CPU cap 4. Keep setup failures and
   corrected exact-fixture reruns. Verify original failures, negatives and native
   timings are retained byte-for-byte, and source changes contain no AX actions,
   input injection, permission prompt, generalized title-error swallowing or
   target-selector relaxation.
4. Independently bind the changed-source union to the frozen hash and compare
   helper/controller/workflow/product bytes with the control. Audit CF ownership
   and cleanup paths, native timing constants and no-input privacy.
5. Reproduce all maintained relevant pure suites in a separate true depth-one
   clone with initialized sparse paths. Prove one commit, absent parent/control
   history and no remote use by test execution. Restore only exact frozen tracked
   fixtures when needed; keep each failed attempt.

Source acceptance requires every criterion to pass or a documented scoped reason
why a specific test cannot execute here. A meaningful counterexample rejects
readiness until corrected. Winner, reason, largest gap and unjudged claims will
be explicit. Pure results cannot approve actual macOS API behavior, Swift/native
compilation, CI, gameplay, Intel/ARM qualification or shipping gates. No native
process, CI run, dispatch or nested agent is authorized.

## Initial setup result

Direct reads under `/workspace/sightbreak` failed because that existing checkout
has no materialized instruction files. Its HEAD and other worktrees were left
unchanged. Instructions and original installed skills were then read with
`git show` from the frozen candidate, and this own sparse worktree was created
with `--no-checkout`, sparse initialization and explicit checkout. The installed
Gauntlet and No AI Slop sources and evaluation were read before registration.
