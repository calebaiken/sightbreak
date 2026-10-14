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

## Phase B — bounded state privacy

Implemented recipient-specific welcome/snapshots, explicit field authorization, static-cover relevance, conservative opaque-smoke filtering, dead-teammate viewpoints, private objective activity, scoped impacts and unattributed hidden gunfire. Client revocation removes cached geometry/collision and snaps reappearing actors to their first authorized position. Native smoke replication now applies authority age without competing growth tweens. Details and disclosure limits: [STATE_PRIVACY.md](../network/STATE_PRIVACY.md).

- Maintained privacy suite: **55/55**; smoke presentation **26/26**; match rules **75/75**; two real ENet clients pass movement, reconnect, feedback and received-dictionary permission checks.
- Independent reviewer: external first-spawn/reveal error **0 m**; visible feet through low cover preserved; silent hidden cloud absent; event-before-snapshot audio preserved; initial and updated mature-cloud scale correct. **494 malformed-field mutations: 55 accepted/applied safely, 439 rejected, no script errors**.
- Native demo + match/cosmetic lifecycle rerun: passed, 11 + 19 checks; cosmetic texture bytes stable at 4,350,915. These are software-rendered observations.
- Independent review accepts a bounded development commit subject to full regression results and the Claude dependency. It explicitly does not award initiative-wide 8.5 scores, production acceptance or merge authorization.
- The first implementation failed independent low-opening, first-pose, malformed-crouch, smoke-rim and replica-age probes. Each was corrected and retested; this report does not suppress those intermediate defects.

Tested Phase B implementation commit: `728e634f242a21ed5319f7917afda4aa721c4821` (subsequent documentation commits do not change implementation). Full aggregate rerun: all checks through HUD ran; exactly the same ten Unicode failures stopped the aggregate. Every later suite was executed separately: economy/native network passed, PostgreSQL 48 passed, native HTTP economy 14/14, conservation simulation and ten manifest tests passed. No test was removed or declared passed after failing.

Independent evidence: `/workspace/reviews/competitive-independent/PHASE_B_REVIEW.md`, source hashes and probes beside it. Maintained logs: `/workspace/reviews/competitive-privacy.log`, `competitive-network.log`, `competitive-phaseb-render.log`, `competitive-phaseb-full.log`, `competitive-phaseb-remaining.log` and `competitive-phaseb-protocol-final.log`. The existing Unicode HUD failure remains an integration blocker.
