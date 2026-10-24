# Independent R6 source verdict: REJECT

Exact source `c8827e7d158431097a5413273b5a1e93715961b0`, sealed handoff
`abd5a57223ffe8c4481271f06884eb5fe883b96f`, analyzer SHA-256
`c53b1ced5743c7440d0530874115d474da2a70f2416c7515e098109837182be8`.

The unchanged source emitter wins this comparison: R6 marks an impossible peer
expiry as CONSISTENT and diagnostically complete. The largest remaining gap is
lifecycle clock consistency at a claimed expiry. Queue/receipt ownership improves
on rejected R5 and passes the retained adversarial models; it does not close this
whole-reader correctness gap. No actual replay, native admission or release is
approved. Root confirmed the preregistered actual-log replay was not executed.

This uses the existing independent critic, explicitly reused because new threads
were unavailable. No fresh-context or blind-review claim is made. I did not
implement the candidate. Original R5, captured prototypes, prior assessment
`239792ce` and additive held-core assessment `5c5aca24` remain unchanged. The
final exact source was tested afresh; prototype passes were not transferred.

## Reproducible false complete result

`own-causal-v3/joined_idle_expiry_with_real_clock/` is the admitted positive.
It has a live joined peer9/generation1, an observed authority tick, then the
source's expiry-before-disconnect hook, forget and a fresh rebind. Its expiry
age is 30002 and remaining join deadline is -10005.

The paired `own-causal-v3/joined_expiry_before_idle_and_before_deadline/` changes
only two fields on observation 9, reason peer_expired:

| Field | Positive | Impossible mutation |
| --- | ---: | ---: |
| input_age_msec | 30002 | 0 |
| deadline_remaining_msec | -10005 | 20000 |

Client bytes and every other authority field/row are identical. Both initialized
views return `transition_status=CONSISTENT`, `diagnostic_complete=true`, errors[].
The complete inputs and results are retained independently under `depth-causal-v3/`.

The actual necessary predicate is in
`game/scripts/network/peer_lifecycle.gd:53–61`, branches 57/59: an entry expires
when `(rejected OR not joined) AND now>=deadline`, or when joined and
`now-last_input>=IDLE_MSEC(30000)`. The mutated joined row satisfies neither
branch. An unobserved rejected flag cannot explain it because its remaining
deadline is positive. The emitter samples both fields from the same lifecycle
entry at `game/scripts/gameplay/match.gd:1312`; `_service_peers` emits the
expiry at 885–889 before disconnect/forget. A later monotonic sample cannot
turn an already elapsed threshold back into both unelapsed thresholds.

Reproduce using a fresh output path from an exact frozen source checkout:

```sh
taskset -c 4 python3 scripts/analyze_input_consumption.py \
  --client /workspace/reviews/windows-input-reader-r6-independent-20261024/docs/reports/gauntlet/windows-input-reader-r6-independent-20261024/own-causal-v3/joined_expiry_before_idle_and_before_deadline/client.txt \
  --authority /workspace/reviews/windows-input-reader-r6-independent-20261024/docs/reports/gauntlet/windows-input-reader-r6-independent-20261024/own-causal-v3/joined_expiry_before_idle_and_before_deadline/authority.txt \
  --output /tmp/r6-impossible-expiry-NEW.json
```

The CLI return expression therefore yields exit 0 for that impossible fixture. The registered complete
oracle reproducer returns nonzero because one of 28 expectations fails:

```sh
taskset -c 4 python3 <this-report>/controls/causal_cases-v3.py \
  --source <exact-c882-checkout> --output <fresh-output-directory>
```

These are synthetic pure observations, not acquired Windows output. The defect
establishes a validator false complete result; it does not identify a historical
disconnect cause. Any correction must preserve the full source expiry predicate,
including latent rejection/deadline possibilities, and keep generation/order
ownership explicit rather than adding an idle-only rule.

## Final exact-source evidence

All runs use CPU4. Both own source and the initialized depth view produce:

| Check | Own | Depth |
| --- | ---: | ---: |
| Registered queue models | 13/13 | 13/13 |
| Registered aggregate models | 5/5 | 5/5 |
| Independent generated histories | 36948/36948 | 36948/36948 |
| Complete causal/lifecycle-clock cases | 27/28 | 27/28 |
| Additional epoch/equal-time/order cases | 23/23 | 23/23 |
| Retained required source verdicts | 139/139 | 139/139 |
| Selected maintained pure methods | 224 pass, 3 inherited skips | same |
| Shell syntax checks | 13/13 | 13/13 |

The 51 fresh complete-reader cases expect 22 CONSISTENT, 25 INVALID and 4 UNKNOWN;
actual results are 23 CONSISTENT, 24 INVALID and 4 UNKNOWN. The sole mismatch is
above; UNKNOWN stays diagnostically incomplete. The fresh cases cover delayed
A headers overwritten globally by B, opaque duplicate endpoints, immutable
queued intent, no new local calls, same-peer/new generation, expiry then rebind,
foreign exposed pops, reset before/after a cached acceptance, intermediate
accepted epochs, out-of-range epochs, equal milliseconds, and ambiguous
accept/pop order. An invalid client cache remains INVALID alongside authority
UNKNOWN. Every final fresh input/result byte matches across the two views.

