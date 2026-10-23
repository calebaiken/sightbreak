# Independent graphics integration review

**Recommendation:** keep the combined build as a development preview. The default rigged weapon path has passed the technical checks below. The visual 8.5/10 gate is **not met**; do not present PR #2 or this preview as polished or release ready. Fix the fallback projection before claiming the static fallback is supported. Production device performance remains **UNVERIFIED**.

Reviewer: a separate Codex agent, independent of Claude's author/reviewers. This is not a human acceptance review or a physical-device graphics audit. No tracked files, art assets, shader source or source PR branches were changed by this reviewer. External fixtures and counterfactual captures are clearly marked.

## Exact inputs and environment

- Initial PR #2: `8c18357e3a8045599ea3a805c115c5bebc76f97b`.
- Initial combined tree: `e896c81e11e407517d7e99c3fd94ff0317e6c823`.
- Refreshed PR #2: `64ec59884e22f6b71179c585e4679ae6e3b2f87c`.
- Refreshed combined source: `d084e5003ac915550c368a86176df9063375bb59`. Source SHA and game-tree ID are recorded with the captures.
- Linux; Godot 4.7.2 stable `ed1daf0bf`; Compatibility OpenGL 4.5; Mesa 25.0.7 llvmpipe, LLVM 19.1.7; Xvfb `:99`; Dummy audio. These are native engine captures under software rendering, not phone GPU or physical-input measurements.

**Aspect caveat:** the art fixtures set `root.content_scale_size` to the requested ratio. Their 20:9 and 4:3 images are real native renders at those sizes, but they explore a filled viewport; they do not establish the shipped default keep-aspect behavior. The parent integration report handles actual keep/expand policy probes. No shipping stretch policy was changed.

## Confirmed integration behavior

The initial combined `actor.gd` diff against PR #2 contains only the existing Codex `SBMovementStep` constant aliases and movement delegation. Claude's weapon/pivot/muzzle/ejection, rig and shader interfaces remain intact. The refreshed staging change affects visual offset/rotation only. Movement, ammunition, reload duration, damage and economy remain outside animation authority.

The projection scales both X and Y by positive zoom derived from `abs(PROJECTION_MATRIX[1][1])`, preserving aspect and renderer Y sign. Depth compresses monotonically toward reversed-Z near plane `z=w`, preserving the model's own depth ordering. Native depth tests confirm that the weapon is not occluded by nearby world surfaces and that its apparent projection is independent of the world FOV. This does not validate untested Vulkan, Metal or mobile drivers, or geometry crossing behind the eye.

World/inspection paint has a separate shader with no POSITION override. The first-person body, paint, rigged arms and muzzle flash use the narrower projection. Native pixel tests confirm that the earlier vanished inspection/procedural paint regression is fixed.

## Executed checks

| Check | Source | Result |
| --- | --- | --- |
| Maintained weapon-art contract | PR #2 `8c18357` | 69/69 assertions; two audio objects at immediate test exit |
| Maintained weapon-art contract after refreshed staging and audio drain | Combined `d084e500` | 73/73 assertions; no ObjectDB warning |
| Independent 30-cycle equip/reload/reset, death and respawn fixture | `8c18357`, combined `e896c81`, combined `d084e500` | 183/183 each; authority values invariant under visual ticks at 30/60/120 Hz; removed animation players freed |
| Native paint visibility | Both combined heads | 4/4 each: inspection skin 59,824 changed pixels; default 56,548; procedural sidearm 11,716; authored rifle 39,736 |
| Native projection/depth stress | Combined `d084e500` | 18/18: world FOV 42/82/110 degrees and opaque world surfaces 0.30/0.10/0.055 m from eye; 102,532 visible weapon pixels each; zero image differences across the nine conditions |
| Native stills before staging fix | Combined `e896c81` | 16 captures, eight each at 1280×720 and 1600×720 |
| Native stills after staging fix | Combined `d084e500` | 24 captures, eight each at 1280×720, 1600×720 and 1024×768; sizes independently checked with Pillow |
| Native motion fixtures | Combined `d084e500` | Nine sequences, 115 frames each (1,035 total), covering sunlit/backlit/shade at all three sizes; all exits 0; source SHA unchanged across batch |
| Motion state review | Combined `d084e500` | All nine CSVs: ammunition 30 → 23 during burst → 30 only at completed reload; final clip time and reload remaining both zero; no early ammunition credit |
| Magazine vertex/framing probe | Combined `d084e500` | All 1,497 magazine vertices inside frame at 14% and 84% reload in all three aspects; 14% margin is only 3.79 pixels at 720-pixel height |
| Synthetic replicated reload clock | Combined `d084e500` | 120 visual ticks, 40 pose-time changes and 80 held poses with 20 Hz authority updates; no live-network smoothness acceptance claimed |

