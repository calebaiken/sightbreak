# Desktop alpha preflight — 2026-10-20

Implementation base: PR #16 head **d2439acdd5f73df7bae5ada62ee1e3dec2cf30db**,
on isolated `codex/desktop-steam-readiness`. `git diff 701ce2c d2439ac -- game
backend server` is empty. The working checkout was clean before branching. Main,
V3 and all source-owner branches are preserved; no merges or force pushes.

The native Godot 4.7.2 project separates actor/combat rules, authoritative match
and ENet state, local training/settings, and a PostgreSQL account/economy service.
Offline 5v5, round economy, objectives, four weapons, utility, HUD/settings,
authenticated admission, private snapshots, reconnect and durable server results
already exist. Protocol 6, prediction default-off and live rewind off remain the
contracts for this milestone. Backend/item transfers and earned-only rules are
outside the desktop implementation's runtime changes.

All repository paths, development docs, workflows, local history/worktrees and
remote branches were inventoried. Required V3 docs were read at PR #17's exact
head. GitHub PR metadata and source-bound reviews were refreshed, rather than
treating their older descriptions as current state:

| PR | Observed head | Integration decision |
| --- | --- | --- |
| #16 V2 | `d2439ac` | Base; V2's 74-group matrix and 12-condition campaign are historical |
| #17 V3 | `320e0ef` | No frozen V3 pass; provenance/process cleanup corrections remain under review |
| #18 client recovery | `ccd0955` | Strong fixture/restart evidence; real PostgreSQL recovery and aggregate QA pending; defer |
| #19 batched trade reads | `89215fb` | Bounded read-only source delta and retained responses; independent/integration gates and unbounded history remain; defer |
| #20 input freshness | `0cbc3ae` | Narrow correctness fix with source review; aggregate/outcome gates pending; defer |
| #21 prediction diagnostics | `6d2b38d` | Additive diagnostics; independent real-map evidence pending; defer |
| #14 bots | `48eb058` | Current native review blocks missing match/module/actor interfaces; retain V2 |
| #2 graphics | `bb5212d` | Current source-bound review holds mixed visual changes and sleeve obstruction; retain V2 |

Evidence: [V2 report](STABILIZATION_V2_REPORT.md), [live V3 status](https://github.com/calebaiken/sightbreak/blob/320e0ef3cca01566bb5858c90a8021b136737be0/docs/reports/DEVELOPMENT_V3_PROGRESS.md),
[V3 procedure](https://github.com/calebaiken/sightbreak/blob/320e0ef3cca01566bb5858c90a8021b136737be0/docs/engineering/DEVELOPMENT_V3_VALIDATION.md),
[bot review](https://github.com/calebaiken/sightbreak/pull/14#pullrequestreview-5576455853),
[graphics review](https://github.com/calebaiken/sightbreak/pull/2).

Immediate defects: Linux-specific setup/launch/export paths; no Windows/macOS
presets; verifier and packager require all three old targets; receipt comparison
does not bind the exact commit or validation code and permits re-attestation;
static menu version is stale. Desktop focus/display behavior requires native
input testing. These can be corrected without changing network RPCs, bot/art
interfaces or account/economy contracts.

Host: Debian 13, Linux x86_64; official engine
`4.7.2.stable.official.ed1daf0bf`. Native Windows/macOS execution needs separate
runners. Linux rendering here uses Xvfb/llvmpipe, which is genuine native
execution but provides no physical GPU or human gameplay acceptance. Per-category
8.5 quality, physical mobile, controller, production security and public-match
gates remain open. Desktop export success cannot satisfy them.
