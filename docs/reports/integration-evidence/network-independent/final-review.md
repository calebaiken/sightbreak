# Independent final integration QA

Date: 2026-10-14 UTC. Reviewer: separate Codex reviewer agent, resuming the previous independent review's evidence after environment recovery. This is independent same-model review and execution, not an external security audit or human playtest. No production files, art assets, commits, source PR branches or GitHub state were modified by this reviewer.

**Recommendation: REQUEST CHANGES / defer unconditional integration acceptance.** The final exports are correctly bound to the tested source and the actual Linux executable passes native input, authoritative combat/reload, and clean-exit verification. Those successes do not resolve the full-capacity reconnect failure, the new saved-HUD regression, or the unmet visual quality gate. An explicitly labeled diagnostic development preview is supportable; release readiness and the blanket 8.5/10 gate are not.

## Exact source and independent artifact verification

Final export/source commit: `60cf125bb2c05606e71a4a68482d31ec26dc69bb`.

- Game tree: `e0f32d2b7f2f174ee08788b8a1f00f7f377bcbcb`.
- Independently recomputed shipping source-content SHA256: `31ce631c1193a56981e6db591d45f1b9e991f81bccd5412a6849cda64e6a1fa0`.
- All three source manifests identify this exact export commit, game tree and runtime content; exported game source was clean.
- Separate parser recomputed all 58 payload file SHA256 values, Linux/iOS packed-resource MD5/SHA256, and Android ZIP CRC. Required imported rifle, static hands, rigged arms and networking modules are present. No test harness scripts are packed.
- Linux has 118 packed resources, Android 120 assets, iOS 118 resources. All 31 compiled scripts are byte-identical across targets. Relative to independently parsed prior `d084e500` exports, the only changed compiled script is `main.gdc`; the other 30 are unchanged.
- Fresh `apksigner verify --verbose` passes v2/v3 signatures. Android badging confirms package `com.sightbreak.game`, `0.3.0-dev` / build 3, minimum SDK 24 / target 36. This is debug signing, not release signing or installation evidence.

| Artifact | Bytes | SHA256 |
| --- | ---: | --- |
| `builds/linux/sightbreak.x86_64` | 84,118,328 | `401b2709f5ac1d5c3730a6e9b5759160a17f770f109c95f96021948880d54891` |
| `builds/android/sightbreak-debug.apk` | 67,374,404 | `e752773d9ae282f8f6d73769462795ce03ecc8bdd7743d18ee7c876557314463` |
| `builds/ios/sightbreak.xcodeproj/project.pbxproj` | 15,914 | `bc5060fca682b7a98571f6ba3d55f26d5232263d1cc18d3480ca79bb71557cc1` |

The iOS row hashes the project file only; all 50 iOS payload files were checked separately. The project includes device/simulator engine archives and has empty signing-team settings. It is an unsigned exported Xcode project, not a compiled, signed, installable or device-tested iOS app. Final distributable ZIP hashes belong to the parent packaging manifest.

Raw evidence: `final-artifacts/results.json`, per-target pack-content JSON, `apksigner.log`, `android-badging.log`. The independent parser is `check_final_artifacts.py`.

## Actual final Linux executable: PASS

Executed the maintained `scripts/verify_integration_export.py --reload-mode keyboard --xvfb /workspace/tools/xvfb/usr/bin/Xvfb --output /workspace/reviews/integration-20261013/final-native-ui` from the final worktree. This launches the actual exported ELF normally and uses native X11 mouse/keyboard events. A source-engine authority fixture runs separately on loopback; no editor-only `--script` flag is passed to the exported executable.

Observed and checked:

