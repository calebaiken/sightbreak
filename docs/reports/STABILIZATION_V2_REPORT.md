# SIGHTBREAK stabilization and development build V2

**Development preview; keep PR16 draft. Production and 8.5 quality acceptance are not granted.** This checkpoint continues the previously delivered integration. It retains source-owner branches, PR15, all historical PRs and the fallback artifact. Main is not merged or rewritten.

## Frozen source and preserved baseline

| Input | Exact SHA |
| --- | --- |
| Final V2 campaign/export source | `701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd` |
| Final game tree, including maintained tests | `2d2b174c2145e9755ddfc78a1369e74443fcc400` |
| Shipping content SHA256, excluding tests/import cache | `12d50718f295f04d21de691f31fbde8f03612b145680aaa592ef9e6e08cd5eec` |
| Previous PR16 checkpoint | `a939f1e7e0c32a5ef7ffbad0a714beb3af365259` |
| Previous exported/distributed source | `4316c58c8f5ae38ea924631fc48e4b1e7d5df873` |
| Gemini PR14 | `7397efd8d10be727840aa91def951f79bdfaff64` |
| Claude PR2 | `5357329fa06136ac0d81b58ace97f872f37bebfa` |
| Claude UI PR12 | `7e41de635a92763bd608203faf2c4689255bf727` |
| Research PR13 | `7dd0628410589136a8ec128de1e1c9b0c1543133` |
| Marketplace guard PR15 | `228c3828e0588a9f9486b64c42f9f618a741e193` |
| PR11 base | `11573e587f13dfd832613a0c09dbc615f46d3461` |
| Main baseline | `e67f2c86777d98d3cb3ad6bc7e851ef1826af26d` |

A final read-only GitHub check at 2026-10-16 06:06 UTC confirms main, PR15, Claude PR2, UI PR12, research PR13 and the historical PRs remain preserved. **Gemini advanced during the frozen campaign** to `48eb0586e273f96dc20b346ed444d00ab0f3ac30`, two commits beyond the integrated 7397efd. Their subjects describe navigation, hearing, anchors, damage-look and purchase changes. That new source is **not integrated or independently validated in V2**; the AI findings below bind to 7397efd plus the explicitly documented integration correction. Re-audit the new source before the next checkpoint. [Final head receipt](three-agent-evidence/stabilization-v2/final-source-heads.json) and [after-freeze comparison](three-agent-evidence/stabilization-v2/gemini-after-freeze-compare.json) preserve this distinction.

The machine-readable manifest is [source-manifest-r2.json](three-agent-evidence/stabilization-v2/source-manifest-r2.json). Separate detached checkouts hold the complete regression, native packages and destructive negative controls. No source or tooling commit is made inside a running campaign checkout. Later evidence/report commits on PR16 do not change its shipping content.

The environment is running with current enforced restricted-network policy. Existing Godot 4.7.2, Python 3.12, backend venv, development PostgreSQL, Xvfb/Mesa and Android SDK/Java were reused. Every original worktree was inspected and clean; no uncommitted work was discarded. The engine is official `4.7.2.stable.official.ed1daf0bf`; the unrelated system Godot 4.6.3 is not used. Physical devices and hardware GPU profiling remain outside the measured environment.

