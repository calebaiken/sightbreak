# Astra systems V3 — live progress

Updated 2026-10-22. Systems implementation: Astra. Integration and independent QA: Sol.
Branch: `astra/systems-v3-recovery`, based on PR #16
`d2439acdd5f73df7bae5ada62ee1e3dec2cf30db`.

## Reference and reconciliation

The reference stays **701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd** (frozen V2),
including the retained [74-case matrix and impairment/PostgreSQL evidence](../reports/STABILIZATION_V2_REPORT.md).
PR #16 changes after this reference affect documentation/export verification, not game or backend code.
New comparisons run both sources on the same host; Windows timings are not compared as if they were the retained Linux campaign.

Original stack reconciled 2026-10-19; refs and recorded handoffs refreshed after the restart on 2026-10-22.
`git merge-base --is-ancestor` and `git cherry` distinguish ancestry from equivalent patches:

| PR | Current head | Reconciled state in #11 / frozen V2 / #16 |
|---|---|---|
| #3 privacy | `f60389b` | Ancestor of all three; recipient allowlist retained |
| #4 movement | `0fc8d54` | Ancestor of all three; prediction remains experimental |
| #5 lifecycle | `e8b9d8e` | Ancestor of all three; superseding #10 recovery integrated |
| #6 durable results | `99773c3` | Last two commits (`30ebfce`, `99773c3`) are patch-equivalent, not direct ancestors; fixes present |
| #7 history | `4401ff8` | Last commit patch-equivalent; diagnostic history present, live rewind disabled |
| #8 validation | `89c0e99` | Ancestor of all three; old pending claims superseded by retained V2 evidence |
| #10 reconnect | `8100d35` | Runtime integrated; sole non-ancestor commit adds account-validation documentation/evidence |
| #15 expected price | `228c382` | Ancestor of frozen V2/#16, intentionally after #11; guarded price and legacy receipt fingerprints retained |

Research backlog: B-27 is implemented by #15. **B-21 was genuinely unfinished in V2**:
`EconomyUI._perform` recorded uncertain receipts only in RAM, after the request,
and `_retry_pending` cleared the record before resending. Logout also discarded it.
PR #18 now persists before dispatch and restores the exact account/server-bound receipt.
B-28 lists further backend work; the bounded trade-read efficiency candidate is in PR19.

## Independently judgeable slices

| Slice | Declared failure mode / metric | State | Source and evidence |
|---|---|---|---|
| S1 / B-21 | Process exit around commit; exact receipt must survive restart and settle once | Source, r6 blind and r7 second-kill critics pass; PostgreSQL oracle pending | [PR #18](https://github.com/calebaiken/sightbreak/pull/18), runtime `7b6f379`; **0/27 → 27/27 recovered**; follow-up harness `e0cd1e4` adds kill after retry409, **0/9 → 9/9**; journal41/recovery12/armory749/menu51 pass; [report](../reports/CLIENT_RECOVERY_V3.md) |
| S2 | Fully acknowledged stale input batches incorrectly refresh transport liveness | Source and blind critics pass the bounded native comparison; individual queued-to-ACK transition trace pending | [PR #20](https://github.com/calebaiken/sightbreak/pull/20), runtime `f3ceaad`, tested `77f2040`, neutral evidence `0cbc3ae`; stale-window travel **1.003–1.020m → 0m**, horizontal stop315–332ms, stale peer retired32.057–32.072s vs still bound34s;16valid native pairs and11regression groups per source |
| S3 | Per-trade item/name hydration scales database statements with history size | Astra and Sol source/blind critics pass the bounded read slice with qualifications; both selected V, now disclosed as the candidate; Sol's two assurance controls pending | [PR #19](https://github.com/calebaiken/sightbreak/pull/19), runtime `4a8e9ea`, executed checkout/harness `8070436`, evidence `89215fb`; 40 trades × 20 items/side **1,643 → 8 SQL statements**; baseline 61/candidate 74 PostgreSQL checks pass; 168 received responses and 336 table snapshots retained; small-read timing regressions disclosed |
| S4 | Missing repeated-ACK observations during experimental prediction/reconciliation | Source and fresh blind critics pass the coverage improvement; per-insertion 121-snapshot bound trace pending; earlier TIE retained | [PR #21](https://github.com/calebaiken/sightbreak/pull/21), runtime `0fbce12`, campaign harness `1a941e8`, evidence `6d2b38d`; held-snapshot visibility **20/40 → 40/40**, all **1,224 reconciliations** observed; legacy outputs identical, six maintained gates pass; no gameplay-accuracy win claimed, default-off gate retained |

Each candidate needs an exact runtime commit, repeatable command, raw logs, matched
baseline, separate blind critic, and a recorded Sol handoff. A passing smoke test
does not activate a feature gate. Failed trials remain in the evidence record.

## Coordination and gates

- [PR16 systems handoff](https://github.com/calebaiken/sightbreak/pull/16#issuecomment-6274885599)
- [PR12 narrow transaction-hook handoff](https://github.com/calebaiken/sightbreak/pull/12#issuecomment-6274889863); comments/reviews refreshed before editing.
- [Sol V3 integration / QA PR #17](https://github.com/calebaiken/sightbreak/pull/17); shared harness portability belongs to Sol. Systems slices use focused separate harnesses.
- Sol handoffs refreshed through integration head `320e0ef`. Its [source-bound PR19 findings](https://github.com/calebaiken/sightbreak/pull/19#issuecomment-6275997901)
  request an executed SQL-parameter-bound negative control and actual imported-fixture
  provenance. Both are being addressed as test/harness changes against frozen runtime `4a8e9ea`.
- [Sol's second backend blind verdict](https://github.com/calebaiken/sightbreak/pull/19#issuecomment-6354432171)
  was frozen before [the verified second identity release](https://github.com/calebaiken/sightbreak/pull/19#issuecomment-6354506652).
  M is V2 `701ce2c`; V is checkout `8070436` with runtime `4a8e9ea`. The read-only fixture's
  eight empty monetary tables do not establish mutation/concurrency safety on their own.
- The [network blind verdict](https://github.com/calebaiken/sightbreak/pull/20#issuecomment-6354437453)
  distinguishes simulation-time input neutralization from wall-time peer retirement. Four
  reported live-peer structures empty after retirement; this is not universal actor-state erasure.
- The [prediction blind verdict](https://github.com/calebaiken/sightbreak/pull/21#issuecomment-6276374296)
  accepts observation coverage, not gameplay accuracy. Its cache-bound trace follow-up uses frozen harness `b4b3db0`.
- Protocol 6 remains matched. Prediction defaults off; live rewind stays disabled.
- Preserve Claude UI/visual nodes and API, Gemini bot interfaces, movement delegation,
  expected-price capture, authoritative economy, and offline-training separation.
- Sessions/credentials remain memory-only. A durable receipt is not authentication.
- App-process restart durability is the first target; host power-loss durability is not established by a process-kill test.

## Next recorded actions

1. Finish the S1 exact-source native PostgreSQL lost-response oracle.
2. Retain the S2 single-batch queued/unacknowledged-to-fully-acknowledged trace and judge it against both sources; preserve the completed native campaign and failed fixture trials.
3. Close Sol's two S3 assurance findings, archive the now-released second key and frozen verdicts, and retain the first qualified verdict.
4. Finish and independently judge S4's 121-insertion cache/anchor trace; preserve its completed coverage win and activation gates.
5. Refresh Sol's source-bound findings and keep each candidate independently reviewable. Repair and verify raw Git-blob byte preservation before evidence handoff.
