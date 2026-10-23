# SIGHTBREAK — Gemini Development Division Status & Cross-Model QA Report

## 1. Development Slice Summary (Tactical AI v1)

- **Branch**: `gemini/tactical-bot-intelligence-v1`
- **Base Branch**: `claude/independent-audit-visual-v04`
- **Base Commit SHA**: `148760e19ae14755ced379245df6c5510ad4cdd4`
- **Changed Files**:
  - `game/scripts/gameplay/bot_ai.gd` (+ `game/scripts/gameplay/bot_ai.gd.uid`) — Modular `SBBotAI` tactical intelligence system.
  - `game/scripts/gameplay/match.gd` — Narrow delegation of `_bot_input`, `_nearest_defender`, `_cover_position`, and damage/elimination/round hooks to `SBBotAI`.
  - `game/scripts/gameplay/arena.gd` — Hardened `RelayYard.bot_navigation()` with nearest-waypoint fallback when `from` or `to` lies inside an expanded obstacle AABB.
  - `game/tests/bot_ai_regression_test.gd` (+ `game/tests/bot_ai_regression_test.gd.uid`) — Dedicated AI regression and negative-control test suite.
  - `scripts/validate.sh` — Registered `bot_ai_regression_test.gd` in the headless validation runner.
  - `docs/ai/TACTICAL_AI_ARCHITECTURE.md` — Architecture and shared-file contract documentation.
  - `docs/ai/BOT_BEHAVIOR_QA.md` — Baseline vs. improved evaluation, test coverage, and QA scorecard.
  - `docs/ai/GEMINI_DEVELOPMENT_STATUS.md` — Cross-model review of PR #2 (Claude graphics) and Codex compatibility assessment.

