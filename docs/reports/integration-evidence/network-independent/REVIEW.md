# Independent integration networking review — current source, final evidence pending

Reviewer: separate Codex reviewer agent. Same-model AI review, not external security audit or human acceptance. No gameplay, art, branch ownership, or GitHub mutations performed by reviewer. Parent specifically authorized replacing only the two defective export-verification tools; those changes were made after independent native-UI reproduction and committed by the parent in d8a10ff.

## Scope and source

Reviewed combined merge e896c81e11e407517d7e99c3fd94ff0317e6c823 (PR1 227d6c8 + Codex stack through 89c0e99 + PR2 8c18357), then instrumentation commit 9bb0674d687b70aa464a2446357deaa99a93460b. Final runtime review was refreshed against d084e5003ac915550c368a86176df9063375bb59, incorporating Claude PR2 64ec598. Relative to that exact Claude actor.gd, the combined actor differs only by three movement constant aliases and replacing the original movement body with SBMovementStep.advance. The d084 runtime matrix and original ten-client summaries have been inspected. Source was refreshed again to 4ae4e5c5570dfc3cb31fd5b3a07e9ca96cd247eb, which adds Claude PR1 98ff57c4a9ec6735db68c4e65ad36f6fe5a26ca6 status-layout work and test-only instrumentation. Relative to d084, the only shipping change is main.gd; all gameplay/network modules remain unchanged. The fresh independent 321-check probe passes on 4ae4e5c with a clean log. The new full matrix and rebuilt-artifact/UI acceptance remain pending; prior runs are not relabeled as testing the new head.

Exact final reviewed source hashes: final-source-checks.json; preliminary hashes remain in instrumentation-checks.json. Godot 4.7.2.stable.official.ed1daf0bf; Linux cloud environment; headless independent probes. No physical mobile device or encrypted Internet transport assessment.

## Confirmed boundaries

- Both network snapshot send sites explicitly pass the authority's peer-to-actor binding; the full-state overload is reserved for offline/server tests. Recipient construction uses separate public, observable, team, and own allowlists. Enemy private ammo, inventory, funds, health, recoil, and reload timers do not cross this boundary. Own movement acknowledgments, grounded state, and jump-held state are likewise owner-only.
- Snapshot transforms are buffered and sampled separately from current combat metadata. Visibility revocation erases old buffered transforms. Client collision and visuals are removed on revocation; this does not remove server hit volumes.
- Client movement prediction remains false by default. It replays movement only; ammo, damage, rewards, objectives, and currency remain authoritative. Live shooting does not read SBHitHistory; diagnostic history recording is opt-in and false by default.
- Authored rifle/rig presentation is additive to shared actor integration. Visual animation seeks and model transforms do not advance weapon rules or grant damage. Authority still uses the unchanged capsule/ellipsoid shot volumes.
- Compatible admission still reserves capacity/account claims before one-use ticket consumption, with peer-generation/deadline guards at async completions. Incompatible pre-gameplay handshakes cannot call account admission.
- Durable result delivery preserves exact canonical identities in SQLite before unlinking handoff records. It does not replace backend transaction authority. Claimed durability is process-crash recovery with a clearly documented pre-SQLite power-loss boundary.

## Independently executed checks

External fixture integration_authority_probe.gd, using the combined project resources:

- 321 checks passed: 240 visual ticks across 30/60/120Hz leave the complete actor snapshot and weapon cooldown map unchanged; presentation cannot complete reload ammunition; rendered body animation leaves the tested authoritative hit intersection unchanged; owner-only reconciliation fields and all enemy private fields remain absent; default prediction/history remain disabled and history remains empty.
- The 321-check fixture was rerun on final d084e50 and passed. Intermittent immediate-shutdown warnings were independently isolated under verbose mode to AudioStreamWAV + AudioStreamPlaybackWAV, not textures. Actor._exit_tree already stops the players, but AudioServer releases the stopped playback asynchronously. Adding 200ms drain time to the external fixture yields a clean final run. Both the original warning and corrected-fixture logs remain preserved. This matches the maintained weapon-art/integration-lifecycle fixture change, without changing gameplay code.
- Pure export-guard mutation tests reject every one of 15 omitted required imported art/network paths and three test-harness/empty-pack cases. This tests validation logic, not actual builds. Results and exact hashes are in instrumentation-checks.json.

## Instrumentation review