All nine motion sequences, CSV state logs, contact sheets and derived MP4s are enumerated by `motion-summary.json`; the final capture runner log records each completed invocation. MP4 frame rate is **30 frames per second of simulated fixture time**, not measured runtime FPS. Source PNGs are retained. Contact sheets preserve aspect ratio and label simulated state. They support frame-sequence inspection, not human input-feel acceptance.

The initial runner was intentionally stopped after its second completed still fixture when PR #2 advanced. Its exit 143 is an orchestration stop, not a failed game run. No old-head motion run occurred.

## Findings and classification

### A1 — Static fallback hands have the wrong projection

**New PR #2 regression. Nonblocking for the default rigged preview; blocks claiming fallback fidelity.**

`game/scripts/gameplay/weapon_model.gd:515` binds static-hands ORMMaterial3D while the rifle uses a 54-degree projection and the world camera uses 82 degrees. Trigger: `SBWeaponModel.use_rigged_arms = false`, or omit the rigged-arm resource while keeping the static fallback. Native `fallback/02-current-static-fallback.png` shows the support hand floating ahead of the muzzle and the firing hand detached to the left of the receiver. `fallback/03-static-matched-projection-counterfactual.png` uses the same geometry/textures with the first-person shader assigned at runtime; the hands reconnect. The procedural-glove fallback likewise uses regular world-projection materials.

Required correction: apply the same first-person projection to every attachment in an authored first-person build. Add a material-contract assertion and native fallback capture; the current existence-only fallback test misses this. The counterfactual did not edit any source or asset.

### A2 — Test-exit WAV objects were an audio-drain issue

**Nonblocking test-harness issue; corrected in the combined test.**

Verbose initial test output identifies one AudioStreamWAV and one AudioStreamPlaybackWAV, not OpenGL textures. An identical external test copy with a 0.2-second post-free drain passed all assertions without warnings; the combined maintained test now includes that drain and passes 73 checks cleanly. The 30-cycle lifetime fixture also clears without warnings. This is evidence for asynchronous audio teardown timing, not proof of a persistent gameplay resource leak. No texture-leak warning occurred in this review's native fixtures.

### A3 — The rigged-arm PackedScene is not retained

**Nonblocking optimization/documentation issue.**

`ResourceLoader.has_cached(RELAY_AR_ARMS)` is false immediately after build. `_add_arms` loads and instantiates without retaining the PackedScene; the resource cache is weak. Repeated equip verbose logs show the scene being loaded again, so the comment that the PackedScene remains cached is inaccurate. Consider retaining the immutable PackedScene if equip/load measurements justify it. No mobile hitch cost or FPS impact has been measured.

### A4 — Reload staging is improved, with narrow framing margins

**Confirmed fix; remaining visual limitation.**

The previous mid-reload hand/magazine were below frame. Refreshed native grabs now show both, and independent projection of every actual magazine vertex confirms the 14% and 84% claims at all three tested ratios. The maintained test checks a wrist and bottom-center point; it does not itself prove that every vertex is inside. At 15%, 36 of 1,497 magazine vertices fall below the viewport by at most 2.80 pixels at 720 height. Mid-swap intentionally leaves the frame. This is a substantial staging correction, with little margin for additional bob/sway. Moving/reduced-motion variants were not visually accepted here.

### A5 — Online skeletal reload presentation remains quantized to snapshots

**Pre-existing timer-presentation limitation, amplified by the new rig; nonblocking for a preview.**

