# Independent source verdict: ACCEPT, bounded observability only

Winner is exact candidate `d5277180a7705befd64d2f40a362ad566e83d91b` over
original `4854aed946d25d27482af66c332f84aa51cea8fb` for capture-guard
evidence. It records the existing guard inputs and the reached validation stage
without changing the guard outcome or native-read order. This is an identified
source comparison; no blind visual comparison or numeric quality score applies.
Fresh preregistration `314cc65e` precedes detailed code/output inspection.

The largest remaining gap is actual macOS evidence from the changed helper.
Swift compilation, ABI behavior, report emission and a valid native capture have
not been observed for this candidate. The original missing post-capture frame
and its cause remain unknown. This verdict does not release or perform a native
run, retry, input action or gate promotion.

## Exact source and preservation

Helper SHA-256 is
`6fa1ca610e84daecc988c9fa46c980fce50e10d1a5029242b2e8da0cc480b6a9`.
Replacing only its exact registered diagnostic block with the old guard recovers
every original byte, SHA-256
`6b64561032d86b60dc1276aea1a642f427b48a1b5257934e89b71afb4269f71f`.
I independently compared that fixture with the exact baseline Git blob and bound
the new helper hash. The old source-preservation fixtures and digests remain
unchanged. The two adapted preservation suites reverse only this block before
checking their original bytes; all other changes still fail. Fresh controls
reject 21 distinct unauthorized mutations plus malformed/duplicate blocks.
This is an exact new-version allowance, not a broad helper pin relaxation.

The sole runtime delta replaces one compound guard with the same two dimension
predicates followed by the same exact-owned-window read and 0.5-point bounds
comparison. Dimension mismatch still performs zero post-capture ownership reads;
dimension agreement performs exactly one. An ownership error still throws.
The original guard message, owner/PID/window/layer/visibility checks, permission
preflights, scale bounds, input prohibition, PNG/Vision tail, derived analysis,
controller retries and stage/whole budgets are unchanged. There is no new retry.
Game and workflow trees are byte-identical to the baseline.

New values have fixed shape: two configured pixel dimensions, one fixed stage
string, and four coordinates from the already validated exact-owned-window
frame. No unowned title, profile field, private text or new native query is added.
Additional synchronous report assignments do not establish equal native timing.

| Reached boundary | Recorded stage | Post-capture bounds |
| --- | --- | --- |
| Image dimensions disagree | `pixel_dimensions` | Absent; ownership read was skipped |
| Exact ownership read throws | `exact_owned_window` | Absent; no valid owned frame was returned |
| Owned frame disagrees | `bounds_agreement` | The same returned frame used by the guard |
| Both guards pass | `complete` | The same returned frame used by the guard |

`complete` belongs to `post_capture_validation_stage`; it is not whole-helper
success. PNG creation/finalization and Vision still follow, and `passed=true`
and exit 0 still occur only after the preserved success tail. Existing catch
paths retain failure. The controller treats diagnostic fields as advisory and
continues to validate core receipt identity, geometry, PNG dimensions and status.
Native source binding and these exact shapes constrain helper-generated fields;
this change adds no general validator for arbitrary diagnostic JSON.

## Independent checks

All runs used CPU affinity `[4]` and source/pure synthetic execution only.

| Evidence | Result |
| --- | --- |
| [Own maintained matrix](receipts/maintained-pure.log) | 15 commands / 139 top-level methods pass |
| [Clean exact depth-one maintained matrix](receipts/depth-one-maintained-pure.log) | Same 15 commands / 139 methods pass |
| [Fresh controls](receipts/independent-controls-final.log) | Eight methods pass |
| [Fresh controls against depth-one source](receipts/depth-one-independent-controls.log) | Same eight methods pass |
| [Original source negative](receipts/original-depth-one-new-diagnostics-negative.log) | Expected exit 1; three failures retained |
| [Exact provenance recomputation](receipts/bindings.json) | Source, fixture, original receipt, tree and checkout bindings pass |

The fresh controls use success-marked synthetic helper receipts with a complete
stage label, then challenge wrong owner/window, changed geometry, invalid scale,
image dimensions, permission/event fields, failure status and late successful
returns. Every invalid core case remains failed with one unaccepted capture,
zero focus/CGEvents and no AX observation. A valid synthetic control still
completes the existing exposure-only path and posts zero input events. These
are invented controls, not native captures or semantic observations.

Independent source interpretation checks all four stages, missing observations,
exact returned bounds, dimension short circuit and the 0.5/0.500001 boundary.
It recognizes only the exact pinned guard syntax and cannot prove Swift semantics
or native ABI. The maintained suites independently retain the original guard
outcome equivalence and original failed-receipt controller replay.

Both own depth-one checkouts have initialized indexes and materialized sparse
files, one reachable commit, `is-shallow-repository=true`, and clean status before
and after checks. They were cloned with shared objects from existing exact local
shallow clones; they do not rely on ancestor Git lookups. Their isolated indexes
and source identities are recorded in [setup receipts](receipts/depth-one-setup.log)
and [bindings](receipts/bindings.json).

## Retained failures and limits

The unchanged [original 859-byte capture receipt](receipts/original-failure-39943145541.json)
hashes to `d63129b91900c6ad5d2a99767e6d4c35dacc8ec254e54be28981a1613adb1ecf`.
It matches both the fixture and the original actual-report Git blob at `617b348b`.
That actual report covers run `39943145541`, job `120379229239`, source `4854aed9`.
Requested/reported 1024 by 684 pixels at scale 1 agree. Under that exact source,
the remaining false predicate is the post-capture bounds comparison. Actual
post bounds, destination and cause were not retained. The original run remains
failed before PNG/Vision/focus/pin/AX; the new source supplies none of those
missing observations retroactively.

The old-source negative has two missing-block failures and one mutation-premise
failure because the original lacks the new assignment. It demonstrates the new
suite rejects the old source, not that the original controller newly regressed.
The builder's [first test-only failure](receipts/retained-builder-first-diagnostics-failure.log)
remains retained: a whole-flow timeout was incorrectly expected to include an
ordinary-close success field. The frozen test handles whole-flow timeout without that field; my late-return
controls preserve timeout failure and do not demand late success.
My two read-only inspection path mistakes are retained in
[setup notes](SETUP_NOTES.md). No candidate source control failed in this review.

The actual original report and its artifacts remain the authority for old native
observations. I did not re-audit its ZIPs, reparse compiled payloads, compile Swift,
run Godot/import/export, invoke CI or dispatch anything. Native emission, full
descendant cleanup, successful AX traversal, Deploy exposure, gameplay, Intel,
physical devices and all whole release gates remain unqualified by this review.
