# M9: environment readability pass

Evidence for the three changes listed in `docs/art/GRAPHICS_BACKLOG.md` ("Environment readability pass (M9)").

| Item | Value |
| --- | --- |
| Piece | Far skyline behind the attacker-end wall, darker crate lids, thicker crane cables in `RelayYard` |
| Bar | Independent critic's ranked defect list and readability judgement; no reference imagery available (`docs/roadmap/BARS.md`); no parity claim |
| Source | Branch `claude/environment-readability-v1`, stacked on `claude/combat-impact-vfx-v1` |
| Renders | `sheets/`: all twelve review views, BEFORE (left) and AFTER (right), MEDIUM tier, 1280x720 native Godot renders under llvmpipe, downscaled to 800x450 tiles |
| Blind check | 12 randomised unlabelled pairs: new 6, ties 5, old 1. The critic judged the shipped state; nothing was retuned afterwards |
| Timings | `data/timings-*.json`, median of 40 frames per view: 464 ms before, 474 ms after (relative, one host, within noise) |
| Not covered | Motion and parallax, a GPU, player silhouettes against the skyline, human judgement |
