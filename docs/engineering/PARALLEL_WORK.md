# Parallel engineering work

## Verified baseline — 2026-10-13

- Main: `e67f2c86777d98d3cb3ad6bc7e851ef1826af26d`.
- Claude PR #1: `cf9a630417fa1e50d76b59dd6f45ce8819de6ce8`, branch `claude/independent-audit-visual-v04`; fetched directly from GitHub. Main does not contain this head.
- Codex: `codex/competitive-network-systems`, **stacked on that exact corrected head**. Do not integrate before PR #1. No merge authorization has been given.
- No additional graphics branch was advertised by `git ls-remote` at the check. Recheck before shared-file integration.
- GitHub API access is blocked by the environment proxy. Git fetch works. Open/closed PR status and comments cannot yet be independently confirmed through the API. An `api.github.com` environment configuration draft was saved; saving does not activate it.

## Ownership and contracts

Codex owns network modules/tests, server lifecycle, backend reliability, measurement and build tooling. Claude owns meshes, materials, shaders, visual UI, animation and art production. Preserve weapon attachments, muzzle transforms, operator scene roles, cosmetic identifiers and import conventions.

Shared `match.gd` changes must be small integration commits. Actor movement/presentation changes must preserve combat timing and visual contracts. No broad file replacements. Offline authoritative simulation remains available.

## Milestones and integration

1. Baseline verification and architecture documentation.
2. Recipient-specific state authorization (protocol bump required).
3. Timestamped movement buffering and prediction.
4. Server admission/lifecycle hardening.
5. Separately reviewable lag-compensation foundations.
6. Durable match-result delivery.
7. Simulation, measurement and builds; independent review.

Each milestone needs its own commits and review branch/PR. Stacked PRs target their immediate dependency until reconciled with main. Re-run gameplay, economy, layout and renderer regressions before integration. The baseline Unicode kill-feed defect belongs to Claude's UI work; it must not be hidden or silently fixed in networking commits.

See [QA](../reports/CODEX_NETWORK_QA.md) for evidence, remaining failures and environment details.
