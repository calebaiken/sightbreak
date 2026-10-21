# Independent review — final S12 Linux CI

**Final Linux CI remains FAIL.** The completed job independently supports a playable exported offline flow, a genuine player plant, and a complete stock match with earned-profile restart. Defuse approach and the layout aggregate failed and remain unresolved gates. Original images support useful functional UI coverage without converting those failures into passes.

## Exact run, source and shipped bytes

Original run [39673232413](https://github.com/calebaiken/sightbreak/actions/runs/39673232413), Linux job [119476278093](https://github.com/calebaiken/sightbreak/actions/runs/39673232413/job/119476278093), source `e3c1194a9c7bb2ff8a5e3b81ab122513dce4a32c`, clean game tree `45b6c6ea9d3244700e324e90d6df4778ee28d18e`.

Runtime content SHA256 is `0c471fb5c52826aa0391db7d4514429d08dc683f53d96e89f9176557d8a6f7ed`; validation SHA256 is `2f5ea31bacef994fd0a14b981e5b6abfca8e83a78da050c29d76c43a2fdc09fc`. The actually executed CI ELF SHA256 is `d7413ef20731cdb6d785e6511d59085834286fb66ac7ec7aaf97efd6c9815841`, matching that artifact's receipt. The independently executed local extracted S12 ELF has a different recorded hash (`fa05beef...`); these byte identities must remain distinct even though source/game-tree identity agrees. No binary reproducibility claim is made.

The engine is `4.7.2.stable.official.ed1daf0bf`, host `Linux-7.0.0-1017-azure-x86_64-with-glibc2.39`, Ubuntu 24.04 runner, Mesa 25.2.8 llvmpipe with LLVM 20.1.2, X11/Xvfb, dummy audio. Both full-match logs retain the unsupported VSync warning. Physical hardware, audio quality and real-time performance are not covered.

Full decoded original job log: `independent-qa-s12-linux-full.log`, 1,142,113 bytes, SHA256 `65e60a0733d298ba1490d75918920a9869abe01a995eba6256c3e049638a9e00`. Original QA artifact `12381946357` is 36,436,976 bytes, SHA256 `d7cb132ab35c2c8ed48f7e5ac3b3b47db59b5c0cc06bdd76e6217d1910f1f0d4`.

Because that original exceeds the managed download limit, the authorized read-only slicer reused its isolated diagnostic branch. [Diagnostic run 39676464953](https://github.com/calebaiken/sightbreak/actions/runs/39676464953) succeeded at commit `cb7de108095171a3f114faf0d950e0f277b1c9d8`. Only the original source run/artifact/SHA defaults changed from the previous slicer version. The runner verified original source binding and full archive digest and copied unchanged observations; gameplay was not rerun. Local reviewed commit `b8c4c5240b09926a609344e5b9a146c297f640e2` and the published connector commit share tree `c58b8283eb79f7fcd62eca91b208465f4115d337`.

| Managed subset | Artifact ID | Bytes | SHA256 |
| --- | --- | --- | --- |
| retained-qa-objectives-39676464953 | 12382820930 | 5210876 | `8d45984fda6517db12aafe5349bd263fa7098efec9032599d11f241c63b06665` |
| retained-qa-layouts-39676464953 | 12382756409 | 11583247 | `4313888560b7acc3a0a6f0a7a633662c325179e16cb4fe598036be5451a81fbd` |
| retained-qa-full-match-39676464953 | 12382621657 | 5620925 | `f6eac3274033f7cc0abc991eb54bb9b78418fbb138db62a68f4d29e50e6892cd` |
| retained-qa-other-39676464953 | 12382117540 | 16995103 | `4905cdd26323960ba5c3f4c4b7495c1f603605bebd9ade4b0d916c1a571d173d` |
| retained-qa-index-39676464953 | 12381238223 | 10862 | `db2af157d51f1665b992f5531b818a838c95cf4bea4e9e1a7886046cc20728e8` |

All five downloaded archives match their GitHub digests and indexed original archive/source identity. All **206 original extracted entries** match indexed length and SHA256, with exact inventory and safe paths/types checked. The index preserves deliberate exclusions such as cache/binaries/TSV; no original pass/failure record was edited. Evidence integrity alone does not imply gameplay acceptance.

## Final exact gate table

| Gate | Final S12 Linux status | Evidence and limit |
| --- | --- | --- |
| Pinned toolchain, packaging controls, export and structural inspection | PASS | Completed original steps, exact clean-source artifact receipts. |
| Native graphical startup | PASS | Actual Linux export ran graphically; headless checks are separate. |
| Native authority/compatibility source regressions | PASS | Actor, match, privacy, prediction, peer lifecycle, input mode, offline observer and objective-HUD suites all exit 0 with their native log gates. |
| Exported network keyboard/pointer input | PASS | Original dedicated native-input step succeeds; this is local authoritative input coverage, not internet-security acceptance. |
| Offline input/settings/restart/focus | PASS | 192.998 s; both app roots exit 0 and cleanup is empty. Actual runtime-loaded settings and neutral-input recovery observations are retained. |
| Player plant and natural objective resolution | PASS | 90.509 s; final E edge spans 180 ticks / 3 simulation seconds, contribution 0→1, funds 800→1100. Ordinary bots later defuse; next round and clean exits are retained. |
| Player defuse scenario | FAIL | 57.201 s: `Legitimate native movement did not reach the requested floor position`. Ordinary bot plant was observed, but player approach failed before successful defuse qualification. Actual app required forced cleanup; this is not a clean-exit pass. |
| Stock full match and earned-profile restart | PASS | 567.025 s; eight natural rounds, final 7:1 defeat, one completion, earned XP/Credits preserved and actually loaded by reopened process. Both apps/Xvfb exit 0, cleanup empty. |
| Four-resolution/touch layout aggregate | FAIL | 960×540 and 1280×800 complete; 1280×720 and 1920×1080 fail OCR deadlines, with forced cleanup. Detailed visual scope follows. |
| Overall Linux job | FAIL | Defuse and layout failures are preserved. Successful later/other-host observations do not replace them. |

## Original full-match images and independent accounting

Raw `07-operation-complete.png` visibly shows DEFEAT, FINAL 07:01, eight rounds, zero eliminations/assists/objectives, seven deaths, +120 XP and +250 Credits. Raw `08-final-scoreboard.png` truly shows ten roster rows and the match-over 7:1 score. The recorded visible-roster state agrees with the frame. Raw `09-reopened-menu.png` shows one match, seven deaths and 250 stored training Credits, while `10-reopened-earned-profile-stock-match.png` shows a separate new round-1 buy phase.

The raw trace starts with ten living actors in ordinary stock-spawn/side/random-seed conditions, protocol 6, prediction disabled and unchanged 15/100/35/3/5-second rules with first-to-seven scoring. Native input produces 0.381111 m initial displacement, fire to 14/60 and reload to 15/59. Round sequence is 1–8, with ordinary halftime rotation. The single `completed` event records one completion callback; the local player ends on defense and correctly loses 7:1.

Accounting independently recomputes 120 XP from the base award with no kills/objectives, and 250 Credits from 100 participation plus the first-daily 150. The offline profile advances from no matches/history to exactly one entry, XP 120, level 1, seven deaths and Credits 250. The second actual process's initial observer event contains the entire earned profile, equal to the saved `training_after`, in an uncompleted stock match. Settings agree and no second completion occurs. This is runtime loading as well as disk preservation, with no account reward claim.

Nineteen read-only data assertions pass in `independent-qa-s12-linux-recomputed.json`; that audit explicitly leaves the underlying Linux CI status false. Full-match simulation duration is 268.633 s versus 567.025 wall seconds. These timings are evidence of the virtual software-rendered run only.

## Four sizes: original-image scope

| Size | Original-image finding | Acceptance scope |
| --- | --- | --- |
| 960×540 | Live HUD, ten-row roster and visible settings fields are readable and contained. Controller finishes in 40.139 s with app/display exits 0. | Functional captured-layout pass at default scale. This agrees with the separate extracted-S12 960 result and does not erase S10's earlier failure. |
| 1280×720 | Live HUD, ten-row roster and Field Settings are readable. The original `touch-hud-check-13-ocr-original.png` visibly shows actual active FIRE/RELOAD/USE controls, not a paused field menu. | Controller still FAILS: Tesseract exceeds the remaining 4.576 s, total 70.203 s; toggle-off/final completion and clean exit are not established by this case. No named final touch capture was produced, but the unchanged raw confirmation image supplies scoped visual evidence. |
| 1920×1080 | The last original menu-confirmation frame visibly shows a readable, contained main menu. | FAIL before named menu/live captures: Tesseract timeout 12 s, case 20.156 s. Live HUD/roster/settings remain UNVERIFIED for this S12 CI case. S10's distinct successful 1920 evidence stays separately source-bound. |
| 1280×800 | Original live HUD, ten-row roster and settings fit a 1280×720 content area with preserved 40-pixel upper/lower bars. Case completes in 59.393 s with clean exits. | Functional letterboxed-layout pass, not unrestricted 16:10 layout or Steam Deck certification. |

Fifteen original screenshots were independently viewed at their native pixel dimensions and their hashes retained. No raw image was transformed or substituted. Secondary text, other scales, settings below the scroll area and physical input feel need additional human/device review. No 8.5/10 category score is certified. Weapon silhouette/detail, character art, material depth and polygonal smoke remain visible quality limitations.

## Preserved failures and follow-up boundary

A separately executed local extracted-S12 defuse scenario genuinely passed the full 300-tick/5-simulation-second defuse after ordinary bot planting; its detailed independent report is `independent-qa-r12-extracted-review.md`. That does not erase this CI approach failure. Conversely the local extracted plant attempt failed while this CI plant passed. The existing evidence demonstrates functionality and remaining trajectory/automation reliability limits; it does not justify a fully green cross-platform alpha claim.

The new diagnostic workflow exists only on `codex/qa-artifact-slices`; no root game/runtime files or frozen branch were changed by this review. No local engine process was launched. Later uncommitted/documentation/controller changes are outside the frozen source qualification above. Original S7, S10 and S12 failures remain retained.

Supporting files: `independent-qa-s12-linux-ci-metadata.json`, `independent-qa-s12-linux-slice-descriptors.json`, `independent-qa-s12-linux-slice-integrity.json`, `independent-qa-s12-linux-recomputed.json`, and `independent-qa-s12-linux-extracted/`.
