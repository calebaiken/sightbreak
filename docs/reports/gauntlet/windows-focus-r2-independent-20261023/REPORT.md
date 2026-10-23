# Independent R2 and timing source review

| Component | Exact source | Verdict |
| --- | --- | --- |
| Corrected fence only | `fa718efcbe6aa36e53ca12474454a5dccfc5e9b9` | ACCEPT for the declared source-only diagnostic |
| Fence plus isolated Escape schedule | `691076fbe866ae798666e731c423ad4cc20fd876` | ACCEPT for the separately preregistered source experiment |

These verdicts grant no native attempt, retry, surviving/living-input acceptance
or gameplay acceptance. Actual Windows run 39907358390 remains failed at
`b2e0293`: death tick 1166 precedes release ACK 1192. The original evidence does
not establish missed input on a living actor. No engine, import, UID generation,
native input, OCR executable, export, CI or service ran in this review.

## Original rejection replay

The original critic's `0d4f7e0` probe bytes and all 77 declared case definitions
are unchanged, SHA-256
`cc2efb2fd551fb47852bef688aacb5cd92a1d83501940062c68b29d80b699248`.
`replay_original.py` loads each exact source's helper and controller AST and
executes that original probe. The old assertion
`dead_bad_counter_wall_msec_MISSING reproduces false acceptance` now fails at
both freezes because the defect is fixed. The old 49 assertions remain historical
defect reproductions; this review does not claim they pass against corrected code.

Separate corrected expectations pass for all 77 cases at each freeze, with 335
independent assertions per freeze. Missing, negative and string timestamps now
record structured loss before freshness can hide the snapshot, and no later
state is searched. Null/wrong-type nested fields and null baseline actors reject
without the former `AttributeError`. Reader scope errors and non-object JSON
retain their exact raw values, including null and strings. Boolean movement
vectors reject. Original dead release and death/life/actor/round/phase changes
cannot become successful moved states. Valid living movement still passes.
Full raw receipts for the same 19 representative cases and all 77 summaries
are retained separately for fence and timing sources.

## Additional actual-reader and timing controls

`additional_controls.py` adds 31 declared cases and 136 assertions per source.
It extracts the actual reader, focus wrappers, wait, dispatch, pause and cleanup
AST, with only file-read outcomes, UI delivery and monotonic time supplied by the
pure harness. It verifies:

- Genuine unavailable reads retain the existing publication-gap behavior. A
  valid stale BUY/other-round frame does not replace the previous valid state.
  A subsequent fresh neutral frame and living movement can complete normally.
- An available empty JSON object, null, list, boolean, number or string rejects
  at both the immediate snapshot and response boundary, retaining the exact raw
  value and stopping before a later state. An unavailable immediate pre-key read
  fails closed without dispatch or retry.
- Fresh scope, phase, round, life, health, UI and vector losses reject with
  baseline/previous-valid/rejected receipts. Subsequent mutation of the declared
  raw object cannot alter those retained values. The generic active-focus hook
  also validates timestamps before filtering.
- Both sources retain Escape-down at declared time zero and Escape-up at 0.3 s.
  Fence-only resume enters the existing ACK wait at 1.3 s; combined source enters
  it at 0.3 s. These are deterministic scheduling controls, not native latency
  measurements. Delayed/stale ACKs, death, the original ten-second ACK timeout,
  whole-budget capping and interrupted-hold cleanup remain enforced. Generic tap
  still holds 0.3 s and sleeps one second after key-up.

The fence-only source passes its five maintained pure groups: 54 methods with
three original Windows-only reader skips on Linux. The combined source passes
six groups: 62 methods with the same three skips, including all eight maintained
timing methods. Original stdout/stderr logs are retained. No aggregate engine
suite or Windows sharing test was run.

## Mutation and preregistration audit

`audit_source.py` passes 57 independent assertions. It binds clean detached
checkouts and exact source bytes, compares against original `b2e0293`, and
confirms unchanged named captures, literal stage budgets, whole/transition waits,
generic tap, physical dispatch, held-neutrality function, HUD pause analysis,
game tree and CI. Aggregate registration adds only the appropriate pure groups.

Timing preregistration `71de706847e2b696d49da8599ab20a9c987a1df3` precedes
implementation `34b70a0` and final freeze `691076f`. Reversing exactly the one
focus-resume Escape-down/0.3-second-hold/up prefix to `tap('Escape')` makes the
entire combined controller AST equal to corrected fence source `fa718ef`.
The corrected helper and focus tests are byte-identical across both freezes.
This exact comparison preserves the ACK, complete inertia check, both fresh
neutral samples, 11a/11b/11c captures and all fences, physical W/LMB release ACK,
fresh-W test, every other tap invocation and all remaining controller behavior.

The existing wait checks the deadline before calling its condition. A declared
blocking callback can therefore finish after the deadline; the original 77-case
probe preserves that observation at both freezes. This unchanged baseline
limitation is not an added timeout or an extension introduced by either component.
No native duration or source-delta cause can be inferred from the fake clock.

Only own review artifacts were created. The original rejected review and builder
failures remain intact; no canonical mission/source record was edited. The
largest remaining gap is an actual current-source, fixed-order native trial
that preserves a living actor through fresh W response and capture. G1/G6/G7/G12
and broader product gates remain open, with no runtime approval from this review.
