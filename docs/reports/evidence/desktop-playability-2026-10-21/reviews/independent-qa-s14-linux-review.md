# Independent final S14 Linux evidence and delivery review

Read-only audit of completed run **39678945538**, job **119496049540**, on 2026-10-21. No source mutation, engine launch, test rerun, timeout change or retry was performed for this review.

## Identity and retained evidence

- Source `d6784ab2d81dae204b6a699f0177f7e9d70bec4e`; game tree `45b6c6ea9d3244700e324e90d6df4778ee28d18e`; runtime-content SHA-256 `0c471fb5c52826aa0391db7d4514429d08dc683f53d96e89f9176557d8a6f7ed`; validation SHA-256 `fa8c8697056ca74c9b7347b1622ebd881fa727306147d5c42ef15564afe9d86d`.
- Executed Linux ELF SHA-256 `664c1395b95ed60b8806b0f601fe0c57a5bd5df249639a1b545e938800f25249` (84,221,848 bytes).
- Full raw job log: `independent-qa-s14-linux-full.log`, 665,880 bytes, SHA-256 `405600ad25608fa9ebee80a264abadee71f028bf98bfb6dd30dee33bce93ec0d`.
- Downloaded QA artifact **12384822538**: 23,011,777 bytes, verified SHA-256 `ffd4272f3219c166a52531bd15b2be56d5db3b661baaba51b80c174347ac0f71`. Safe extraction retained 147 original observation files. `independent-qa-s14-linux-artifact-integrity.json` records per-file hashes and excluded cache/state/other files. Originals were not rewritten.
- The native inner development ZIP is **36,514,099 bytes**, receipt-backed SHA-256 `5eed61ce8bd2c465255f5712970df3765e50774635bc47ba24732316cd2704c5`. This audit did not download/re-inspect the 143,619,511-byte outer build artifact **12385190678**. Do not equate this receipt with the separately extracted local S12 packages.

## Exact completed gates

The whole Linux job is **FAILURE**. Export/inspection, native graphical menu, eight source suites, network input, player defuse and stock full match pass their individual gates.

- **Stock full match PASS:** natural rounds 1 through 12; final **6:6 DRAW**; 447.433333333255 simulation seconds / 1088.423666821 wall seconds; 0 kills, 0 assists, 12 deaths, 0 objectives. One ordinary completion/history entry, +120 XP and +250 offline Credits. The earned training profile equals the second application's actually loaded initial profile; normal initial/reopened exits are 0/0, cleanup errors empty.
- **Defuse PASS:** 84.590468027 wall seconds; actual interaction edge tick 1305 to completion tick 1605, exactly 300 ticks / 4.999999999999801 simulation seconds. Recorded approach is 3.399974823 m, contribution 0 to 1 and match funds 800 to 3800. Initial/reopened exits 0/0, cleanup empty. The software-render host does not qualify five-second physical wall-time performance.
- **Offline input FAIL:** 220.302932559 wall seconds, `Natural exported round completion`; the unchanged round-observation gate expires. The client is subsequently terminated with -15; no successful close/reopen is claimed. Recorded cleanup errors are empty.
- **Plant FAIL:** 63.498663561 wall seconds, `Legitimate native movement did not reach the requested floor position`; the client is subsequently terminated with -15. This is not a player-plant scenario pass.
- **Layouts aggregate FAIL:** 960x540 completes capture generation in 49.010563195 seconds. The next 1280x720 case captures its menu, then Xlib aborts with `BadWindow`, `X_GetProperty`, resource `0x600003`. There is no final 1280x720 case receipt; 1920x1080 and 1280x800 are not reached. Cleanup after that abrupt controller exit is **UNVERIFIED**. This differs from the retained earlier OCR timeouts and does not establish a game crash.

## Original images and documentation challenge

Independently viewed the unchanged full-match summary, ten-row held-Tab scoreboard, earned reopened menu and reopened live stock-match images, plus defuse hold/completion originals. The summary visibly shows 6:6 / 12 rounds / +120 XP / +250 Credits; the reopened menu shows one match and 250 training Credits. The final defuse image shows POST, DEVICE/DEFUSED, living 100 health and 3800 funds. These agree with their receipts. Low-detail procedural graphics and smoke remain visible; these images do not award an 8.5 quality gate or certify physical hardware.

Reviewed the current delivery report and README/build/testing/limitations/milestone/Steam wording. **No remaining material factual correction found in the final S14 Linux paragraphs/table or package provenance.** The report correctly preserves S12 packages versus later S13/S14 validators, source-specific failures, receipt-only native ZIP hashes, unchanged five-second reload wait, Windows offline recognition failure, Intel startup failure and unverified hardware/mobile/macOS gameplay/Steam gates. Reproduction requires a new export for a new documentation/tooling HEAD; old S12 receipts are not re-attested.

The current red overall jobs and incomplete native interaction/layout qualification remain release blockers. Successful stock matches, saved progression and separate objective passes are genuine scoped evidence, not complete desktop release acceptance.
