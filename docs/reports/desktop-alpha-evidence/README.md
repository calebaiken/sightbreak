# Desktop alpha evidence — 2026-10-20

See the [delivery report](../DESKTOP_ALPHA_REPORT.md) for source identities, commands,
platform scope, failures and acceptance limits. Final implementation/build/test
freeze is `0fb74800cffb96077069144028d113e308ef1744`; this directory was committed
later without changing runtime or validation source. Original screenshots are
copied byte-for-byte. [Evidence SHA256s](evidence-checksums.txt) cover this selection.
Full attempts remain in `/workspace/desktop-evidence/` on the development host;
CI evidence retains its own source identities and expires after14 days.

| Evidence | Scope |
| --- | --- |
| [Frozen suite receipt](frozen-regressions.json), [raw log](frozen-regressions.log), [controller](frozen_regressions.py) | Full displayed maintained suite plus isolated PostgreSQL/admission/crash-outbox/native-economy/simulation; exit0 and exact source unchanged |
| [Linux network receipt](native-network-final/results.json), [authority](native-network-final/authority.json), [server log](native-network-final/server.log), [settled capture](native-network-final/08-settled.png) | Actual export, six shots, real R reload, both exits0; synthetic loopback guest authority |
| [Linux offline receipt](native-offline-final/results.json), [client log](native-offline-final/client.log) | Real exported living-player fire/reload, natural round, buy/switch, roster/settings/reopen; full match/plant/defuse remain unverified |
| [Fire](native-offline-final/05-after-fire.png), [reload](native-offline-final/06-after-reload.png), [roster](native-offline-final/06b-scoreboard.png), [SMG purchase](native-offline-final/06e-purchased-smg.png), [settings](native-offline-final/07b-field-settings.png), [reopen](native-offline-final/09-reopened-menu.png) | Selected original rendered pixels; OCR preprocessing did not alter these files |
| [Before focus correction](focus-baseline/04-focus-restored.png), [after](focus-candidate/04-focus-restored.png) | Separate comparison sources/receipts; frame-budget exit, not final normal-close qualification |
| [Windows retry raw CI](ci-windows-final-retry.log), [first failure](ci-windows-final.log), [source diagnosis](windows-reload-assessment/ASSESSMENT.md) | Exact0fb retry passes unchanged assertions; original reload-completion timeout remains unexplained |
| [Linux CI](ci-linux-final.log), [macOS ARM CI](ci-macos-arm-final.log), [Intel failure CI](ci-macos-intel-final.log), [earlier macOS14 abort](ci-macos-r1-decoded.log) | Hosted native execution; graphical success and failure kept separate |
| [CI artifact metadata](ci-artifacts.json) | API-returned artifact IDs/digests/source and expiry; outer diagnostic archives are not release payloads |
| [Manifest](packages/manifest.json), [package checksums](packages/checksums.txt), [export exits](packages/export-results.json), [inspection](packages/verification/results.json) | All five local exports; exact source/payload/mode/version receipts and Android signature/iOS project checks |
| [Extracted delivery](delivery-final/results.json), [launcher log](delivery-final/linux-launcher.log), [verifier](verify_delivery.py) | 311 archive/payload/mode/native-format checks and extracted Linux launcher exit0 |
| [Manifest controls](manifest-final.log), [optimized run](manifest-final-optimized.log) | 24 tests in each run; stale/content/mode/version/reused-output rejection remains enforced |
| [Independent final review](final-independent-review.md), [capture/executable hashes](final-independent-review-hashes.json) | Agent source and original-image review, not independent human/hardware or8.5 acceptance |

Earlier failed manifest runs `manifest-r1.log`–`manifest-r9.log`, X11 close and
D-Bus cleanup failures `native-network-r1/` and `native-network-r2/`, offline
OCR/buy-phase attempts `native-offline-r1/` and `native-offline-r2/`, initial main
expectation `main-candidate-r1.log`, profile guard `baseline/profile.log` and
initial validation execute-bit failure `maintained-r1.log` remain recorded.
The passing isolated profile rerun is `baseline/profile-isolated.log`. Earlier
sources are supporting comparisons, not final-source passes. Corrected runs did
not delete failures or bypass assertions. The diagnostic scripts are evidence
controllers outside the frozen repository source; they are excluded from game
packages. No user saves, credentials, account journals, caches or binary payloads
are committed in this evidence directory.