Per-client UDP forwarding counters mirror aggregate byte/packet/drop accounting and measure actual forwarded UDP payloads. RTT is intentionally added as half-delay per direction; jitter/loss/reordering are synthetic. Resource timeline values now include current RSS alongside cumulative peak RSS and cumulative CPU. Final report interpretation must retain those distinctions; values after a process exits retain its last successfully sampled values.

The disabled-prediction comparison still collects `prediction_errors_m`; those values are stale authoritative owner pose versus acknowledgment, not prediction accuracy. Do not label them evidence of disabled prediction's error or compare them as prediction quality. First-motion measurement remains process callback movement, not physical touch-to-photon latency. Remote render-position error is measured against server ground truth at the intentionally delayed replica timeline (configured 100 ms interpolation delay), not the opponent's current server position. It does not remove or measure transport-to-screen latency.

The reconnect-at fixture explicitly closes the real transport, runs the existing reconnect path, and requires the same actor identity plus connected/fresh snapshot state at completion. It does not equate a short packet blackout with a reconnect.

The accepted-snapshot metric advances only after the replica buffer accepts a newer tick; the final freshness gate requires recent accepted state. A terminal blackout negative control correctly fails. Pack-content presence, source manifest matching and actual exported runtime exercise must be reported together; presence checks alone cannot establish executable behavior.

## Actual artifact inspection at d084e50

Independent inspection used a separate pack-directory parser, verified every Linux/iOS packed resource against its directory MD5, checked the Android ZIP CRC, and recomputed every 58 manifest payload file SHA256 across all targets. All source manifests bind d084e5003ac915550c368a86176df9063375bb59, game tree2ea3b38192fa4233d40e07208f0408e97c8558a4 and independently recomputed source-content SHA2568eed24e4c284034afd1eb9d383c7f3e981eabb12b17cafb158b0452a7554e9f6.

- Linux ELF:84,116,520 bytes; 118 resources; 31 compiled scripts.
- Android APK:67,370,308 bytes; 120 assets; 31 compiled scripts. Fresh apksigner verification succeeds with v2/v3; badging confirms0.3.0-dev build3, minSDK24/targetSDK36, arm64-v8a/x86_64.
- iOS:118 packed resources; 31 compiled scripts; actual ARM64 and simulator engine archives present; landscape orientation, local-network usage text, bundle ID/version/build, and empty signing team checked. This remains an unsigned project, not a compiled or installable iOS application.
- All 31 compiled scripts are byte-identical across Linux/Android/iOS packs. Required imported rifle, static hands, rigged arms and network modules are present; no test harnesses are packed.
- Exact raw artifact hashes and per-resource hashes are retained in actual-artifact-checks.json and target-pack-content.json. Actual exported Linux native menu/join/fire/fixture-triggered reload were exercised after this inspection; clean engine exit and the final rebuilt artifacts are tracked separately below.

## Confirmed new verification defect

The proposed scripts/fixtures/export_integration.gd is a SceneTree script, but this actual Godot export template does not support the editor-only --script entry flag. Independently launching the exported ELF with --script <fixture> plus the existing --smoke option runs the normal menu and prints SIGHTBREAK_MAIN_READY screen=menu, not EXPORT_INTEGRATION. Without --smoke, the proposed driver run times out. --help exposes no --script switch. An external positional .tscn with a Node driver also aborts explicitly because this template was compiled without path overrides.

Classification: **blocking for claiming that the planned external-driver export verification passed; not a discovered gameplay regression**. Preserve d084 runtime and verify through supported real executable menu/server flows, or explicitly change the validation implementation. Running the editor with a pack would only prove pack resource execution and must not be mislabeled as the exported executable. Clean decisive reproduction and unsupported-scene logs are preserved. Parent notified immediately.

## Final regression and network evidence

Independently inspected matrix-final/summary.json: all 47 groups pass at exact d084e5003ac915550c368a86176df9063375bb59, with exit 0 and no detected error logs. Includes gameplay, weapon/body/head volumes, smoke, privacy, interpolation/prediction primitives, protocol/account capacity, 51 PostgreSQL tests, economy, outbox SIGKILL/retry/lost-ACK scenarios, short reconnect soak, native renderer lifecycle and Unicode HUD bounds. This is 47 test groups, not 47 assertions or physical devices.

Independently checked all 12 ten-client campaign summary files and all five aggregate UDP counters per direction against the ten relay counters. Every sum agrees. These are eleven headless Godot processes per condition on loopback with synthetic impairment, not mobile/cellular measurements. Source 85edf895c05a9c4070d19e2e96a5752ade55006b, runtime hash unchanged from d084.

