# Astra systems V3 — live progress

Updated 2026-10-19. Systems implementation: Astra. Integration and independent QA: Sol.
Branch: `astra/systems-v3-recovery`, based on PR #16
`d2439acdd5f73df7bae5ada62ee1e3dec2cf30db`.

## Reference and reconciliation

The reference stays **701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd** (frozen V2),
including the retained [74-case matrix and impairment/PostgreSQL evidence](../reports/STABILIZATION_V2_REPORT.md).
PR #16 changes after this reference affect documentation/export verification, not game or backend code.
New comparisons run both sources on the same host; Windows timings are not compared as if they were the retained Linux campaign.

Current refs fetched 2026-10-19; `git merge-base --is-ancestor` and `git cherry` distinguish ancestry from equivalent patches:

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
| S1 / B-21 | Process exit around commit; exact receipt must survive restart and settle once | Current source critic passes; fresh blind review and PostgreSQL oracle pending | [PR #18](https://github.com/calebaiken/sightbreak/pull/18), exact runtime/harness `7b6f379`; **0/27 → 27/27 recovered**, including9 rejected retries before delayed original commits; journal41/recovery12/armory749/menu51 pass; [report](../reports/CLIENT_RECOVERY_V3.md) |
| S2 | Fully acknowledged stale input batches incorrectly refresh transport liveness | Native fixture calibration and matched evidence underway | [PR #20](https://github.com/calebaiken/sightbreak/pull/20), runtime `f3ceaad`; protocol and queued retransmission semantics preserved |
| S3 | Per-trade item/name hydration scales database statements with history size | Narrow blind performance win; actual-response/state artifact gap being closed; source review pending | [PR #19](https://github.com/calebaiken/sightbreak/pull/19), runtime `4a8e9ea`;40trades×20items/side **1,643 → 8 SQL statements**; baseline61/candidate74 PostgreSQL checks pass |
| S4 | Experimental prediction/reconciliation divergence under impairment | First matched probe ties; missing repeated-ACK observations verified; additive diagnostic candidate underway | [PR #21](https://github.com/calebaiken/sightbreak/pull/21), initial probe `d5bdd53`; runtime initially unchanged, no accuracy win claimed; default-off gate retained |

Each candidate needs an exact runtime commit, repeatable command, raw logs, matched
baseline, separate blind critic, and a recorded Sol handoff. A passing smoke test
does not activate a feature gate. Failed trials remain in the evidence record.

## Coordination and gates

- [PR16 systems handoff](https://github.com/calebaiken/sightbreak/pull/16#issuecomment-6274885599)
- [PR12 narrow transaction-hook handoff](https://github.com/calebaiken/sightbreak/pull/12#issuecomment-6274889863); comments/reviews refreshed before editing.
- [Sol V3 integration / QA PR #17](https://github.com/calebaiken/sightbreak/pull/17); shared harness portability belongs to Sol. Systems slices use focused separate harnesses.
- Protocol 6 remains matched. Prediction defaults off; live rewind stays disabled.
- Preserve Claude UI/visual nodes and API, Gemini bot interfaces, movement delegation,
  expected-price capture, authoritative economy, and offline-training separation.
- Sessions/credentials remain memory-only. A durable receipt is not authentication.
- App-process restart durability is the first target; host power-loss durability is not established by a process-kill test.

## Next recorded actions

1. Finish fresh S1 blind M/Q review and the exact-source native PostgreSQL lost-response oracle.
2. Publish S2 matched outcomes and independent critic; retain its failed fixture trials.
3. Close S3 actual-response/state evidence gaps and finish independent safety review.
4. Judge S4 additive diagnostics against a declared coverage metric; no prediction activation from diagnostic improvement.
5. Refresh Sol's source-bound findings and keep each candidate independently reviewable. Repair and verify raw Git-blob byte preservation before evidence handoff.
