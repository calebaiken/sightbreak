# Provenance: gauntlet-loop

| Field | Value |
| --- | --- |
| Upstream | https://github.com/robonuggets/gauntlet-loop |
| Upstream file | `.claude/skills/gauntlet-loop/SKILL.md` |
| Upstream commit | `9b1975a1b8f01981f3f1e6b667ad3aaf907178ea` (2026-08-06) |
| Vendored | 2026-10-21 |
| License | Creative Commons Attribution 4.0 International (`LICENSE` in this folder) |
| Attribution | RoboNuggets (packaging). The upstream README credits the technique to Matt Shumer, who named it while building Claude of Duty. |
| Local changes | None. `SKILL.md` and `LICENSE` are byte-identical to the upstream commit. |

SHA-256 at vendoring time:

```
6a345a43bf58966c83d50b6caf8be34a3fee725fb3c75778ed33fa206352b835  SKILL.md
9ba9550ad48438d0836ddab3da480b3b69ffa0aac7b7878b5a0039e7ab429411  LICENSE
```

Review before install: the skill is plain markdown. It contains no scripts, installers, network calls or shell commands. The upstream installation instructions are `git clone` plus `cp`; this copy was made from a reviewed clone, so nothing was piped to a shell.

The upstream skill writes a prompt for another session and does not run the loop itself. The executing counterpart for this repository is `.claude/skills/sightbreak-gauntlet/SKILL.md`.

To update: re-clone upstream, diff against this folder, read the diff, then replace the files and this record.