- Original campaign: 11/12 conditions pass; one client fails explicit reconnect under impairment with 0.7s stress delay. Failure retained.
- Ordinary 0/50/100/150/200ms RTT, jitter/loss/reorder/impaired conditions: render-position p95 approximately0.0077–0.011m except 200 ms RTT 0.1138 m. ACK position divergence p95 0.245–0.476m; this does not prove acceptable human movement feel. Ordinary server callback work p95 5.56–11.03ms, callback interval p95 16.7–23.2ms. Ten-recipient observed UDP payload approximately 48–54kB/s upstream and 111–124kB/s downstream, including the finite run's connection/warmup period. Wire/IP overhead is excluded.
- Blackout recovers but render-position p95 1.959 m and 5 hard corrections; original reconnect p95 2.120 m and 7 hard corrections. These recovery errors must not be hidden by reporting only ordinary steady-state cases.
- Disabled-prediction run passes connection/freshness, but its 1.275 m ACK comparison is not prediction error. The fixture still collects stale authoritative owner pose against acknowledgment.
- Three subsequent impaired 0.7 s reconnect repeats and a no-loss control pass; terminal blackout correctly fails freshness. Standard production 2 s reconnect with earlier blackout passes 10/10.

### Confirmed outstanding reliability blocker: close notification lost at full capacity

Source 47a350d clean, production runtime identical to d084. Run ten clients, 100 ms RTT, no jitter/loss/reorder outside an explicit blackout 7.8–9.3 s, close all transports at 8 s, reconnect using the actual 2 s client delay. At 22 s only 5/10 reclaim the same identity with fresh accepted snapshots. Clients 0, 2, 5 remain connecting; clients 3, 4 enter terminal failed with the slot-reservation rejection at approximately 17.9 s. Failed clients have no accepted update for 14.6–15.4 s. Evidence: reconnect-close-blackout/summary.json and per-client notification timelines. The matrix and successful repeats do not override this result.

Source inspection supports a lifecycle/capacity race: ENet has only ten transport peers; a valid resume token is ignored while its old actor binding remains, after which general capacity rejects admission. The final client failure path does not retry a transient occupancy rejection. The precise causal split between ENet transport retention and application binding retention is not proven. Classification: **blocking for the requested robust reconnect/8.5 networking gate; attribution as pre-existing versus introduced is UNVERIFIED**. PR #1 already has relevant occupied-token and ten-peer constraints; a matched baseline failure has not been run.

Recommended separate follow-up: keep ownership, replay protection and ticket-before-capacity ordering intact; add an explicitly bounded reconnect state with backoff for transient capacity/old-session occupancy, preserving the token/deadline. Any server-side takeover needs authenticated identity, generation-safe old-binding retirement and strict pending-peer limits. Test simultaneous old/new peers, token replay, lost disconnect/ACK packets, capacity denial, idle cleanup, and account ticket nonconsumption. Do not simply raise unlimited peer capacity, discard reservations or treat every admission failure as retryable.

## New foundation HUD blocker on 98ff57c

