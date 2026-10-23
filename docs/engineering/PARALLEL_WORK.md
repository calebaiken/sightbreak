# Parallel engineering work

## Mission execution ownership — 2026-10-22

Active Codex draft PR27 is `codex/v1-mission-playability`, based on PR24 → PR23 →
PR22 → PR16. Read NEXT_SESSION for current exact source and acceptance, rather
than applying historical main/protocol identities below. Main remains 4d8cdb3.

Live ref refresh finds Claude PR26 at 778c89a (game/scripts unchanged from 5288a69)
and new PR28 `claude/fair-actor-order-v1` at 2641ddf, based directly on PR23.
PR28 proposes authority shuffle 6ed3ee0 and separate bot habits 0871bc9. Neither is
integrated here. Codex f13ed03 already resolves the reproduced duel-order defect
with movement/action/contact phases, independently reviewed in 178 checks. Do not
replace it with a blind shuffle cherry-pick. Squad-symmetric bot habits are a
separate M5 candidate requiring exact-source qualification against this stack;
PR28 statistics on shuffle do not automatically qualify the two-phase stack.
Keep both authors' branches, evidence and shared-file contracts intact.

## Current integration checkpoint — 2026-10-14

- Active Codex validation branch: `integration/sightbreak-network-art-preview`, draft [PR9](https://github.com/calebaiken/sightbreak/pull/9), base `codex/network-validation-builds`. Tested/export source60cf125; later documentation commits retain that identity.
- Main remains e67f2c8. Dependencies: PR1=98ff57c, PR2=64ec598, PR3–8 stack tip89c0e9. Source PR branches and main are untouched by this work; no automatic merges or force pushes.
- Initial actor constants conflict: keep ViewmodelShading plus SBMovementStep aliases/delegation. Later graphics and HUD refreshes merge cleanly. No art/model/material/Blender changes; shipping aspect policy unchanged.
- Modified integration surfaces: actor constants only at merge; tests/validation, network simulation barrier/campaign, rendering/aspect probes, native export verifier, build manifests and documentation. Existing attachment/muzzle/rig/cosmetic contracts remain intact.
- Full47-group suite passes with updated foundation; adversarial HUD and full-capacity reconnect still fail. Graphics fallback and5.5/10 visual gate remain open. See [combined report](../reports/COMBINED_INTEGRATION_REPORT.md) and [conflicts](INTEGRATION_CONFLICTS.md).
- GitHub API works now; findings posted to PR1,PR2,PR5. This is actual GitHub coordination, not direct communication with Claude.
- Correct/reverify PR1, reconcile PR3→8 in order, and independently accept PR2 before final integration. Lifecycle needs backend ticket inspection; outbox needs persistent launcher/worker/backend. Keep protocol5 matched, prediction off by default, live rewind disabled. PR9 must not bypass constituent review.

## Historical record (superseded where noted above)

## Verified baseline — 2026-10-13

- Main: `e67f2c86777d98d3cb3ad6bc7e851ef1826af26d`.
- Claude PR #1: `cf9a630417fa1e50d76b59dd6f45ce8819de6ce8`, branch `claude/independent-audit-visual-v04`; fetched directly from GitHub. Main does not contain this head.
- Codex: `codex/competitive-network-systems`, **stacked on that exact corrected head**. Do not integrate before PR #1. No merge authorization has been given.
- No additional graphics branch was advertised by `git ls-remote` at the check. Recheck before shared-file integration.
- GitHub's normal `/pulls` page independently confirms PR #1 is open and the sole listed open PR. GitHub API access is blocked by the environment proxy, preventing API writes. Git fetch works. An `api.github.com` environment configuration draft was saved; saving does not activate it.

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

## Phase B integration surfaces

New modules: `state_privacy.gd`, `snapshot_schema.gd`. `match.gd` passes recipient IDs at both snapshot send sites, filters effect/notice channels, validates packets and handles geometry revocation. Protocol is now 3. `utility.gd` gains the narrow `set_replica_lifetime(remaining)` contract: network replica age controls growth/fade without a birth tween; offline/authority animation stays on the existing path. No mesh, material, shader, UI or attachment identifier changed.

Privacy tests, network dictionary inspection and a CPU/payload profiling harness are maintained. Independent reviewer accepted the bounded development scope after adversarial corrections; complete quality gates and Claude's Unicode HUD correction remain outstanding. Before rebasing, preserve Claude changes around shot effects, spectator camera, snapshot application and smoke growth; reconcile these small integrations explicitly.

## Movement branch

Current work: `codex/network-movement`, stacked on published privacy branch `acfa7041ea61ae835a158d324e276472d8dfdd22`. Target its eventual PR at `codex/competitive-network-systems`. Timestamped interpolation is isolated from future local prediction in separate commits. Protocol 4 adds tick/epoch headers; `match.gd` presents remote transforms every render callback. No asset/animation-node contract changes. The UDP impairment harness uses real guest processes and isolated loopback ports; it does not deploy a server.

## Updated Claude dependency and preserved stack — 2026-10-13

Claude PR1 advanced to `77e0433166b71c9de1456ef8639ce125d1b92029`. Independent focused recheck passes hit-volume40, weapon28 and hostile handshake8; Unicode feed height still fails in this environment. No main/PR merge authorized or performed. Graphics branch observed at `498311e4d63aa5d50f2be59777c1c79f09b6a66a` (`claude/cs2-fidelity-art-production`) is Claude-owned and untouched.

New `codex/state-privacy-v2` is based directly on verified Claude77e0433 and replays the four Codex privacy commits. The older published `codex/competitive-network-systems` remains intact; no force push. Target the new privacy PR at Claude's audit branch while it remains unmerged. The v2 movement/lifecycle branches will stack on this privacy branch. Narrow cherry-picks preserve Claude's first-hello decision logic and updated body-volume intersection, without replacing shared files wholesale. Cross-system regressions are required on the resulting stack; historic evidence on cf9a630 does not automatically certify this new base.
### Prediction integration contract

`actor.gd` delegates its existing movement section to `SBMovementStep`; weapon logic and visual attachment contracts are unchanged. `match.gd` queues own reconciliation for fixed physics and uses the new input stream. Protocol 5 changes the input RPC payload to bounded compressed bytes and adds owner-only movement acknowledgment fields. This change requires matched client/server builds. Independent review found and drove fixes for synthetic input edges, epoch stalls and persistent input backlog; these have maintained regressions. Prediction accuracy/feel and adverse network results remain a separate acceptance gate.

### Current v2 stack

- Privacy: `codex/state-privacy-v2`, base Claude77e0433, branch tipf60389b before later evidence.
- Movement: `codex/network-movement-v2`, base privacy, tip0fc8d54. One shared conflict in `_peer_disconnected` was resolved by preserving **both** Claude handshake cleanup and Codex input-stream cleanup. Actor hit-volume changes and all art contracts remain intact.
- Lifecycle: `codex/network-lifecycle-v2`, base movement. Adds `peer_lifecycle.gd`, bounded admission cleanup, provisional slot/account claims and backend ticket-inspection route. Requires updated backend for account admission. No new gameplay RPC or art interface. Full native regressions on the reconciled stack remain required.

Original branches are preserved. No PR merge, force push, public deployment or direct communication with Claude has occurred. A precise latest HUD review comment is prepared in `docs/reports/CLAUDE_PR1_FOLLOWUP.md`; API access still controls whether it can be posted.

### Durable results branch

`codex/durable-match-results` stacks on lifecycle `e8b9d8e06bf0a2a2b8f356a7df5d85f4b6c665f8`. Shared integration only changes the match submission status to `queued_for_delivery` when the server-local outbox accepts a handoff. No visual resources or economy rates change. New Python worker and launcher supervision require persistent server-local storage; see `RESULT_OUTBOX.md`. Backend change only permits exact previously committed result acknowledgments after the freshness window. New stale results remain rejected. This branch requires the updated backend and launcher together.

### Combat history foundation

`codex/combat-history-foundation` stacks on durable results `e954158`. Adds one server-only helper, deterministic parity tests and a four-line diagnostic recording hook in `match.gd`; recording is opt-in, live damage does not use rewind. Reuses existing actor static hit-volume math without changing actor.gd, attachment names, animations or art. Graphics branch advanced to `9e8acdf` during the upstream recheck and remains untouched. Do not activate compensation without the separate fairness/integration gates in `LAG_COMPENSATION.md`.

### Validation/build branch

`codex/network-validation-builds` stacks on combat history (including the same reviewed outbox follow-up fixes, cherry-picked without rewriting published history). Owns regression orchestration, UDP impairment metrics and manual CI. Tests keep Claude's existing Unicode HUD failure visible. No visual/UI/asset changes. GitHub API remains blocked; branch publication is not PR creation. Small PRs must target the preceding dependency and remain unmerged until Claude PR1 and all applicable blockers are resolved.

## Published coordination — 2026-10-13

GitHub API access recovered during final validation. Independent PR1 blocker was actually posted: https://github.com/calebaiken/sightbreak/pull/1#issuecomment-6151054451 . Claude graphics work is open PR2, targeting its audit branch; observed graphics head advanced to `fd943c1` and remains untouched.

| Draft PR | Branch | Required base |
| --- | --- | --- |
| #3 | codex/state-privacy-v2 | claude/independent-audit-visual-v04 |
| #4 | codex/network-movement-v2 | codex/state-privacy-v2 |
| #5 | codex/network-lifecycle-v2 | codex/network-movement-v2 |
| #6 | codex/durable-match-results | codex/network-lifecycle-v2 |
| #7 | codex/combat-history-foundation | codex/durable-match-results |
| #8 | codex/network-validation-builds | codex/combat-history-foundation |

All were created as drafts, none merged. Outbox readiness/quarantine follow-ups were appended to the result branch and cherry-picked into its descendants; published history was not rewritten. Retarget only after the preceding dependency integrates, reconcile each shared-file hunk with Claude's current source, and rerun the matrix. The app's PR attachment tool reports no handler; the PRs themselves exist on GitHub.