`match.gd` receives reload time at 20 Hz and does not advance a separate presentation timer. `actor.tick_visual` seeks the clip directly from that value. An independent synthetic callback fixture produced only 40 pose-time changes over 120 visual ticks. Offline authority-driven motion captures cannot prove online animation smoothness. A future fix should interpolate/advance a bounded visual clock while keeping authoritative reload duration, ammunition, cancellation and completion unchanged.

### A6 — Visual quality remains below the required gate

**Blocking for the 8.5 visual acceptance milestone; nonblocking for making a diagnostic preview build.**

The five largest observed weaknesses are:

1. Ready composition: the bore vanishing point is `(515.806, 374.349)` against a `(640, 360)` center at 1280×720; the support wrist is 0.875 m from the eye. The rifle reads as displayed sideways, with an extended arm.
2. Hand/glove/sleeve shape: broad mitten-like grip, rounded finger segments, smooth tan surfaces and regular sleeve rings; fine glove construction is not readable at actual capture scale.
3. Lighting/material separation: the graphite receiver and support arm become hard to distinguish in shade; backlit edges become much brighter than the broad dark surfaces.
4. Framing and inspection: the firing side is heavily cropped at 4:3; reload staging is improved but the action leaves frame mid-swap; the pre-existing inspection viewport downscales large layouts (`stretch_shrink = 2` at 1280×720).
5. Presentation consistency: flat star muzzle flash, box casings and block-like environment detailing sit beside a much more detailed rifle. The cosmetic stripe finish is visibly simpler than the geometry it covers.

These judgments are from actual rendered images and frame sequences, not triangle counts or the mere presence of a rig.

## Visual rubric: weapon/arms integration slice only

Anchors: 5 = blockout/rough presentation; 7 = coherent alpha; 8.5 = consistently polished; 10 = exceptional. This does not rescore operators, the full map, HUD, competitive play, or untested device behavior.

| Category | Score | Evidence-based reason |
| --- | ---: | --- |
| Geometry/composition | 6.0 | Recognizable detailed carbine; weak ready alignment and reach, cropped firing side |
| Materials/surfaces | 5.5 | Real surface maps and highlights; glove/sleeve read simply, default receiver loses detail in shade |
| Lighting | 5.0 | Functional world response and viewmodel fill; large sun/shade readability gap |
| Models/animation presentation | 5.5 | Rig and staged grab/seat are useful improvements; hand shape and off-screen middle action remain rough; online timing limitation |
| Effects/cosmetic presentation | 4.5 | Functional skin and inspection restored; flat flash/casing and broad skin bands |
| Identity/consistency | 5.5 | Graphite/crimson/gold remain; detail mismatch between rifle, hands and world |
| Competitive visual readability | 6.5 | Center mostly clear and depth projection stable; bore/aim mismatch and weak shade contrast |

**Approximate mean: 5.5/10.** This subjective slice score is not a whole-game score or a replacement for technical tests. It does not meet 8.5. Input feel, mobile GPU frame pacing, thermal/battery cost, Metal/Vulkan behavior and live-network animation smoothness remain **UNVERIFIED**.

## Integration guidance

Preserve the `SBMovementStep` delegation and Claude's viewmodel/pivot/rig code together. Fix A1 in Claude's graphics branch; keep future visual clock work separate from authoritative timers. Existing contract checks establish node/material/authority behavior, not production art quality. The default rigged path is suitable for continued isolated integration and physical-device testing once the parent report's full regression/build gates are met. This review does not authorize a merge.

## Reproduction files

Run from the frozen combined worktree, after resource import, with the repository's `scripts/godot.sh` wrapper:

```bash
scripts/godot.sh --headless --script res://tests/weapon_art_test.gd
scripts/godot.sh --headless --script /workspace/reviews/integration-20261013/art-independent/actor_art_lifecycle.gd
DISPLAY=:99 scripts/godot.sh --audio-driver Dummy --script res://tests/paint_visibility_test.gd
DISPLAY=:99 scripts/godot.sh --audio-driver Dummy --script /workspace/reviews/integration-20261013/art-independent/projection_render_test.gd
DISPLAY=:99 scripts/godot.sh --audio-driver Dummy --script /workspace/reviews/integration-20261013/art-independent/fallback_projection.gd
```

