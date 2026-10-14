# Independent PR #1 foundation recheck

Reviewed commit: `227d6c8245a75522b8144c8004de2a86d61b833b`.
Negative control: `77e0433166b71c9de1456ef8639ce125d1b92029`.
Read-only worktrees; no tracked changes or GitHub operations made by this reviewer.

Independent execution/source inspection by a separate same-model reviewer agent. This is not an external security audit or human acceptance. The follow-up below directly executes this exact PR1 head's native ENet protocol and account admission against its own isolated PostgreSQL backend. Broader economy/full combined regression remains assigned to the parent integration run.

## Disposition

**The Unicode kill-feed blocker is fixed on the reviewed head.** The original exact 77e0433 checkout reproduces 10 failures out of 1,325 checks under the same installed Noto CJK environment. Current head passes 2,435 headless checks and 2,442 native checks, including the deliberate taller CJK fallback. Seven native captures have their actual PNG dimensions verified; the 1560x720 Unicode normal/taller images were visually inspected. All four rows are visible; width does not push ammo, score, radar, funds, or other tested HUD positions.

Source inspection confirms `_fit_kill_feed_frame` sums actual live row minimum heights plus gaps, preserves the Latin reserve and does not propagate child widths. Expiry skips queued rows and recomputes the reserve. Independent additional probe at 1440x720 (18:9), both scales, adds expiration and old-height negative-control checks: 597 checks passed. Old Latin-only reserve is demonstrably too short for the same taller rows; clearing them restores the reserve and leaves ammo geometry unchanged.

The weapon timing/body correction remains intact. Source differences since 77e0433 do not change actor.gd or match.gd. Read and exercised sustained intervals, held-trigger reload resumption, switch cooldown/deploy separation, recoil recovery, rendered head/helmet agreement, standing/crouched body capsule parity, rounded feet, empty-head-space pass-through, blocking world geometry, tangencies and 40–140m rays.

## Test results

| Group | Checks | Failures | Execution |
|---|---:|---:|---|
| HUD overflow current | 2,435 | 0 | Headless; system and taller CJK |
| HUD overflow current | 2,442 | 0 | Native OpenGL; 7 captures |
| HUD negative control 77e0433 | 1,325 | 10 expected | Headless; reproduces old blocker |
| Independent 18:9 + expiry HUD probe | 597 | 0 | Headless |
| Weapon integrity | 28 | 0 | Headless; 7 executions total |
| Hit volume | 40 | 0 | Headless; includes dense ray grids |
| Hit feedback | 10 | 0 | Headless |
| Actor | 72 | 0 | Headless |
| Landscape UI | 196 | 0 | Headless |
| UX contract | 32 | 0 | Headless |
| Touch | 34 | 0 | Headless |
| Additional status/touch diagnostic | 32 configurations | See finding | Same 16 configurations on both heads |

HUD matrix: 960x720,1180x820,1280x720,1560x720,1600x720;100% and130% text; ordinary/max ASCII/CJK/stacked combining names; grapheme-boundary truncation for Latin marks,Thai,Devanagari,flags,keycaps. Taller fallback pass actually executed. Independent probe adds1440x720. No physical mobile display/safe-area/font testing is implied.

## Remaining findings

### Pre-existing, nonblocking for this correction: enlarged status text overlaps utility controls

At130% UI text scale, the actual centered status-text glyph rectangle intersects FRAG at960,1280,1560,1600x720 in buy/live phases; at960 buy also SMOKE. Identical intersections reproduce on77e0433. No glyph overlaps in these fixtures at100%. The latest funds relocation preserves status Y and shortens buy text; it did not introduce this defect. Current native1560x720 Unicode screenshot visibly confirms it.

Reproduction: run `status_touch_probe.gd` using the desired worktree's `scripts/godot.sh --headless --script <absolute probe path>` and the isolated state directory. The probe uses actual font string size and centered glyph bounds, not the full-width Label control rectangle. Logs `status-touch-current.log` and `status-touch-old-77e0433.log` preserve exact rectangles. Existing landscape checks exercise100%; current overflow130% checks omit this collision. Recommend Claude extend layout coverage at130% and clear utility controls without changing shipping aspect policy.

### Unverified intermittent exit warning

The first weapon-integrity execution passed28 assertions but emitted `4 ObjectDB instances were leaked at exit`. Six immediate verbose repeats passed and did not reproduce any leak warning. Initial log lacks leaked instance types. This is not evidence of an OpenGL texture leak, nor proof the warning is harmless. Record for lifecycle follow-up; origin remains unverified. The native HUD run emitted no resource/texture leak warning.

### Environment-only native audio initialization

