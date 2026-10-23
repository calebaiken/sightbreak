# Desktop playability P1 preflight — 2026-10-21

The fetched remote state matches the supplied checkpoint. New isolated worktree
`/workspace/sightbreak-playability`, branch `codex/desktop-playability-p1`, starts
at PR #22 `82a03fcbf69f931e7eb91db7d566481b03745cf9`. The stacked draft targets
`codex/desktop-steam-readiness`; main, PR #22 and concurrent branches are protected.
No merge, reset, rewrite or force push is part of this milestone.

| Reference | Fetched identity |
| --- | --- |
| main | `4d8cdb33ce18a6adcf6e2af5556b6f083535536c` |
| PR #16 / V2 | `d2439acdd5f73df7bae5ada62ee1e3dec2cf30db` |
| PR #22 head | `82a03fcbf69f931e7eb91db7d566481b03745cf9` |
| PR #22 frozen tested source | `0fb74800cffb96077069144028d113e308ef1744` |
| PR #17 / V3 | `320e0ef3cca01566bb5858c90a8021b136737be0` |
| PR #18 recovery | `ccd0955a2cf5d8bcad4e9e9e2fba8ad399591f5e` |
| PR #19 trade reads | `89215fbd81e8a1fb5eede134d789cde61544eda3` |
| PR #20 input freshness | `0cbc3ae7a9a017aa179eaeff61cf902629de1c0d` |
| PR #21 prediction diagnostics | `6d2b38dffe9c591d6cec6fc34b92bbc8d06fe008` |

All open PRs/remote branches and recent workflow runs were enumerated. PR review
endpoints #17–#22 were empty at inspection; source-bound repository reviews and
retained failures remain the evidence, not an assumed current approval. No gated
V3, bot or art branch is integrated. Mandatory desktop report/preflight/checklist,
limitations, milestones, Steam preparation and specification were read.

The current native CI checkpoint is run 39384250334: Linux, Windows retry and macOS 15
ARM jobs passed their stated scopes; Intel macOS default and explicit OpenGL
startup timed out after 120 seconds. Earlier Windows reload failure and macOS 14
ANGLE exception remain retained. A prior pass is not evidence for this candidate.

Architecture remains native Godot 4.7.2 with authoritative match/actor rules,
protocol 6 ENet, local-only training/settings and a separate PostgreSQL account
service. Primary corrections are control-mode/capture/focus consistency,
exported objective/full-match/persistence validation, native Windows offline
coverage and measured macOS startup comparison. Prediction and live rewind stay
off; earned-only economy, private snapshots, account authorization and recovery
contracts remain separately regression tested.

Capability tests explicitly simulate desktop touch hardware and mobile/controller
inputs; they cannot qualify physical touchscreen/controller devices. Exported
objective starting-layout tests must declare initial conditions, retain ten
living actors/stock equipment/AI/timers/collisions, use actual OS input and leave
all objective/winner/progression transitions to ordinary game rules. Standard
full-match validation retains stock spawns/teams/randomness and time_scale 1.

New evidence lives in fresh `/workspace/playability-evidence/` attempts and new
ignored build roots. Historical PR #22 artifacts/receipts are immutable. Current
Steam integration/publication, production Internet security, signing/notarization,
physical device performance and every applicable 8.5 quality gate remain outside
any inference from this preflight.
