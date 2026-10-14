# Integration checkpoint — 2026-10-14

Working branch: `integration/sightbreak-network-art-preview`; draft PR #9 targets PR #8 for validation only. No main/source PR branch was changed or merged. Published integration source d8a10ff; later harness commits do not change shipping runtime.

## Verified inputs / incoming update

- Runtime d084e500 contains foundation227d6c8, network stack89c0e99 and graphics64ec598.
- Full regression matrix:47/47 groups passed on clean d084e500.
- New foundation98ff57c fixes the independently reported130% status/control overlap. It is fetched and under independent review, **not yet integrated/tested** at this checkpoint. After frozen performance measurements finish, merge it only into this isolated branch and run the full matrix again.
- Graphics remains64ec598 at the latest GitHub check. Its static fallback projection defect is reported on PR #2; independent weapon/arms visual rubric5.5/10 does not meet8.5.

## Confirmed networking blocker

Twelve-condition, ten-real-client campaign on85edf895:11/12 pass, one failed aggressive0.7s reconnect. Three impaired repeats/control pass; normal2s reconnect passes. A close-overlap blackout on47a350d clean (ten clients,100ms RTT,blackout7.8–9.3s,close8s,real2s retry) recovers only5/10:two terminal slot-reservation rejections and three still connecting at22s. This blocks robust reconnect acceptance. Attribution to foundation versus stack remains unverified. Preserve ownership/ticket/capacity protections; a safe bounded retry/old-binding follow-up is required. PR #5 comment: https://github.com/calebaiken/sightbreak/pull/5#issuecomment-6160142760 . Prediction remains opt-in, live rewind disabled.

## Evidence and remaining work

Workspace evidence: `/workspace/reviews/integration-20261013/`. Independent reports in `pr1-independent`, `art-independent`, `network-independent`; matrix47 logs in `matrix-final`; network campaign and follow-ups retain failures. Three scenario render runs, weapon cost and baseline render comparison are completing via `run_remaining_measurements.py`; outputs/logs enumerate exact progress. These software diagnostics are not device FPS.

Native exported d084 Linux executable has actually joined/fired and displayed replicated rigged reload. Earlier --script verifier was invalid and is replaced by supported native UI automation. First timed-quit attempt timed out: clean export teardown remains pending. Final verifier needs a rebuilt binary and an optional held-R input mode prepared by the reviewer. Existing three exports are still d084 artifacts; **rebuild all after the incoming HUD merge**, verify hashes/content/native runtime, then package.

Remaining: finish isolated rendering/native network/import measurements; independently verify98ff57c; merge and rerun47 groups; refreshed aspect captures; exact-source Android/Linux/unsigned iOS exports and independent artifact check; full evidence/checksum packaging; final QA/docs/PR descriptions and push verification. Do not mark mobile startup, Xcode compile/signing, production Internet security, human movement feel or overall8.5 acceptance as passed.

Maintained entry points: `scripts/validate_matrix.py --render`, `scripts/run_network_campaign.py`, `scripts/simulate_network.py`, `scripts/profile_render.sh`, `scripts/export.sh`, `scripts/verify_builds.py`, `scripts/verify_integration_export.py`. Full runtime content SHA256 before incoming HUD change: `8eed24e4c284034afd1eb9d383c7f3e981eabb12b17cafb158b0452a7554e9f6`.