- Actual native menu → Local Network → Join.
- Protocol 5 admission with owner input acknowledgments; final largest acknowledgment 2,327.
- Four server-authoritative rifle shots, magazine 30 → 26.
- Native desktop R key observed in server input, then reload start and completion. Fixture automatic reload was disabled.
- Actual rendered authored rifle/arms, headshot feed, staged reload, then settled 30/86 ammunition/reserve.
- Client and source-authority process exit codes both 0; supported `--quit-after 300` completed naturally. No termination fallback was used.
- Client/server logs contain no script error, engine error, ObjectDB leak or GL texture leak. The native driver logs the expected unsupported VSync-mode warning under llvmpipe.
- Both executable and source authority in `results.json` bind exact `60cf125`; actual ELF SHA matches the manifest before execution and runtime source stayed unchanged during verification.

Eight raw 1280×720 X11 captures are hashed in `final-native-captures.json`. Direct visual inspection establishes these captions:

- `01-exported-menu.png`: actual menu.
- `05-after-fire-input.png`: delayed pre-fire rendered frame, still 30/90; its filename describes automation timing, not visible combat state.
- `06-after-authority-reload-start.png`: still 30/90 rendered, with visible headshot feed/casings; not a visible reload-start frame.
- `07-after-authority-reload-completion.png`: actual rendered reload is still in progress, label **RELOADING 0.8s**, staged rifle/magazine visible.
- `08-settled.png`: reload finished visually, **30/86**, ready rifle/arms.

Do not use screenshot filenames as proof of synchronized visual and authoritative timing. Software rendering delays are substantial. Desktop key injection and native executable behavior are verified; touch on real phones, mobile GPU performance and human input feel remain unverified. Earlier unsupported-export-driver and timeout attempts remain preserved and are not reclassified as passing.

An initial CLI invocation without `--xvfb` was rejected before launch; its log is preserved as `final-native-ui-invocation-missing-xvfb.log`. The corrected invocation above is the successful run.

## Full regression and cleanup evidence

Independently inspected `matrix-98/summary.json` and raw logs: **47/47 maintained groups pass** on clean `4ae4e5c5570dfc3cb31fd5b3a07e9ca96cd247eb`. These cover gameplay, hit volumes, smoke, privacy, input/replica primitives, protocol/admission, real PostgreSQL/economy/outbox recovery, short reconnect soak, HUD, weapon-art and native renderer lifecycle. Recorded highlights include 51 PostgreSQL tests, 14 native HTTP economy checks, 10-round natural bot completion (3:7, 64 kills, halftime and plant), and actual process-kill/database-outage/lost-ack outbox recovery with exactly 10 grants/rewards and unchanged wallets on replay.

The only changes from that matrix source to `60cf125` are test instrumentation: atomically publish the shared measurement barrier and omit the artificial first frame sample. There is no shipping game-script/asset/project diff. The final exports and native/network follow-ups execute `60cf125`; the 47-group matrix is not relabeled as a direct run at a different SHA. Prior independent 321-check authority/privacy/default-off probe on `4ae4e5c` likewise applies to unchanged shipping runtime.

**Important nested-log qualification:** the matrix summary's 47 passing outcomes do not imply every nested log is warning-free. The compatible current/current protocol client recorded three ObjectDB instances at shutdown; release/release recorded two. Their classes are not identified in those nonverbose logs. Two fresh verbose current/current reproductions at `60cf125` both joined and exited 0 without a warning, so the intermittent diagnostic remains unresolved. It is not established to be an OpenGL texture leak or persistent gameplay defect. Earlier separate art-fixture WAV/playback-drain findings do not prove the classes in this different warning. Preserve `protocol-cleanup/client-{0,1}.log` and the original warnings.

The deliberately incompatible legacy protocol cases also record expected low-level engine auth/packet errors while correctly rejecting admission. These should be distinguished from a successful same-version run's errors. The actual exported native UI run and dedicated maintained render-lifecycle checks are clean for the checks they perform.

## Shared measurement barrier and native ten-client trial

Source review confirms the barrier waits for all client processes to accept a snapshot, publishes a common start epoch atomically, maps that epoch once into each process's monotonic clock, resets measurement counters and keeps processes connected until every final report exists. The first artificial zero-length interval is omitted. Final accepted-state count/freshness and connected-state gates were preserved. The initial startup-skew trial remains a failed harness trial; it cannot substantiate a common ten-client interval.