`native-captures.sh` records all sizes and motion views. `package_motion.py` only derives labelled sheets and H.264 videos from the saved native PNGs; it does not generate game art. Audio is not assessed in the silent derived videos. `projection_contract.gd` projects actual magazine vertices; `replicated_reload_clock.gd` reproduces the held presentation clock without pretending to be a live-network playtest. Logs and source scripts are included for reproduction.

## Independent performance addendum — recorded campaign review

This performance assessment is a separate same-model-family review of the parent Codex profiling work, not an external performance audit. This addendum reviews the completed `profile-pr1`, `profile-combined`, `scenario-profile/run-{1,2,3}` and `weapon-cost.log` recordings and their harness source. No new render or benchmark was started by this reviewer. Inputs are fingerprinted in `performance-assessment.json`. The runner pins Godot to CPUs 0 and 1 with two Mesa workers, but CPU affinity is not exclusive ownership of a shared host. These numbers are wall frame time under llvmpipe, not GPU timing, phone FPS, battery or thermal evidence. The metrics files do not themselves embed a commit SHA; preserve their campaign/source binding in the parent evidence manifest.

### Fixed-camera PR #1 versus combined comparison

Three runs per head, 24 measured frames per view after eight warmup frames, standard quality, 1280×720. The authored-gun views show a consistent resource increase; gun-hidden controls help distinguish it from a general scene slowdown.

| View | PR #1 median of medians (ms) | Combined (ms) | Change | Draw delta | Primitive delta |
| --- | ---: | ---: | ---: | ---: | ---: |
| approach | 447.422 | 558.426 | +24.81% | +2 | +33,078 |
| site | 401.768 | 509.083 | +26.71% | +2 | +33,078 |
| overview | 388.768 | 392.567 | +0.98% | +0 | +0 |
| operators | 428.248 | 433.757 | +1.29% | +0 | +0 |

Godot-reported texture residency increases from 55,942,068 to 61,538,676 bytes: **+5,596,608 bytes (+5.34 MiB)** in every view, including gun-hidden views because the authored resources remain loaded. CPU static allocations increase by about 802 KB. These are resource counters, not physical GPU VRAM/RSS measurements. The fixed draw/primitive/texture counts repeat exactly across all three runs.