The separate foundation reviewer reproduced a previously saved narrow-center custom HUD. I independently inspected its raw headless report and native frames 00/01 in pr1-status-98ff57c/saved-captures. At 960x720, 130% text and 100% button size (corrected against the foundation reviewer's saved-layout reproduction), the helper selects a 6 px center gap, wraps the buy prompt into 23 lines (Label height 756 px), pushes health/ammo outside the viewport and oscillates back to the full row. The native next frame visibly shows vertically stacked letters and missing health/ammo. Existing 325 landscape assertions pass because they cover default layouts. Classification: **new blocking mobile/custom-HUD regression in Claude PR1 98ff57c, inherited by the combined tree**. The foundation reviewer owns the detailed reproduction/PR communication. Do not modify Claude visuals through the networking branch or dismiss this from a passing default-layout test.

## Native network harness follow-up

The initial native-plus-nine-headless trial at d2b72f1 failed client 0 and client 1. Client0 accepted 328 snapshots before a server disconnect at its 18.012 s wall, then reached 25.269 s wall with only 9.738 s logical simulation. Staggered process initialization meant the server/headless duration windows ended before the slow native process's window; this run cannot establish a successful common ten-client interval. It remains preserved as failure. Reconnection's configured 2 s engine-delta timer took 6.384 s wall in that slow render environment; this production behavior was not changed by test instrumentation and says nothing about untested phones.

Reviewed the new 4ae4e5c test-only startup barrier: every client must have accepted a snapshot, parent publishes a shared start epoch, each probe maps it once to local monotonic time, measurement counters reset, and all peers remain connected until every final report exists. Final accepted freshness/count/state/reconnect gates remain unchanged. Reports include boundary lateness and whole-proxy traffic explicitly includes startup/measurement/drain. I flagged the non-atomic start.json publication (partial JSON polling race) and artificial first 0 ms frame sample. Independently inspected follow-up60cf125bb2c05606e71a4a68482d31ec26dc69bb resolves both with atomic os.replace and first-interval omission. The fresh native barrier trial remains pending.

## Actual exported native UI evidence and remaining verifier gate

Actual d084 Linux ELF was launched directly on isolated Xvfb:101 at 1280x720, with source Godot authority at /root/Sightbreak/Match on loopback. Native mouse inputs selected Local Network and Join. Protocol 5 admission, applied owner snapshot acknowledgment, authored rifle/rig rendering, seven server-authoritative shots 30→23, a headshot feed, and replicated staged reload 30/83 are evidenced by raw ImageGrab captures and authority logs. Reload was explicitly triggered by the source authority fixture. Desktop R-key injection remains UNVERIFIED.

Capture 07-exported-reloaded.png actually depicts RELOADING 0.7s, rigged support hand and detached magazine; capture 08-exported-reloaded-settled.png depicts 30/83 and the ready rifle. Capture 06 is still pre-reload due software-render timing. File labels must not substitute for visual inspection. The supported --quit-after 1500 exceeded 120s and the driver terminated the client; this attempt therefore does **not** pass clean-teardown validation. Failure log preserved at export-ui/automation.log.

The maintained verifier now uses only supported native UI and a clearly labeled source-engine fixture, validates the actual ELF hash/runtime content, flushes authority evidence before exit waiting, uses timing-neutral capture labels and a settled frame, defaults to 300 iterations, and fails explicitly on timeout/errors/leaks. Python syntax/CLI checks pass. Parent committed these two tools in d8a10ff; final rebuilt binary rerun is required.

## Remaining gates

- Runtime source reviewed at d084e50; 45/45 initial and 47/47 final groups independently inspected. Twelve-condition ten-client measurements and failed close-loss reconnect are inspected above. Final rebuilt artifacts, native clean teardown, and packaging remain pending.
- Opt-in local prediction still has substantial acknowledged real-map divergence; competitive enablement is not accepted by this review.
- Live combat rewind is disabled and remains unvalidated; explicit actor/account possession generation is still required before any live rewind activation.
- Static-cover and opaque-smoke filtering are conservative, intentionally disclose peeking margins/translucent rims, and do not claim perfect anti-cheat. Prior observations can be retained by modified clients; spatial audio allows inference.
- ENet account/reconnect bearer transport is trusted-LAN only. Production Internet confidentiality, anti-replay transport, infrastructure security, sustained/mobile performance, physical safe areas, human movement feel, and external audit remain UNVERIFIED.
- Reward freshness still limits first delivery after long backend outages. Queuing is not backend award acknowledgment.

## Provisional disposition

**Request changes for the reconnect reliability gate and new custom-HUD regression; defer unconditional integration approval.** No new authority/privacy integration defect was found in inspected code or the independent 321-check probe, but the full-capacity lost-close reproduction fails the requested multiplayer reliability gate and the latest foundation adds a visually confirmed custom-HUD regression. Final packaging/UI verification remains open. Any scoped development-only acceptance must explicitly carry these limitations; this review does not award an overall 8.5/10 or production readiness.

Provisional category assessment against the user gate: gameplay authority 8.5/10 (regressions+independent visual/authority isolation; custom HUD usability separately fails), backend transaction/recovery reliability 8.5/10 within the documented process-crash/LAN envelope, maintainability 8.5/10 (modular boundaries, isolated shared actor integration), test coverage 8.5/10 for the exercised development scenarios; networking correctness 7.5/10 and stability 7.5/10 due the reproducible reconnect defect; prediction/interpolation 7.5/10 due real-map divergence/recovery corrections and absent human acceptance. These are scoped engineering judgments, not statistical confidence. Competitive Internet integrity/security, mobile performance, thermal/battery behavior and physical-device acceptance remain **UNVERIFIED**. A scoped numeric score cannot authorize disabled prediction/rewind or override an exploitable defect. Final export-tools result is pending and may change packaging acceptance only.
