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

Research backlog: B-27 is implemented by #15; **B-21 is genuinely unfinished**:
`EconomyUI._perform` records uncertain receipts only in RAM, after the request,
and `_retry_pending` clears the record before resending. Logout also discards it.
B-28 lists further backend work; bounded efficiency candidates are under audit.

## Independently judgeable slices

| Slice | Declared failure mode / metric | State | Source and evidence |
|---|---|---|---|
| S1 / B-21 | Process exit after a keyed transaction commits but before its response; exact receipt must survive restart and settle once | Implementing | Process-kill A/B fixture and disk/error/account-isolation checks planned |
| S2 | Prediction/reconciliation or lifecycle gap with matched impairment | Independent audit | Selection pending source-backed findings |
| S3 | Backend efficiency with preserved authority/economy | Independent audit | Selection pending measured bounded workload |

Each candidate needs an exact runtime commit, repeatable command, raw logs, matched
baseline, separate blind critic, and a recorded Sol handoff. A passing smoke test
does not activate a feature gate. Failed trials remain in the evidence record.

## Coordination and gates

- [PR16 systems handoff](https://github.com/calebaiken/sightbreak/pull/16#issuecomment-6274885599)
- [PR12 narrow transaction-hook handoff](https://github.com/calebaiken/sightbreak/pull/12#issuecomment-6274889863); comments/reviews refreshed before editing.
- Protocol 6 remains matched. Prediction defaults off; live rewind stays disabled.
- Preserve Claude UI/visual nodes and API, Gemini bot interfaces, movement delegation,
  expected-price capture, authoritative economy, and offline-training separation.
- Sessions/credentials remain memory-only. A durable receipt is not authentication.
- App-process restart durability is the first target; host power-loss durability is not established by a process-kill test.

## Next recorded actions

1. Implement persist-before-send and same-account/server exact recovery; retain unknown receipts across retry/sign-out.
2. Freeze S1 runtime, reproduce matched process-kill workloads and applicable UI/economy checks.
3. Publish candidate PR/evidence; have a separate harsh critic rank unlabelled results and identify the largest remaining gap.
4. Incorporate source-bound Sol findings and advance independent S2/S3 while review is pending.
