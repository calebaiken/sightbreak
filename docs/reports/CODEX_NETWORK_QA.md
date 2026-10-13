# Codex competitive systems QA

## Phase A baseline (2026-10-13)

Tested source: corrected Claude PR #1, `cf9a630417fa1e50d76b59dd6f45ce8819de6ce8`. Main verified at `e67f2c86777d98d3cb3ad6bc7e851ef1826af26d`. Codex branch is stacked; no changes were merged.

Environment: Linux x86_64 cloud, Godot 4.7.2 official `ed1daf0bf`, Python 3.12, PostgreSQL 17 Docker (daemon 28.4.0), Xvfb :99, Mesa 25.0.7 llvmpipe LLVM 19.1.7. Native rendering is software rendering. No phone, mobile GPU, Xcode signing or physical-device performance evidence.

| Check | Observed result |
| --- | --- |
| Six-pair real-process protocol matrix | All passed; matching builds join; old/missing hello dropped around 5.1 s; protocol mismatch rejected around 0.1 s |
| Account admission, isolated new PostgreSQL database/API | Guest and mismatch rejected; same ticket then admits legitimate client; replay rejected; fresh-ticket reclaim succeeds |
| Weapon integrity / head-body volume | 28/28 and 33/33 passed; independent old capsule footprint probe agrees with corrected body |
| Actor/world/hit feedback/render budget/smoke/match | 72/25/10/21/26/75 checks passed respectively |
| Natural full bot match | Ten rounds, 3–7, 64 kills, halftime and planting observed, exactly one result; 303.6 simulated seconds |
| Profile/touch/main/landscape/UX | 10/34/35/144/30 checks passed respectively |
| HUD overflow | **954/964 passed; 10 failures** for Unicode rows, all five viewport sizes at both scales |
| Remaining maintained checks after aggregate stopped at HUD | Economy UI/recovery/cosmetics and two real ENet clients passed; no failing test removed |
| PostgreSQL regression / native real HTTP economy | 48 passed (one dependency warning); 14/14 case/market/trade checks passed |
| Build-manifest tests / economy conservation simulation | Ten tests passed; item and currency conservation passed |
| HTTP bridge fault injection | Three identical bounded retries and redirect refusal passed |
| Native renderer lifecycle | Demo capture succeeded, 11 match + 19 cosmetic checks passed; cosmetic texture bytes stable at 4,350,915 across six cycles |

Logs retained at `/workspace/reviews/competitive-baseline.log`, `/workspace/reviews/competitive-baseline/`, `/workspace/reviews/competitive-protocol-baseline/`, and the `.local/validation/` run paths printed there. Independent reviewer probes are under `/workspace/reviews/competitive-independent/`. These workspace paths are evidence locations, not remotely published artifacts.

### Corrected PR disposition for Claude

**Request changes for integration:** Unicode kill-feed rows remain clipped vertically in headless and native rendering. In `game/scripts/main.gd`, `_layout_hud` measures the feed height using the Latin string `Ag`; fallback Unicode fonts have taller row metrics. At 100%, frame bottom is 166 px and final row bottom 174 px (8 px clipped); at 130%, frame bottom 197 px and row bottom 203 px (6 px clipped). `hud_overflow_test.gd` reproduces all ten failures. Size the frame from actual row minimum heights/fallback metrics and rerun the maintained suite in native rendering. The original horizontal overflow is corrected. Codex has not edited Claude's visual UI.

Pre-existing admission risk independently reproduced: a compatible silent peer remains connected after 26 seconds without joining. Nonblocking handshake strictness issues: protocol 2.9 is coerced to 2; a peer rejected for 99 can then submit 2 and be admitted before its delayed drop. These do not themselves bypass account authentication (a modified peer can claim the protocol), but exact and terminal negotiation should be enforced in server hardening.

The environment proxy currently prevents posting this report to PR #1. No comment or review has been claimed as published.

## Quality gates

The 8.5/10 target remains required. No blanket passing score is assigned. Networking privacy, prediction, Internet security, sustained performance, mobile devices and final integration remain **UNVERIFIED / NOT ACCEPTED**. Passing baseline tests do not establish those gates. The reviewer is a separate AI agent; this is not an external security audit or human acceptance.
