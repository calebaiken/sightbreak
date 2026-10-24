# M8: surface-aware impacts and persistent bullet holes

Evidence for the change in `SBCombatEffects`. Design notes, limits and next steps are in `docs/art/GRAPHICS_BACKLOG.md`.

| Item | Value |
| --- | --- |
| Piece | A world hit now throws the sparks, puff and mark of the surface it hit (steel, concrete, asphalt, other), and leaves a bullet hole that stays until the round changes |
| Bar | Judged by a fresh-context critic for hit readability and material read, no reference imagery available (see `docs/roadmap/BARS.md`); no parity claim |
| Source | Branch `claude/combat-impact-vfx-v1`, stacked on `claude/graphics-tiers-v1` |
| Renders | `sheets/`: each of four surfaces at about 4 m and about 10 to 13 m, a burst of nine hits. Left BEFORE, right AFTER; top the instant after the burst, bottom once the particles are gone. 1280x720 native Godot renders under llvmpipe, downscaled. Effects are stepped by hand at 60 Hz because software rendering gives frames longer than a spark's life |
| Blind check | 16 randomised unlabelled pairs: the new presentation won 14, 2 ties (far asphalt), the old won none. The critic saw the first tint set; the puff tints were then lowered, measured with `data/dust_probe.gd` (the lit puffs render about three times brighter than their tint, so the first tints came out snow white). The retuned render was inspected but not re-judged blind |
| Cost | `data/draw-calls-*.txt`: +1 draw call and +128 primitives per frame (a 64-quad pool) at every view, measured on the first version; the later tuning changes colours only |
| Tests | `scripts/validate.sh` on the final state (see the PR); `combat_impact_test` (25 checks) and the updated pool-budget checks in `actor_test` |
| Not covered | Motion, sound, a GPU, decal behaviour at grazing angles past 80 m, clutter after many bursts against player models, human judgement |
