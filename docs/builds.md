# Native builds

SIGHTBREAK is a native Godot 4.7.2 project. The Linux build is a desktop development target; Android and iOS are the intended mobile targets. This repository does not use a webview or a browser renderer.

## Linux development and export

Prerequisites: Linux x86_64, Bash, curl, unzip, Python 3 and a GPU driver supporting OpenGL 3.3. Downloads use HTTPS and pinned checksums. The editor ZIP is about 70 MB; the official export-template bundle is about 1.22 GiB. Setup extracts only Linux x86_64, Android and iOS templates.

```sh
./scripts/setup.sh
./scripts/godot.sh --editor
./scripts/godot.sh
./scripts/export.sh linux
./builds/linux/sightbreak.x86_64
```

Use `scripts/setup.sh --editor-only` to skip templates. Default tool downloads are in the checkout's sibling `tools/` directory. Override with `SIGHTBREAK_TOOLS_DIR`; state lives in ignored `.local/`, overridable with `SIGHTBREAK_STATE_DIR`. Both overrides must be consistent across setup/run/export. `GODOT_BIN` can point to an existing Godot 4.7.2 binary. The wrapper sets writable XDG data/config/cache paths without changing HOME. Native game saves are under `.local/data/godot/app_userdata/SIGHTBREAK/` when launched through it.

In a cloud machine without a physical display, `--headless` checks scripts/logic only. For screenshots or software-rendered inspection, run Xvfb and use `DISPLAY=:99 LIBGL_ALWAYS_SOFTWARE=1`. Software rendering does not establish real device frame rate. The setup task extracted Debian's verified Xvfb package to `/workspace/tools/xvfb/usr/bin/Xvfb`; this optional utility is not needed on a desktop.

## Android debug APK

```sh
./scripts/setup.sh
./scripts/setup-android.sh
./scripts/export.sh android
export PATH="${ANDROID_SDK_ROOT:-${SIGHTBREAK_TOOLS_DIR:-../tools}/android-sdk}/platform-tools:$PATH"
adb install -r builds/android/sightbreak-debug.apk
```

The Android setup needs Java 17 or 21 with `keytool`, installs Google's command-line tools 19.0, platform-tools 37.0.1, build-tools 36.0.0 and API 36, and accepts the stable SDK package licenses. Command-line and platform-tools archives have pinned SHA256 hashes; SDK Manager verifies SDK packages against Google's repository metadata. It generates a local development keystore with the standard `android` debug password and stores SDK paths in ignored Godot editor settings. No release signing secrets are stored in the repository.

The preset uses Godot's native prebuilt template (no Gradle plugins), Android 7/API 24 minimum (the prebuilt template default), API 36 target, ARM64 plus x86_64 emulator support, immersive landscape and Internet permission for the optional economy service. Build output is `builds/android/sightbreak-debug.apk`. The Android preset disables automatic device polling in the cloud; enable Runnable in the Godot export dialog for one-click local device deployment. Debug signing permits local install; it does not create a Play Store release. Device performance, touch behavior, thermal load, battery use and suspend/resume require physical Android testing. Verify the APK signature with the SDK's `apksigner verify --verbose` before sharing.

## iOS project and signing

The `iOS` preset uses Godot 4.7.2, ARM64, iOS 15 minimum, landscape orientation and bundle ID `com.sightbreak.game`. `./scripts/export.sh ios` prepares an unsigned Xcode project on Linux or macOS, including the game PCK and engine frameworks. It stages a copy of the game under ignored `.local/`, so export cannot rewrite source signing configuration. Godot requires a Team ID even for project-only export; the script uses an explicit temporary sentinel and removes it from generated files. No real Apple identity is supplied or bundled. The generated Info.plist explains local-network permission for LAN matches.

Open `builds/ios/sightbreak.xcodeproj` on macOS with current Xcode. Select the SIGHTBREAK target, set your Development Team in Signing & Capabilities, and choose a unique bundle identifier if necessary. Select an attached iPhone/iPad and Run. The artifact includes `BUILD-ON-MAC.md` and a compile-only `xcodebuild` command. An Apple developer account and review are needed for App Store distribution; no paid account is needed for Linux/Android development.

This Linux cloud machine cannot compile with Xcode, sign an IPA, install on iOS, or measure Apple-device performance. The generated project is preparation for those steps, not evidence of successful iOS execution.

## Reproducible delivery packaging

Commit game changes, then export every target from that same game source:

```sh
./scripts/export.sh linux
./scripts/export.sh android
./scripts/export.sh ios
python3 scripts/verify_builds.py
python3 scripts/build_manifest.py package
(cd builds && sha256sum --check checksums.txt)
```

