# Market refresh guard handoff

Draft [PR29](https://github.com/calebaiken/sightbreak/pull/29) remains open and
unmerged. Own branch: `codex/m3-market-refresh-guard-20261023-0322`.
Exact base: `ad6cdc20db2a2f3ac179ba3cf3bed502620b6171`.
Preregistration: `95e423b81012158a9c2b7f5accf4dde14cdb2884`.
Exact corrected source tested and independently reviewed:
`985a9d71be546723adfb38f406302537a0a3f751`. Subsequent changes retain docs and
raw decoded CI logs; source is unchanged.

Actual [CI run 39896279199](https://github.com/calebaiken/sightbreak/actions/runs/39896279199),
job `120227376236`: 37 tests in 0.084 seconds, OK, zero skips. First iteration
`a4217377` passed 36 tests, then independent source review exposed a queued
downstream-write deadline edge. That rejected source and full original logs are
retained. The correction checks remaining work time inside the publication lock;
its deterministic regression passes in the final run.

Independent source/pure verdict: PASS. Critic branch
`codex/m3-market-refresh-critic-20261023-0342`, evidence
`c00f38a3fc58a7909f5f09c664b8023dfe6c2669`. See the separate
[review files](https://github.com/calebaiken/sightbreak/tree/c00f38a3fc58a7909f5f09c664b8023dfe6c2669/docs/reports/gauntlet/m3-market-refresh-guard/independent-critic)
and component [REPORT.md](REPORT.md).

To reproduce on a usable checkout of the PR branch:

```sh
git show ad6cdc20db2a2f3ac179ba3cf3bed502620b6171:scripts/test_postgres_receipt_recovery.py > /tmp/sightbreak-market-refresh-baseline.py
cd scripts
SIGHTBREAK_REFRESH_BASELINE=/tmp/sightbreak-market-refresh-baseline.py python3 -B -m unittest -v test_postgres_receipt_oracle test_postgres_receipt_guards test_postgres_receipt_refresh
```

The baseline fixture executes the actual original Run.execute with runtime
boundaries mocked and falsely accepts stale matching login values. The corrected
runner rejects before final SQL or observer unless both fresh, successful GETs
belong to final_recovery/origin1 and occur between replay forwarding and native
completion. Request provenance, complete downstream writes and serialized marker
publication prevent in-flight and concurrent-read false acceptance.

The accepted market archive remains exactly
`9e3eb7d7a2cb4ebdad8c94b0e0f59b25cc40b6d252074926311213630960d793`;
its actual native source remains `882931dd7024c2b200a72b2a52017dd98b95ee6a`.
The retained-timeline test uses its explicit original success-only event schema.
Future campaigns always require the new strict schema.

The selected filesystem environment failed provisioning:
`container_creation / container_service_failed / transport_timeout`. No native
or production service ran for this increment. When an execution environment is
usable, the next component boundary is an exact-source native market campaign
with the new event schema and independent actual runtime/SQL witnesses. Preserve
original budgets, ownership checks and guard assertions. Whole mission,
G3/G7/G16, store/case, rendered recovery and remote qualification remain open.

Root owns canonical NEXT_SESSION on separate
`codex/v1-resume-checkpoint-20261023-0338`. PR29 has no net NEXT_SESSION diff
and changes no game/backend/server source or original accepted raw evidence.
