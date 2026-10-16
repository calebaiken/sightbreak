# Independent final evidence audit — stabilization V2

**The source-bound network campaign, three local native exports, actual exported network-client input, and corrected live offline-input evidence are supported. CI artifact delivery is supported by completed-job/upload/API/download receipts. The full regression matrix is still pending and is not counted as a final 74-group pass.** This was a read-only evidence audit; no new Godot/engine execution, source modification, download, merge or GitHub post was performed.

## Source identity

Final tested/exported game: `701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd`, game tree `2d2b174c2145e9755ddfc78a1369e74443fcc400`, shipping SHA256 `12d50718f295f04d21de691f31fbde8f03612b145680aaa592ef9e6e08cd5eec`. The build worktree is detached at that commit and tracked-clean. This reviewer independently recomputed the shipping hash using the documented exclusion of tests/import cache. It matches the source manifest, export manifests and native receipts.

The strengthened offline controller is separately committed at `a9d873eea9373fe7425b6e84da5e5971468af0a4`; independently hashing that committed script produces `30d408a9a92ab10472036a9e589e2e831b5e30bd5edc9cc10fe2dafd74c134c3`, matching the successful live-input receipt. This controller identity must not be substituted for the game/export source. Primary changes after 701 do not change `game/` at this audit point.

## Imported network campaign

`network-r2-imported/campaign.json` contains exactly 12 completed conditions: RTT 0/50/100/150/200, jitter, loss, reorder, combined impairment, blackout, reconnect and prediction disabled. All 12 commands exit 0, each embedded summary equals its standalone raw `summary.json`, all summaries bind to clean 701 source, and no condition reports failures. Each has 10 clients, maximum ENet occupancy 10, a shared stop, and 10 distinct final authority actors/peers. This reviewer scanned all 132 server/client logs with the maintained error/leak rule; none fails.

This supports **12/12 in the imported, loopback real-process campaign**, within its 18-second measurement windows and synthetic impairment scope. It does not establish public-Internet or physical-cellular performance. The aborted campaign started before import is separate retained evidence, not part of these passes. Details: `network-audit.json`.

## Local native exports and package identity

The final `builds/manifest.json` and external **`export-r2-packaging.json`** match. All three platform source records match the aggregate manifest and say completed/clean 701. This reviewer independently verified every recorded platform payload's byte size/SHA256, all five distributable descriptors, and the package `checksums.txt`.

| Local final artifact | SHA256 |
| --- | --- |
| Linux ELF | `808f66b6d78b0547ddba9e47d4b8449d7fae478f2ccce5307a1eeccdddbccbbe` |
| Linux ZIP | `e4d8fdbe9f4192989bc5b66126011d4342f3d270f5815f0e54163fb70f80017c` |
| Android APK | `8cd5a9c967bc5e26d4f0ef1152783aee616f12e409376ee134852a8fad6d7424` |
| Android ZIP | `3baa8ca0350fb6139bd64c8fd03bf27128e169a413f20b96564fff9b3b16b75d` |
| Unsigned iOS Xcode ZIP | `1092056e039c99f1167be7f83cf081b576f54b93525b06243833d95b1405bfee` |

Independent pack/directory inspection verifies 130 Linux resources, 132 Android assets and 130 iOS resources, with tests excluded and required imported scenes/textures/compiled modules present. This includes bot AI, reload audio/phases, confirmation UI and movement helper. The retained verification/raw metadata logs confirm Linux menu/demo checks; Android v2/v3 signing, SDK 24/36, ARM64/x86_64, landscape/launcher metadata; and unsigned iOS project metadata with local-network permission. The iOS project says marketing 0.3.1/build 4 and an empty signing team. It is not a compiled/signed iOS app or physical-device validation. Details: `artifact-audit.json`.

The earlier external `export-packaging.json` identifies aee6 and different package hashes. It is retained history; final links/checksums must use the r2 descriptors above.

## Actual exported client evidence

`native-network-r2/results.json` binds the actual Linux ELF hash above to both clean 701 source and the source-engine authority. Client and server exit 0 with clean raw logs. The server observes actor 1, six shots, ammunition falling to 24, a native client reload command, reload completion, protocol 6 and prediction default false. Final input acknowledgment is 1231. This is a guest loopback authority fixture, not an actual rewarded account match.

