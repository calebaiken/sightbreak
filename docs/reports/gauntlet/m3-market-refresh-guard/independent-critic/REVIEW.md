# Independent market final-refresh guard review

Verdict: PASS for the source and pure-regression scope at
`985a9d71be546723adfb38f406302537a0a3f751`. The candidate closes the demonstrated
runner false acceptance and preserves the accepted historical market evidence.
This is not a new PostgreSQL/API/native qualification or a whole v1 gate closure.

The critic inspected the actual GitHub source and independently fetched both
completed CI job logs. No local command, engine, service or database execution
occurred. The selected execution environment failed to start.

## Comparison and authority

- Baseline: `ad6cdc20db2a2f3ac179ba3cf3bed502620b6171`.
- Preregistered criteria: `95e423b81012158a9c2b7f5accf4dde14cdb2884`,
  `docs/reports/gauntlet/m3-market-refresh-guard/REPORT.md`.
- Initial candidate: `a421737727a331b84b11ada16f51a792eef831fe`.
- Corrected source and pure-test freeze:
  `985a9d71be546723adfb38f406302537a0a3f751`.
- Builder draft: [PR29](https://github.com/calebaiken/sightbreak/pull/29).
- Critic branch: `codex/m3-market-refresh-critic-20261023-0342`.

The critic read AGENTS.md, the original gauntlet-loop and no-ai-slop skills,
no-ai-slop/eval.md, and the project sightbreak-gauntlet skill at the baseline.
This is a source and executable-regression comparison, without a blind-pair
claim or a builder-assigned score.

## Source findings

The old final comparison uses a phase dictionary that retains successful login
reads. Those values already show the settled purchase before the final retry.
The full mocked baseline Run.execute reaches focused_checks_passed even when
there are no successful post-replay refresh observations. This demonstrates a
runner acceptance hole; it does not demonstrate a failure in the accepted
historical native run.

The corrected runner captures phase and request clocks under its RLock at
ingress. It uses that same lock for complete downstream response writes and the
forwarded marker/read publication. Event timestamps and native phase changes
also occur under the lock. An already in-flight old request retains its old
provenance; a follow-up request cannot overtake the replay-forward marker.
A failed or short downstream write produces no successful read observation.

The new strict-default oracle requires the unique third-response and final
completion markers in both retained and clock order. The replay marker must
belong to final_recovery/origin1. Exactly one /me and /inventory observation must
have that phase/origin, successful GET status, ingress after the replay marker,
and response before native completion on both clocks. It compares both selected
values to the same native observation. Run.execute calls it before final SQL,
observer release or success. Missing, failed, stale, wrong-phase, wrong-origin,
duplicate and mismatched observations fail closed.

The initial candidate computed the downstream socket timeout before waiting
for the new publication lock. A queued handler could therefore begin its write
after the work deadline using a timeout calculated earlier. The critic held
acceptance for this source finding. The corrected freeze moves remaining(10)
and settimeout inside the lock immediately before sending headers. Its new
deterministic control queues the handler, expires the deadline while publication
is blocked, and requires no timeout/header/read publication after release.
This is a corrected source finding, without an observed service-runtime failure.

The comparison changes only the oracle/runner, one existing fake connection,
the new pure tests, a read-only PR CI workflow and evidence. Existing economic,
mutation identity, wrong-account/origin, session revocation, ownership,
credential, 240-second work-deadline and separate cleanup controls remain.
No game/backend/server source or original raw archive changes appear.
The inspected modules start no engine, service or database on import.

## Actual CI output

| Frozen source | Run / job | Actual result |
| --- | --- | --- |
| a4217377 | [39896121360](https://github.com/calebaiken/sightbreak/actions/runs/39896121360) / 120226880722 | 36 tests, 0.126 s, OK, no skips |
| 985a9d71 | [39896279199](https://github.com/calebaiken/sightbreak/actions/runs/39896279199) / 120227376236 | 37 tests, 0.084 s, OK, no skips |

The independently retrieved full logs are retained alongside this report.
They show exact frozen checkouts and git show of the actual baseline runner,
followed by the original nine oracle and seventeen guard groups plus the new
refresh groups. They explicitly show the baseline full-execute false acceptance,
the candidate full-execute rejection before final SQL/observer, the valid fresh
case, the retained archive case and the corrected queued-deadline control.
All process, socket, HTTP and database boundaries in the new orchestration
fixture are replaced or forbidden. This fixture tests runner acceptance; its
mocked SQL/economic predicates are not database proof.

Both jobs pass with one checkout-action Node 20 deprecation warning. The
workflow has contents: read, does not persist checkout credentials, installs no
dependencies, and invokes only the stdlib pure suite after preparing its source
bar. No paid service, native lane or live credential action was requested.

## Historical evidence and remaining gap

The critic independently fetched and decoded the accepted compressed archive:
19,069 bytes, SHA-256
`9e3eb7d7a2cb4ebdad8c94b0e0f59b25cc40b6d252074926311213630960d793`.
The in-tool SHA-256 calculation passed the standard abc vector first.
The retained timeline actually has login reads at rows 62/63, third-response
forward at 67, successful reads at 68/69, native completion at 71, final SQL at
72 and observer readiness at 73. Native returned values equal those fresh reads.

The archive regression pins those compressed bytes and original source
`882931dd7024c2b200a72b2a52017dd98b95ee6a`. Its historical success-only schema
requires an explicit legacy switch used only by that test. Strict future
runtime calls reject the missing new provenance. Old records are neither
retrofitted nor relabeled as new strict-schema runtime evidence.

The largest remaining gap is an actual native/service run using the new schema.
No such run is accepted here. The original 882931dd market result keeps its
original factual scope; store/case recovery, remote or power-loss conditions,
rendered consent, broad aggregate/platform qualification and the v1 gates remain
open.
