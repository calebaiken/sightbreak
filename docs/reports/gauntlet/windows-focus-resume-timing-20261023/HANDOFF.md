# Separate timing hypothesis handoff, unapproved combined source

Combined source freeze `691076fbe866ae798666e731c423ad4cc20fd876`, own branch
`codex/windows-focus-liveness-fence-20261023`. Fence-only correction is separately
frozen at `fa718ef`; timing preregistration is `71de706`, implementation
`34b70a0`. The final test-only followup `691076f` keeps the maintained tests free
of a dependency on historical Git objects. Historical comparison stays in the
review script, where the exact fence-only source is an explicit input.

Only the focus-stage `tap('Escape')` after 11a becomes Escape-down, `pause(.3)`,
Escape-up. It then enters the same explicit unpaused acknowledgment wait.
`timing-delta.json` verifies that reversing this one invocation replacement
makes the entire controller AST equal to the fence-only freeze. Generic taps
retain their original 0.3-second hold and one-second post-up sleep. The local
aggregate script adds the pure timing group; no CI file changes.

The original failed trace supports this scheduling hypothesis: its focus
Escape-up completes at 137.703 and resume wait begins at 138.828, and the source
contains a deliberate one-second post-up sleep. Removing that known idle sleep
does not establish why the actor died or promise survival. It changes no health,
AI, seed, scene, game, objective, economy, capture or deadline.

Eight pure timing methods execute actual extracted statements, physical
dispatch/pause/wait/freshness helpers and the existing final release loop with
declared inputs. They check the 0.3-second hold and immediate ACK start, delayed
fresh unpaused ACK, stale ACK rejection, dead-state rejection, original ten-second
ACK timeout, whole-budget capping, existing Escape release when a deadline blocks
the hold, and unchanged generic tap behavior. Seven full declared event/state
receipts are in `semantic-controls.json`. These are not native latency readings.

An initial pure harness run omitted the `fence` closure binding in its declared
namespace and raised NameError in five cases. That failure is retained in
`initial-pure-harness-failure.log`; the harness binding was corrected before the
source freeze. No production behavior was altered to resolve it.

The final combined source passes all six pure groups: 8 timing, 16 focus,
15 capture, 11 Mac menu, 7 reader and 5 OCR-token methods. This is 62 discovered,
with the original three Windows-only reader skips. The unchanged independent
77-case definitions and actual wait AST also replay with all corrected outcomes
passing; their original 49 defect assertions remain preserved. As in R2, the
old assertion that a malformed dead-state timestamp causes false acceptance
now fails as expected. Full combined raw receipts are separate from the
fence-only receipts and the original rejected source.

`source-preservation.json` confirms original named captures, literal stage
budgets, whole/transition wait helpers, generic tap, held-neutrality function,
HUD pause analysis, game tree and CI unchanged. The exact AST comparison against
the fence correction also preserves both fresh neutral samples, full inertia
settle constraint, all capture context fences, physical release ACK, fresh-W
fence and all remaining controller behavior.

No engine, import, UID, native input, OCR executable, export, CI, service, retry
or canonical mission edit occurred. This builder cannot approve the candidate.
Independent review and exact combined-source approval must precede any single
fixed-order living-input retry; no later life/round/seed search is authorized.
Actual candidate native living-input response and G1/G6/G7/G12 remain unverified.