The native invocation omitted `--audio-driver Dummy`: absent ALSA hardware caused an initial `ERR_CANT_OPEN`, followed by successful dummy fallback. All2442 assertions and 7 captures completed, exit0. The VSync mode warning is from Xvfb/software driver. Use `--audio-driver Dummy` for clean future cloud-native runs; sound/device behavior remains unverified.

## Recommendation / quality boundary

Recommend **development-branch acceptance of PR1 at `227d6c8`**: corrected Unicode feed, weapon/body integrity, exact-head protocol compatibility and account admission all pass the focused independent review. Combined integration still requires its full stack regressions; this recommendation does not imply release approval. Enlarged mobile status overlap remains open; physical devices, native audio, production transport/security and the complete integration quality categories remain outside this review. No broad 8.5/10 score is awarded from a focused unit/native fixture pass.

## Reproduction / evidence

Environment: Godot 4.7.2.stable.ed1daf0bf, Linux cloud, Xvfb:99, Mesa 25.0.7 llvmpipe LLVM 19.1.7, Compatibility OpenGL 4.5, Noto Sans CJK installed. Software rendering is correctness evidence, not phone GPU performance.

Import: `SIGHTBREAK_STATE_DIR=/workspace/reviews/integration-20261013/pr1-review-state scripts/godot.sh --headless --editor --import --quit`.

Headless HUD: same state plus `timeout 540 scripts/godot.sh --headless --script res://tests/hud_overflow_test.gd`.

Native HUD: `DISPLAY=:99 LIBGL_ALWAYS_SOFTWARE=1` plus same state and `timeout 540 scripts/godot.sh --script res://tests/hud_overflow_test.gd -- --capture-dir=/workspace/reviews/integration-20261013/pr1-independent/captures`.

Focused tests use `--headless --script res://tests/<name>_test.gd`, finite 300s bounds. Logs/manifest/checksums live beside this report. `evidence-manifest.json` binds every raw log, independent probe and native PNG to hashes. The independent probe source derives the existing matrix and adds explicit 18:9/expiry/negative-control checks outside the reviewed checkout.

## Exact-head protocol and isolated account follow-up

The six-pair real Godot/ENet matrix ran from this PR1 checkout using its own `scripts/test_protocol_compat.sh`. Current protocol is 2. The stock released client/server are unpacked from actual `e67f2c8` git archive. Future protocol 3 is a test-only copy with only the protocol constant bumped. All six pairs pass; native processes run headless for network testing.

| Pair | Observed | Result |
|---|---|---|
| Release/release | Joined 0.56s | PASS |
| PR1/PR1 | Joined 0.30s | PASS |
| Release client / PR1 server | No admission; first drop 5.1s; legacy client retries | PASS |
| PR1 client / release server | Explicit missing handshake failure 5.1s; no retries | PASS |
| Future 3 client / PR1 server | Explicit mismatch 0.1s | PASS |
| PR1 client / future 3 server | Explicit mismatch 0.1s | PASS |

`protocol/matrix.md` and 12 server/client logs retain the source matrix evidence. `protocol-run.log` records the successful script summary.

Account verification used the PR1 checkout's **own unchanged** `backend/migrate.py`, `backend/app.py`, `scripts/test_account_network.py` and `game/tests/account_network_probe.gd`, with fresh isolated PostgreSQL databases. PR1's fixture hard-codes HTTP 8080 and ENet 27992; both ports were checked free. A random test-only server key was created under ignored `.local/secrets/server.key` and removed after each run. Backend was stopped and test database dropped. The external isolation wrapper derives from the current integration wrapper but redirects ROOT to PR1, fixes the fixture port, and points Python at the existing venv. No combined backend implementation was used.

Two runs pass all five roles: guest rejected; incompatible protocol 99 rejected (first 0.68s) before gameplay admission; **same unused ticket** subsequently authenticates slot 1 with server-authoritative account display name / waiting roster; ticket replay rejected; newly issued ticket reclaims account slot. Raw HTTP log from the second run records exactly 200 consume for compatible admission,401 for replay,200 for fresh-ticket reclaim. The incompatible peer produced a protocol rejection and no ticket consumption request. Second run preserves full Godot server log by redirecting the unchanged Python fixture's `tempfile.TemporaryFile` to a review file through `runpy`; assertion/game/backend code remains unchanged.

Reproduce: `timeout 200 scripts/test_protocol_compat.sh <new output dir>` from PR1; then `SIGHTBREAK_STATE_DIR=<isolated state> timeout 150 /workspace/sightbreak/.venv/bin/python <review directory>/account_isolated_pr1.py` with 8080/27992 free and local PG 55432 ready. `account-pr1.log`, `account-pr1-godot-server.log`, `account-pr1-backend.log` preserve final run; `*-first.log` preserve initial run. Wrapper stores no production secrets. This is localhost development transport verification, not Internet encryption/security acceptance.
