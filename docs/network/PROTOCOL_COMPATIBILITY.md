# Protocol compatibility

Never negotiate through gameplay RPCs. Preserve the corrected PR's bounded raw SceneMultiplayer authentication hello, before any gameplay RPC or ticket consumption.

| Protocol | Contract |
| --- | --- |
| Unversioned | Original main `e67f2c8`; incompatible with all versioned builds |
| 2 | Corrected Claude PR `cf9a630`; full snapshots and existing effect RPCs |
| 3 | Codex recipient state authorization, relevant/hidden roster semantics, attributed visible-shot and unattributed audible-shot events |
| 4 | Tick/epoch snapshot headers and continuous remote interpolation; exact 20 Hz authority replication |
| 5 | Compressed redundant numbered input commands, round sequence reset, owner-only movement acknowledgments/grounded state and prediction replay |
| 6 | Explicit authority-only transient resume-busy RPC; invalid resume credentials are terminal; bounded client recovery |

Any change to RPC names/order/signature, input or snapshot meaning requires a version bump. A version assertion is compatibility negotiation, not proof that a client is honest. Account authentication remains separate.

Baseline real-process matrix verified matching version-2 builds, rejection of unversioned/future clients, missing-server-hello failure, and unconsumed tickets on incompatible account admission. Protocol-3 matrix and account admission also pass in the workspace; rerun after finalizing each milestone. Use `scripts/test_protocol_compat.sh`, `scripts/test_account_network.py`, and their isolated backend fixture instructions.

Remaining baseline hardening: numeric fractional versions currently truncate, and rejection is not terminal if a peer resubmits a valid hello during the delayed drop. Neither grants an account identity. Tightening those and post-handshake peer deadlines belongs to the server-hardening milestone.

## Updated dependency / lifecycle integration

Claude77e0433 now verifies exact whole-number protocols and makes the first hello decision terminal; eight hostile real-process checks pass. The earlier strictness issues above are historical. Codex preserves those changes. Lifecycle enforcement changes no gameplay RPC schema beyond protocol5, so version5 remains the movement/lifecycle wire contract. Account servers additionally require the backend `/server/tickets/inspect` route. Preflight is read-only; backend consumption still revalidates the ticket transactionally. Missing route fails safely rather than falling back to consuming blindly.

## Reconnect correction (2026-10-14)

Protocol6 is required on both sides. A decoded mismatch remains terminal even during recovery. Transport/authentication interruption may retry only within the existing20-second recovery episode. Neither transient busy nor protocol rejection inspects or consumes an account ticket. Fresh duplicate-account/capacity rejection remains terminal and preserves the ticket. See [reconnect contract](RECONNECT_RECOVERY.md).
