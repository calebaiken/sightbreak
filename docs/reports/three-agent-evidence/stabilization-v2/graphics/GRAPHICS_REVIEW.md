# Independent graphics review — stabilization V2, frozen Claude 5357329

**Development-preview integration verdict: conditionally suitable as a frozen graphics input. Clean-regression acceptance and the 8.5/10 visual-quality gate remain open.** Native shaders and the revised GLB function correctly in the sampled scenes, and the change does not replace gameplay authority. However, the targeted functional tests retain ObjectDB exit warnings. The hip-pickup change reduces the original problem without fully resolving it, and a separate visible magazine pop is reproducible in the calm reduced-motion variant. Visual quality is around **5.5–6/10**, rather than 8.5/10.

This is a new, read-only assessment of the new source and newly executed native captures. Earlier ratings were not substituted for this review. No shipping/source branch was edited or pushed, and no GitHub review was posted by this reviewer.

## Frozen source and compatibility

Reviewed Claude `5357329fa06136ac0d81b58ace97f872f37bebfa` against previously integrated graphics `ed8575454452d8f67c006814a1917fa6cc24fb46`. The immediate shader parent is `f4a763a3c9712c15ae0c369e4f7ee65adf9d38dd`.

The detached review worktree is `/workspace/sightbreak-stab2-graphics`. Its tracked files remain clean. `source-review.json` records the exact changed files and GLB hashes. The game diff contains the arms GLB, three presentation/material scripts, and three tests. `actor.gd` and `match.gd` are byte-identical to the older Claude graphics checkpoint: no new RPC, combat, ammo, prediction, privacy, admission, ticket or results behavior is introduced by these graphics commits. Integration must retain the existing Codex movement delegation instead of replacing the whole older actor file.

Independent GLB decoding finds the mesh vertex/index payloads unchanged. Changes affect the normal `reload` animation channels, including left-forearm translation and hand/finger rotations; the calm clip is unchanged. This supports treating the update as an animation revision, not an anatomy/modeling improvement. The normal hip target moves from 31 cm to 36 cm below the well, and the carry target also changes.

The former 0.80 metal roughness floor is replaced by a camera-space studio environment plus a 0.30 receiver minimum. The handguard receives a separate material with a 0.62 minimum roughness and 0.30 metallic multiplier. Both first-person surface and cosmetic shaders disable engine ambient lighting and add the studio term. Inspection keeps its separate regular world shader. The studio adds fragment arithmetic, including several power terms, rather than an extra reflection viewport or rendering pass.

## Executed evidence

Godot 4.7.2, native OpenGL compatibility, Mesa llvmpipe software rendering, 1280×720. Toolchains were reused. Review displays were 102, 103 and 104; existing displays were left alone. Native command receipts, exact arguments, source identities, exit codes and timings are in `native-runs.json`, `surface-run.json`, `calm-first-draw-run.json` and `supplemental-runs.json`. `capture-manifest.json` hashes 232 accepted original PNG artifacts.

| Check | Observed result | Gate interpretation |
| --- | --- | --- |
| Network-enabled editor import | Completed without engine errors | Pass |
| Native `weapon_art_test.gd` | 179 assertions, 0 failures; **8 ObjectDB instances leaked at exit** | Functional pass; clean-exit gate fails |
| Isolated headless `reload_sequence_test.gd` | 92 assertions, 0 failures; **32 ObjectDB instances leaked at exit** | Functional pass; clean-exit gate fails |
| Seven native reload sequences | Sunlit, shade, backlight, dark, reduced current/calm/still; 168 simulated ticks each; final ammo 25/70 after five shots | No shader errors or ObjectDB warnings in these capture logs |
| Correct 20 Hz timer-injection sequence | Literal `--authority=snapshot`; 168 simulated ticks; final ammo 30/70 | Presentation fixture passes; no live-network claim |
| Independent surface probe | Default and four patterned finishes at three poses, two remote-world lighting states, three inspection cases | 20 clean native captures; actual per-part material state recorded |
| Existing weapon-art capture | Eight native first-person/inspection stills | Clean capture log |
| Consecutive calm first-draw capture | Frames 66/67/68/69, from a 72-tick partial reload | Reproduces visible magazine spawn in one tick |

The 92 functional reload assertions include magazine identity, grip/contact, cancellation before/after seating, round reset, weapon switching, ammunition/timer authority, and local/snapshot/jitter/regression presentation clocks. They are implementation checks and do not establish visual quality. The leak warnings are retained verbatim; this reviewer has not attributed them to new shaders or resolved them. Audio implementation did not change in these graphics commits. The primary leak investigation remains necessary.

Two unsuccessful/setup attempts are preserved. Initial sandbox-restricted editor import emitted socket errors; the accepted import is the network-enabled rerun. An initial sequence used unsupported `--authority=snapshot20hz`, which the fixture silently treated as its local path. Its `snapshot20hz/` output is **discarded as snapshot evidence**. `snapshot-correct/` uses the supported literal and is the accepted rerun. Neither unsuccessful attempt was deleted or reclassified as a product pass.