Original screenshots were inspected. `03-exported-network-rifle.png` shows 100 health and rifle 30/90; `08-settled.png` shows 100 health and rifle 30/84, consistent with six shots followed by reload. The file named `07-after-authority-reload-completion.png` still visually shows the client reload animation, demonstrating software-rendered lag; it must not be represented as a frame proving the visible weapon had already finished. The authority receipt and later settled frame support completion.

`native-offline-r2-live-input/results.json` matches the same ELF and game source, records normal exit/clean logs, and binds the separately hashed controller. Original `05-after-fire.png` and `06-after-reload.png` visibly show a living local player at 100 health with **SIDEARM 14/60 → 15/59**. Both display a live round; no eliminated/spectating state appears. The ammunition sum is conserved at 74. The later original `08-return-menu.png` shows return to the actual menu. This supports the narrow native offline fire/reload/menu flow, not offline kills, tactical quality or phone performance.

Earlier `native-offline/` and `native-offline-r2/` receipts set `passed=true` under a weaker controller. Those flags must be interpreted as flow/clean-exit only. For example the older r2 `05-after-fire.png` is explicitly eliminated/spectating with 15/60. These old attempts are not accepted gameplay passes. The draft report correctly says so. Details: `native-receipt-audit.json`.

## CI distribution receipt

Completed job `116833910480` in run `38858072161` has API status completed/conclusion success and successful export/inspection/package/upload steps. Decoded job output prints passed verification for source 701 and shipping content 12d507…, then successful finalization of artifact **12028135819**, size **287,276,825 bytes**. API metadata agrees with the upload log's aggregate SHA256 **`8f230eab3d953ba40f1981286e71137e07f2ff5548b0ad5eda355c58c9ec5f1e`** and says unexpired. The sanitized supported-connector receipt records successful download and a reusable file reference.

This reviewer inspected those static receipts and performed no additional aggregate download/rehash. The CI aggregate digest is distinct from the local nested platform ZIP hashes. The preserved `actions-v2-runs.json` remains an earlier in-progress/null snapshot; the later completed job, artifact API, upload log and download receipt establish the completed delivery. A final run-status receipt would remove this bookkeeping ambiguity. Details: `ci-receipt-audit.json`.

## Draft report and preserved independent evidence

The draft `docs/reports/STABILIZATION_V2_REPORT.md` contains no material source or acceptance overclaim in the reviewed text. It correctly separates shipping source from controller tooling, retains the historical 64/70 result, leaves final matrix results pending, distinguishes functional/source correctness from failed 8.5 tactical/visual gates, and preserves target-device/unexplained timing limitations.

The broad wrapper's unmutated audio-cancel baseline really says FAILED in retained raw output. Its discarded raw cause is not recovered by ten later serial successes or 21 prototype successes. The draft's residual qualification is necessary and must remain after a successful matrix. Maintained graphics controls N25/N26/N27 are caught; raw N25/N26 output includes actual finish-luma failures, while N27 catches loss of the polymer split. These checks validate test sensitivity, not the open visual-quality gate.

The source and original menu screenshot confirm the static `0.3.0-dev` banner despite project/Android/iOS/manifest metadata 0.3.1-dev/build 4. The draft correctly calls this a known cosmetic identity issue; metadata/source manifests govern package identity. It should not claim the menu banner was corrected.

All six checked independent Markdown files are byte-identical between external originals, the primary worktree and committed subtree: AI review, audio causality, timing review, network review, graphics review and graphics PR2 payload. `verbatim-audit.json` records their hashes. The graphics review retains its frozen-source 8/32-warning reproductions and attributed later harness-fix follow-up, without silently changing either.

The report's pending-results paragraph is a temporary placeholder: final publication should append completed local export/native/network/CI results using r2 descriptors, while the full matrix must remain pending until its frozen final summary and logs complete. At this audit snapshot the matrix records **59/59 completed rows**, lacks final completion fields, and is not a final 74/74 result. `matrix-snapshot-pending.json` preserves that boundary. No main merge, production acceptance, physical-device signoff or universal audio-determinism claim follows from this evidence.

## Final completion addendum — 2026-10-16 UTC

**The new complete frozen campaign is independently supported as 74/74 PASS on `701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd`.** This final section supersedes the earlier pending-matrix and pending-run-status observations above; those observations remain as the record of what was available at the earlier audit snapshot. It does not revise the historical 64/70 campaign or relabel any unsuccessful attempt.

