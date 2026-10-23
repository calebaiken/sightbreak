# Market qualification handoff

Branch `codex/m3-postgres-receipt-recovery` is based on root
`89393f3d1e059a3da35533e0bd84e98a098c691c` in sparse worktree
`/workspace/sightbreak-postgres-receipt-recovery`. Native-tested source is
`882931dd7024c2b200a72b2a52017dd98b95ee6a`; subsequent evidence commits do not
change its runner, oracle, tests or production source.

Ordered builder commits before the evidence handoff:

- `8e9de18`: preregister production SQL benchmark, components and criteria.
- `38d78ff`: actual native probe and selected-field SQL/pure oracle.
- `f5bea861`: owned production runner and guard controls; rejected source-only
  freeze retained, never transaction-tested.
- `f61424bd`: close independent mutation-observation / SQL-metadata gaps and
  enforce early ownership, snapshot identity, expiry and listener checks.
- `882931dd`: retain all corrected and failed prelaunch control outputs.

The fresh source review is 66760d65 in branch
`review/m3-postgres-market-receipt`; accepted runtime review is 5aa3992d, which
includes that source review and `independent-critic/RUNTIME_REVIEW.md`. Integrate both builder and independent evidence histories
without importing unrelated root/review changes. Root canonical mission files
were left untouched. No push, merge or deployment was performed.

The implementation changes only test orchestration/probes and component docs.
Production backend/server trees remain 67027b4fa17674ef067c84401af76eb1524419ac /
667e900f73c12d75f6824d4befcadeae4223050e. Actual game tree is
`d41b8d07985ff63a221e41dfabb6f90dc2eb13c6`; production game files match accepted
1f3616af. Expected maintained aggregate count changes: none. The new fixture
runner remains an explicit local campaign; no database/service is started by
importing the pure test modules or by ordinary native test discovery.

Read-only verification after integration, with no services or native engine:

```sh
python -B scripts/test_postgres_receipt_oracle.py
python -B scripts/test_postgres_receipt_guards.py
sha256sum docs/reports/gauntlet/m3-postgres-receipt-recovery/market-receipt-evidence.tar.gz
```

Expected pure totals are 9 and 17. Expected archive SHA-256 is
9e3eb7d7a2cb4ebdad8c94b0e0f59b25cc40b6d252074926311213630960d793.
The archive's runtime result is `runtime-r1/report.json`; cleanup readback is
`runtime-r1/builder-cleanup-readback.json`. Its complete 66-member hash manifest
is `runtime-manifest.json`. No rerun is needed to inspect this evidence.

`RUNTIME_PLAN.md` retains the exact command and bounded independent SQL witness
procedure used. Do not automatically repeat it: the declared single attempt
passed and cleanup is complete. Any later runtime requires root coordination.
No engine, API, proxy, PostgreSQL container/volume or campaign listener remains.

The next independently testable transaction component is store recovery: actual
`POST /store/buy`, exact original UUID plus `definition_id: key`, one original
operation, one 150-credit debit and one original minted key through restart and
repeated lost response. Preregister its own source-backed SQL oracle before
implementation/runtime. Case opening needs a separate original-input/random-roll
oracle. Neither is qualified by this market result. Actual rendered recovery
is another boundary and cannot be claimed from native method invocation.
