# Independent reconnect correction review

## Scope and provenance

- Correction branch: `codex/reconnect-recovery`.
- Reviewed runtime commit: `6c03dc8be897730251863b118ebaf25d7cad2443`, based on PR #5 `e8b9d8e06bf0a2a2b8f356a7df5d85f4b6c665f8`.
- Environment: Linux 6.18.44 x86_64, Python 3.12.14, Godot 4.7.2.stable.official.ed1daf0bf. Headless native Godot and loopback ENet; no phone, mobile GPU, cellular, Xcode or Internet-security claim.
- This separate reviewer inspected the production diff and authored adversarial tests. The reviewer is the same model family, not a human/external security auditor. The parent engineer implemented all production corrections.
- Additional review tests and validation-script edits made the checkout dirty. The three reviewed runtime files match the named commit byte-for-byte; SHA256 values and evidence checksums are in `review_manifest.json`. The ten-client summary accurately records `dirty=true` and must not be relabeled a clean checkout.

## Findings and dispositions

| Finding | Classification | Result |
|---|---|---|
| Lost client close retains ten ENet transports, preventing replacement authentication | Original blocking reliability defect | Correction bounds ACK/ping transport lifetime and client resume attempts without expanding transport capacity. Exact scenario recovers 10/10. |
| Valid resume credential treated as absent while old actor is still bound | Original blocking reliability defect | Explicit transient response precedes account inspection; current owner retains authority. |
| Admission rejection reason overwritten when old recovery timer expires | New candidate regression found by independent test | Fixed by using terminal cleanup; before log retained, corrected 24-check suite passes. |
| Interrupted resume authentication terminates otherwise recoverable session | Existing recovery coverage gap | Bounded retry now works; explicit decoded mismatch remains terminal. Positive native probe and deliberately reverted-behavior negative control distinguish the change. |
| Lost welcome after server rotates token leaves client holding invalid credential | Existing adjacent reliability defect, independently reproduced | One bounded pending alias per actor allows recovery after retirement; revoked on first accepted input for the admitted generation. Original failed log retained. |
| Ten-account full-capacity reconnect with real HTTP/PostgreSQL | Unverified in this focused review | Spy account-bridge tests verify call ordering only. Full account-process scenario remains required. |
| Stale asynchronous ticket-consume completion during peer reuse | Partially verified | Existing generation/deadline unit regression passes; no new real delayed-HTTP race experiment was performed by this reviewer. |

The engine mechanism was independently checked against Godot source commit `ed1daf0bf001b61586d9930840f2f1394092c079`; exact fetched blob manifest is `engine-source.json`. ENet silently ignores a CONNECT when its fixed peer array has no free slot. Its maximum timeout is checked at retransmission opportunities, so the configured 5000 ms maximum is not a promise to retire at precisely 5.000 wall-clock seconds. A forced multiplayer mapping removal alone would not immediately free the ENet slot; this correction avoids that shortcut.

## Independently executed tests

| Test | Result | Evidence |
|---|---|---|
| Policy/deadline, invalid tokens, terminal failure, stale deferred transport cleanup | 24/24 passed|`corrected-review-test.log`|
| Native ENet busy token, duplicate account, wrong/expired guest token, sole actor authority | 13/13 passed|`admission-corrected-review.log`|
| Native ENet pending-alias owner safety, repeated lost welcome, deadline retention, first-input revocation, expiry rejection | 23/23 passed|`alias-review-test.log`|
| Lost welcome after committed resume |Pass, original actor restored|`lost-welcome-corrected-review.log`|
| Suppress one resume server-hello callback |Pass, original actor and accepted tick restored in 7.241 s|`auth-loss-corrected-review.log`|
| Auth-loss negative control restoring old terminal callback |Expected fail at 5.050 s, no accepted snapshot|`auth-loss-corrected-negative-control.log`|
| Existing peer generation/deadline test |Pass|`existing-peer-generation-test.log`|

The two native admission/alias fixtures use separate SceneMultiplayer roots and real UDP/ENet in one process. They are not ten independent client processes. The account bridge is a spy that counts inspection/consumption; it is not a replacement for PostgreSQL transaction validation. The alias expiry boundary is tested by explicitly setting a past monotonic deadline, while grant bounds and unchanged repeated-retry deadlines are checked against the actual clock. It is not a measured 20-second wait.

Initial failed evidence is preserved: `initial-review-test.log` has 22/23 passing and the terminal-reason regression; `lost-welcome-review.log` has a valid fixture and failed recovery. `auth-loss-negative-control.log` is the earlier deliberately failing callback control. No failing check was removed to obtain the corrected results.

## Ten-process evidence independently inspected

The parent engineer executed the process campaign. This reviewer checked its raw client reports, server occupancy samples and summary under `../committed-close-loss/`.

Exact requested scenario: ten separate clients plus one dedicated server; 100 ms simulated RTT; blackout 7.8–9.3 s; transport close 8 s; two-second initial retry; 22 s shared measurement.

- 10/10 recovered their original actor and remained connected with fresh accepted snapshots.
- Recovery after close: 8.881–10.108 s. No terminal rejection.
- Accepted snapshot ages at cutoff: 16–38 ms.
- All ten final actor bindings have fresh input acknowledgments 225–298; input-idle ages 15–39 ms. Recovery is supported by restored input authority as well as transport state.
- Maximum sampled ENet occupancy 10 and actor bindings 10; no sampled duplicate actor binding. No overflow transport pool.
- Cloud server tick duration p95 = 20.366 ms and interval p95 = 35.959 ms. These values do not establish 60 Hz performance acceptance and are not mobile frame rates.

The untouched old integration trial recovered 3/10; its instrumented PR5 baseline retained eight old transports/bindings at the final sample and recovered 0/10. These independent trials differ in outcome and both remain evidence. Initial corrected-candidate seed/jitter campaigns are additional parent-run evidence, not substitutes for the final combined-tree matrix. The earlier delayed-retry freshness failure remains preserved; retesting with a cutoff sampled before evidence serialization is required.

## Security assessment

The reviewed correction does not raise the ten-player or transport limit, remove ownership checks, accept client-reported damage, change reward eligibility, or consume a ticket while a valid busy resume is waiting. Fresh duplicate-account admission cannot evict a live owner. Nonempty invalid/expired credentials cannot silently allocate an unrelated guest actor. The pending alias resolves only to the server's current reservation, cannot evict a live actor, is limited to one entry per actor, and cannot renew its deadline when the same old token repeats. First accepted input removes it only for the matching peer/generation.

ENet remains an unencrypted trusted-LAN transport. A stolen bearer credential can impersonate its holder after the live owner retires. Initial admission interrupted after ticket consumption but before the first delivered welcome still needs a fresh ticket; no previously delivered resume credential exists. Long outages beyond bounded recovery require a new session. Ranked disconnect eligibility policy is unchanged.

## Recommendation and remaining gates

No unresolved blocking defect was found in this focused correction after the reviewed fixes. Proceed to the isolated combined integration and full regression matrix. **Defer full merge readiness and the 8.5 quality gate acceptance** until the actual integrated branch passes the protocol matrix, account-backed capacity/reconnect scenarios, delayed-backend races, repeated-cycle/long-outage cases, economy regressions and broader networking measurements.

No numerical 8.5 score is inferred from these tests. Physical-device performance, human responsiveness, production Internet security and external audit remain UNVERIFIED. This report does not authorize any merge.
