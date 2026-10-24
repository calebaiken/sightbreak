# Held 60e619 model assessment addendum

This addendum preserves 239792ce and all earlier artifacts byte for byte. The
assessed target is the explicitly UNFROZEN captured analyzer SHA-256
60e619383050839113f1e11fcd9cfdf836dec93686367f27df86cd540307db26.
No final whole-reader/source verdict or native/readiness release is granted.
Builder's later 0d5db0f85116ca1db2496a0f8726025ed2358e47/b2681a57 is a separate
target; none of these results is transferred to it. Builder subsequently froze
c8827e7d158431097a5413273b5a1e93715961b0 (analyzer c53b1ced), adding
local projection ownership caching. That target is also unassessed here.

The registered 13 queue cases and five aggregate cases all match on held60e619.
The four earlier invalid queue admissions, the multi-peer false INVALID and the
persistent two-key aggregate contradictions no longer reproduce in this captured
core. The genuinely ambiguous duplicate-owner case still returns the expected
UNKNOWN. These are isolated InputTransitions results, not whole-analyzer
`diagnostic_complete` or runtime outcomes.

## Independent generated persistent histories

GENERATED_HISTORY_PLAN was committed 114a90b2 before execution. Its oracle
independently enumerates source staging, immutable first receipt and sorted pop;
it does not import ReceiptHistory or the builder's expected oracle values. It
fixes all feasible source completions before importing the prototype.

| Registered family | Concrete source histories | Visible prefixes | Feasible completions | Infeasible completions | Matches |
| --- | ---: | ---: | ---: | ---: | ---: |
| Two receipts, unknown middle keys | 1,548 | 678 | 1,224 | 5,484 | 6,708/6,708 |
| Pop between receipts | 836 | 536 | 664 | 1,304 | 1,968/1,968 |
| Two receipts, joint fire/reload | 5,184 | 1,936 | 4,008 | 24,264 | 28,272/28,272 |
| Total | 7,568 | 3,150 | 5,896 | 31,052 | 36,948/36,948 |

There are no invalid admissions, valid rejections or UNKNOWN results in these
finite families. The raw compressed JSONL retains every projected input, expected/
actual/error, source witness for feasible cases and complete oracle completion
set for its prefix. Gzip SHA-256 is
17338d29d2f7458f222cdbcb9e8fc955ef43926925d2958c4948253f053766ea;
uncompressed JSONL SHA-256 is
2acea6539a1db9a46d5ea11ce6e9f13c8dbd5a84ab8c357c68cd4756473821ce.
The 2,265,534-byte file is generated-history-results-v3/cases.jsonl.gz.

Expected invalidity is stronger than difference from one concrete source run.
Histories with the same packet projections, queue counts and any intermediate
pop are grouped, retaining ALL feasible queued payload assignments. Each tested
completion is valid if any such source witness exists. This avoids rejecting a
legitimate alternate assignment of unreported command fields.

The finite key oracle is closed only for these fully drained small histories.
A hidden key outside the named alphabet would remain queued or appear in the
complete observed drain; there are no skips/resets or unobserved removals that
could erase it. This reasoning must not be reused for an incomplete capture.
The generated families use one peer, at most two accepted packets, queues below
backlog size and a flushing tick after each accept/pop, so each interval exposes
at most one new local call. They do not prove general multi-call coalesced
ownership, arbitrary-length circulation, reset/epoch interpretation or full
acquisition coverage. Builder's separate >500 tiny tests are not included in
these independent counts.

## Model scrutiny and remaining boundary

The revised representation preserves potential first-receipt origins, immutable
payload sums, observed pop origins and historical ACK/cardinality cutoffs. Integral
circulation imposes one unique-key assignment, while retained alternatives keep
past payload choices consistent. The generated two-receipt and intermediate-pop
families exercise that persistent relation beyond the original example fixes.
The multi-peer 13-case positive also checks separation of global progress from
local queue obligations.

The following remain explicit final-review gates rather than inferred passes:

- Multiple unexposed local calls can produce UNKNOWN; this assessment deliberately
  does not claim their complete reconstruction. Distinguish genuine unresolved
  context and bounded search from source INVALID, and preserve diagnostic scope.
- General multi-peer event ownership, generation/lifecycle boundaries, expiry
  before disconnect, stale persistent metadata and cache invariants need whole-
  analyzer tests with actual schema/lifecycle validation.
- Reset/epoch interpretation changed after this snapshot. Assess the exact new
  delta and its valid/invalid order alternatives before executing a final target.
- Full non-document path/mode/blob/working-byte composition, inherited assertion
  preservation, historical/versioned fixture provenance, supported maintained
  checks and initialized-depth disclosures remain required at final freeze.

The source-based fixture adjudications in FIXTURE_ADJUDICATION remain binding:
retain the impossible old seq21/22 positive and its later ACK regression as
historical, add a distinct feasible consume21/latest22/queue1 version, and change
only the duplicate receive construction to queue1 while preserving assertions.
No old 108/30 artifact or expectation is rewritten here.

The revised captured core wins this bounded comparison: it resolves the retained
queue/ownership/aggregate defects and matches every independently feasible or
infeasible generated completion. The largest remaining gap is whole-reader
causality across coalesced multi-peer events and generation/reset boundaries,
including the newer local projection cache.

This assessment supports the captured core within the named finite bounds. It is
not approval of newer code, whole-reader readiness, packet identity, delivery,
latency, terminal capture completeness, Godot APIs or a native run. Root and
builder received the exact results before any new readiness decision.
