# V3 evidence index

**Development validation in progress; no V3 candidate is verified.**

The [live progress page](../../DEVELOPMENT_V3_PROGRESS.md) records current
dispositions. The [validation guide](../../../engineering/DEVELOPMENT_V3_VALIDATION.md)
defines reproduction, fresh-output rules and platform limits. V2's 74-group
matrix, separate twelve-condition ten-client campaign and exported-client flows
belong to reference `701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd`, not V3.

## Frozen integration and CI

| Source / receipt | Meaning |
| --- | --- |
| `7b6a71a683ec5d1ed42d7245395c640225058e20` | First tooling/source freeze. GitHub rejected its workflow before any job ran. |
| [Original rejection and lint correction](ci-attempts/workflow-rejected-7b6a71a/README.md) | Original failed run retained; checksum-verified actionlint rejects the old workflow and accepts the corrected expression context. Lint is not native validation. |
| `2a026e61cabee3c66334066d45e92eb3ec6c2641` / [run 39880125007](https://github.com/calebaiken/sightbreak/actions/runs/39880125007) | **Failed.** [Independent receipt audit](ci-attempts/run-39880125007/AUDIT.md): matrix 82/83; separate twelve-condition ten-client campaign meets its recorded gates; ten audio baseline groups pass and A5/A6/A7 are caught. Actual package inspections pass, but both exported-client flows fail. These substeps do not establish candidate acceptance. |

The frozen game otherwise retains V2 behavior, with development version metadata
`0.3.2-dev`, build 5. No Astra PR #18–#21 runtime is part of this CI source.

The **next, not yet CI-verified integration** contains qualified backend read
batching (`88bfc51`) and additive snapshot diagnostics (`456d9be`), plus reviewed
matrix/X11/offline-inspection repairs. Those changes are not attributed to the
older `2a026e6` run. The live progress page records the subsequent freeze and run.

## Independent input decisions

| Input | Published evidence / disposition |
| --- | --- |
| Bot PR #14, `48eb058…` | [Exact-head report and raw controls](ai-input-review/REPORT.md): blocked by native match/actor contract regressions. Adapter-only helper results are not working-match results. |
| Art reconciliation, `79a9591…` | [Frozen blind review and native images](graphics-input-review/REPORT.md): held. Clearer shade cloth does not offset worse normal-pickup sleeve obstruction. The old calm magazine pop belongs to V2, not the candidate. |
| Art PR #2 source binding | [Separate corrected binding](graphics-pr-binding/README.md): eleven scoped visual blobs match the real PR head. This preserves, rather than rewrites, the original invalid-token attempt; whole-game trees are not equal. |
| Backend PR #19, first round | [Post-freeze binding](backend-input-review/round1/binding/POST_FREEZE_ADDENDUM.md) retains the measured-app hash discrepancy. Historical SQL arithmetic is not proof of exact executed candidate bytes. |
| Backend PR #19 source review | [Inspection-only review](backend-input-review/source-review/original/SOURCE_REVIEW.md): no introduced runtime defect found in the scoped source. Its saved controls were not executed. Later mapped response/state and direct bind-cap/fixture-provenance assurance support narrow local integration as `88bfc51`, not general latency or production acceptance. The first-round executed-app capture is still missing. |
| Backend PR #19 mapped retention and assurance | [Mapped review and exact retained controls](backend-input-review/round2-mapped/README.md): actual responses, net-equal snapshots, direct 500-bind negative controls and imported-fixture checks support the narrow read slice. Small-workload latency regressions, eight empty tables and the missing original app capture remain explicit. |
| Input PR #20 native component | [Frozen neutral verdict, source binding and raw attempts](input-boundary-review/REPORT.md): queued retries preserve original commands; fully acknowledged replays are rejected by the candidate. This component run did not execute Match timers, UDP, actor fire or stock-client reconnect. The separate network-key binding remains a distinct review. |
| Snapshot PR #21 | [Outcome freeze and post-freeze binding](snapshot-observability-review/REPORT.md): diagnostic coverage improves while captured legacy projections tie. Accepted only as additive observability; reconciled observations are not every wire snapshot or consumption-time error. Default-off instrumentation overhead is unmeasured. |
| Receipt recovery PR #18 | Held. Normal post-commit restart examples favor recovery, but separate native controls reproduce shallow success-result validation and an unpublished staging-lock leak. Source-PR feedback is not a claim of a forged backend response or a full-client exploit. |

Further recovery, input-freshness, backend-retention and snapshot-diagnostic
reviews are separate slices. A neutral outcome verdict, a source binding, a
candidate's native test run and an integration acceptance decision are distinct
records; none substitutes for the others.

## Integration's own adversarial controls

- [Original provenance, Python-runtime and harsh-critic controls](integration-controls/README.md)
  retain wrong-commit packaging success, the installed Python 3.14 shutdown
  failure and subsequent explicit Python 3.13.15 controls.
- [Process-boundary before/after controls](process-boundary-controls/README.md)
  retain real exited-parent / late-descendant false-success reproductions and
  corrected matrix, export-watchdog, campaign and artifact-verifier behavior.
  Synthetic artifact fixtures are not game exports.
- [Source-stable serial tooling review](pre-freeze-tooling-review/README.md)
  records ten normal suites / 272 tests plus 74 optimized verifier tests, all
  actual exit 0 after a retained failed OCR-cleanup attempt. These are pure or
  synthetic controls, not native matrix groups.
- [Last bounded critic and test-only follow-up](freeze-followup/README.md)
  retain the POSIX-pathlib / Windows-mock isolation failure and corrected
  17-test result without relabeling the earlier serial run.
- [Actual failed Linux CI and raw substep evidence](ci-attempts/run-39880125007/AUDIT.md)
  retain the sole matrix-unit failure, both failed exported-client flows, campaign,
  audio and package receipts. Archive integrity is not candidate acceptance.
- [CI repair controls and independent critique](ci-repair-followup/README.md)
  retain 67 maintained tests, 26 synthetic controller controls, four protocol/layout
  checks and the critic's source-custody addendum. Actual Linux/X11 retry is required.
- [Latest source-stable retry tooling](retry-tooling-review/README.md)
- [Pre-commit source and staged-payload custody](retry-freeze/README.md): 2,443 ledger payloads, 44 unchanged Python files and seven exact upstream source bindings; read-only checks, not another test or acceptance run.
  records **280 normal tests plus 74 optimized verifier tests**, all actual exit 0,
  and four transferred backend files' AST/upstream-byte checks. It did not run
  PostgreSQL, the backend test suite or a new native matrix.

Each published packet has its own byte ledger and scope/omission notes. Exact
historical bytes and failed attempts are retained. CRLF archival data is not
silently normalized to make a source-whitespace check pass.

## Limits that remain mandatory

Exceptional Linux supervisor death can still leave detached descendants outside
recoverable ownership. That path fails closed; it is not verified cleanup.
Windows resource measurements unavailable from `/proc` remain null/unavailable.

[Actual Valve CS2 references and the unchanged rubric](CS2_REFERENCES_AND_RUBRIC.md)
inform visual judgments. Historical scores are not current scores; stills cannot
establish animation quality or device performance. Physical Android/iOS install,
sustained GPU/thermal/battery behavior, touch/gyro, human full-match/gunplay,
production/security and evidence-backed **8.5 in every applicable category**
remain unverified. Development artifacts cannot waive those gates.