The native sequences advance real actor logic at a fixed simulated 60 Hz and save 25 stages, with extra stages around hip retrieval. They do not demonstrate real-time 60 FPS. Only the narrow calm first-draw run saves consecutive ticks at the exact transition. No APK/iOS executable, physical phone, mobile GPU, battery/heat behavior or audio listening test was performed by this reviewer.

## Visual strengths in the new source

The receiver remains a coherent dark finish through the saved sunlit reload stages, with restrained edge highlights and a more distinct glossy edge on the magazine. There is no obvious broad pale/beige receiver flip in the inspected native stages. The new response avoids depending on the previous uniformly rough 0.80 finish. Default and Obsidian, Crimson Archive, Spectral Circuit and Blacksite patterns render successfully; their colors and patterns remain recognizable across ready/insertion/return. Actual audit values confirm that the receiver and handguard retain distinct materials, rather than only testing the shader text.

The native skin probe covers Obsidian/Rare at wear 0.1, Crimson Archive/Legendary at wear 0.05, Spectral Circuit/Epic at wear 0.45 and Blacksite/Mythic at wear 0.8. Rarity is metadata/UI classification, not proof of a separate expensive shader. The receiver's 0.30 minimum preserves substantially more of the finish's authored gloss range than the previous 0.80 floor. The handguard's intentionally rougher first-person material remains separately configured for every tested finish. Visual material quality is still simpler than a convincing high-fidelity coated-metal surface.

The normal revised pickup is lower than the old one. At equivalent frame 074, the new magazine's top begins about 30 pixels lower than in the archived prior capture, and by new frame 078 a gripping portion of the hand is visible. Thus this is a partial improvement in staging; it should not be described as unchanged or as fully fixed.

Two distinct magazines, their discard/replacement order, the visible grasp at insertion, and return to a seated magazine remain coherent. The native timer-injection sequence retains equivalent poses without a visible material/program fallback. Inspected normal/current/calm/still insertion stages do not show a new large hand-to-magazine separation or obvious mesh clipping.

Inspection captures use the regular world shader with no first-person position override. The real remote actor's existing lightweight world proxy responds to world illumination and becomes dark when direct/ambient/reflection lighting is disabled; the new studio does not accidentally illuminate that proxy. The remote proxy is not the detailed authored/skinned first-person rifle, so this is not a claim that detailed third-person cosmetics were added or verified.

## Remaining actionable issues

### P2 — normal/current pickup still shows magazine before the grasp

Inspect [new sunlit 074](/workspace/reviews/stabilization-v2-20261016/graphics/sunlit/074.png) and [reduced current 074](/workspace/reviews/stabilization-v2-20261016/graphics/reduced-current/074.png). At progress 0.5556, a substantial part of the replacement is visible while the fingers holding its base remain below the viewport. Sleeve pixels at the lower-left do not make the grasp readable. New [sunlit 078](/workspace/reviews/stabilization-v2-20261016/graphics/sunlit/078.png) begins to show the holding hand. The artifact is shorter/lower than before, but the unsupported-looking phase still exists.

