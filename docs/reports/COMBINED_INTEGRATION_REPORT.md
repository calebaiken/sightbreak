# Combined development preview — integration report

**Disposition: request changes; retain draft PR [9](https://github.com/calebaiken/sightbreak/pull/9).** The integrated development build works in the tested default paths, but the complete 8.5/10 gate is not met. No PR was merged, no public server was deployed, and no source PR branch was changed by Codex.

## Exact source and dependencies

| Input | Commit |
| --- | --- |
| Main, unchanged | `e67f2c86777d98d3cb3ad6bc7e851ef1826af26d` |
| Claude foundation PR1 | `98ff57c4a9ec6735db68c4e65ad36f6fe5a26ca6` |
| Codex PR3–8 stack | `89c0e997c9f706d91b02e5ac412853c4d35cd112` |
| Claude graphics PR2 | `64ec59884e22f6b71179c585e4679ae6e3b2f87c` |
| Refreshed full matrix | `4ae4e5c5570dfc3cb31fd5b3a07e9ca96cd247eb` |
| Final exports and native ten-client test | `60cf125bb2c05606e71a4a68482d31ec26dc69bb` |

Branch: `integration/sightbreak-network-art-preview`, isolated worktree. Final export game tree: `e0f32d2b7f2f174ee08788b8a1f00f7f377bcbcb`; runtime content SHA256: `31ce631c1193a56981e6db591d45f1b9e991f81bccd5412a6849cda64e6a1fa0`. Matrix and export runtime contents are identical: the intervening commit fixes only the excluded network test probe's start barrier. Later documentation commits do not reidentify these builds.

The initial actor.gd conflict was resolved by retaining both Claude's ViewmodelShading preload and Codex's SBMovementStep constants/delegation. No file was replaced wholesale. Subsequent graphics 64ec598 and foundation 98ff57c merges had no conflicts. Weapon, muzzle, rig, shader and animation ownership interfaces survive. See [conflict record](../engineering/INTEGRATION_CONFLICTS.md).

## Implemented and verified

- Recipient-authorized state, continuous remote interpolation, opt-in movement prediction, bounded lifecycle/admission, durable server result outbox and disabled combat-history diagnostics remain intact. Prediction is **off by default**; live rewind is **disabled**; protocol 5 requires matched builds.
- Authored Relay AR, rigged arms, skeletal reload and independent viewmodel projection operate alongside the network stack. No Claude asset, material, Blender pipeline or visual-design file was edited by Codex.
- Added reproducible cross-branch actor/lifecycle checks, aspect probes, active rendering fixtures, a ten-client campaign runner and source-bound export checks.
- Corrected test-only defects: asynchronous audio teardown needed a200 ms drain; exported Godot templates cannot execute editor-only external `--script` drivers; staggered renderer startup required a common measurement start and retaining peers until all reports finish. Failed attempts remain in the evidence.

## Regression results

**47/47 maintained groups passed** on4ae4e5c with correctedPR1 and graphics 64ec598. Exact commands, exits and durations: [matrix summary](integration-evidence/matrix-98/summary.json). This is a group count, not an assertion count or a blanket quality score.

| Area | Evidence |
| --- | --- |
| Weapons, head/body, smoke |28 /40 /26 assertions passed |
| Privacy, movement, hit history |55 /725 /638 passed; live history/rewind remains disabled |
| Authored weapon, actor integration |73 /183 passed; visual ticks preserve authority at 30/60/120 Hz |
| Landscape / Unicode HUD |325 landscape;2435 headless and 2442 native feed checks passed |
| Full natural bot match |10 rounds,3–7 score,64 kills, halftime/planting, exactly one result,303.6 simulated seconds |
| Protocol/admission |Six-pair compatibility matrix, hostile handshake, guest/account/capacity and ticket preservation/replay passed |
| Lifecycle soak |Two clients, eight reconnects each,64-second fixture, six round transitions passed |
| PostgreSQL / native HTTP economy |51 PostgreSQL tests (one dependency warning);14/14 real HTTP economy checks; marketplace/trading/ownership/conservation pass |
| Durable results |Godot and worker SIGKILL, backend outage, lost acknowledgment and duplicate replay: exactly10 grants/rewards, no duplicate wallet change |
| Native renderer |11 match and 19 cosmetic checks; texture counters plateau across five/six cycles; no new GL texture leak observed |
| Independent authority review |321/321 on the refreshed combined runtime; presentation cannot change replicated combat state |

**Additional adversarial tests fail:** the custom status-layout probe reports54 checks /7 failures in headless, native and combined-tree execution. The minimal persisted-layout probe reports9 /5. These are reported separately because the maintained default-layout suite misses them. No failing checks were removed. Nested compatible protocol-client logs contain intermittent ObjectDB warnings (three instances current/current, two release/release). Two verbose current/current reruns are clean; classes/ownership remain unresolved. These are not observed GL texture leaks, and the47-group pass does not mean every nested log is warning-free.

## Findings and classification

| Finding | Classification | Evidence / action |
| --- | --- | --- |
| Unicode fourth feed row clipped | Confirmed fixed at 227d6c8 and retained at 98ff57c | Independent old negative control reproduced10 failures; taller Noto fallback/native checks pass |
| Custom status line alternates into a vertical column | **New blocking PR1 regression** | At960×720,130% text,100% buttons, save grenade=[0.459375,0.82], smoke=[0.540625,0.82]. A6 px gap expands buy text to 756 px and hides health/ammo. Consecutive native frames prove oscillation;227 stays stable. [Exact correction request](https://github.com/calebaiken/sightbreak/pull/1#issuecomment-6160402580) |
| Full-capacity reconnect after lost close | **Blocking reliability defect; attribution UNVERIFIED** | Ten clients,100 ms RTT, blackout7.8–9.3 s, close8 s, real2 s retry: only5/10 recover within22 s; two terminal capacity rejections, three still connecting. Prior foundation has related constraints, but no matched baseline attribution. [PR5 finding](https://github.com/calebaiken/sightbreak/pull/5#issuecomment-6160142760) |
| Static fallback hands detach from authored rifle | New PR2 regression; nonblocking for default rig, blocks fallback acceptance | Hands use82° world projection while rifle uses54°. Native same-projection counterfactual reconnects them. [PR2 finding](https://github.com/calebaiken/sightbreak/pull/2#issuecomment-6159907178) |
| Visual target | **Failed quality gate** | Independent weapon/arms slice5.5/10, below8.5. This is not a replacement score for the historical whole game |
| Online reload poses update at 20 Hz | Pre-existing presentation limitation |120 visual ticks produce40 pose-time changes; retain ammunition authority when adding a future visual clock |
| Weak PackedScene cache not retained | Nonblocking optimization/comment issue | Repeated equip reloads the scene; no measured phone hitch claim |
| No usable status-row interval | Pre-existing custom-layout limitation | Fully occupied row still overlaps targets; requires bounded fallback |
| Slow-frame reconnect timer | Measured limitation | Configured2 s engine-delta timer took6.384 s wall in a slow software-render trial; no phone inference |
| Production Internet, devices and human feel | **UNVERIFIED** | No encrypted ENet/server identity acceptance, external security audit, phone measurements or Xcode compilation |

## Network and rendering measurements

One dedicated server plus ten real Godot clients ran all 0/50/100/150/200 ms RTT, jitter,3% loss,5% reordering, blackout and reconnect conditions. Original campaign:11/12 conditions pass; aggressive0.7 s reconnect has one failed client. Three repeats and no-loss control pass, and normal2 s reconnect passes10/10. The close-overlapping blackout still fails5/10. Successful repeats do not erase it.

Ordinary server callback work p95:5.56–11.03 ms; callback interval p95:16.7–23.2 ms. ACK position divergence p95:0.245–0.476m. Delayed remote-position error is generally0.008–0.011m,0.114m at 200 ms RTT; blackout/reconnect rise to 1.959/2.120m. This compares with the intended100 ms-delayed timeline, not current-time opponent accuracy. Experimental first-motion measurements are process callback latency, not touch-to-photon. Prediction stays opt-in.

Fresh60cf125 trial: one native plus nine headless clients,100 ms added RTT, prediction disabled, shared25 s window: **10/10 pass**, all 499-ish accepted updates (489–500), final accepted age0.036–0.337 s. Server work p95=9.223 ms; interval p95=17.136 ms. Native callback intervals p50/p95=288.899/475.282 ms under llvmpipe; no phone FPS claim. Native start/stop lateness30/102 ms is recorded. This fixture's12 draws/36,944 primitives does not represent ten visible authored rifles. Whole proxy duration44.409 s includes12.558 s startup and report/exit drain.

Matched static cameras: authored viewmodel adds2 draws,33,078 primitives and 5.34 MiB tracked texture residency. Weapon-visible software frame medians increase24.8–26.7%; hidden-weapon controls differ about1%. Three-round scenario wall timings vary1.9–5.3× and are diagnostic only. Inspection/case panels are small, reload is a fixed pose, case sampling covers partial opening, and bot camera faces a wall. Full details and raw distributions: [performance report](../network/PERFORMANCE_REPORT.md).

All ten keep/expand aspect configurations pass default crosshair/touch/HUD bounds at 60cf125. Keep preserves114.19° horizontal world FOV; expand changes visibility with aspect ratio. Shipping policy remains **keep**, pending a competitive FOV decision. Device safe areas and physical touch comfort remain unverified. See [aspect review](../engineering/MOBILE_ASPECT_REVIEW.md).

## Builds and evidence

All targets exported cleanly from60cf125. APK v2/v3 signatures, landscape manifest, minSDK24/target36 and arm64-v8a/x86_64 payloads pass. Linux menu/demo startup passes. iOS plist/project is unsigned and landscape-only. Independent inspection hashes58 payload files, validates PCK resource hashes/APK CRC, and confirms31 identical compiled scripts across targets. Only main.gdc differs from earlier d084 exports, matching Claude's HUD update. Test harnesses are excluded.

| Artifact | Workspace path |
| --- | --- |
| Android debug APK | `builds/android/sightbreak-debug.apk` |
| Linux executable | `builds/linux/sightbreak.x86_64` |
| Unsigned iOS project | `builds/ios/sightbreak.xcodeproj` |
| Portable packages | `builds/sightbreak-{android,linux}-debug.zip`, `builds/sightbreak-ios-xcode-project.zip` |
| Exact source/payload checksums | `builds/manifest.json`, `builds/checksums.txt` |

Final native export UI: **PASS**, actual60cf125 Linux ELF. Native menu/join, four server-authoritative shots30→26, observed R-key reload and completion30/86, client/server exit0 via supported `--quit-after 300`. Capture07 visibly shows RELOADING0.8 s and staged magazine;08 shows30/86. Captures05/06 are delayed pre-fire frames, despite later authority event timestamps. No error/leak is logged in this actual-export run. Native capture names are timing-neutral; captions must follow visible frame contents, not authority event times. Physical Android installation and macOS/Xcode compile/sign/device validation are **not performed**.

Curated evidence is versioned under [integration-evidence](integration-evidence/README.md). **Artifact upload is blocked:** the GitHub draft exists with zero assets; uploads.github.com returned Forbidden even on an approved retry. All packages and raw archives remain locally in builds/. A saved cloud network draft adds that host; review/save/publish is required before retry. Curated evidence and exact build manifests are committed to GitHub. See the index for paths and prepared checksums. Independent agents are separate reviewers of the implementation, not external auditors or human acceptance.

## Environment

Linux x86_64 kernel6.18.44; Godot4.7.2 official ed1daf0bf (binary SHA2568d106cbe6144c2dc7e881d61d2429c1a8a76e6b22ef48bd5e48dcf934953f71e); Python3.12.14; PostgreSQL17; Java21.0.12.1; Android build-tools36.0.0. Native: Xvfb, Mesa25.0.7 llvmpipe LLVM19.1.7. CPU quota4, IDs0–4; matched rendering uses CPU0,1 and two Mesa workers. GPU timings, battery and thermals are unavailable.

## Quality gate and integration order

Independent scoped gameplay authority, backend process-crash reliability and maintainability meet the reviewer's8.5 development rubric. Networking/stability/prediction are7.5; test coverage8.0; visuals5.5. Broad competitive security, device performance, physical mobile input and human feel remain UNVERIFIED. A numerical score cannot override the reconnect or HUD defect. See the [final independent review](integration-evidence/network-independent/final-review.md) for scope and rationale.

1. Claude corrects PR1's new custom-HUD regression; rerun defaults, adversarial persisted layouts and full matrix.
2. Reconcile Codex PR3→4→5→6→7→8 in dependency order. Correct and verify full-capacity reconnect before claiming lifecycle acceptance. Do not automatically enable prediction or live rewind.
3. Review PR2 independently. Correct its fallback, raise visual quality with comparable captures, and preserve its assets during integration. If graphics follows movement, retain both actor interfaces described above.
4. Rerun the combined matrix, build checks and independent review after dependencies move. PR9 is an aggregate validation preview, not a shortcut around constituent approvals or permission to merge main.

Preserve protocol 5 parity, ticket-inspection backend compatibility and the persistent outbox launcher/worker/backend as a unit. ENet remains trusted-LAN development transport; do not use production credentials. Earned-Credits policy, odds, ownership, trading and real-money-disabled behavior remain unchanged. New result delivery after 15 minutes and disconnected-player reward eligibility remain explicit policy limits. Resume from the versioned reports, not from an assumed earlier branch head.
