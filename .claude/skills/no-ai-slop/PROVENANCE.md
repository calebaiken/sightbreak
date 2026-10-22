# Provenance: no-ai-slop

| Field | Value |
| --- | --- |
| Upstream | https://github.com/petergyang/no-ai-slop |
| Upstream files | `skills/no-ai-slop/SKILL.md`, `skills/no-ai-slop/eval.md`, `LICENSE` |
| Upstream commit | `000650b156983f5159695b441477f4e63b25dc85` (2026-09-01) |
| Vendored | 2026-10-21 |
| License | MIT, Copyright (c) 2026 Peter Yang (`LICENSE` in this folder) |
| Local changes | None. All three files are byte-identical to the upstream commit. |

SHA-256 at vendoring time:

```
992b365f51a2f62cf4c1c5ed22049a9ee551dfea677550c1a72b371c0ceadd62  SKILL.md
8ad8d83ed1abe7fc054ad74966bfca64fc182bc71f59d701b24b962c39d11ad7  eval.md
b7a7fe370cc4c9e974528c7cea7841cf8ac886bc9ed947edb11b289441fba4a8  LICENSE
```

Review before install: markdown only, no scripts or network calls. The upstream repo also ships a Codex plugin manifest and a `scripts/build_plugin.py`; neither was copied or run.

Scope: this skill edits and audits **writing**. It says nothing about visual design. Judge rendered UI with the gauntlet loop and screenshots, not with this skill.

How SIGHTBREAK applies it: `docs/roadmap/COPY_STYLE.md` lists the player-facing surfaces, the established voice and the audit procedure. Run the skill's Detect job on a surface, fix with the Edit job, then answer every question in `eval.md`.

To update: re-clone upstream, diff against this folder, read the diff, then replace the files and this record.
