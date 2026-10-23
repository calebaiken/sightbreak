# Desktop development build commands — 0.3.3-dev (build 6)

Current source identities, native results, package hashes and remaining blockers
are in the [playability report](reports/DESKTOP_PLAYABILITY_REPORT.md). The local
five-target development package set is bound to frozen `e3c1194`; later native-host S14
bundles have their own source receipts and qualification outcomes. Export, verify
and package one exact clean source in a new
build root. Distribute the named inner game ZIP; Actions diagnostic bundles also
contain logs and test state and are not game distributions.

This continuation adds Windows x86_64 and macOS Universal 2 to the existing Linux,
Android and iOS project. Godot remains **4.7.2.stable.official.ed1daf0bf**. The
[preflight](reports/DESKTOP_PREFLIGHT.md) records the preserved V2 base; V2's test
results are historical. See the [Steam plan](STEAM_RELEASE_READINESS.md) and
[desktop checklist](DESKTOP_TESTING.md). Native execution results are recorded
separately from artifact inspection in the [desktop QA report](reports/DESKTOP_ALPHA_REPORT.md).
That report links native CI packages and records exact frozen source `0fb7480`;
later documentation commits do not re-attest those artifacts.

Use Python 3.12+ on Windows 10/11 x86_64, Linux x86_64 or macOS. No Bash is required
for desktop setup, export, inspection or packaging. On Windows use `python`; on
Linux/macOS substitute `python3` if needed. In a clean committed checkout:

```sh
# Select ONE target: windows, linux, macos, android or ios.
python scripts/toolchain.py setup --targets windows
python scripts/export.py windows
python scripts/verify_builds.py --targets windows --graphical
python scripts/build_manifest.py package --targets windows
```

Replace `windows` with `linux` or `macos` for the matching native host. Setup
installs only selected export templates from the SHA512-verified official archive;
it does not require all five platform SDKs. Python setup defaults to the host's
desktop target. Bash wrappers remain available. Android additionally requires
`scripts/setup-android.sh` and its Java/SDK tooling; select `--targets android`
when installing Godot templates. iOS remains a distinct unsigned Xcode-project
export, not a macOS application or an IPA. Existing mobile CI explicitly selects
`--targets linux android ios`.

| Target | Export output | Distributable |
| --- | --- | --- |
| Windows | `builds/windows/SIGHTBREAK.exe` (+ console launcher) | `sightbreak-windows-debug.zip` |
| Linux | `builds/linux/sightbreak.x86_64` (+ `sightbreak.sh`) | `sightbreak-linux-debug.zip` |
| macOS | `builds/macos/SIGHTBREAK.app` (+ development console launcher) | `sightbreak-macos-debug.zip` |
| Android | `builds/android/sightbreak-debug.apk` | `sightbreak-android-debug.zip` |
| iOS | `builds/ios/sightbreak.xcodeproj` | `sightbreak-ios-xcode-project.zip` |

Packages include the actual game resources, license/copyright notices and source
receipt. Extract the Linux ZIP preserving executable bits, then run
`linux/sightbreak.sh` (or the ELF directly). Windows users launch
`windows/SIGHTBREAK.exe`. macOS users launch `macos/SIGHTBREAK.app`, or its native
`Contents/MacOS/SIGHTBREAK` executable from a terminal for logs. macOS requires
11+ on Intel and 13+ on Apple Silicon for this pinned toolchain; both architectures
still need full native gameplay qualification. Apple Silicon startup passed on
macOS 15; Intel graphical startup timed out on the hosted software renderer.
Development apps are ad-hoc signed and not
notarized; public distribution needs Developer ID signing/notarization and actual
Gatekeeper validation. Do not embed signing identities or credentials.

The tested nontouch desktop uses keyboard/mouse. Use Escape to release the pointer and open
the field menu, including in-match settings. Focus loss opens a menu and requires
explicit resume; offline training suspends while network authority continues.
Windowed, borderless fullscreen and exclusive fullscreen are saved in settings;
exclusive mode may map to normal fullscreen on some platforms/compositors.
Mouse look uses unscaled screen motion. Desktop defaults to keyboard/mouse even
when touchscreen hardware is available. **SHOW TOUCH CONTROLS ON DESKTOP** opts
into touch HUD/input; Android/iOS keep mobile defaults. After explicit resume,
release held keys, mouse buttons, controller or touch inputs before new actions
are accepted. Physical touchscreen/controller delivery, hot-plug, high DPI and
controller-only menus remain unverified.

For contended hosted Windows automation, offline validators optionally accept
`--hosted-render-priority below-normal`. This changes only the owned test game
process scheduling after window/PID verification; it changes no shipped setting,
affinity, rules or deadline. Native scenario gates still apply and may fail.

`GODOT_BIN`, `SIGHTBREAK_TOOLS_DIR` and `SIGHTBREAK_STATE_DIR` remain supported.
Godot uses repository-local XDG state on Linux, native AppData on Windows and
native Library/Application Support paths on macOS. Never repurpose HOME. Saves
remain offline training/settings; they cannot become account Credits/items.

For a new attempt, choose a fresh **ignored** build root before every command:
`SIGHTBREAK_BUILDS_DIR=/absolute/path/to/checkout/builds/attempt-2` (PowerShell:
`$env:SIGHTBREAK_BUILDS_DIR = "C:/path/to/checkout/builds/attempt-2"`). Existing
exports/receipts/archives are rejected, not overwritten. Every export, verifier
and package must use the same exact clean commit, game tree, physical source and
validation-tool bytes. Hashes and physical/delivery modes bind every payload.
Signing, platform tooling and filesystem differences can change output bytes;
this is exact input/output provenance, not a binary reproducibility promise.
Default verifier/package commands retain the old Linux+Android+iOS selection;
use `--targets` to build/inspect/package a subset or all five explicitly.

