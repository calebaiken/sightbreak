# Independent review — S10 Linux exported evidence

The completed Linux job **failed overall**. Its stock full-match, plant, defuse, authority and network-input steps passed; offline focus qualification and the four-case layout controller failed. Original screenshots independently support a complete stock match and useful partial layout coverage, not a four-resolution pass. This review does not relabel S10 evidence as S12 qualification.

## Exact provenance and retrieval

- Original run: [39670078785](https://github.com/calebaiken/sightbreak/actions/runs/39670078785), Linux job [119465329709](https://github.com/calebaiken/sightbreak/actions/runs/39670078785/job/119465329709).
- Source commit: `34c720a4a8c394f89734b04d4c998c32d7f85954`, clean game tree `45b6c6ea9d3244700e324e90d6df4778ee28d18e`.
- Runtime content SHA256: `0c471fb5c52826aa0391db7d4514429d08dc683f53d96e89f9176557d8a6f7ed`; validation SHA256: `b1596d491947e1f4f70434b166827261b843ac262da4fc01ff9889ffa5b61bde`.
- Tested engine: `4.7.2.stable.official.ed1daf0bf`; host `Linux-6.17.0-1022-azure-x86_64-with-glibc2.39` (Ubuntu 24.04 runner), software-rendered native graphical exports.
- Executed Linux ELF SHA256: `3ad3661c7180ce9878977b21ed9d5f534d579689122d5c9af3a64ecf04837385`. This is the CI artifact's exact shipped-byte identity; it differs from the local S12 ELF and must not be substituted into that receipt.
- Original QA artifact: `12380194162`, 44,702,833 bytes, SHA256 `4397439b7c09cccf360b7be1980bb2fa75516c7692e7d959af4764e7c590bd83`.
- Full decoded original job log is retained as `independent-qa-s10-linux-full.log`, SHA256 `705cc19f7e1ba5f84076666f31dd9a378f80d947f6d65511e1741cdb5bab5aa4`.

The original archive exceeds the managed 32 MiB download limit. An authorized isolated diagnostic branch (`codex/qa-artifact-slices`, published commit `8a1fa4180fa3079eae7396449e10591c4a89e27f`) produced smaller observations-only artifacts on GitHub. [Diagnostic run 39675027567](https://github.com/calebaiken/sightbreak/actions/runs/39675027567) completed successfully. It verified original run/source/artifact binding, archive length and GitHub digest, then copied unchanged entry bytes with original paths, sizes, CRCs and SHA256 into bounded subsets. It did not run the game, modify observations, or change qualification results. The frozen game branch was untouched. The local reviewed commit `e00be14d3cf89d18de77f8f555efd2c41cce9f74` and published diagnostic commit have identical tree `ab0329c24391597375ba7f8e24ae55437cdfa9da`; publication used the connector after the local CLI token returned HTTP 401.

| Downloaded subset | Artifact ID | Bytes | SHA256 |
| --- | --- | --- | --- |
| retained-qa-index-39675027567 | 12381776096 | 11307 | `e34516454032180bda9a1b5aee810eef723cd98e92c3dc8317324e236432f15b` |
| retained-qa-other-39675027567 | 12381371457 | 14859886 | `64d6b9d957295c8bb05497b81917d9ba71a9a9e3efa73c640a0b253b625ea829` |
| retained-qa-full-match-39675027567 | 12380689320 | 5753640 | `102b52be7fbaa36ab29e5cdeb739025390971289b365fc70e4d53101056b8446` |
| retained-qa-layouts-39675027567 | 12380549605 | 18643005 | `debebbb58fb9bef247567a454905fded234ea8db9db5d63bc7c18d914f91f504` |

All four downloaded subset archive digests matched GitHub metadata. The index binds to the original archive/source. All **185 extracted original entries** matched indexed byte length and SHA256; safe paths/types and exact entry inventory were checked. No full archive or export binary was downloaded outside the managed limit. The separately published objectives subset remains available on GitHub but was not needed for this requested screenshot review.

## Four requested layout cases

| Native size | Retained result | Independent original-image finding |
| --- | --- | --- |
| 960×540 | FAIL: `Actual rendered main menu: confirmation exceeded its wall budget`, 16.249 s | The last raw menu-confirmation PNG is a readable, correctly contained main menu. There is no live HUD, roster or settings capture for this case; those gates remain UNVERIFIED in S10. Forced cleanup is retained. |
| 1280×720 | FAIL: final Tesseract call exceeded its remaining 1.749 s wall budget; case 64.936 s | Actual live HUD, ten-row Tab roster and Field Settings are readable and contained. Raw `06-touch-hud-opt-in.png` really shows active FIRE/RELOAD/USE controls. The last raw keyboard check shows those controls removed, but the automated case still failed its deadline and forced cleanup. |
| 1920×1080 | Capture controller PASS, 74.890 s, clean native exits | Original live HUD, ten-row roster and settings are readable and fit the rendered frame, with default touch controls absent. This is functional layout coverage at default scale, not high-DPI or comprehensive visual acceptance. |
| 1280×800 | Capture controller PASS, 54.318 s, clean native exits | The actual desktop PNG is 1280×800 with 40-pixel top/bottom bars preserving a 1280×720 content area. HUD, ten-row roster and settings are readable and contained in that area. This establishes letterboxed operation, not unrestricted 16:10 composition or Steam Deck certification. |

Eighteen original PNGs were visually inspected and hashed, including all available size scopes, touch enable/disable observations, firing/reload, match completion, final roster and restart. Raw native images were not resized or edited by this reviewer. The 960 and 720 failure classifications are preserved even where their last native images look correct. The S7 touch capture that showed Field Settings remains invalid historical evidence; the distinct S10 active-HUD image does not retroactively fix S7.

## Stock full-match result

The native exported full-match controller completed in **817.326 wall seconds**, with both application processes and Xvfb exiting 0 and no teardown errors. Its actual trace declares stock spawns/teams/random seeds, ten unique actors in 5v5 teams, protocol 6 and prediction disabled. Rules remain buy 15 s, round 100 s, device 35 s, plant 3 s, defuse 5 s and first to seven. The process command contains only opt-in read-only offline observation flags; no fixture or seed flags were supplied.

The local player moved 0.381111 m by native input, fired to 14/60 and reloaded to 15/59. Raw fire/reload PNGs corroborate those authority observations. Trace rounds progress naturally from 1 through 10, including ordinary halftime role/score rotation. Final result is 7–3, human on defense, defeat, zero kills/objectives and nine deaths. The single `completed` event reports exactly one completion callback.

Raw `07-operation-complete.png` visibly shows DEFEAT, 7:3, ten rounds, +120 XP and +250 Credits. Raw `08-final-scoreboard.png` now truly displays the ten-player final Tab roster, with match-over state and visible-roster observation agreeing. This resolves the S7 missing-roster image gap for this new S10 capture only. These images do not confer an 8.5/10 quality rating.

Reward accounting recomputes correctly: 120 base XP, 100 participation Credits and 150 first-daily Credits. The stored profile moves from no matches/history to exactly one match/history entry, 120 XP, level 1 and 250 Credits. A genuinely separate reopened process loads that entire earned profile in a second ordinary, uncompleted stock match; no second completion occurs. The reopened menu visibly shows 250 training Credits, one match and nine deaths, and the subsequent capture shows a new round-1 buy phase. The ordinary 800 in-match funds remain a separate value from the 250 stored training Credits.

Seventeen independent full-match data assertions passed in `independent-qa-s10-linux-recomputed.json`. This is evidence for this actual S10 execution, not proof of arbitrary exactly-once behavior under every interruption or an S12 pass. Its simulation duration is 428.817 s, so wall duration must not be described as real-time hardware performance.

## Retained failures and remaining limits

The S10 offline input/settings flow stops at `Native focus loss pauses actual offline match`; initial application exit is 0 but reopened clean-exit acceptance was not reached. Native actions show OS W/LMB held and focus moved to root, but the required fresh game observation did not complete. This remains a failed qualification attempt; the exact evidence is retained under `offline-input/`. A later independently audited S12 local success is separate evidence.

The S10 layout aggregate remains failed because 960×540 and 1280×720 did not complete. Physical keyboard/mouse feel, touchscreen hardware, controllers, high-DPI scale changes, audio, performance, mobile execution and repository-wide 8.5 quality acceptance remain outside this review. Materials, environment/character detail and the block-like weapon presentation still need art review and improvement; no subjective score is certified here.

S12 shares the same game tree/runtime content but has a different source commit and validation digest. Any S12 claims must identify its own run and exact artifacts. Earlier S7/S10 failures and incomplete coverage are preserved.

Evidence files: `independent-qa-s10-linux-slice-descriptors.json`, `independent-qa-s10-linux-slice-integrity.json`, `independent-qa-s10-linux-recomputed.json`, `independent-qa-s10-linux-extracted/` and the original full job log. No local engine or native gameplay process was launched for this review.
