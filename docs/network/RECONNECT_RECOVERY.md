# Bounded reconnect recovery

Correction branch `codex/reconnect-recovery`, based on PR5 head
`e8b9d8e06bf0a2a2b8f356a7df5d85f4b6c665f8`. This is a focused dependency of the
existing PR6–9 stack; it does not replace that stack or authorize merging main.

## Reproduced cause

The untouched integration `a6b913c` recovered3/10 in the specified22-second trial
(10 processes,100ms added RTT, blackout7.8–9.3s, close8s, retry2s). Six clients
remained connecting; one terminally rejected capacity. An instrumented PR5
baseline retained all ten CONNECTED ENet peers and actor bindings after the lost
close. Eight remained at the final sample; no replacement admission occurred.
Godot4.7.2 ENet silently drops new CONNECT requests when its fixed ten slots are
occupied. Separately, the old join path treated a valid but occupied resume token
as absent and returned terminal capacity failure. Both are actual failure paths.

## Contract

- Keep ten ENet transports and ten actors. No overflow transport pool or eviction
  based on a new client's claimed account/name.
- Set ACK/ping transport timeout parameters to32/3000/5000ms and ping interval500ms
  after the first hello. ENet checks its maximum at retransmission opportunities;
  this is **not** a promise of disconnect at exactly five wall-clock seconds.
  The separate30-second accepted-gameplay-input idle rule remains unchanged.
- A valid token whose actor is still bound gets an explicit transient response,
  before any account service call. The old owner keeps sole authority until its
  transport retires. Fresh duplicate-account tickets cannot evict it.
- A recovery episode has one monotonic20-second deadline, at most five attempts,
  2–4second bounded backoff, and a five-second connecting-attempt budget.
  Duplicate callbacks cannot renew it. Explicit protocol/credential/admission
  rejections are terminal. Interrupted authentication can retry within the same
  existing episode. Deferred cleanup is bound to the retired transport object.
- Nonempty wrong/expired resume tokens never fall back to a new guest actor or
  consume a supplied fresh account ticket. Request a fresh session explicitly.
- Rotate credentials on admission. During an unconfirmed **resume**, retain at
  most one previous token per actor for20 monotonic seconds. It references the
  new reservation and cannot evict its live owner. Repeated lost welcomes cannot
  renew that alias deadline. First accepted input from the admitted peer and
  generation removes it; reset/expiry also clear it. This closes the independently
  reproduced lost-welcome-after-rotation gap without granting duplicate authority.
- No reward policy changes: ranked disconnect still invalidates eligibility under
  the existing policy. A retry does not create an account or match-result identity.

## Scope and limits

Trusted LAN ENet remains unencrypted: a stolen bearer can impersonate its holder
once the old owner has retired. This is not production Internet authentication.
The recovery window is bounded, so prolonged outages require a new session.
Initial account admission interrupted after ticket consumption but before its
first welcome still requires a fresh ticket; there is no previously delivered
resume credential to recover. No rewind activation or prediction-default change.

## Evidence and regressions

Initial corrected candidate:10/10 recovery in the exact scenario; additional
seeds7302/7303/7304 and100ms RTT+35ms jitter+2% loss+12% reordering passed. Early
0.7s retry passed. The8s delayed-retry trial restored10/10 but failed one freshness
check: the probe serialized evidence between its report timestamp and assertion,
advancing age from653ms to756ms. The failure is retained. Freshness is now latched
once at the cutoff before I/O; the750ms bound is unchanged. Fresh retest required.

Independent review tests preserve terminal reasons, strict deadlines, malformed
and expired credentials, duplicate-account ticket inspection/consumption order,
live-owner safety, stale deferred cleanup and lost welcome. Process harness records
ENet occupancy, actor bindings and accepted input acknowledgments as well as client
snapshot freshness. Final post-commit campaign and full integration matrix must be
reported separately; these initial results are not a complete quality acceptance.
