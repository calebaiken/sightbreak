# Evidence for the Codex PR #1 blockers

Captured on the same host as the rest of this branch's evidence: a 4 vCPU Linux container with Godot 4.7.2 official, Xvfb and Mesa llvmpipe. These are software-rendered viewport captures, not phone photographs. `sha256.txt` hashes every file. The findings, fixes and decisions are in [`docs/audits/CODEX_REVIEW_RESPONSE.md`](../../../../audits/CODEX_REVIEW_RESPONSE.md).

## Final head

- **`matrix-d0278f0.log`:** the RESULT line of every suite in the full regression run on commit `d0278f0`.
- **`validate-d0278f0.log`:** that run's `scripts/validate.sh` output:
  - 1,915 native assertions;
  - the natural 10-round bot match;
  - two ENet clients with reconnect.

## `hud-fallback/` — Codex follow-up at `77e0433`

The CJK fallback-face row height defect.
- **`compare-feed-crop-noto-cjk-130.png`:** the feed at 1560×720 and 130 % text with Noto Sans CJK as the CJK face. Before (`77e0433`) the fourth row is clipped; after (`7756e35`) the frame has grown to it.
- **`before-*/after-*.png`:** the full captures:
  - `after-taller-face-*` is the test's second pass, with the system's CJK face made 6 px taller on purpose;
  - `after-system-fonts-*` uses this host's own WenQuanYi Zen Hei.
- **`noto-cjk-fonts.conf`:** the fontconfig recipe that selects Noto Sans CJK without installing anything.
- **`logs/`:**
  - the unchanged test at `77e0433` under Noto: 1,325/10 headless, 1,331/10 native;
  - the negative control (old frame, final test): 20 and 30 failures;
  - the final head's headless and native runs.
- **`../validate-7756e35.log`:** `scripts/validate.sh` on the final head, exit 0.

## `hud/` — blocker 1

- **Sources:** `game/tests/hud_overflow_test.gd --capture-dir`.
  - "Before" is the reviewed head's `main.gd`, which failed 49 checks. Its captures came from the first, ellipsis-agnostic version of the test; that log is included.
  - "After" is the final code at `d0278f0`, with 1,333 checks native and 1,327 headless. Its screenshots are pixel-identical to those taken at `89a743a`.
- **`compare-*.png`:** half-scale before/after sheets, all with two 24-character names:
  - 960×720, 1180×820, 1280×720, 1560×720 and 1600×720;
  - plus 1560×720 at 130 % text with Unicode/CJK names.
- **`before-*/after-*.png`:** full-resolution originals for 960×720 and the Unicode case.
- **`stacked-marks-before.png`, `stacked-marks-after.png`:** the second review's tall-name case, one letter plus 23 combining marks.
  - Before is the reviewer's native capture at `fc52e68`: the newest rows are pushed out of the clipped feed.
  - After is the same scenario at `d0278f0`: all four rows are 26 px and fully visible.

## `hit-volumes/` — blocker 2

- **`grid-*.json`:** `docs/audits/probes/hit_grid_probe.gd` output for the 0.3.0 archive (`baseline`), the reviewed head (`pr`) and commit `6e144a0` (`fixed`).
  - The rays sit on 1 cm cell centres: front and side, standing and crouched, horizontal and plunging.
  - **`grid-final.log`:** the same probe on the final head (`d0278f0`) gives cell-for-cell identical views. The tangent and 64-bit span changes only move results within micrometres of the surface.
- **`compare-pr.md`, `compare-fixed.md`:** `compare_hit_grids.py` tables:
  - cells that became hits;
  - cells that stopped hitting;
  - headshot/body reclassification against 0.3.0.
- **`grid-standing_front.png`, `grid-crouched_front.png`, `grid-standing_front_plunging.png`:** the three builds side by side.
  - Red marks hits where 0.3.0 missed.
  - Dark marks 0.3.0 hits that now miss: the air beside the head that H-2 removed.
- **`hit-volume-test-on-pr-head.log`:** `hit_volume_test.gd` run against the reviewed head (8 failures).

## `protocol/` — blocker 3

- **`before-*.log`:** the four pairings of 0.3.0 and the reviewed protocol, using real separate server and client processes. Mixed pairs log "rpc node checksum failed" and stay in "joining".
- **`after-*.log`, `matrix.md`:** `scripts/test_protocol_compat.sh` from the full regression run on `d0278f0`. It has six pairings, including a protocol-bumped copy of this build.
- **`hardening-before/`, `hardening-after/`, `handshake-hardening.log`:** `scripts/test_handshake_hardening.sh`.
  - It runs hostile clients against the real dedicated server, and hostile servers against the stock client.
  - Before is `fc52e68`: 7 of 8 checks fail. The 14,560-line flood is elided in the middle.
  - After is `d0278f0`: 8 of 8 pass.
- **`account-network.log`:** from the same run:
  - a protocol-99 client is rejected;
  - the same join ticket then admits the real client to slot 1.
