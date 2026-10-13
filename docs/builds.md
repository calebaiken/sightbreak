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
python3 scripts/build_manifest.py package
(cd builds && sha256sum --check checksums.txt)
```

Every export records the Git commit, game tree, and a content digest of shipped source in its `source.json`. Export fails if source changes during the build or if Godot logs errors despite exiting successfully. Packaging refuses uncommitted game source, incomplete exports, changed binaries, or stale source. Each ZIP includes engine license notices; normalized ZIP timestamps make packaging repeatable for identical inputs. Engine export timestamps and local Android debug signing keys can change binary hashes between rebuilds; byte-for-byte reproducible APKs across different workspaces are not claimed. Seven `python3 scripts/test_build_manifest.py` regression checks cover these provenance guards.

## Trust and release boundaries

Godot editor and templates are pinned to the SHA512 values published in the official `godotengine/godot` 4.7.2 release. Downloads retain TLS and checksum verification. To upgrade, deliberately update the version and compare new official checksums; do not edit hashes merely to silence a mismatch. `docs/GODOT-LICENSE.txt` and `docs/GODOT-COPYRIGHT.txt` contain the engine's license notices. Redistribute them with builds.

The client and service remain a development implementation. Public competitive service deployment, anti-cheat hardening, external account binding, payment providers, production custody, release signing and device performance certification are separate release work.

## Validated build artifacts

The final cloud build includes the camera lifecycle, saved-profile validation and reward-bridge redirect fixes. Both native exports completed without script or export errors. The exported Linux executable passed menu startup (`--headless -- --smoke`) and an offline match startup (`--headless --quit-after 120 -- --demo`), both exiting successfully. Independent inspection of the embedded Linux PCK and Android ZIP confirmed that test harnesses are excluded.

Android `apksigner verify --verbose` confirmed APK v2/v3 signatures. `aapt dump badging` confirmed package `com.sightbreak.game`, API24 minimum, API36 target, ARM64 and x86_64. These are debug development artifacts; no physical mobile device performance or installation is claimed.

| Artifact under `builds/` | Bytes | SHA256 |
| --- | ---: | --- |
| `linux/sightbreak.x86_64` | 73,864,520 | `06e18858c1cc5eb28cb11e08535c12ce2a5c48def3d22d7a823808cbc17101b6` |
| `android/sightbreak-debug.apk` | 57,105,591 | `2976214ba47290374be03c659d026a918251902132246b5e1a79cd7f11b29c66` |

The matching machine-readable record is `builds/manifest.json`; verify downloaded copies from the builds directory with `sha256sum --check checksums.txt`. Rebuilding changes these hashes.

Native rendering validation under Xvfb/Mesa software rendering produced usable output, but logged two unresolved GL texture leaks at shutdown (349,524 bytes each), including a normal demo exit. Headless checks do not exercise that rendering path. This remains a rendering cleanup issue requiring further diagnosis and real device testing. iOS remains an export preset awaiting macOS/Xcode and signing.
