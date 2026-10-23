# Desktop alpha implementation and validation — 2026-10-20

SIGHTBREAK 0.3.2-dev (build 5) now has Windows x86_64 and macOS Universal 2 exports, preserved Linux/Android/iOS exports, portable selected-target tooling, strict source-bound packages and native CI. The exported Linux build completes the tested living-player offline flow with real input and persistent settings. This is a development delivery, with incomplete platform and commercial acceptance recorded below.

## Source, dependencies and environment

- Branch: `codex/desktop-steam-readiness`; [draft PR #22](https://github.com/calebaiken/sightbreak/pull/22), stacked on PR #16 `d2439acdd5f73df7bae5ada62ee1e3dec2cf30db`.
- **Frozen implementation/build/test source:** `0fb74800cffb96077069144028d113e308ef1744`.
- Game tree: `ce6ac523e5882302bf95f53314b388f5cd7805a3`.
- Physical runtime-content SHA256: `7db95847f40a5b3a4a286493d8536f36c7d595fe0e778993bb9b2d4da8785f0e`.
- Local validation-tool-content SHA256: `35cbf7d559e1e732ac4344a6584b44bfbd27c05b84570bd50874f515c2954bfe`.
- Official engine: `4.7.2.stable.official.ed1daf0bf`; editor/templates retain official SHA512 checks. Local host: Debian 13, Linux 6.18.55 x86_64, glibc 2.41, Python 3.12.14; Xvfb/X11, Mesa 25.0.7 llvmpipe, two software-render threads. Dummy audio mixing is not speaker/listening acceptance.

The [preflight](DESKTOP_PREFLIGHT.md) records inspected branches, PR heads, interfaces and integration gates. PR #16 has the same game/backend/server trees as the supplied V2 source `701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd`. PR #17 and #18–#21 remain separate unfinished candidates; bot #14 and art #2 were not merged. Backend, dedicated server, gameplay/AI/weapon mechanics and network directories have no diff from the selected base. Protocol 6, default-off prediction, disabled live rewind, account admission, reward/idempotency/price consent and offline/account separation are preserved. V2 passes are historical.

Documentation/evidence commits after the frozen source do not relabel its artifacts. To reproduce or revalidate these exact receipts, check out the frozen SHA in a clean isolated worktree. Verifiers deliberately reject these artifacts against a different HEAD, even a later documentation-only commit. A new qualification needs a fresh build root and export. No main or other developer branch was changed or force-pushed.

## Changes delivered

The Python toolchain selects Windows/Linux/macOS editors and independently requested templates, preserving native AppData/Library/XDG behavior. Export, inspection and packaging no longer require Bash or all mobile SDKs for a desktop target. Windows PE resources carry the game icon/name and version 0.3.2.5. macOS carries both Mach-O slices, metadata/icon/executable modes and development ad-hoc signing; the app is distinct from the unsigned iOS project.

Manifest/ZIP checks bind the exact clean commit, game tree, physical runtime and tooling bytes, every payload hash, and physical/archive mode. Stale exports, changed bytes/modes, incomplete payloads, reused export roots, developer files and credentials are rejected. Required generated Android signature metadata, the macOS console launcher and precisely scoped iOS asset catalogs are accepted. Signing/filesystem differences prevent a binary-equality promise. Packages exclude test harnesses and local caches/journals; outer CI evidence artifacts also contain diagnostic state and are not themselves release payloads.

Desktop focus loss now clears actions/look, releases the cursor and opens an explicit-resume field menu; offline play pauses, including an already-open buy menu, while network authority continues. Field settings are available during play; text scaling rebuilds the HUD. Saved windowed/borderless/exclusive fullscreen and unscaled screen-relative mouse motion are implemented. Version text comes from project metadata. Existing touch/controller paths are preserved; hardware qualification remains open. Source review also identifies inherited touchscreen-desktop routing: `DisplayServer.is_touchscreen_available()` forces touch HUD and suppresses mouse capture even on a desktop. Touchscreen laptops therefore retain a P1 input-selection defect; the verified nontouch desktop results do not clear it.

Native controllers use X11/XTest or Win32 `SendInput`, raw screenshots and normal OS window close. Each attempt is bounded, source checked and process owned; nonzero exits, leaks and surviving descendants fail. Isolated Xvfb automation suppresses unavailable D-Bus/accessibility autolaunch; product startup is unchanged, and portal/screen-reader qualification remains UNVERIFIED.

## Platform evidence

| Platform | Export/package inspection | Native execution and remaining scope |
| --- | --- | --- |
| Linux x86_64 | PASS; ELF/PCK/modes, packaged launcher and all shipped bytes | PASS locally and Ubuntu 24.04.5 CI: graphical menu, real network input/reload, living-player offline flow, settings/reopen and normal exits. X11 software rendering; Wayland and physical GPU behavior UNVERIFIED. |
| Windows x86_64 | PASS; AMD64 PE, icon/version/PCK and package | PASS native export/menu and exact-source retry of real input: four authority shots, native R command/reload, client/server exits 0 via WM_CLOSE. The first final-source attempt timed out awaiting reload completion; cause unresolved, retained. Native Windows Server 2025 VM evidence does not establish Windows 10/11 physical-PC performance or full offline/objective coverage. |
| macOS Universal 2 | PASS; both slices, plist/icon/PCK/modes; ad-hoc development bundle | Apple Silicon macOS 15.7.9: PASS default graphical menu, headless menu/demo and five native source suites. Intel macOS 15.7.9: FAIL graphical startup (120-second timeout, Apple Software Renderer); explicit OpenGL diagnostic also timed out. Full macOS input/gameplay, Gatekeeper, Developer ID/notarization UNVERIFIED. |
| Android | PASS; APK resources, ABI/version/SDK/launcher/orientation, v2/v3 debug signatures | Physical/emulated Android execution UNVERIFIED this milestone. |
| iOS | PASS; unsigned Xcode project/resources/catalogs/modes | Xcode compilation, signing, simulator and iPhone execution UNVERIFIED. This is not a macOS app or IPA. |

Final CI: [run 39384250334](https://github.com/calebaiken/sightbreak/actions/runs/39384250334), exact frozen source. Linux and Apple Silicon jobs passed. Windows passed attempt2 with unchanged source/assertions; its attempt1 reload-completion timeout remains retained and unexplained. Intel failure remains red; diagnostic overrides do not satisfy the default launch gate. Earlier macOS 14 ARM jobs abort with `NSInvalidArgumentException` in ANGLE/AppleParavirt (`newArgumentEncoderWithLayout:`), retained in raw evidence. A macOS 15 ARM pass does not clear that older-host failure or the Intel failure.

## Executable gameplay and regression results

| Check | Actual result |
| --- | --- |
| Local exported Linux + real authority | Exit 0; six server-observed shots, rifle 30→24, native R command, completed 30/84 reload, protocol 6 with prediction disabled, client/server exits 0 and no cleanup errors. Synthetic guest practice rifle, no account rewards. Native move/aim was delivered; this fixture does not measure authoritative displacement. |
| Exported Linux offline | Exit 0; ten-player offline 5v5, living player, WASD/mouse/fire, sidearm 13/60→15/58 with 73 total rounds and 100 health, natural round 2, funded SMG purchase, live-phase 1/2 switching, Tab roster, field settings, sensitivity changed through UI, normal close/reopen and saved equality. Existing offline record preserved. |
| Focus before/after | Baseline restored focus shows active HUD; candidate shows FIELD MENU / Training is paused / RESUME. Independent original-image review. Comparison used a frame-budget exit, separate from the final normal-close passes. |
| Maintained gameplay/UI/network/backend suite | `bash scripts/validate.sh --backend`: exit0 with exact before/after source identity. 51 recorded suite log files completed, including five rendered probe groups; actor 73, main 42, landscape 9217, UX 2227, HUD 2435, privacy 55, prediction 725 and peer 16 checks. Natural bot lifecycle: 12 rounds, 6–6, 78 kills, halftime, one result (plant_observed=false). Real ENet lifecycle/network, 61 PostgreSQL tests, admission capacity, result crash/outage/lost-ack/restart replay (exactly 10 grants), native economy 37/37 and economy simulation conservation passed. One dependency deprecation warning retained. |
| Packaging negative controls | `python3 scripts/test_build_manifest.py -v` and `python3 -O scripts/test_build_manifest.py -v`: each exit 0, 24 tests. Includes stale/source/content/mode/missing/extra payload and version controls. |
| Extracted delivered packages | Exit 0, 311 checks across five ZIPs: inventory/hashes/modes/safe paths, ELF/PE/Mach-O/PCK inspection and actual extracted Linux launcher exit0. All 9 entries in final `checksums.txt` verify. |
| Independent review | [Agent audit](desktop-alpha-evidence/final-independent-review.md) independently checked source corrections, receipt/binary hashes and original Linux captures. No human quality score or physical-device acceptance is awarded. |

Raw logs/receipts and selected original captures are in [desktop-alpha-evidence](desktop-alpha-evidence/README.md); binary/package provenance is in its [manifest](desktop-alpha-evidence/packages/manifest.json) and [checksums](desktop-alpha-evidence/packages/checksums.txt). Native source tests are distinguished from exported-client gameplay. The prior all-suite run without a display is supporting evidence only; it is not the frozen rendered gate. Earlier fresh PostgreSQL run: 61 passed, exit 0; final combined status above governs acceptance.

The exported offline check has **not** completed player-driven planting/defusing, a full exported match, or a newly earned completed-match training increment. The preserved record is not proof of new training rewards. Grenade/smoke input, controller-only navigation, physical input feel, mixed-OS peers, DPI/resolution/window-mode combinations, accessibility/portals and sustained frame pacing still need qualification. Headless bot tests do not close these gaps. No new ten-client 12-condition campaign, complete V3 matrix, production Internet-security acceptance, Steam Deck certification or per-category 8.5 acceptance is claimed.

## Commands and artifact identity

The raw JSON records full commands and actual exits. Actual export commands and reproduction commands follow (the network receipt records its full native subprocess argv; the offline receipt does not retain its top-level display argv):

```sh
# Same SIGHTBREAK_BUILDS_DIR for export/verify/package; all on frozen clean source.
python3 scripts/export.py linux
python3 scripts/export.py windows
python3 scripts/export.py macos
python3 scripts/export.py android
python3 scripts/export.py ios
python3 scripts/verify_builds.py --targets linux windows macos android ios --graphical
python3 scripts/build_manifest.py package --targets linux windows macos android ios
python3 scripts/verify_integration_export.py --target linux --display :118 --visit-armory --timeout 240 --output /workspace/desktop-evidence/native-network-final
python3 scripts/verify_offline_export.py --display :119 --timeout 300 --output /workspace/desktop-evidence/native-offline-final
bash scripts/validate.sh --backend
python3 /workspace/desktop-evidence/verify_delivery.py /workspace/desktop-evidence/delivery-final
sha256sum --check checksums.txt
```

Exports were actual serial per-target subprocesses with separate exit/timing records. The offline line is a reproduction example using a new free display; its original display number was not recorded in the receipt. The controllers used `/workspace/tools/xvfb/usr/bin/Xvfb` through `XVFB_BIN` and fresh numbered displays; the combined suite used display117 and an isolated regression state. Native Windows CI uses `--target windows`; macOS CI separately runs the matching bundle. Export/import/debug logs are preserved with each local target and in CI artifacts. Do not count a command that was not run as evidence.

Local delivery root: `builds/desktop-alpha-final/`. Each ZIP includes `source.json` and notices; the root manifest/receipt binds all outputs to the frozen SHA.

| Development package | Bytes | SHA256 |
| --- | ---: | --- |
| sightbreak-linux-debug.zip | 36500706 | `89d3c8e1fa4d54f5c1bd5401d52ac9e4cad0b17e722e62bdb5abfe8b78c23c45` |
| sightbreak-windows-debug.zip | 44501937 | `a242e1d78e00fb01f8648fd34a48ba6342aee69ddd7412c617bd9447469d0972` |
| sightbreak-macos-debug.zip | 77646530 | `8ee429a756fc02de53f27f23432dd0bca62b52a5af8b016d2eee973a618dfa81` |
| sightbreak-android-debug.zip | 62892187 | `5ace828657d9733b443883fb5336b27b934c61369afb309127ac357582141bea` |
| sightbreak-ios-xcode-project.zip | 129587498 | `8711bc6790553b273baded7d0f37bebe9d4cd48fcde2d6cb8f8fe230d1758ff0` |

The local executed Linux ELF SHA256 is `75762e4791223ae02a4ba94b466c665e0ebcd5fc5e088f674ddab41b25019ef2`. Independently exported CI binaries can differ; their own source receipts and checksums govern them. The Windows retry records physical validation-content hash `4ab5e4b5e4db2d263e59131670bb6383ed4c8662c9b7f78abb868be5212cae85`; it must not be relabelled with the local Linux hash. CI development artifacts retain 14 days: [Linux](https://github.com/calebaiken/sightbreak/actions/runs/39384250334/artifacts/12247140127), [macOS ARM-host universal bundle](https://github.com/calebaiken/sightbreak/actions/runs/39384250334/artifacts/12247185832), [failed Intel diagnostics](https://github.com/calebaiken/sightbreak/actions/runs/39384250334/artifacts/12247215871), [Windows successful retry](https://github.com/calebaiken/sightbreak/actions/runs/39384250334/artifacts/12247885095). Download the inner named package as the game payload. Failed-attempt artifacts are evidence, not qualified release packages.

## Failures retained and next milestone

| Severity | Finding / disposition |
| --- | --- |
| P1 | Intel macOS default graphical timeout and macOS14 ANGLE abort; reproduce on appropriate native hardware with real GPU, retain crash/hang logs and compare pinned renderer/toolchain behavior. macOS gameplay remains UNVERIFIED. |
| P2 | Intermittent Windows authority-reload completion timeout in first final-source run; exact-source retry passed unchanged assertions. Root cause not established. Next diagnostic: retain server/input timing and foreground/button-state receipts; do not relax the gate or substitute automatic reload. |
| P1 | Touchscreen-equipped desktop input selection still treats touchscreen availability as mobile mode and suppresses mouse capture. Correct desktop/mobile feature routing and then test actual touchscreen hardware. |
| P1 | Exported complete objective/full-match/training-earned and Windows offline/restart coverage incomplete. Add real native full-flow evidence before calling the desktop milestone accepted. |
| P1 release | Human gameplay/art/animation/audio 8.5 gates, physical hardware/performance/mobile QA, production transport/security/operations and signing remain open. |
| P2 | Wayland, physical controller/Steam Input, display/DPI/window modes, accessibility and mixed-platform real-peer compatibility need their specific acceptance evidence. |
| P2 | Current official Steamworks documentation could not be retrieved through the authorized network; actual partner/legal/store configuration and all Steam SDK/auth/cloud/input integration remain unimplemented. |

Earlier failures remain visible: generated macOS/Android sidecars initially rejected; original X11 close timeout and D-Bus descendant audit failures; offline OCR/settings and buy-phase switch attempts; main-test neutral-input expectation; isolated-profile guard refusal; initial validation script execute-bit failure. Corrected candidate results do not erase these attempts. Raw evidence identifies scope and actual exits; no assertion was disabled to turn a failure green.

[Steam readiness](../STEAM_RELEASE_READINESS.md) documents native depots/launch design, private beta workflow, signing/notarization, optional SDK/input/cloud/achievements, store/privacy/support prerequisites and trusted Steam-ticket-to-existing-account architecture. Official Godot sources were fetched; blocked Steam links are review targets, not current-doc certification. There is no Steam upload, live service, payment, fabricated App ID or economy replacement. Upload-ready templates were deferred until real IDs/partner configuration can be reviewed.

Next three tasks: (1) correct touchscreen-desktop routing, reproduce native platform/input failures and finish complete exported objectives/restart/controller/DPI qualification; (2) independently qualify narrow V3 input freshness, then durable recovery against PostgreSQL without enabling prediction/rewind; (3) repair match/actor contracts before any AI port and address measured hand/reload framing with native motion captures and independent human critique. P5 art replacement was deferred while P1/P2 gates remain open.
