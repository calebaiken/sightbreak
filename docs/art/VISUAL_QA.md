# Visual QA

## Procedure for every visual change

1. **Cycles review renders** from the generator.
   - `render_views.py` with all seven views (left and right ¾, side profile, top, receiver, grip and magazine, materials), plus `eye`, which reproduces the in-game camera.
   - Fix every visible defect before baking.
2. **In-engine captures** with `game/tests/weapon_art_capture.gd`:
   - backlit yard: ready, firing, reload;
   - sunlit yard;
   - hall shade;
   - sunlit with a skin;
   - the inspection studio with a skin.
   - Repeat with `--procedural` for the before set.
   - All on Xvfb/llvmpipe at 1280×720.
3. **Contract test:** `weapon_art_test.gd` must pass, along with the rest of `validate.sh`.
4. **Review:** score against the project's seven-part rubric (`docs/reports/QA-0.3.md`; anchors 5 = blockout, 7 = coherent alpha, 8.5 = consistently polished, 10 = exceptional) and against `VISUAL_GAP_ANALYSIS.md`.
   - Only categories the change touches are re-scored.
   - Stills cannot score motion.
   - A reviewer from the same model family as the author is recorded as such and does not count as independent acceptance.

## Relay AR slice (2026-10-13)

Evidence: [`docs/reports/media/art-v1/`](../reports/media/art-v1/README.md).

**Reviewer:** a separate Claude agent. It is the same model family as the author, so this is **not independent acceptance**. It had stills only (no motion), llvmpipe captures (no device shading or compression artefacts), and no CS2 reference images; its CS2 comparisons come from general knowledge.

**Images reviewed:** the captures in `captures/before-procedural/`, the authored set before the follow-up commits (kept in `reviewed-v4/`), and the Cycles renders.

Scores cover the first-person weapon, hands and inspection only, not the whole game:

| Category | Before | After | Reviewer's reason (abridged) |
| --- | ---: | ---: | --- |
| 2 Materials and surfaces | 4.0 | 5.5 | Baked occlusion and normals give panel lines, bevel highlights and a readable sight glass. But the default graphite finish discarded the baked albedo, so the receiver read as matte plastic without wear. |
| 4 Models and animation presentation | 4.5 | 5.5 | It is now a recognisable carbine with a rail, slots, brake and optic. The hands read like mannequin parts, and reload is still a whole-rig tilt. |
| 5 Combat and cosmetic effects (incl. inspection) | 4.5 | 5.0 | Inspection shows a real-looking rifle. Effects are unchanged, and the skin is a flat two-tone band that blows out. |
| 6 Identity and consistency | 5.0 | 5.0 | A generic AR silhouette. It is now more detailed than the box-built environment, and the hands are less detailed than the rifle. |
| 7 Competitive readability | 6.0 | 6.0 | Less of the central 40 % is covered (5.6 % against 6.4 %); in exchange, the forearm covers more of the lower centre. |

- **Categories not re-scored:** 1 (geometry) and 3 (lighting), because the environment and scene lighting did not change.
- **Mean of the five categories:** about 4.8 → 5.4.
- **Whole-game effect:** about +0.1, at most +0.2, from the independent 6.6 baseline. That is still below the 7 "playable alpha" anchor and far below 8.5. The reviewer put a CS2-like first-person weapon at about 9 on this rubric.

**Defects, ranked by the reviewer:**
1. Hand anatomy: tube fingers and a claw-like support grip.
2. A pipe-like sleeve with no folds; it is the largest and least detailed thing on screen.
3. The flat default graphite finish.
4. CAD-like surfaces and a faceted grip.
5. A heavy roll; the support hand sits at the handguard tip.
6. Inspection framing: the muzzle at the frame edge.
7. The two-tone skin band and blow-out.
8. Weapon and background merge in shade.
9. Detail mismatch with the box-built environment.
10. Unchanged effects (star flash, box casing, tilt reload) now stand out.

**Fixed after the review (not re-scored):**
- the casing origin (`039ade9`): casings no longer appear beside the gun;
- defect 3 (`b376e61`): without a skin, the rifle shows its baked anodised surface with wear;
- defect 6 (`b376e61`): the inspection placement is re-centred.

The final captures are in `captures/after-authored/`. Every other defect stays open and is listed in `docs/DEVELOPMENT_STATUS.md`. The next steps, in the reviewer's order, are:
1. Rigged glove hands with real anatomy.
2. Sleeve shape and gear, with a reduced roll and the support hand moved to mid-handguard.
3. Layered default materials and UV-based skins with wear masks.
4. Weapon lighting checked on real GPUs.
5. Authored reload, equip and inspect animation.