The near-identical gun-hidden geometry and roughly 1% timing changes support a relative software cost associated with the authored viewmodel in the gun-visible views. They do not establish a mobile performance regression of the same magnitude. Combined site p95 reaches 648.101 ms in one run despite medians of 507.611–509.960 ms; retain tails and run ranges rather than reporting one precise universal frame time. First presentation is especially cache/scheduling sensitive (PR #1 approach 1,005–6,714 ms, combined 1,186–2,911 ms) and was not decomposed into shader compilation versus other work.

### Eight scenario measurements and their limits

| Scenario | Median of run medians (ms) | Run median range (ms) | Reported draw calls | Reported primitives |
| --- | ---: | --- | --- | --- |
| empty-yard | 285.572 | 245.596–505.766 | 23 | 37,452 |
| authored-idle | 391.557 | 382.442–897.284 | 30 | 73,554 |
| reload-pose | 489.132 | 364.299–728.579 | 30 | 73,554 |
| six-smoke-clouds | 1905.706 | 1062.908–2043.866 | 72 | 94,506 |
| live-ten-actor-bots | 703.358 | 245.826–725.146 | 24/25 | 38,708/39,668 |
| interactive-inspection | 58.896 | 31.089–164.331 | 8 | 20,038 |
| case-reveal-fixture | 20.164 | 13.239–50.412 | 17 | 18,112 |
| market-20-fixture-listings | 29.888 | 21.206–43.895 | 48 | 6,350 |

Across scenarios, run medians vary by **1.9× to 5.3×**. Draw, primitive, texture and node counts are stable for the fixed fixtures, while wall time is much less stable. The scenario runs are useful for locating expensive software workloads and checking resources, not for narrow performance acceptance thresholds. A p95 from 24 samples is effectively the second-largest sample and cannot characterize rare stutters.

**Active versus idle:** the inspection callback increments yaw and calls `_request_render()` on every `_frame`. Case progress goes through its property setter, which updates transforms and requests rendering; its real-time tween is killed and progress is explicitly advanced every frame. Therefore these two scenarios are actively rendering, not timing a cached idle viewport. However, source and native screenshots confirm the inspector occupies only **250×240 pixels** and the case **260×240 pixels** at the top left of a 1280×720 window. The outer window size must not be presented as their effective 3D render resolution or full-screen UI cost.

The 24 measured case frames cover only part of the opening cycle. With initial progress 0.8 and a 0.025 advance per frame, first/warmup frames wrap it to about 0.025 before sampling; samples then span about 0.05–0.625. Much of that interval has the reward hidden. The final draw/primitive values are one last-frame counter, not a per-frame distribution or the maximum full-reveal cost. Record actual viewport sizes/progress and use a full-cycle sample window for a stronger future comparison.

**Reload:** `reload-pose` freezes `reload_remaining` at half duration. The actor visual tick runs, but after the initial seek/warmup `_arms_time` stays constant and the AnimationPlayer does not seek each sample. Its 71–80 microsecond visual-tick medians across idle/reload/smoke therefore exclude advancing the complete reload animation and GPU skinning; they cannot establish animation overhead for a moving clip. Label it as a held-pose rendering measurement, or advance a separate fixture progress variable for future active-reload profiling.

**Bots:** the ten-actor match runs real offline AI/physics. Its local viewpoint faces a wall in the saved image; only 24–25 draws and 38,708–39,668 primitives are visible at the sampled end. It is not ten visible combatants, ten network clients, or a worst-case battle view. Live state and accumulated physics work can differ between runs. Fixed visible actor placement and a seeded trajectory would make graphical comparisons stronger.

**Smoke:** six stationary clouds increase draws from 30 to 72 and primitives from 73,554 to 94,506 versus the authored fixture. Texture residency changes by only 21,844 bytes, while software wall time increases greatly. This is consistent with a costly transparency/fill workload; no GPU profiler here separates fill, sorting, blending or other costs. Six overlapping clouds deserve device profiling, not an invented phone FPS estimate.

**Marketplace:** this is a static synthetic 20-listing page. It measures UI rendering/layout with no backend request, scrolling interaction or transactions. It does not validate marketplace latency or transaction integrity. Resource memory is process-wide after prior scenarios and caches, so values cannot be summed as independent per-scene allocations or interpreted as a leak series. Nodes drop from 401 in the bot scene to 21 in inspection, which supports cleanup of that transition but is not a soak/leak proof.

### Separate weapon variant benchmark

The authored versus procedural resource delta repeats the fixed-camera result: **+2 draw calls and +33,078 primitives** (28/40,476 to 30/73,554). This is the strongest reproducible comparison in that fixture. The authored wall-time median is 498.878 ms versus procedural 287.746 ms, but round medians have wide ranges (authored 372.175–507.140; procedural 270.353–381.731). Do not mix these timings with the other camera workload.

The static-hands versus rigged result (501.800 versus 498.878 ms, +872 primitives for the rig) **does not establish that skeletal animation is free or faster**. The static fallback has the projection mismatch documented in A1, so the two variants do not cover the same pixels or perform the same shader work. Both are idle; the reload clip does not advance. Also `rounds_ms` is sorted before serialization, losing chronological round identity and preventing a paired per-round noise analysis. Retain per-round order and match projection/material coverage before attributing a delta to skinning.

### Performance acceptance

The supplied render campaign records `network-native` as a failure for clients 0 and 1; its successful scenario/profile steps do not convert that into a passing rendered-network acceptance result. Use the parent networking review for diagnosis and any later rerun. This addendum does not supersede that failed record.

**Performance quality gate: UNVERIFIED for target devices.** The resource increase and software-relative costs are measured, while active full-size inspection/case cost, advancing reload evaluation, worst-case visible combat, GPU frame time, thermal behavior, battery use and physical touch responsiveness still require appropriately scoped evidence. No performance score of 8.5 is supported by these data alone.