Independently reconciled **all twelve aggregate UDP counters** against their per-client counters in `network-native-shared`: sums for counts/bytes and maximum for datagram sizes all match. There are one dedicated authority, nine headless clients and one actual native rendered Godot client, with synthetic added RTT 100 ms, prediction disabled and no loss/jitter/reordering in this particular trial.

- 10/10 connected with fresh accepted state after the nominal 25 s shared window.
- 489–500 accepted snapshots per client. Final native accepted age 0.337 s; headless peers 0.036–0.075 s.
- Shared start offsets 0–30 ms, measurement end lateness 0–102 ms. These bounds are recorded, not hidden by claiming perfect simultaneous callbacks.
- Server callback work p95 9.223 ms, interval p95 17.136 ms; maxima 99.560/111.902 ms. The sampled duration is short, not a soak or sustained mobile target.
- Whole proxy window 44.409 s, explicitly including startup/measurement/drain: 2,347,330 upstream and 5,468,583 downstream UDP payload bytes, about 52.86/123.14 kB/s. ENet payload framing is included; IP/UDP header cost is excluded.
- Maximum UDP payload 1,392 bytes, 30 datagrams over 1,200. This flags MTU/fragmentation risk; it does not demonstrate observed Internet fragmentation.
- Native client reports 87 actual callback intervals: p50 288.899 ms / p95 475.282 ms under llvmpipe. Draw/primitive snapshot is 12 / 36,944, textures 55,942,068 bytes. This is the current fixture's scene/pistol path, not the authored-rifle profile. There is no phone FPS or GPU timing inference.
- Native first movement callback at 0.856 s versus 0.200–0.251 s for headless clients is software callback response, not physical touch-to-photon latency.
- The 1.275 m disabled-prediction ACK comparison is stale authoritative pose disagreement, **not prediction accuracy**. Prediction was off and no reconciliation correction occurred.

Detailed computed audit: `final-network-inspection.json`. Original twelve-condition headless campaign and follow-up reconnect results remain valid only with their own source/timing provenance; the barrier trial does not replace them.

### Independent barrier controls

- Existing independent 2-client / 5 s / 100 ms RTT control at `60cf125` passes with 100 accepted snapshots each and fresh accepted ages 0.033/0.016 s.
- Newly executed 2-client / 8 s / 100 ms RTT terminal-blackout control at `60cf125`, blackout from measurement second 3 for 20 s, **correctly returns exit 1**. Both clients retain a connected label but accepted snapshots are 5.010/5.026 s stale; both fail. All reports reach the shared-stop barrier. This proves the connected label alone cannot produce success.
- The CLI `--blackout-at` help still describes time after client launch; code now correctly measures from the common measurement start. This is a nonblocking tooling-documentation nit. Old and new campaign timing must remain explicit.

## Outstanding findings and integration gates