Every export records the Git commit, game tree, and a content digest of shipped source in its `source.json`. Export fails if source changes during the build or if Godot logs errors despite exiting successfully. Packaging refuses uncommitted game source, incomplete exports, changed binaries, or stale source. Each ZIP includes engine license notices; normalized ZIP timestamps make packaging repeatable for identical inputs. Engine export timestamps and local Android debug signing keys can change binary hashes between rebuilds; byte-for-byte reproducible APKs across different workspaces are not claimed. Eight `python3 scripts/test_build_manifest.py` regression checks cover these provenance guards.

## Trust and release boundaries

Godot editor and templates are pinned to the SHA512 values published in the official `godotengine/godot` 4.7.2 release. Downloads retain TLS and checksum verification. To upgrade, deliberately update the version and compare new official checksums; do not edit hashes merely to silence a mismatch. `docs/GODOT-LICENSE.txt` and `docs/GODOT-COPYRIGHT.txt` contain the engine's license notices. Redistribute them with builds.

The client and service remain a development implementation. Public competitive service deployment, anti-cheat hardening, external account binding, payment providers, production custody, release signing and device performance certification are separate release work.

## Validated 0.2.0 development artifacts

These exports contain the renderer lifetime mitigation, touch/HUD corrections, weapon and arena polish, bot lifecycle changes, and cosmetic recovery work. All targets were exported from committed game tree `79e725c31ae9c5ae401c0ea55deb50b6007366da`; the exact shipped-source SHA256 is `1eb2e937a11b672b89b41127bdad07c2f1c42a6fea48d079169e60bec43d0e58`. Documentation-only commits can follow without changing that game tree. The machine-readable manifest records the Git commit at each export and the full payload checksums.

`python3 scripts/verify_builds.py` passed against the actual final artifacts:

- Exported Linux menu startup and 120-frame offline startup completed without runtime errors.
- Linux and iOS PCK directories each contained 48 resources; test harnesses were excluded. Android asset inspection also excluded test harnesses.
- Android signature verification passed v2/v3; version `0.2.0-dev`/code `2`, API24 minimum/API36 target, ARM64 and x86_64, landscape orientation, and exported `com.godot.game.GodotAppLauncher` alias were confirmed from the APK.
- Generated iOS Xcode project contains the game PCK, native frameworks, landscape Info.plist, LAN permission explanation and empty Development Team. It is an unsigned project, not an IPA.
- Artifact provenance guards compared committed game tree, shipped-source digest and every payload file before verification and packaging. Eight regression checks cover stale source, changed/missing payloads, uncommitted source and the prebuilt Android SDK configuration.

| Artifact under `builds/` | Bytes | SHA256 |
| --- | ---: | --- |
| `linux/sightbreak.x86_64` | 73,914,592 | `950c55e0d7af82423cc9c24cb7ae3d4e9794029242d50a2d293d684759d51a75` |
| `sightbreak-linux-debug.zip` | 30,660,079 | `906d2f0a3eb06cd2ffeb0fc57bfe29555ba5e268e106cc8062d76ec2ce17eb03` |
| `android/sightbreak-debug.apk` | 57,155,775 | `d2b4e1492ccba6abc198a3b7909ab3f834d121c16ae3bd2af77be653ca0e1b8f` |
| `sightbreak-android-debug.zip` | 57,184,469 | `a5df858ad1f635b43e74305dcef9aa46081dc30543138ef6e722199ee89f7952` |
| `sightbreak-ios-xcode-project.zip` | 123,976,053 | `6b92053a8ad384e34ffae9bcbae1fe9fe2ae70abceaa4db6c1e38bd90687cdbb` |

ZIPs include engine license notices and per-target source provenance. The iOS ZIP also includes `BUILD-ON-MAC.md`. Verify local copies with `(cd builds && sha256sum --check checksums.txt)`. The tracked records are [build manifest](reports/build-manifest.json) and [artifact validation](reports/build-validation.json).

The original two GL texture teardown errors were isolated to retiring a newly created procedural sky before its first rendered frame in Godot's Compatibility renderer. The project mitigation shares an immutable sky. Independent native demo and repeated menu/match lifecycle checks passed on Xvfb/Mesa; see [QA](reports/QA.md) and [diagnostic reproduction](diagnostics/README.md). This does not establish physical GPU/mobile behavior or indefinite memory stability.

No physical Android installation, mobile performance measurement, macOS/Xcode compilation, signed IPA, or Apple-device execution is claimed. Use [device testing instructions](DEVICE_TESTING.md) to record the remaining release evidence. These artifacts remain development builds; the full 8.5/10 acceptance gate has not been achieved.