The branch-scoped `Desktop playability P1` Actions workflow builds and executes on
Windows, Linux and macOS runners, retaining failures and development artifacts.
Its graphical startup check is separate from real Windows/Linux pointer/keyboard
network tests and Linux living-player offline/restart tests. Runner evidence is
not physical GPU, Steam Deck, mobile, human balance or 8.5 quality acceptance.

---

The following build records and commands are historical and keep their original
versions, source identities, hashes, failures and validation limits.

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

Every export records the Git commit, game tree, and a content digest of shipped source in its `source.json`. Export fails if source changes during the build or if Godot logs errors despite exiting successfully. Packaging refuses uncommitted game source, incomplete exports, changed binaries, or stale source. Each ZIP includes engine license notices; normalized ZIP timestamps make packaging repeatable for identical inputs. Engine export timestamps and local Android debug signing keys can change binary hashes between rebuilds; byte-for-byte reproducible APKs across different workspaces are not claimed. Twenty-four `python3 scripts/test_build_manifest.py` regression checks cover these provenance guards.

## Trust and release boundaries

Godot editor and templates are pinned to the SHA512 values published in the official `godotengine/godot` 4.7.2 release. Downloads retain TLS and checksum verification. To upgrade, deliberately update the version and compare new official checksums; do not edit hashes merely to silence a mismatch. `docs/GODOT-LICENSE.txt` and `docs/GODOT-COPYRIGHT.txt` contain the engine's license notices. Redistribute them with builds.

The client and service remain a development implementation. Public competitive service deployment, anti-cheat hardening, external account binding, payment providers, production custody, release signing and device performance certification are separate release work.

## Validated 0.3.0 development artifacts

These exports contain the authored Relay Yard surfaces and architecture, shared weapon models, combat effects, mobile HUD improvements, and native cosmetic presentation. All targets were exported from committed source `538f52f9a9dfb5dac38209b7541bde145fc01976`, game tree `ab35c845326fe859c86f3d0b4e37038e82e18c44`; the exact shipped-source SHA256 is `2c6cf58b4c49914d5d8901bc81e73e4e3734c939fcf11464448fbae39e72d60a`. Documentation-only commits can follow without changing that game tree. The machine-readable manifest records the Git commit at each export and full payload checksums.

`python3 scripts/verify_builds.py` passed against the actual final artifacts:

- Exported Linux menu startup and 120-frame offline startup completed without runtime errors.
- Linux and iOS PCK directories each contained 66 resources; test harnesses were excluded. Android asset inspection found 68 asset entries and also excluded test harnesses.
- Android signature verification passed v2/v3; version `0.3.0-dev`/code `3`, API24 minimum/API36 target, ARM64 and x86_64, landscape orientation, and exported `com.godot.game.GodotAppLauncher` alias were confirmed from the APK.
- Generated iOS Xcode project contains the game PCK, native frameworks, landscape Info.plist, LAN permission explanation, version `0.3.0`/build `3`, and empty Development Team. It is an unsigned project, not an IPA.
- Artifact provenance guards compared committed game tree, shipped-source digest and every payload file before verification and packaging. Ten regression checks cover stale source, changed/missing payloads, uncommitted source, bundled licenses, target version consistency and inherited prebuilt Android SDK configuration.

| Artifact under `builds/` | Bytes | SHA256 |
| --- | ---: | --- |
| `linux/sightbreak.x86_64` | 74,058,680 | `88636e5b4d949de2c772114876a53435a42087b2f548353f4410d3cd29a7db9c` |
| `sightbreak-linux-debug.zip` | 30,800,111 | `20e1d591410375fdf2bc2cf9ad230f21e2dbc06b9108e3a3d6461a5f645ea879` |
| `android/sightbreak-debug.apk` | 57,305,124 | `5db3bf8ab03e14e8b4d9ef69f713f2a957b3d99f0c21dec597d0d6703e289280` |
| `sightbreak-android-debug.zip` | 57,329,857 | `33746170070b85c589dd85cde26073eb34dc40a01302d5612ce377c3a988d16e` |
| `sightbreak-ios-xcode-project.zip` | 124,115,785 | `1c4346480252fecfa5544e4da986ab5f6f690a3dfb3717e34fd04dc7e62e2a1b` |

ZIPs include engine license notices and per-target source provenance. The iOS ZIP also includes `BUILD-ON-MAC.md`. All five listed checksum checks passed. Verify local copies with `(cd builds && sha256sum --check checksums.txt)`. The tracked records are [build manifest](reports/build-manifest.json) and [artifact validation](reports/build-validation.json).

The shared immutable sky mitigation from 0.2 remains in place. Current native lifecycle and visual acceptance results are recorded separately in [0.3 QA](reports/QA-0.3.md); see [diagnostic reproduction](diagnostics/README.md) for the original renderer defect. Desktop software rendering does not establish physical GPU/mobile behavior or indefinite memory stability.

No physical Android installation, mobile performance measurement, macOS/Xcode compilation, signed IPA, or Apple-device execution is claimed. Use [device testing instructions](DEVICE_TESTING.md) to record the remaining release evidence. These artifacts remain development builds; consult the independent QA report for scored categories and unresolved release gates.