This remains a projection/staging problem, not proof that the magazine is detached in 3D. [Actor's hand transform](/workspace/sightbreak-stab2-graphics/game/scripts/gameplay/actor.gd:1191) drives the replacement during the held interval. Restoring the first-draw `< 5%` assertion measures the first visibility tick only; it does not prove that the subsequent rise includes a visible grasp. Correct the path/framing together and verify the visible hand/magazine relationship throughout pickup, not just at the first drawn tick.

### P2 — calm reduced-motion variant spawns a large magazine visibly in one tick

The new consecutive native pair is decisive: [frame 066](/workspace/reviews/stabilization-v2-20261016/graphics/calm-first-draw/066.png) shows empty fingertips near the lower edge; [frame 067](/workspace/reviews/stabilization-v2-20261016/graphics/calm-first-draw/067.png), one simulated tick later, shows a replacement extending roughly 200 pixels upward into the viewport. The CSV changes from `new_drawn=0` to `1` at progress 0.5037 and emits the pouch cue. There is visible hand contact, but the object appears abruptly in view.

[Replacement visibility is toggled at ACQUIRE](/workspace/sightbreak-stab2-graphics/game/scripts/gameplay/actor.gd:1209), and the calm clip's pickup position is already inside the picture. The new normal-path first-draw assertion does not validate this variant. Coordinate the visibility event and retrieval staging for each clip, and add a meaningful variant-specific first-draw check. This is inherited calm behavior newly verified here, not a claim that f4a changed the calm asset.

### P2 — the shipped reduced-motion default still keeps full rigged reload roll/lift

The default remains `current`, whose [roll/lift/recoil multipliers are 1.0](/workspace/sightbreak-stab2-graphics/game/scripts/gameplay/actor.gd:139). New current captures retain the normal whole-rifle reload motion. Sway, bob, equip swing and seat kick have separate reductions, so the setting does have an effect; the rigged reload roll/lift themselves remain full amplitude.

Calm visibly reduces roll and keeps the hand/magazine relationship more readable at pickup, but has the confirmed appearance pop above. Still removes roll while shifting the weapon much higher into the upper-right. Neither fact is sufficient reason to switch the default without correcting/reviewing the complete action. No claim of clinical comfort or vestibular safety follows from these images.

### P2 — finish-stability probe overwrites the shipped polymer handguard material

The existing [probe resets both receiver and handguard to `actor._finish`](/workspace/sightbreak-stab2-graphics/game/tests/reload_discolour_probe.gd:314) before each condition, including `base`. New [CosmeticMaterial.apply](/workspace/sightbreak-stab2-graphics/game/scripts/ui/cosmetic_material.gd:75) deliberately clones the finish for the handguard and changes roughness/metallic parameters. The probe consequently discards that clone and measures a handguard with receiver settings. A passing base luminance/hue result cannot be claimed as validation of the shipped receiver-versus-polymer pair.

Preserve/restore each part's actual base material when applying experiments. The independent surface captures in this review retain the real clone and audit receiver floor 0.30/metal scale 1.0, handguard floor 0.62/metal scale 0.30. The defect is in validation fidelity; it is not evidence that normal gameplay loses the clone.

## Remaining art-quality limitations

Shade and dark frames still suppress glove/receiver detail strongly. Compare [shade 090](/workspace/reviews/stabilization-v2-20261016/graphics/shade/090.png) and [dark 090](/workspace/reviews/stabilization-v2-20261016/graphics/dark/090.png) with sunlit 090: the grip, glove and receiver become a dark group with limited construction detail. Backlight adds clear rim/tube highlights, but the broad receiver remains simple. The studio is deliberately camera-anchored rather than a physical reflection of the yard. Its continued key/gloss in dark conditions is not a shader compilation error; the resulting readability/world-light balance still needs art direction. It did not look like an extreme white/emissive weapon in these captures.

The rounded right gripping fingertips and broad, flattened open left palm/finger fan remain visible at [sunlit 118](/workspace/reviews/stabilization-v2-20261016/graphics/sunlit/118.png). The GLB mesh comparison confirms that these shapes were not remodeled. New shader stability and altered pickup depth do not establish better anatomy. Refine phalange/knuckle planes, thumb/palm volume, finger spacing and return curl while preserving the existing successful grasp contact.

These observations explain the approximately 5.5–6/10 visual estimate. The finish/staging changes make useful, specific progress, but they do not close the anatomy, low-light detail, default reduced-motion and pickup issues. The 8.5 gate is not accepted.

## Shader cost and practical limits

`performance-comparison.json` compares immediate parent f4a with 535 sequentially on the same review display, so both sides use the revised GLB and differ in the shader/material update. Ten rendered samples per state, after warmup, at 1280×720 on llvmpipe:

| State | Before median ms | After median ms | Delta |
| --- | ---: | ---: | ---: |
| Ready | 251.506 | 250.500 | -0.40% |
| Mid reload | 244.015 | 268.850 | +10.18% |
| Flash | 273.193 | 271.250 | -0.71% |
| Smoke | 245.381 | 238.099 | -2.97% |

Draw calls and primitives are identical in each corresponding state. Both have 37,598 total viewmodel-node triangles, 5,592,824 compressed imported texture bytes, and a 12 µs median `tick_visual` reload cost in the probe. Those are not total GPU/VRAM costs. P95s are noisy on this shared CPU host (for example ready after 466 ms versus before 270 ms); the experiment does not establish a reliable shader-overhead percentage. It neither proves a broad performance regression nor clears target-device cost. The fragment arithmetic should receive an actual mobile GPU profile before a mobile-performance claim.

## Acceptance boundary

The frozen presentation source is compatible enough for the lead integrator to carry into a development checkpoint while preserving existing authority and recording the warnings/findings. It is not a clean-regression signoff, production acceptance, complete visual-quality acceptance or mobile-performance acceptance. Keep the 8/32 ObjectDB warnings, the four actionable findings above, and actual device/export checks visible in the new campaign. Do not rewrite prior failed evidence or the historical 64/70 result.

## Integration follow-up received at review close

The lead integrator has carried frozen 5357329 into checkpoint `aee6b7396928489662eb9917c7e403a1a00a21af` and is running its separate full campaign. Narrow integration commit `b5ad8c8` saves/restores `paint_original[part]` in the lighting probe; this reviewer independently inspected that patch and confirms it addresses the base-material clobber described above. The source-owner PR #2 still needs the equivalent test correction if it is not brought forward there.

The lead also reports a demonstrated test-harness deferred-mixer ownership cause for the ObjectDB warnings, with clean isolated/loaded runs after explicit world deletion and a 0.5-second mixer drain. Those integrated reruns are the lead's evidence, not executions performed by this graphics reviewer. This frozen-source report retains its original 8/32-warning reproductions and does not recast them as a shipping audio-source defect. The separate full integrated campaign, rather than this report, determines final clean-regression status. Visual findings and shared-host performance limits above remain unchanged.
