# Competitive security review

## Implemented controls

- Authoritative simulation owns movement collision, weapon timing, ray hits, damage, ammunition, objectives and match results. Predicted movement is opt-in presentation/replay only. Input packets cannot grant extra simulation time; malformed, nonfinite, stale-epoch and unreasonable-sequence input is rejected. Packet budget applies before decompression.
- Recipient snapshots allowlist data, withhold private enemy inventory/funds/health, restrict objectives and spectator viewpoints, and filter hidden transforms against static cover and a conservative opaque smoke core. Effects have separate authorization, including unattributed quantized audible gunfire. Details and remaining inference: `STATE_PRIVACY.md`.
- Claude's raw first-hello compatibility decision is retained, strict and terminal. Gameplay RPCs and account ticket operations occur only after compatibility admission. Handshake drop timers and new peer deadlines use monotonic wall time.
- A compatible peer must join within20 seconds. One join attempt per transport; rejected peers are forcibly disconnected after500ms. Joined peers with no valid input expire after30 seconds. Tables are bounded by the ten transport slots. HTTP completions carry a peer-generation guard, and deadlines are checked at the point of admission, preventing stale completion from reviving peers.
- Account admission first inspects a ticket using a trusted-server-only read-only endpoint. It reserves a free/reclaimed slot and account claim before consuming the ticket. Consumption revalidates expiry, revocation, identity and replay protection transactionally. Duplicate/full rejections preserve the unconsumed ticket. A disconnect or timeout during an already-sent consume request can still consume it; the client must obtain a fresh ticket. This distributed operation is not falsely described as atomic with ENet admission.
- Backend economy still uses PostgreSQL transactions and existing idempotency/ownership/conservation rules. No case odds, values, earning rates or real-money features changed. Server credentials remain environment-only, excluded from game exports and snapshots.

## Evidence and classification

| Finding/control | Status |
| --- | --- |
| Hidden snapshot/private field exposure | Scoped development fix, adversarial privacy tests passed; outer translucent smoke regions intentionally remain disclosed |
| Fractional/reversed protocol admission | Claude77e0433 fixes independently verified by eight real-process hostile scenarios |
| Silent post-auth peer and ignored rejection | Fixed by server deadlines; native hostile clients dropped at~20.2s and~0.8s, all temporary state released |
| Joined client with no inputs | Fixed30-second timeout; native fixture dropped at~30.3s |
| Late HTTP response resurrecting peer | Fixed generation/deadline checks; independent real ENet delayed-bridge races pass |
| Ticket consumed on full/duplicate rejection | Fixed preflight/claims; real PostgreSQL+HTTP+Godot capacity/reclaim test passes |
| Prediction replay authority | Combat excluded, one server step per tick; independent tests pass; collision/feel gate remains unverified |
| Unicode kill-feed clipping | Pre-existing Claude PR integration blocker, still reproduced on77e0433 |

## Remaining production concerns

ENet has no encryption or cryptographic server authentication here. Its connection checks and raw protocol version are not proof of an honest client. Reconnect tokens and one-use account tickets are bearer credentials; use only fictional test accounts on trusted development LANs. Do not use production accounts or long-lived production secrets over this transport. HTTP server credentials use verified HTTPS except exact loopback development origins; redirects are refused.

Internet options need a separate transport prototype and audit: an authenticated encrypted datagram tunnel terminating before ENet, or a native authenticated encrypted transport integration with mobile lifecycle support. Evaluate handshake identity, key rotation, replay protection, MTU overhead, latency, NAT behavior and DoS before choosing. No public service or paid infrastructure has been provisioned.

Deadlines bound one process's tables; they do not defeat distributed handshake floods, many source addresses, compromised authenticated accounts, automation or aim assistance. Input activity is not proof of human participation. Visibility is conservative and modified clients can retain past positions and infer motion from legitimate sound/public events. There is no perfect anti-cheat claim.

The current all-player reward eligibility rule voids a match after a disconnect or insufficient participation; it can penalize active teammates. This is an explicit unresolved product decision, unchanged by networking work. Durable reward recovery and bounded rewind are separate milestones. No blanket8.5 security/competitive acceptance, external audit or production-release approval is claimed.