The reviewer independently derived the expected inventory from the frozen `validate_matrix.py` and maintained `validate.sh`, and matched all 74 unique summary names. All 72 execution rows bind to 701, exit 0, have their actual raw log present, and independently pass the maintained native-error plus `HARNESS_ERROR` scan. The final two passing rows have valid underlying JSON: no nested ObjectDB/leaked-instance logs, and equal initial/final source records with both whole-checkout clean-state flags false for dirtiness. The final native render/HUD/paint execution logs pass; their durations are 56.069 / 197.034 / 16.221 seconds. The lifecycle log records 12 natural rounds, 380.9 simulated seconds, 78 kills, halftime and one result report, with `plant_observed=false`; it does not establish natural objective completion.

Both detached regression and build worktrees remain clean at exact 701. Independent filesystem rehashing again produces game tree `2d2b174c2145e9755ddfc78a1369e74443fcc400` and shipping SHA256 `12d50718f295f04d21de691f31fbde8f03612b145680aaa592ef9e6e08cd5eec`. The primary checkout's later evidence/tooling commits preserve the identical game tree and shipping hash, with no game working-copy changes. Final matrix summary SHA256 is `57cf6696c7583c6c779b42c4096c18801a1a91c8a8d1f30b4f0fac6f58b51b04`. See `matrix-final-audit.json` and the read-only reproducibility script `audit_final_receipts.py`.

All **187** recursively retained matrix `.log` files were scanned. There are **zero ObjectDB/leaked-instance warning logs**. Ordinary engine ERROR lines remain in four deliberately incompatible legacy/current protocol process/userdata paths (two original logs plus their userdata duplicates). All eight expected protocol outcomes pass, including rejection/timeouts for these legacy pairings. A fifth path, `protocol/release-e67f2c8/docs/reports/native-render.log`, is copied historical release-tree evidence with two old texture-leak ERROR lines. These diagnostics are explicitly classified in the JSON; the result is not a universal assertion that every archived log is engine-error-free. All 187 primary evidence-copy logs are byte-identical to the external originals, as are final summary/identity/resource-audit JSON. The primary `MATRIX.md` contains all 74 rows and the negative/history qualifications. All 25 relative links in the final report resolve except this final audit's own target, which is intentionally awaiting the parent's verbatim evidence copy.

The newly saved **`actions-v2-final-run.json`** independently records run 38858072161 as completed/success at head 701. It removes the earlier run-snapshot bookkeeping ambiguity and agrees with the completed job, successful upload, artifact API and supported-connector download receipts already audited above. Artifact 12028135819 remains source-bound, 287,276,825 bytes, aggregate SHA256 `8f230eab3d953ba40f1981286e71137e07f2ff5548b0ad5eda355c58c9ec5f1e`. The reviewer performed no new download or aggregate byte rehash; local nested package verification and the CI aggregate receipt remain distinct evidence.

The final head receipt shows Gemini PR14 advanced to `48eb0586e273f96dc20b346ed444d00ab0f3ac30`, two commits beyond integrated 7397efd. The saved comparison identifies changes in `arena.gd` and `bot_ai.gd`. **Those later changes are not integrated or independently validated by this campaign.** The final report now explicitly preserves that source boundary and requests renewed independent validation before their integration. All six earlier independent Markdown reports remain byte-identical among external evidence, primary working copy and committed subtree; their original observations, warnings and attributed follow-ups remain intact.

The final report's completed matrix/export/network/native/delivery statements are supported within the scopes documented above. Its historical-failure, unexplained broad-wrapper cancellation, static menu 0.3.0-dev banner, local-versus-CI checksum, weak earlier offline attempt, rendering-lag, natural-objective and device limitations remain accurate. Ten later serial and 21 prototype successes still do not recover the discarded cause of the broad-wrapper baseline failure. Maintained graphics negative controls establish sensitivity, not visual quality. Tactical/visual 8.5 acceptance remains failed; physical mobile, public Internet, listening quality and production acceptance remain unverified.

**Final verdict: accept the evidence as a source-bound development checkpoint for clean 701: complete 74/74 matrix, separate imported 12/12 network campaign, three inspected local exports, actual exported native client fire/reload flows, and completed CI artifact delivery. No merge, production, tactical/visual-quality or physical-device acceptance is implied.** No engine run, source edit, network action or GitHub post was performed in this final audit.