| Finding | Classification | Evidence and required response |
| --- | --- | --- |
| Full-capacity reconnect with lost close | **Blocking reliability gate; introduced vs pre-existing UNVERIFIED** | Preserved ten-client close at 8 s / blackout 7.8–9.3 s / actual 2 s retry run reclaims only 5/10; two terminal reservation rejections, three still connecting. Normal reconnect/soak passes do not negate it. Follow up with bounded transient retry and generation-safe ownership/capacity handling; never bypass token/ticket protection. |
| Saved custom HUD oscillation in PR1 `98ff57c` | **New blocking mobile regression** | Foundation review: 960×720, **130% text, 100% buttons**, saved grenade `[0.459375,0.82]` and smoke `[0.540625,0.82]`; fitter chooses a 6 px gap, actual label becomes 756 px tall and alternates with normal frame, hiding health/ammo. Independent headless/native edge matrix: 54 checks / 7 failures; default 325 pass. This reviewer directly inspected the broken raw native frame. Fix in Claude's source branch and add actual bounds/convergence coverage. |
| Static hands fallback projection mismatch | **New PR2 regression; nonblocking for default rigged preview, blocking fallback support claim** | Graphics reviewer counterfactual and directly inspected raw frame show detached hands when static world projection at 82° is paired with rifle at 54°. Correct every first-person attachment projection in Claude graphics branch; preserve assets. |
| Weapon/arms visual gate | **Blocking required quality milestone** | Separate screenshot-driven rubric approximately 5.5/10 for weapon/arms integration slice, not whole game. Do not average successful technical checks into visual acceptance. |
| Intermittent protocol ObjectDB shutdown warning | **Unresolved, nonblocking diagnostic pending identification** | Current/current 3 instances in full matrix; two fresh verbose current/current follow-ups clean. No evidence naming them textures. Do not suppress or relabel original logs. |
| Online reload presentation steps | **Pre-existing limitation** | Graphics reviewer sees 40 pose-time changes across 120 visual ticks under 20 Hz authoritative reload updates. Any smoothing must remain presentation-only. |
| Weak PackedScene cache | **Nonblocking optimization/documentation issue** | Graphics reviewer confirms rig scene is loaded again after weak cache release. No mobile hitch impact measured. |
| Production transport/security and devices | **UNVERIFIED** | ENet remains trusted-LAN bearer transport; no Internet confidentiality audit, external security audit, phone installation, thermal/battery, Metal/Vulkan or Xcode compile/sign evidence. |

The prior independent report's custom-HUD text-scale typo has been corrected from 100% to 130% using the foundation review's exact saved-layout reproduction. This is evidence correction, not changed test conditions.

## Evidence-based quality disposition

The scores below are scoped engineering judgments with anchors: 5 = significant known failure, 7.5 = useful development behavior with unresolved gate, 8.5 = demonstrated correctness in the stated tested envelope. No numerical score overrides an exploitable defect or extends evidence to an untested platform.

| Category | Disposition | Basis / limit |
| --- | --- | --- |
| Networking correctness | **7.5/10, below gate** | Normal same-version/freshness and impairment runs work; full-capacity lost-close recovery fails. |
| Server gameplay authority | **8.5/10 within tested LAN envelope** | Weapon/head/body/smoke/round tests, 321 independent authority-isolation checks, real exported input→server shot/reload. This does not grade broken HUD usability. |
| Competitive integrity | **No new inspected authority/privacy defect; broader acceptance UNVERIFIED** | Recipient allowlists, visual/simulation separation and disabled rewind verified; no claim of perfect anti-cheat or adversarial Internet validation. |
| Security | **UNVERIFIED for production** | Trusted-LAN account admission/regression evidence exists; public transport/infrastructure/human audit gates absent. |
| Prediction/interpolation | **7.5/10, below gate** | Ordered replica tests and normal movement evidence pass; real-map ACK divergence/recovery corrections and human feel remain unresolved. Prediction stays opt-in/default false. |
| Stability | **7.5/10, below gate** | Native clean exit and resource plateaus pass; reconnect and custom HUD failures persist. |
| Performance | **UNVERIFIED against mobile targets** | Reproducible cloud counters/wall distributions exist; no representative devices or reliable GPU timings. |
| Backend recovery/transactions | **8.5/10 in tested process-crash/isolated-DB envelope** | Real outage/crash/idempotency/economy tests pass; first-delivery freshness after long outages and pre-SQLite power-loss boundary remain documented limitations. |
| Maintainability | **8.5/10 for integration boundaries** | Modular network helpers, narrow shared actor merge, source-bound tools/docs and isolated branches preserve ownership. |
| Test coverage | **8.0/10, below full milestone gate** | Broad maintained matrix and independent negative controls are valuable; custom HUD and full-capacity reconnect defects remain outside passing maintained gates. Add their regressions before promoting the broader 8.5 claim. |

No aggregate score is awarded. The source/artifact verification gate is complete. The full competitive/mobile/visual integration gate remains blocked. Retest corrected foundation/graphics source heads and the full networking stack before recommending an integration merge; retain prediction and combat rewind defaults. Parent owns final GitHub/evidence publication, not this reviewer.
