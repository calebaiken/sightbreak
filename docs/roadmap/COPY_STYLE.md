# Player-facing copy

Applies `.claude/skills/no-ai-slop` (upstream: https://github.com/petergyang/no-ai-slop, MIT) to everything a player reads. The skill judges writing only. Judge layout, contrast and legibility with rendered screenshots instead.

## Voice to keep

SIGHTBREAK reads like a field system: short, operational, concrete. Existing terms stay: Relay Yard, DEPLOY, match funds, Credits, requisition, operator record, field menu, relay device. Button labels are uppercase imperatives (`DEPLOY · OFFLINE 5V5`, `RETRY PENDING TRANSACTION`). Do not rename them for style.

## Surfaces

Main menu and settings. Buy menu and weapon descriptions. HUD hints (objective, role and phase guidance). Pause menu. Scoreboard and match results. Inventory, case odds, market and trade text. Error, loading, empty and disconnected states. Tooltips. README, installation text, release notes and store-facing text.

## Procedure

1. Collect the strings for one surface. For UI, read them from the scene code and from a native screenshot, because the shipped string is the one that counts.
2. Run the skill's **Detect** job. Quote each pattern found with a fix in a few words.
3. Run the **Edit** job with the minimum effective change. Keep established terms and real uncertainty.
4. Answer every question in `.claude/skills/no-ai-slop/eval.md`. Fix and re-check on any "no".
5. Check the new string still fits its control at the largest text scale and the narrowest layout.
6. Record the surface, the strings changed and the pattern fixed in the worklog.

## Rules specific to this game

- Never state a number the code does not enforce. Odds, costs, timings and limits come from the source or from `docs/economy.md`.
- Honest states beat reassuring ones. If the service is unreachable, say that and what still works.
- Do not claim physical-device, human-play or CS2-parity results that are `UNVERIFIED`.
- Strings that appear in tests are changed together with the tests.