### Cross-Branch Compatibility Verification (Codex & Claude Tracks)
- Checked `game/scripts/gameplay/match.gd` across Codex's networking stack (`codex/state-privacy-v2` PR #3 through `codex/network-lifecycle-v2` PR #5, `codex/reconnect-recovery` PR #10, and `integration/sightbreak-reliability-refresh` PR #11).
- Codex's changes in `match.gd` touch network peer lifecycle, snapshot privacy (`SBStatePrivacy`), and input buffering, leaving `_bot_input`, `_nearest_defender`, and `_cover_position` untouched.
- By isolating all new AI logic inside `game/scripts/gameplay/bot_ai.gd` and keeping `match.gd` changes strictly confined to the bot methods and 1-line hooks, `gemini/tactical-bot-intelligence-v1` avoids merge collisions with both Codex's networking PRs (#3-#11) and Claude's graphics/UI PRs (#2, #12, #13).

---

## 2. Independent Technical & Visual Review of Claude's Graphics Work (PR #2)

### Reviewed Target
- **Pull Request**: PR #2 — `claude/cs2-fidelity-art-production` ("Graphics slice: Relay AR rifle, rigged arms v3 and viewmodel projection")
- **Reviewed Branch Head SHA**: `ed8575454452d8f67c006814a1917fa6cc24fb46` (through `art-v9`)
- **Base Commit SHA**: `148760e19ae14755ced379245df6c5510ad4cdd4` (`claude/independent-audit-visual-v04`)
- **Evidence Inspected**:
  - Source files: `game/scripts/gameplay/actor.gd`, `game/scripts/gameplay/weapon_model.gd`, `game/scripts/gameplay/viewmodel_shading.gd`, `game/scripts/gameplay/reload_phases.gd`, `game/scripts/gameplay/reload_audio.gd`, `game/scripts/ui/cosmetic_material.gd`, `tools/art/relay_ar_arms.py`, `tools/art/relay_ar.py`, `tools/art/arms_build.py`, `docs/art/VISUAL_QA.md`.
  - Captured frame sheets & closeups (`docs/reports/media/art-v9/`): `before-after-sunlit.jpg`, `before-after-shade.jpg`, `before-after-backlight.jpg`, `hands-closeups-before-after-2560.jpg`, `idle-hand-before-after-2560.jpg`, `glove-preview-construction.jpg`, `variants-ticks-1280.jpg`, `hipstrip.jpg`, `pouch-vs-offscreen-hip.jpg`, `first-shots-135-144.jpg`, `perf-probe.txt`, and `metrics.json`.

---

### 2.1 Independent Category Assessment of PR #2 (`ed857545`)

| Category | Independent Score | Claude Self-Score (`VISUAL_QA.md`) | Assessment Summary |
| :--- | :---: | :---: | :--- |
| **Hand & Glove Anatomy** | **4.5 / 10** | 4.8 - 5.2 / 10 | SDF capsule/metaball finger chains lack distinct phalangeal planes; right grip hand back reads as a smooth putty mass; left support hand opens into a rigid flat palm-up fan (`#54`, `#118`). |
| **Material Differentiation & Lighting** | **5.0 / 10** | 5.5 - 6.2 / 10 | Clamping `METAL_ROUGHNESS = 0.80` fixed sunlit horizon reflection discoloration during reload roll, but flattened the machined receiver into matte plastic identical in luma (`70`) to the polymer handguard; shade/backlight crushes all parts into luma `24-42`. |
| **Reload Mechanical Staging & Animation** | **5.2 / 10** | 5.2 - 5.8 / 10 | Two-magazine node swap is a solid structural upgrade, **but** at hip retrieval (`#69-#78` in `hipstrip.jpg`) the replacement magazine rises 20% into the bottom of the frame for ~10 ticks before the support hand enters the frame (`#81`), appearing to levitate. |
| **Viewmodel Framing & Reduced Motion** | **5.5 / 10** | 5.2 - 6.0 / 10 | `54 deg` viewmodel projection prevents near-plane stretching, and `reload_calm` is a good reduced-motion clip, **but** `reduced_variant` defaults to `"current"` (no roll reduction) and omitting `stock` leaves a bare cylindrical buffer pipe protruding on the right during reload. |
| **Muzzle Flash, Audio & Mobile Rendering** | **5.5 / 10** | 5.5 - 6.4 / 10 | Synthesized 4-voice `SBReloadAudio` with cancel support is clean; however, viewmodel triangle count sits at **37,598 tris** (2x mobile budget) and toggling a real-time `OmniLight3D` on every shot in `weapon_model.gd` risks mobile shader/light-list churn. |

---

### 2.2 Detailed Findings & Actionable Correction Requests for PR #2

#### Finding 1 — Replacement Magazine Levitates Unheld at Bottom of Frame (`#69-#78`)
- **Visual Evidence**: In `docs/reports/media/art-v9/hipstrip.jpg` (frames `#69`, `#72`, `#75`, `#78`) and `before-after-sunlit.jpg` (`#78` hip), the tan replacement magazine (`_magazine_spare`) rises ~60 px into the bottom of the viewport (`new_share = 20%`) while the left support hand (`L_hand`) is still completely below the bottom screen border. The hand does not become visible until `#81-#84`.
- **Root Cause in Source**:
  - In `game/scripts/gameplay/actor.gd:1176-1197`, `_magazine_spare` is parented to `_weapon_pivot` (NOT to the `L_hand` bone) and driven by an independent procedural curve `SBReloadPhases.spare_magazine_offset(progress)` (`game/scripts/gameplay/reload_phases.gd:46-57`) starting at `HIP_IN = 0.44` and `ACQUIRE = 0.50`.
  - Because the procedural magazine translation rises faster in camera space than the `L_hand` bone at `progress = 0.48..0.53`, the top of the magazine enters the viewport ~10 ticks ahead of the fingers.
  - Furthermore, `game/tests/reload_sequence_test.gd` relaxed the first-draw bound from `new_share < 0.05` to `new_share < 0.25` to pass with this visual pop.
- **Correction Request**:
  - Either attach `_magazine_spare` via a `BoneAttachment3D` on `L_hand` during `[ACQUIRE, SEAT]` (`0.50..0.80`) so the magazine cannot physically separate from the grasping fingers, or delay the upward `z/y` curve in `SBReloadPhases.spare_magazine_offset()` between `0.46` and `0.54` so `L_hand` and `_magazine_spare` cross the bottom frustum edge simultaneously.

#### Finding 2 — First-Person Roughness Clamp (`0.80`) Strips Metallic Read and Overrides Cosmetic Skins
- **Visual Evidence**: In `docs/reports/media/art-v9/before-after-sunlit.jpg` (`#0` idle), the upper receiver (`paint_receiver`) and handguard (`paint_handguard`) now have identical median luma (`70` vs `70`) and zero specular highlight differentiation along the chamfered receiver edges.
- **Root Cause in Source**:
  - `game/scripts/gameplay/viewmodel_shading.gd:2112` sets `const METAL_ROUGHNESS := 0.80`, and `game/scripts/ui/cosmetic_material.gd:2061` applies `ROUGHNESS = max(ROUGHNESS, viewmodel_roughness_floor);`.
  - Because `cosmetic_material.gd:2006` authors cosmetic metallic skins with `ROUGHNESS = 0.29 - finish_gloss * 0.14 - gold_mask * 0.08`, clamping `ROUGHNESS >= 0.80` in `VIEWMODEL_CODE` destroys the gloss/gold material distinction on all first-person cosmetic skins!
- **Correction Request**:
  - Instead of clamping surface `ROUGHNESS` to `0.80` (which kills direct sun/key-light specular and cosmetic finishes), attenuate or clamp the horizon/sky reflection contribution in the environment or reduce the reload roll angle from `25.8 deg` to `~16-18 deg` so the receiver side plane does not mirror the bright procedural sky horizon band during reload.

#### Finding 3 — Hand & Glove Silhouette Read in `tools/art/relay_ar_arms.py`
- **Visual Evidence**:
  - In `hands-closeups-before-after-2560.jpg` (`#14`, `#98`), the right hand wrapping the pistol grip shows three rounded, sausage-like finger tips with no flat dorsal phalangeal planes or sharp inter-finger valleys, and the sunlit back of the right hand (`#14`, `#98`, `#118`) still blooms to luma `77-85`, reading as pale putty rather than a dark tactical glove.
  - In `idle-hand-before-after-2560.jpg` and `hipstrip.jpg` (`#54`), the left support hand fingers fan out into a flat, rigid paddle during release/re-grip.
- **Root Cause in Source**:
  - `tools/art/relay_ar_arms.py` builds fingers from smooth SDF capsules blended into the palm volume prior to voxelization/quad-remeshing (`2,100` target quads in `tools/art/arms_build.py`), which smooths away crease valleys between adjacent fingers and flattens knuckle boxes.
- **Correction Request**:
  - Carve explicit negative SDF crease channels between fingers and flatten the dorsal phalanx surfaces with box-SDF intersections rather than pure capsules; curl the index and middle fingers slightly asynchronously during `DROP` (`0.24..0.34`) and `LETGO` (`0.85..0.92`) to eliminate the rigid open-palm fan.

#### Finding 4 — Default Reduced Motion Variant Does Not Reduce Reload Roll
- **Visual Evidence & Source**:
  - `game/scripts/gameplay/actor.gd:138-142` defines `REDUCED_RELOAD_VARIANTS` with `"current": {"roll": 1.0, "lift": 1.0, "recoil": 0.35, "clip": "reload"}` and `"calm": {"roll": 0.4, "lift": 1.3, "recoil": 0.25, "clip": "reload_calm"}`, and sets `var reduced_variant: String = "current"`.
  - When a player enables `reduced_motion` in accessibility settings, `_update_viewmodel()` uses `reduced_variant` (`"current"`), which leaves reload roll at `1.0` (full `25.8 deg` roll!). Meanwhile, `variants-ticks-1280.jpg` clearly shows that `"calm"` provides the best balance of reduced motion and minimal screen obstruction (whereas `"still"` lifts the gun too high into the center-right sightline).
- **Correction Request**:
  - Change the default `reduced_variant` in `game/scripts/gameplay/actor.gd:143` from `"current"` to `"calm"`.

#### Finding 5 — Mobile Rendering Budget (37.6k Viewmodel Triangles & Per-Shot `OmniLight3D` Toggling)
- **Evidence & Source**:
  - `docs/reports/media/art-v9/perf-probe.txt` reports `weapon_tris=37598` (`body`: 10,094, `arms_001`: 9,268, `paint_handguard`: 7,976, `paint_receiver`: 4,508, `grip`: 1,976, `magazine`: 1,392 x 2). This is nearly double the ~18k-23k triangle target for mobile viewmodels.
  - `game/scripts/gameplay/weapon_model.gd:1792-1800` attaches an `OmniLight3D` (`flash_light`) under `_muzzle`, and `actor.gd:1141` toggles `_muzzle.visible = _flash > 0 and alive` every shot (`0.105s` interval on `Relay AR`). Toggling dynamic lights on/off at 9.5 Hz in Godot's mobile/compatibility renderer causes per-object light-list rebinding.
  - Additionally, `actor.gd:483` uses `Time.get_ticks_msec()` for muzzle flash rotation and audio pitch variation, which is wall-clock dependent rather than deterministic per `_shot_index`.
- **Correction Request**:
  - Decimate `body` and `paint_handguard` in `tools/art/relay_ar.py` to bring total viewmodel + arms triangles under `22,000`.
  - Replace the per-shot `OmniLight3D` visibility toggle with either `light_energy` modulation or shader-only muzzle rim illumination on the viewmodel, and replace `Time.get_ticks_msec()` in `play_shot_effect()` with deterministic variation derived from `_shot_index`.

---

## 3. Recommended Next Development Priorities

1. **Execute Headless Godot Validation in CI / Linux Runner**:
   - Run `./scripts/validate.sh` (which now includes `bot_ai_regression_test.gd`) in the Linux Godot 4.7.2 container environment and archive the resulting log output alongside `aggregate-final.txt`.
2. **Tactical AI Slice v2 — Utility Lineups & Mid-Round Economy**:
   - Expand `SBBotAI.buy_equipment()` into team-coordinated eco/force/full-buy rounds (saving credits when team average `< 2000` after a round loss) and add pre-computed smoke/HE trajectory lineups for Site A West Box and Site B East Box executes.
3. **Human-to-Bot Ping / Callout Integration**:
   - Allow human players in offline/practice matches to issue tactical pings or site callouts that populate `_team_ai_state[team].contacts` and `target_site`, giving solo players direct command over bot teammates.