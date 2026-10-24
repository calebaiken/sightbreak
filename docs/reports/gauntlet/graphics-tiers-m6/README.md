# M6: graphics tiers and shadow fill

Evidence for the four graphics tiers and the shadow-fill change. The measurements, rejected settings and next steps are in `docs/art/GRAPHICS_BACKLOG.md`; this folder holds the pictures and timings.

| Item | Value |
| --- | --- |
| Piece | `SBGraphicsQuality` tiers (LOW, MEDIUM, HIGH, ULTRA) and the ambient 0.85 / sun 1.05 fill in `RelayYard` |
| Bar | Readability of the yard at eye level, judged by an independent critic against a modern competitive-shooter map capture from the critic's own knowledge. No reference imagery was available (see `docs/roadmap/BARS.md`); no parity claim |
| Source | Branch `claude/graphics-tiers-v1` on the Codex v1 stack `ad6cdc20` |
| Renders | `sheets/`: twelve review views, each as BEFORE (old MEDIUM look), MEDIUM, HIGH, ULTRA, 1280x720 native Godot renders (llvmpipe under Xvfb, gl_compatibility), downscaled to 800x450 tiles. Not blind: labelled |
| Timings | `data/tier*-timings.json`: median and p95 over 40 frames per view, one host, relative only |
| Blind checks | Two sets of randomised, unlabelled pairs judged by a fresh-context critic: 11 of 12 pairs for the new MEDIUM over the old, and for HIGH over MEDIUM 3 wins, 3 ties, no losses. Details and limits in `GRAPHICS_BACKLOG.md` |
| Tests | `scripts/validate.sh` exit 0 on this branch, including the new `graphics-quality` suite (53 checks) and the rendering probes. Skipped by the script: the catalog drift check (no backend Python here) and three Windows-only tests |
| Not covered | A GPU, a phone, motion and shimmer, a real display, player models in shadow, human judgement |