Here complete-reader means invoking the full analyze function, including schema
and role/link validation. The oracle witnesses establish the named stream,
emitter-selection and lifecycle-clock relationships. Remaining actor/frame
fields are synthetic schema projections; this is not a complete Godot execution
or engine frame-scheduling model.

The generated oracle independently enumerates 7568 concrete source histories and
3150 visible prefixes, then tests 5896 feasible and 31052 infeasible completions.
It groups ALL source assignments with the same visible prefix, including
immutable first receipt, hidden middle keys, duplicate staging, joint fire/reload
budgets and intermediate sorted pops. Expected feasibility is fixed before
candidate import. All 36948 raw inputs/outcomes/source witnesses are retained in
each `generated-histories/cases.jsonl.gz`; SHA-256 is
`17338d29d2f7458f222cdbcb9e8fc955ef43926925d2958c4948253f053766ea`.
The uncompressed stream is
`2acea6539a1db9a46d5ea11ce6e9f13c8dbd5a84ab8c357c68cd4756473821ce`.

These finite generated families drain small queues completely, use one peer,
two accepts and at most one local event per exposed interval. They exclude
resets, skipping and general multi-call ownership; hand cases address named
examples of those boundaries. Their closure argument does not apply to an
incomplete native capture. Receipt-flow budgets and unresolved local histories
can return UNKNOWN. The role validator stops transition analysis at UNKNOWN;
this does not establish that every later transition was consistent.

The 139 requirements preserve exact old 108 and fresh 30 bytes/outcomes plus a
separate corrected queue-state version. One old positive seq21/22 fixture is
explicitly obsolete: queue[21,22] with one pop/skipped0 cannot first consume22,
and its next ACK then regresses22→21. Its original expectation/result remains
historical; the distinct valid replacement consumes21, retains latest accepted22
and queue1. The queued-duplicate unit changes only the independently adjudicated
receive construction line to queue1; all 55 inherited methods and 100 assertion
ASTs remain unchanged. Copied 426 frozen members were independently matched to
both sealed handoff blobs and original R5 builder/critic Git blobs.

The 227 selected maintained methods exclude server-process 11 and Mac 11. They
are not a full maintained-union or API/runtime acceptance claim. No native helper,
Godot, export, CI dispatch, process inspection or Mac review was executed.

## Source and initialized depth composition

`source-both.json` independently binds the full 515-path non-document union,
all Git modes/blob identities/index entries and physical bytes in both views.
There are four changes versus rejected R5 and 511 protected paths, 517 unique
union blobs. The changes are the analyzer, two new pure test files, and the
one-line queued-duplicate fixture correction. Every old mode is preserved;
game/runtime/RPC/controller/privacy/economy/backend/workflow source is exact.
Handoff abd5 is non-document-identical to c882. This branch changes its report only.

Own worktree was created --no-checkout and explicitly read-tree initialized to
the full 12489-path index before source inspection. Its Git object database is
shared with `/workspace/sightbreak`. A separate NEW depth source at
`/workspace/reviews/windows-input-reader-r6-independent-depth-one-20261024`
has exact c882, a clean full 12489-path index, shallow=true, one reachable commit,
no remote, no file/environment object alternates and no parent object (exit128).
Its bounded local pack is 32882960 bytes, SHA-256
`ababdd0e6a72d24c4fde16584779c5c8a2a8cc2ca54723c7858b97dfad7807b5`.
It contains selected source/fixture blobs and tree/index identities, not the
unrelated full document blob tree. No full clone was made. Historical provenance
audits intentionally use the ordinary reviewer repository's older Git objects;
they are not advertised as runnable from the isolated shallow view alone.

## Retained rig and audit failures

The original 26-case v1 pair had client welcome before synthetic server binding.
It produced 12 positive rejections. Before rerun, the registered v2 correction
shifted only client Unix times +9000; every authority input byte stayed exact.
V2 matched 26/26, but its lifecycle ages/deadlines were placeholders. A subsequent
registered v3 modeled connection deadline, admitted/accepted last_input and real
idle expiry; its 28 cases expose the source defect above. Original runners,
inputs, outcomes and stderr remain tracked. Neither rig flaw is counted as a
candidate failure.

The first parity audit failed on corrected seq21 fixture object key ordering:
the frozen builder runner constructs actor.input by iterating a Python set.
Both original serialized inputs remain tracked; parsed objects are identical.
Only that versioned input has a documented semantic parity exception. The next
audit failed on pure unittest elapsed-time text; final audit compares exact
method/failure/error/skip outcomes and retains independent raw timings. All other
case input/result parity is byte exact. Both failed audits remain raw, followed
by successful `evidence-audit-v3.json`; no test expectation was weakened.

`CONNECTED_FIXTURE_ADJUDICATION.md` records a separate read-only foundation gap:
the historical declared fresh peer_connected row uses age/deadline=-1 despite
an initialized lifecycle generation. A broader lifecycle model must version its
helpers before requiring full source consistency. This review changed no old
helper/assertion or product source. Initial path/setup discovery failures are
retained in SETUP_NOTES. Original native failures and the preregistered, unrun
actual replay remain outside this source-only verdict.
