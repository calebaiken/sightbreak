# Kestrel 9 (sidearm), v1

Evidence for the first authored sidearm. Design, parts and pipeline are in `docs/art/WEAPON_PRODUCTION.md` and `docs/art/ASSET_PIPELINE.md`.

| Item | Value |
| --- | --- |
| Piece | The Kestrel 9 pistol (`tools/art/kestrel_9.py`) and its static gloved hands (`kestrel_9_hands.py`), in first person, replacing the procedural sidearm |
| Bar | The Relay AR's standard and the procedural sidearm it replaces; judged by an independent critic from stills. The Relay AR scored 5.5 of 10 in the earlier same-family review, so this is not near the 8.5 acceptance bar (G5 stays FAILED) |
| Source | Branch `claude/weapon-art-sidearm-v1` on the Codex v1 stack |
| Renders | `sheets/`: BEFORE (procedural) and AFTER (Kestrel 9) in ready (three lightings), shot, draw and mid-reload, 1280x720 native Godot renders under llvmpipe, downscaled. `model-*.jpg`: Blender previews of the model and hands from the first complete build (before the later bead, magazine-occlusion and placement fixes) |
| Blind checks | Round 1: six randomised unlabelled pairs, authored 6, procedural 0; critic score 29.5 against 24.5 of 60. Round 2, after the magazine-occlusion, flash-scale, front-bead, grip and placement fixes: authored 6, procedural 0; 35 against 24 of 60 (sights 6, detail 7, hands 6, coverage 4, flash 6, nothing broken 6). The final placement (lower, smaller) and slide gain 1.15 came after round 2 and were inspected, not re-judged blind |
| Tests | `scripts/validate.sh` on the final commit (see the PR); `weapon_art_test` 209 checks including the pistol's contract (nodes, bore height, 14,000-triangle budget, texture sizes, magazine occlusion, draws, pivot, ejection port) |
| Not covered | Reload and draw animation (the hands are static; a reload tilts the pistol and moves its magazine, with no hand reaching it), a GPU, motion and shimmer, sound, human judgement |