All 275 retained baseline evidence hashes and all five local fallback artifact hashes verify. GitHub confirms the original Actions artifact 12023941005 remains unexpired, with digest `5f9235dd55f4570a058eb7599e3805905cf8241b9b52db7623f5c70297018869`. [Fallback download](https://github.com/calebaiken/sightbreak/actions/runs/38846961471/artifacts/12023941005). The [historical report](THREE_AGENT_INTEGRATION_REPORT.md) and original **64/70** matrix remain unchanged; frozen soak reruns are still separate evidence, never rewritten original passes.

## Implemented corrections

- `d232b96` merges exact Gemini 7397efd. The original missing APIs/property error and attacker sound investigation are corrected by its source. Integration adapts the changed round-plan API without replacing the AI system.
- `a143629` removes the new helper's five direct ammo/reserve/utility grants after `actor.buy_weapon()`. Failed purchases now preserve all resources; funded purchases retain the real actor cost, ownership and ammunition rules. Match purchases still use `choose_buy_weapon` plus authoritative actor purchase. The new round plan is selected after actors and the current objective carrier reset, avoiding stale previous-round positions. Independent source/native controls accept this narrow correction.
- `f259ab3` merges exact Claude 5357329, including f4a hip retrieval and the first-person studio/material changes. No actor/main/network runtime script is changed by this graphics merge.
- `fb1e645` frees test-owned reload worlds and waits 0.5 s after deletion before quitting; the protocol client fixture also drains after its Match deletion. Weapon-art teardown gets the same margin. No runtime waveform, event phase, ammo timing or protocol assertion changes.
- `b5ad8c8` corrects the finish probe to preserve each shipped part material. Its base condition previously replaced the new polymer handguard clone with the receiver finish.
- `0672020` adds explicit frozen-source and nested-child leak gates to the full matrix, includes the maintained contact test, and adds a reusable actual-export offline driver with source/hash and clean-exit checks.
- `81434b4` identifies V2 as **0.3.1-dev, build 4** across Android/iOS/project/manifests.
- `aee6b73` changes audio capture to independent sample-frame cue marks, physics stepping and short balanced mixer locks, preserving every original amplitude/timing threshold. It adds capture-discard checks, a simultaneous-shot group and a truly early unlogged-audio negative control. It releases capture-owned scenes/buses before shutdown.
- `701ce2c` applies the same proven post-deletion drain to the natural full bot-match fixture after the first new campaign exposed its immediate-quit leak.

The native offline controller was then strengthened in separate tooling commits: it waits for the real live phase, checks living-player HUD ammunition with OCR, and holds inputs across software-rendered frames. Earlier post-death/no-fire attempts remain unsuccessful gameplay evidence. The game/export source stays 701ce2c; the external controller commit and SHA256 are explicit manifest inputs.

## AI correctness and tactical quality

[Verbatim independent AI review](three-agent-evidence/stabilization-v2/ai/REVIEW.md), source/probe hashes, native logs, invariant probes and all unsuccessful attempts are retained. Gemini 7397efd parses and its dedicated regression passes. Independent native controls cover positive pursuit and behavior-changing memory expiry; nearby/out-of-range/expired/allied sounds; hidden live-coordinate invariance; actual clear LOS, smoke occlusion/removal, wall/FOV negatives; fresh/expired team reports; objective-carrier support; real plant/defuse timers; equipment ownership; and actual movement toward reachable versus blocked anchors.

The new source helper reproducibly turns credits 0, rifle 2/3, utility 0 into rifle 30/90 plus one smoke/grenade even though the underlying purchase fails. Its current round-start caller already reset resources, limiting immediate gameplay impact, but the helper violates authority if reused. The five-assignment integration correction passes the same unchanged independent invariant and funded-positive control. Round reset/loadout contracts are preserved.

Remaining source-owned failures are explicit: three defender anchors lie inside expanded obstacles and fail native arrival; Easy's 18 m hearing bound is bypassed by the second 22 m defender scan; unseen damage direction is overwritten by navigation/scan; declared sound-noise values are unused and remembered shot positions are exact. These are not snapshot entitlement leaks or live hidden-coordinate tracking. Narrow integration did not silently rewrite those tactical policies. [Actionable PR14 review](https://github.com/calebaiken/sightbreak/pull/14#pullrequestreview-5543439605) is anchored to exact 7397efd; this integration does not edit the source branch.

Same original seeds 1847/2026/3141, all three difficulties, ten bots, real 60 Hz physics and two naturally resolved rounds per condition were repeated for PR11, prior integration and V2. Additional observation instrumentation reproduces every common gameplay metric exactly while adding actual interaction-progress attempts and inactive time. No winner/plant/defuse states are injected; only buy waits are skipped.

| Native measurement: PR11 → prior integration → V2 | Easy | Normal | Hard |
| --- | ---: | ---: | ---: |
| Switches / engaged decisions |9.46% →4.21% →5.76%|9.36% →13.17% →15.99%|17.08% →25.67% →35.90%|
| Commanded-movement stall ratio |6.05% →5.75% →4.79%|5.58% →7.24% →10.46%|2.97% →15.65% →11.82%|
| Inactive share of alive actor time |11.51% →6.01% →6.30%|12.11% →10.87% →8.76%|15.06% →22.50% →22.18%|
| Plant attempts / completions |0/0 →0/0 →0/0|2/2 →3/2 →3/2|5/3 →0/0 →0/0|
| Defuse attempts / completions |0/0 →0/0 →0/0|1/1 →2/2 →0/0|1/1 →0/0 →0/0|
| Mean CPU microseconds / bot decision |52.3 →76.5 →71.2|52.0 →126.2 →117.4|56.0 →126.8 →121.5|

The AI comparison source is a143629; final AI/match/actor/arena bytes are unchanged afterward. Every 18-round sample completes. Six Hard rounds with no objective attempts and greater target churn remain a quality warning. These are small controlled samples, not final balance or phone CPU benchmarks. Inactivity can include deliberate scanning, and stall is a displacement proxy. **Source/API/authority correctness improvements are accepted within scope; tactical 8.5 acceptance is failed.**

## Audio and ObjectDB ownership

[Independent causal review](three-agent-evidence/stabilization-v2/audio/CAUSALITY_REVIEW.md) and [network cleanup review](three-agent-evidence/stabilization-v2/network-review/NETWORK_REVIEW.md) reproduce and identify the exact objects. Original reload sequence 92/0 and audio 29/0 still emitted WAV/playback warnings. One stock matched-protocol client leaked a transient sidearm's WAV/playback; both IDs were mapped to its `Match._audible_shot_rpc` voice. The Match was invalid and peer already Offline. No ENet, packet or SceneMultiplayer object appeared in that leak.

The engine marks stopping playback for mixer deletion, then schedules its final unref for a later main-thread AudioServer update. One process frame after freeing the scene does not guarantee both stages. A pure-engine camera/player/synthesized-WAV reproduction eliminates Sightbreak entirely and still shows an immediate-exit warning. A retained-reference probe observes the AudioServer-owned reference drop roughly 27.6 ms after scene deletion.

Post-deletion drains alone close the reproduced warnings: full 92-assertion sequence 6/6 clean (three isolated, three concurrent), forced transient sidearm 3/3 clean and a natural 30 s matched client clean. No audio cache clearing or runtime stop-policy change is justified. The bounded 0.5 s wait is tested under this host's load; the strict leak scanner continues rejecting any residual warning. The new matrix also audits child logs, so successful compatibility outcomes cannot hide another nested resource warning.

The first V2 matrix on aee6 completed a natural 12-round match, 78 kills, halftime and exactly one result, then emitted 13 ObjectDB warnings on immediate exit. It was stopped and preserved as a partial unsuccessful attempt. The same ownership fix was applied to its fixture before the **complete** 701ce2c rerun; the initial failed attempt is not relabeled successful.

## Real mixer timing and limitations

[Independent timing report](three-agent-evidence/stabilization-v2/timing/REPORT.md) reproduces the exact historical early peak 0.06647 on the **unchanged** original test by suspending the process 150 ms. Official engine sources show Dummy processes 4096 frames (about 92.88 ms at 44.1 kHz), then sleeps for a buffer duration without subtracting processing/scheduling time. Its sample count therefore drifts from elapsed wall time. The old silence window uses wall time as a sample index and includes legitimate first-event samples after a pause.

The correction marks independent AudioEffectCapture counters at each cue/cancel, without using measured onset to align itself. Physics stepping matches 3D audio scheduling; AudioServer locks make counters and playback operations atomic against the mixer. No await occurs while locked. Per-event 90 ms deviation, median −45..120 ms, 60 ms early guard, 80 ms cancellation guard and all amplitude thresholds remain unchanged. Five additional assertions reject dropped capture frames. CSV distinguishes wall timestamps and capture frames.

The final atomic prototype passes 21/21 loaded/suspended cases across reload/cancel/shot, and the exact maintained cancellation test passes 10/10 further serial runs. Muting, failing to stop on cancellation, and an actually early unlogged voice are all caught by negative controls. Intermediate unlocked-frame/physics-only attempts and their real failures are preserved, not counted as final passes.

A broad negative-control wrapper's unmutated audio-cancel baseline later reported FAILED, but its wrapper discarded the raw subprocess cause. That failed wrapper remains retained. Ten exact maintained serial cancellation reruns pass 11 checks each with peak 0; they do not establish universal determinism or erase the unexplained wrapper failure. The new frozen complete matrix and separately recorded maintained negative-control results must be read with this residual qualification. This is not a physical output-latency or listening-quality acceptance.

## Graphics compatibility and independent visual review

[Verbatim graphics review](three-agent-evidence/stabilization-v2/graphics/GRAPHICS_REVIEW.md) includes exact source and native-command receipts, all 232 accepted-frame hashes, contact sheets, selected decisive originals and unsuccessful attempts. Seven local sequences cover sun/shade/backlight/dark and current/calm/still reduced motion. A correct literal `--authority=snapshot` timer-injection sequence validates 20 Hz presentation; an earlier unsupported argument silently took the local path and is expressly discarded. Native captures advance simulated 60 Hz; they do not demonstrate 60 FPS.

The new studio shader compiles. Default plus four patterned finish families render; actual surface audits retain receiver floor 0.30 / metal 1.0 and polymer floor 0.62 / metal 0.30. Inspection has regular world shading, and the actual remote proxy darkens with world illumination removed. Authored first-person anatomy, topology and material detail are not newly created by the shader update.

The receiver shows useful graphite/gloss stability and avoids the broad beige flip in saved frames. Lower normal pickup is a partial improvement, but normal/current 074 still shows magazine before a readable grasp. Consecutive calm 066→067 shows a roughly 200 px magazine pop in one tick. Default reduced current retains full rigged roll/lift; calm has the pop and still moves the rifle high. Shade/dark detail and synthetic hand anatomy remain weaknesses. The independent estimate is **5.5–6/10**, with 8.5 unaccepted. [New source-bound PR2 review](https://github.com/calebaiken/sightbreak/pull/2#pullrequestreview-5543503255) requests concrete corrections; no source-owner branch was edited.

Sequential software-rendered comparison against immediate shader parent f4a retains identical draw/primitives and resource counts: 37,598 viewmodel-node triangles, 5,592,824 compressed imported texture bytes. Ready/mid-reload/flash/smoke medians change −0.40%/+10.18%/−0.71%/−2.97%; P95s are noisy on this shared host. This does not establish a reliable shader-cost percentage or physical mobile performance.

## Multiplayer, economy and acceptance boundaries

Independent static review proves the complete backend and network directories, all 11 marketplace-related files and all 13 Match RPC declaration/signature pairs match the previous integration. Actor/main scripts are identical. Protocol 6, recipient snapshots, authoritative damage/ammo, default-off opt-in prediction, disabled live rewind, actor ownership, bounded admission, ticket replay protection and durable results retain their existing contracts. Independent focused privacy 55, snapshot 15, movement 725 (max error 0.075834 m), peer 16 and PostgreSQL 61 checks pass on the documented baseline; final campaign validation is recorded separately below.

PR15's optional strict expected-price guard remains separately reviewable and unchanged. UI sends the exact captured confirmation price; backend pricing stays authoritative. Atomic mismatch rollback, duplicate/concurrent receipts, exact retries, legacy omission/null fingerprints, wallet conservation and trade revisions remain covered. No backend rollout or main merge is performed. Offline rewards remain training-only; ranked gates remain preserved.

The [independent network receipt](three-agent-evidence/stabilization-v2/network-review/final-campaign-preservation-aee6b73.json) binds static review to aee6; 701ce2c changes only bot lifecycle test teardown. The final native campaign, 12-condition network campaign, export inspection and distribution results are recorded below.

## New complete campaign, native exports and distribution

The new complete frozen matrix is **74/74 PASS** on clean 701ce2c, including source-bound four-/ten-client soaks, all eight protocol pairs, hostile-handshake tests, PostgreSQL/account/outbox/economy, reload capture/cancel/shot/contact, UI and native render/HUD/paint checks. The recursive resource audit finds no ObjectDB/leaked-instance warning in retained child logs, and initial/final source identity and clean state match exactly. [All 74 rows](three-agent-evidence/stabilization-v2/matrix-r2/MATRIX.md), [machine summary](three-agent-evidence/stabilization-v2/matrix-r2/summary.json), [child resource audit](three-agent-evidence/stabilization-v2/matrix-r2/nested-resource-cleanup.json), [frozen identity](three-agent-evidence/stabilization-v2/matrix-r2/source-identity.json).

The final native full bot lifecycle naturally completes 12 rounds in 380.9 simulated seconds, with 78 kills, halftime and exactly one result report. It records `plant_observed=false`; this run does not demonstrate a natural plant/defuse. Targeted objective-timer controls and the separate tactical measurements retain their own narrower acceptance.

This is a **new campaign**, compared with the preserved original **64/70**. Added groups cover simultaneous shot audio, rig contact, nested resource cleanup and final frozen identity. Every former failing group passes in this run. Expected legacy-protocol rejection diagnostics and historical logs copied inside protocol fixtures remain classified negative/history evidence; “74/74” does not mean every archived log contains no ERROR word. The separate earlier broad negative-control wrapper failure remains unexplained, despite the passing final capture/cancel checks and sensitive maintained controls.

The separate frozen **ten-client network campaign passes 12/12**: RTT 0/50/100/150/200 ms, jitter, loss, reorder, combined impairment, blackout, reconnect and prediction disabled. Every condition binds to clean 701ce2c and exits 0 with no assertion failures. The independent audit checks all 132 actual server/client logs and final actor/peer ownership. Measurement windows are 18 seconds per condition on loopback with synthetic impairments. [Complete campaign](three-agent-evidence/stabilization-v2/network-r2-imported/campaign.json).

All three local exports pass actual package/resource inspection and manifest verification. Linux/Android/iOS contain 130/132/130 exported resources respectively; harnesses are excluded, and the required AI, gameplay, network, UI, shader and imported GLB resources are present. [Local build manifest](three-agent-evidence/stabilization-v2/builds/manifest.json), [local SHA256 checksums](three-agent-evidence/stabilization-v2/builds/checksums.txt) and [inspection result](three-agent-evidence/stabilization-v2/builds/verification/results.json).

| Package | Verified scope | Local distributable SHA256 |
| --- | --- | --- |
| Linux debug ZIP | Actual x86_64 ELF, native input and clean exit | `e4d8fdbe9f4192989bc5b66126011d4342f3d270f5815f0e54163fb70f80017c` |
| Android debug ZIP | `com.sightbreak.game`, 0.3.1-dev (4), API 24–36, ARM64/x86_64, landscape, v2/v3 debug signature | `3baa8ca0350fb6139bd64c8fd03bf27128e169a413f20b96564fff9b3b16b75d` |
| Unsigned iOS Xcode ZIP | Marketing 0.3.1, build 4, empty signing team; no IPA or Xcode compilation | `1092056e039c99f1167be7f83cf081b576f54b93525b06243833d95b1405bfee` |

The actual exported Linux client is driven through inventory, LAN connection, movement/aim, **six authority-observed shots**, desktop R-key reload and normal exit. Rifle ammunition falls to 24 and reload completes at 30/84; largest acknowledged input is 1231, protocol 6 and prediction defaults off. Both processes exit 0. The screenshot named `07-after-authority-reload-completion.png` still shows the rendering animation; the later `08-settled.png` visibly confirms 30/84. [Network native receipt](three-agent-evidence/stabilization-v2/native-network-r2/results.json).

The final live offline exported-client run enters 5v5, opens requisition, moves/aims, fires and reloads while alive at 100 health, pauses, returns to menu and exits normally. Independent original-image inspection and the strengthened controller's OCR agree: **sidearm 14/60 → 15/59**, total ammunition conserved at 74. The external controller is a9d873e, SHA256 `30d408a9a92ab10472036a9e589e2e831b5e30bd5edc9cc10fe2dafd74c134c3`, using unchanged frozen 701 game/source helpers. Earlier eliminated/no-fire and short-input attempts are explicitly unsuccessful gameplay evidence. [Live offline receipt](three-agent-evidence/stabilization-v2/native-offline-r2-live-input/results.json). Full manually driven exported match/objective completion remains unverified; the natural full match is covered by maintained native source tests.

The established Actions delivery branch advances only to frozen **701ce2c**. [Run 38858072161](https://github.com/calebaiken/sightbreak/actions/runs/38858072161) completes successfully, with all three exports, package inspection and upload steps passing. The supported GitHub download connector follows the artifact redirect successfully and returns the ZIP file reference. This confirms accessibility; distribution is no longer pending.

**[Download development V2: Android + Linux + unsigned iOS project](https://github.com/calebaiken/sightbreak/actions/runs/38858072161/artifacts/12028135819)**. Artifact 12028135819 is 287,276,825 bytes, aggregate SHA256 **`8f230eab3d953ba40f1981286e71137e07f2ff5548b0ad5eda355c58c9ec5f1e`**, expires **2026-10-30 05:54:03 UTC**. Download before expiry. Its own manifest/checksums bind the CI packages to 701ce2c; a fresh CI Android debug key can change APK hashes, so local package hashes above must not be substituted for CI inner hashes. [Final run](three-agent-evidence/stabilization-v2/actions-v2-final-run.json), [artifact metadata](three-agent-evidence/stabilization-v2/actions-v2-artifacts.json), [download receipt](three-agent-evidence/stabilization-v2/actions-v2-download-receipt.json), [decoded job log](three-agent-evidence/stabilization-v2/actions-v2-job.txt).

[Independent final evidence audit](three-agent-evidence/stabilization-v2/final-review/AUDIT.md) independently rehashes local payloads/source, inspects the live screenshots and verifies network/delivery receipts. It separates source, functional, visual and device acceptance; it does not promote the preview to production.

The static menu banner still reads 0.3.0-dev although project/platform metadata and manifests identify 0.3.1-dev (build 4). This cosmetic integration label remains a known issue for the next source update; the delivered artifact identity is its source/manifest, not that stale banner.

## Remaining release gates and next merge sequence

1. Independently validate Gemini’s after-freeze 48eb058 updates against the retained purchase, navigation, hearing, damage-look and sound-precision controls. Integrate only a verified exact revision, then repeat native tactical samples with stronger engagement/objective acceptance.
2. Claude corrects normal/calm pickup visibility, reduced-motion defaults and low-light material/hand detail; retain the corrected per-part probe materials. Art direction, actual audio listening and human accessibility review remain required.
3. With owner approval, reconcile PR1 and the established **PR3 → PR4 → PR5 → PR6 → PR7 → PR8 → PR10** dependency chain before the PR11/PR16 aggregates. Review PR15 separately with PR12’s captured-price UI payload as a coordinated compatible rollout. PR2/PR14 still require the owner-quality follow-ups above; PR13 documentation remains independently reviewable. Repeat affected frozen gates whenever a dependency changes.
4. Keep PR16 a development draft until constituent reviews and remaining quality/timing concerns are accepted. No part of this report authorizes a merge into main.
5. Physical Android install/touch/accessibility and GPU/frame/thermal testing; macOS/Xcode compile/signing and actual iOS; public Internet security and human gameplay remain UNVERIFIED.

| Acceptance class | Evidence / limitation |
| --- | --- |
| Accepted by independent source review | Narrow API/purchase integration, frozen presentation scope, protocol fixture cleanup, unchanged market/network contracts |
| Accepted by native tests | Exact documented targeted controls and the final source-bound matrix, network and exported-client results above |
| Accepted by controlled native simulation | Recorded seeds/rounds and metric definitions; not a final balance claim |
| Requires human review | Tactical feel, anatomy/art direction, listening quality, motion comfort, accessibility |
| Requires physical mobile testing | Touch, phone performance, battery/thermal behavior, device output latency, Android/iOS platform behavior |
| Failed | Tactical 8.5 and visual 8.5 acceptance; original 64/70 and new unsuccessful attempts stay preserved |
| Unverified | Production readiness, physical-device and Internet-security acceptance; unexplained broad-wrapper cancellation failure remains qualified |
