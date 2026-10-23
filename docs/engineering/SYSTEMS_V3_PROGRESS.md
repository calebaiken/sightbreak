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
| S1 / B-21 | Process exit around commit; exact receipt must survive restart and settle once | Source, fixture and PostgreSQL blind outcomes pass; PostgreSQL capture/API review and recovery-input absence control in progress | [PR #18](https://github.com/calebaiken/sightbreak/pull/18), runtime `7b6f379`; **0/27 → 27/27 recovered**; follow-up harness `e0cd1e4` adds kill after retry409, **0/9 → 9/9**; real PostgreSQL **0/3 → 3/3** at prices400/401/10000000, exact single settlement and unchanged second-restart state, harness `31438cbc` / evidence `49268b8`; journal41/recovery12/armory749/menu51 pass; [report](../reports/CLIENT_RECOVERY_V3.md) |
| S2 | Fully acknowledged stale input batches incorrectly refresh transport liveness | Source and blind critics pass the bounded native comparison; supplemental single-batch trace interrupted by agent-tool filter, no new result | [PR #20](https://github.com/calebaiken/sightbreak/pull/20), runtime `f3ceaad`, tested `77f2040`, neutral evidence `0cbc3ae`; stale-window travel **1.003–1.020m → 0m**, horizontal stop315–332ms, stale peer retired32.057–32.072s vs still bound34s;16valid native pairs and11regression groups per source |
| S3 | Per-trade item/name hydration scales database statements with history size | Astra and Sol source/blind critics pass the bounded read slice with qualifications; targeted assurance fixes independently pass | [PR #19](https://github.com/calebaiken/sightbreak/pull/19), runtime `4a8e9ea`, measured checkout/harness `8070436`, response/state evidence `89215fb`, assurance evidence `172c900`; 40 trades × 20 items/side **1,643 → 8 SQL statements**; baseline 61/candidate 74 PostgreSQL checks pass; 168 received responses and 336 table snapshots retained; small-read timing regressions disclosed |
| S4 | Missing repeated-ACK observations during experimental prediction/reconciliation | Source, coverage, 121-insertion boundary and capture/API critics pass; earlier TIE retained | [PR #21](https://github.com/calebaiken/sightbreak/pull/21), runtime `0fbce12`, campaign harness `1a941e8`, campaign evidence `6d2b38d`, boundary harness `b4b3db0` / evidence `d5c738d`; held-snapshot visibility **20/40 → 40/40**, all **1,224 reconciliations** observed; 121st insertion retains120, evicts1 and preserves the anchor; legacy outputs identical, six maintained gates pass; no gameplay-accuracy win claimed, default-off gate retained |

Each candidate needs an exact runtime commit, repeatable command, raw logs, matched
baseline, separate blind critic, and a recorded Sol handoff. A passing smoke test
does not activate a feature gate. Failed trials remain in the evidence record.

## Coordination and gates

- [PR16 systems handoff](https://github.com/calebaiken/sightbreak/pull/16#issuecomment-6274885599)
- [PR12 narrow transaction-hook handoff](https://github.com/calebaiken/sightbreak/pull/12#issuecomment-6274889863); comments/reviews refreshed before editing.
- [Sol V3 integration / QA PR #17](https://github.com/calebaiken/sightbreak/pull/17); shared harness portability belongs to Sol. Systems slices use focused separate harnesses.
- Sol handoffs refreshed through integration head `320e0ef`. Its [source-bound PR19 findings](https://github.com/calebaiken/sightbreak/pull/19#issuecomment-6275997901)
  are addressed by executed SQL-parameter-bound negative controls and actual imported-fixture
  identity checks against frozen runtime `4a8e9ea`. The [independent assurance review](https://github.com/calebaiken/sightbreak/pull/19#issuecomment-6354641157)
  passes the targeted controls at `172c900`: shipping maximum500; mutated batches1600/502 fail;
  matching imports accepted and substituted imports rejected. Historical path reconstruction
  remains post-hoc; the new identity gate was not rerun around a full measured benchmark.
- [Sol's second backend blind verdict](https://github.com/calebaiken/sightbreak/pull/19#issuecomment-6354432171)
  was frozen before [the verified second identity release](https://github.com/calebaiken/sightbreak/pull/19#issuecomment-6354506652).
  M is V2 `701ce2c`; V is checkout `8070436` with runtime `4a8e9ea`. The read-only fixture's
  eight empty monetary tables do not establish mutation/concurrency safety on their own.
  The exact key and Sol freeze anchors are now [archived at `866e2e1`](https://github.com/calebaiken/sightbreak/tree/866e2e1f38461fa245557c9015b6c1a1a97ad745/docs/reports/backend-trade-read-v3/identity-release-r2), with all seven archive files verified against Git blobs.
- The [network blind verdict](https://github.com/calebaiken/sightbreak/pull/20#issuecomment-6354437453)
  distinguishes simulation-time input neutralization from wall-time peer retirement. Four
  reported live-peer structures empty after retirement; this is not universal actor-state erasure.
  The [supplemental trace interruption](https://github.com/calebaiken/sightbreak/pull/20#issuecomment-6354650278)
  adds no acceptance result. Its unfinished local work remains isolated: unpublished head
  `e5712b8` and modified `game/tests/input_ack_boundary_probe.gd` in the network worktree.
- The [prediction blind verdict](https://github.com/calebaiken/sightbreak/pull/21#issuecomment-6276374296)
  accepts observation coverage, not gameplay accuracy. The [boundary PASS](https://github.com/calebaiken/sightbreak/pull/21#issuecomment-6354593942)
  was frozen before the [capture/API provenance PASS](https://github.com/calebaiken/sightbreak/pull/21#issuecomment-6354660494)
  unblinded M as V2 and T as `b4b3db0` with runtime `0fbce12`. All121 legacy rows match;
  historical machine execution remains author-run attestation.
- Protocol 6 remains matched. Prediction defaults off; live rewind stays disabled.
- Preserve Claude UI/visual nodes and API, Gemini bot interfaces, movement delegation,
  expected-price capture, authoritative economy, and offline-training separation.
- Sessions/credentials remain memory-only. A durable receipt is not authentication.
- App-process restart durability is the first target; host power-loss durability is not established by a process-kill test.

## Next recorded actions

1. Finish S1's PostgreSQL capture/API binding and the focused minimal-recovery-input control. The [blind outcome verdict](https://github.com/calebaiken/sightbreak/pull/18#issuecomment-6355013968) is frozen: 3/3 versus 0/3, with all 2,078 consistency checks passing. Original native economy36/37 and separately calibrated37/37 remain retained; the maintained test adopts the executed calibration in `5da86b28`.
2. Preserve S2's completed source/blind-passed campaign, failed fixture trials and isolated interrupted follow-up; claim no supplemental trace result.
3. S4 controller/key closure is published at `37924d1531029b7429ee9289a266a497388001b4`; outcome and capture/API-binding reviews pass and all14 archive Git-blob hashes verify. [Final handoff](https://github.com/calebaiken/sightbreak/pull/21#issuecomment-6354741011). S3's second key and frozen verdict archive are also published; original packet hashes remain fixed.
4. Refresh Sol's source-bound findings and hand off the independently judged candidates for integration. Draft status and activation gates remain in force.
