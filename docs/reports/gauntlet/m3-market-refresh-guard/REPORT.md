# Market final refresh guard

Source baseline: `ad6cdc20db2a2f3ac179ba3cf3bed502620b6171`.
Own branch: `codex/m3-market-refresh-guard-20261023-0322`.
Criteria committed before implementation on 2026-10-23.

The comparison bar is the fetched baseline runner, its pure guard suite and the
accepted market runtime at `882931dd`. A sibling store investigation reproduced
a source hole: login reads survive when final replay succeeds and its refresh
fails, so equality against a phase dictionary can accept stale values. The
accepted market timeline has post-response reads at rows 68 and 69 after marker
67. This change must preserve that evidence and its original source identity.

Required behavior:
1. Final success requires successful GET /me and GET /inventory observations on
   the original proxy and final_recovery phase, strictly after the third market
   response was forwarded and before final native completion.
2. Compare the native result to those selected fresh observations before any
   final SQL snapshot, observer handoff, or success status.
3. Reject absent, failed, stale, wrong-phase and wrong-origin observations.
   Capturing request phase and serializing response publication must prevent
   concurrent proxy threads from reclassifying old requests as fresh.
4. A pure full Run.execute regression must reproduce the baseline false
   acceptance with stale login values and a failed post-replay refresh. Every
   real service, subprocess, network and database entrypoint must be forbidden.
5. Pure tests must accept the exact retained market timeline and exercise
   concurrent publication ordering. Original 240-second work deadline, cleanup,
   ownership, privacy, authoritative economy and import behavior remain intact.

Scope is test tooling, pure regressions, this evidence and a narrowly scoped
stdlib-only pull-request CI workflow if the local filesystem remains unavailable.
No game, backend, production service, original raw archive or accepted report
changes. No merge. New native/runtime or whole-gate acceptance is not implied.
Independent criticism is required after the candidate is frozen.

At preregistration, execution and independent verdict were pending.

## Actual execution

All edits used connected GitHub tools because the selected local environment
was still unavailable. The branch was created from the exact baseline. Draft
[PR29](https://github.com/calebaiken/sightbreak/pull/29) targets
`codex/v1-mission-playability`; it remains unmerged.

First freeze `a421737727a331b84b11ada16f51a792eef831fe` passed
[run 39896121360](https://github.com/calebaiken/sightbreak/actions/runs/39896121360),
job `120226880722`: 36 tests in 0.126 seconds, OK, zero skips. The original
decoded job output is retained in `ci-r1-job120226880722.log`.

Independent source criticism then found a queued-response deadline edge: the
downstream timeout was computed before acquiring the publication lock. Another
response could hold that lock until the 240-second deadline expired. This was
a source finding; no actual runtime failure was claimed. Commit `52c0993f`
moves the deadline check inside the lock immediately before downstream I/O.
Commit `985a9d71` adds a deterministic lock-contention regression that expires
the deadline while the response is queued and requires no downstream send.

Corrected frozen test source `985a9d71be546723adfb38f406302537a0a3f751`
passed [run 39896279199](https://github.com/calebaiken/sightbreak/actions/runs/39896279199),
job `120227376236`: 37 tests in 0.084 seconds, OK, zero skips. Nine existing
oracle groups and seventeen existing guard groups pass alongside eleven new
refresh groups. The original decoded output is retained in
`ci-r2-job120227376236.log`. Both jobs checked out their exact head SHA and
prepared the original runner with `git show ad6cdc20...:scripts/test_postgres_receipt_recovery.py`.

The full mocked baseline execution reaches `focused_checks_passed`, final SQL
and observer with stale login values and no post-replay reads. Corrected full
execution rejects that case, missing reads, failed responses, wrong phase and
wrong proxy before final SQL or observer; it accepts a correctly fresh sequence.
Additional pure controls cover old in-flight ingress, duplicate/mismatched
observations, marker order/provenance, phase changes during upstream requests,
failed/short downstream writes and concurrent replay publication.

The retained archive is read without extraction or modification. Its exact
SHA-256 remains
`9e3eb7d7a2cb4ebdad8c94b0e0f59b25cc40b6d252074926311213630960d793`
and its report still identifies actual native source
`882931dd7024c2b200a72b2a52017dd98b95ee6a`. Its original success-only business
read schema has no invented method/status/ingress fields. An explicit legacy
audit mode accepts those original post-response reads and the native
observation; strict future schema rejects the missing provenance. The actual
runner always uses strict default mode.

The supported compare against the baseline lists only the workflow, pure test
tooling and this new report at the frozen source. No game, backend, server,
accepted raw archive or accepted market report changed. Later evidence commits
retain logs and handoff documentation only. CI emitted one checkout-action
Node 20 deprecation warning; checkout and all test steps succeeded.

## Independent verdict

Fresh critic source/pure verdict: PASS at the exact tested
`985a9d71be546723adfb38f406302537a0a3f751`. The critic independently fetched
the baseline, corrected files, original archive and both actual CI job logs.
Its separate own branch is `codex/m3-market-refresh-critic-20261023-0342`,
review evidence commit `c00f38a3fc58a7909f5f09c664b8023dfe6c2669`.
[Independent report](https://github.com/calebaiken/sightbreak/tree/c00f38a3fc58a7909f5f09c664b8023dfe6c2669/docs/reports/gauntlet/m3-market-refresh-guard/independent-critic)
retains the initial queued-deadline criticism and corrected verdict. The builder
does not approve its own work.

The filesystem environment ultimately failed provisioning:
`container_creation / container_service_failed / transport_timeout`, reported
while querying executor configuration capabilities. This component's concrete
source edits, CI execution and independent review used connected GitHub tools.
Root owns canonical resume updates on its separate
`codex/v1-resume-checkpoint-20261023-0338` branch; this component leaves
`NEXT_SESSION.md` byte-identical to its baseline. No merge occurred.

## Remaining scope

 These mocked controls do not execute
Godot, PostgreSQL, Docker or the production API, and no new native or service
qualification is claimed. Settlement predicates are mocked inside the full
orchestration counterexample; the unchanged separate oracle suite still tests
its declared synthetic economics. Full aggregate, rendered recovery/consent,
store/case, remote hosts, power-loss durability and whole G3/G7/G16 remain open.
The biggest remaining limitation is the absence of an actual fresh-schema
native market campaign. The accepted historical campaign retains its original
source and factual evidence.
