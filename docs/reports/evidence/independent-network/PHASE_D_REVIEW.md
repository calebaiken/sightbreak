# Independent Phase D lifecycle review

2026-10-13. Final helper recheck: `codex/network-lifecycle-v2` at `e8b9d8e06bf0a2a2b8f356a7df5d85f4b6c665f8`. Initial reviewed integration was uncommitted over `97bb68bbae4106076209580289d493b325e0ab81`; integration was subsequently committed as `62d43c9`. Exact reviewed-source fingerprints are retained in `phased-source.sha256`, `phased-races-source.sha256`, and `phased-final-source.sha256`.

Separate Codex reviewer; tracked files were read-only. No merge or PR approval performed. This is same-model technical review, not an external security audit. Environment: Debian13.6/Linux6.18.44, official Godot4.7.2 `ed1daf0bf`, headless engine. Real ENet processes were used; no device or Internet-transport claims.

## Recommendation

Recommend development-branch acceptance after the final full regression matrix, retaining the documented limitations. No unresolved blocking defect was found in the reviewed admission/cleanup changes after the two deadline races were fixed. This is not production approval, does not override the existing Claude Unicode HUD baseline failure, and does not establish an 8.5 security/reliability score.

## Independently found and repaired

1. **Late backend completion could revive expired admission.** `admitted(peer, attempt, now)` originally checked generation/rejection but not the20s deadline. Probe: connected at100ms, tested at21100ms; expired list contained peer2, yet admission returnedtrue and removed it from the expired set by changing state tojoined. A callback processed before the periodic cleanup could thus authorize stale admission. Final current/begin/admitted checks now enforce the explicit monotonic deadline. Recheck: `current=false`, `admitted=false`, peer remains expired. Evidence: `phased-deadline.log`, `phased-deadline-recheck.log` and their external probe scripts.

2. **Late input could revive a joined idle peer.** Initially an admitted peer expired at31000ms but `allow_input` accepted it and `active` reset its timer before the periodic cleanup. Final `allow_input` rejects the expired input before decompression and `active` cannot revive it. Independent final result: expired before `[2]`, allowedfalse, expired after `[2]`. Evidence: `phased-idle-deadline.log`, `phased-idle-deadline-recheck.log`.

## Independent runtime checks

| Check | Result | Evidence |
|---|---|---|
| Final lifecycle unit suite | 16/16 pass | `phased-final-unit.log` |
| Admission deadline adversarial recheck | Expired admission remains rejected | `phased-deadline-recheck.log` |
| Idle deadline adversarial recheck | Expired peer cannot renew via input | `phased-idle-deadline-recheck.log` |
| Two real ENet clients, simultaneous same-account admissions | Two inspections, one consume, one admission; other client fails; maximum temporary account/slot claim1 | `phased-races/same-account.*.log` |
| Disconnect during delayed inspection; fresh claimant follows | Departed peer never consumes; fresh claimant admitted; late inspect ignored | `phased-races/inspect-disconnect.*.log` |
| Disconnect during delayed consumption; fresh claimant follows | Fresh claimant admitted; late old completion never resurrects departed peer | `phased-races/consume-disconnect.*.log` |
| All three race scenarios after clients close | peers, actor slots, pending joins, account claims, slot claims and lifecycle entries allzero; no logged errors | `phased-races.log` |

The three race scenarios execute the actual TacticalMatch RPC, ENet and cleanup paths with a **delayed fake SBEconomyBridge**. They are concurrency/cleanup evidence, not PostgreSQL authorization evidence. External scripts are `phased_admission_probe.gd` and `run_phased_races.py`; ports30301–30303. The fake bridge deliberately accepts fictional ticket values and never accesses real accounts.

## Code inspection conclusions

- Nonconsuming inspection is limited to the trusted server credential and exact server identity. It does not extend ticket expiry or return the ticket/session secret.
- Consumption revalidates ticket/session/player state inside the existing PostgreSQL advisory transaction lock. An earlier successful inspection is not treated as authorization to bypass that final validation.
- Account identity is checked again after consumption. Pending slot/account claims are installed before awaiting consumption, preventing simultaneous admissions from claiming the same account or actor slot.
- Generation checks plus pending-attempt identity and current ENet membership protect awaited responses. Late responses return without erasing a newer request's claims. The lifecycle generation counter is retained across match resets, which avoids an easy generation-reuse mistake.
- Disconnect and rejection release temporary claims, per-peer input state and handshake state. Cleanup is idempotent when explicit server disconnect and engine callbacks overlap.
- Input packet rate limiting runs before decompression; valid current input renews the idle timer. Idle connection handling is separate from reward eligibility/AFK policy.
- Claude's first-hello decision and strict protocol parsing remain present. Rejection timers now use monotonic time, avoiding round/lobby elapsed-clock reset problems.
- The changes preserve server-authoritative positions, damage, ammunition, objectives and currency. No economy probability/rate or teammate reward-policy change was found.

## Lead-run evidence inspected, not independently executed here

The lead engineer's logs report:

- Valid raw peer without join dropped at20.225s; joined peer without input at30.304s; ignored rejection at0.820s; server cleanup tables empty (`/workspace/reviews/lifecycle-native.log`). These intervals include probe/connection startup and should not be interpreted as exact threshold overshoot.
- Full/duplicate-account rejection preserved the supplied tickets; the same tickets subsequently admitted, with consumption/reclaim verified against PostgreSQL (`/workspace/reviews/lifecycle-capacity.log`).
- Guest rejection, incompatible-protocol rejection without ticket/slot use, authenticated identity, waiting roster, replay rejection and account reclaim passed (`/workspace/reviews/lifecycle-account.log`).

Those are supporting lead-run artifacts; this report does not relabel them as independent executions. The final complete network, protocol, backend/economy and rendering matrix remains an integration prerequisite.

## Remaining limitations

- A consumption request already in flight may commit after its peer disconnects, its reply is lost, or its admission deadline expires. Local cancellation cannot atomically undo a remote committed ticket. The old peer is not admitted; a fresh ticket is required. The consume-disconnect probe observes this explicitly (old and new consumption calls, only fresh peer admitted). Do not claim atomic backend-consume-plus-ENet-admission.
- Ten protocol-compatible hostile peers can still occupy bounded transport capacity until deadlines; repeated reconnect floods and public-service DDoS resistance remain production concerns. The lifecycle layer is not comprehensive network abuse prevention.
- A client that sends valid neutral input is still connected; AFK/reward decisions remain the existing match policy. Input liveness is not proof of human play.
- Existing reconnect bearer tokens and their relationship to logout/revocation require a production security policy. ENet traffic remains unencrypted in the trusted-LAN scope.
- The full-server/backend race behavior is covered by the lead's isolated PostgreSQL test, not the fake bridge's assertions. Database-outage/load/soak limits and physical-device networking remain unverified here.

No score is assigned to unverified quality categories. These fixes close the reproduced lifecycle races and improve bounded cleanup; they do not establish production readiness.
