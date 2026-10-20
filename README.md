# SIGHTBREAK

Native tactical FPS · Godot 4.7.2 · `0.3.0-dev`

## Installation

The manual steps below use a prebuilt development package: `sightbreak-linux-debug.zip` for Linux or `sightbreak-debug.apk` for Android. Obtain these from a shared development build, or create them using [Building and validation](#building-and-validation). Compiled packages are generated locally and are not included in a source checkout.

### Linux: manual installation

Requires a Linux x86_64 desktop, an OpenGL 3.3-compatible graphics driver, and `unzip`. The package includes the game engine; a separate Godot installation is unnecessary.

1. Download or copy `sightbreak-linux-debug.zip` to your computer.
2. Open a terminal in the directory containing the ZIP and run:

   ```sh
   unzip sightbreak-linux-debug.zip -d sightbreak
   cd sightbreak/linux
   chmod +x sightbreak.sh sightbreak.x86_64
   ./sightbreak.sh
   ```

3. Choose **DEPLOY · OFFLINE 5V5** to start playing. Offline play requires no account or backend service.

Keep the extracted package together, including its launcher and license notices. To update, extract the new build into a separate directory and launch it from there.

### Android: manual installation

Requires Android 7.0 or newer (API 24+) on an ARM64 device. The APK also includes x86_64 support for compatible emulators. It is a debug-signed development build.

1. Download or copy `sightbreak-debug.apk` to the device. If you received `sightbreak-android-debug.zip`, extract it and use `android/sightbreak-debug.apk`.
2. Open the APK in the device's file manager or browser downloads.
3. When prompted, allow that app to **install unknown apps**, then return to the installer. On Android 7, this setting is usually under **Settings → Security → Unknown sources**; wording varies by manufacturer.
4. Tap **Install**, then open **SIGHTBREAK** from the launcher.
5. Choose **DEPLOY · OFFLINE 5V5**. The game can be played offline after installation.

For updates, install the replacement APK over the existing app. Updates require the same signing key. If Android reports an incompatible signature, uninstalling the older build allows a fresh installation, but removes its local training record and settings.

#### Optional: install over USB with ADB

Install Android platform-tools on your computer, enable **USB debugging** on the device, connect it, and accept the computer authorization prompt. With `adb` on your `PATH`, run:

```sh
adb devices
adb install -r /path/to/sightbreak-debug.apk
adb shell am start -n com.sightbreak.game/com.godot.game.GodotAppLauncher
```

Replace the APK path with the file you downloaded or built. `adb devices` should list the phone as `device` before installation.

### Run from source on Linux

Requires Linux x86_64, Bash, `curl`, `unzip`, Python 3, and a graphical desktop with OpenGL 3.3 support. From the repository root:

```sh
./scripts/setup.sh --editor-only
./scripts/godot.sh --headless --editor --import --quit
./scripts/godot.sh
```

The setup script downloads the pinned Godot 4.7.2 editor and verifies its checksum. The import step prepares the project's assets and scripts before the first launch.

For a manual editor setup, install the Linux x86_64 editor from the [official Godot 4.7.2 release](https://github.com/godotengine/godot/releases/tag/4.7.2-stable), import `game/project.godot` in the project manager, wait for asset imports to finish, and press **F5**. Use the matching engine version for this development build. Tool paths, export templates, and platform requirements are documented in the [native build guide](docs/builds.md).

### iOS development

The repository also supports an unsigned Xcode project export. Generate it with `./scripts/export.sh ios` after installing the export templates, then open `builds/ios/sightbreak.xcodeproj` on macOS. Compilation, Apple signing, and device deployment require Xcode. See the [iOS build instructions](docs/builds.md#ios-project-and-signing).

## About the game

SIGHTBREAK is a native 5v5 tactical first-person shooter built around positioning, controlled fire, round-based weapon purchases, and plant-and-defuse objectives. Matches take place in **Relay Yard**, an original industrial map with two objective sites, connecting routes, cover, and elevated sightlines.

Play a complete match with bots, host a direct-connect LAN session, or use the optional account service for persistent cosmetic inventory and earned progression. The game supports keyboard and mouse on desktop and a configurable landscape touch interface on mobile.

### How a match works

Each player has one life per round. Eliminated players spectate their surviving teammates until the next round.

| Team | Objective |
| --- | --- |
| Attackers | Plant the relay device at either site and protect it until detonation, or eliminate the defenders. |
| Defenders | Prevent a plant until the round timer expires, eliminate the attackers before a plant, or defuse an armed device. |

Rounds begin with a **15-second buy phase**, followed by **100 seconds** to secure a site or stop the attack. Planting takes **3 seconds**; defusing takes **5 seconds**. Once planted, the device has its own **35-second countdown**.

Teams switch sides after six rounds. The first team to win seven rounds wins the match; a 6–6 result after twelve rounds is a draw. Players begin the match with a Kestrel 9 sidearm and **800 match funds**, then earn funds through play to purchase weapons during later buy phases.

### Play modes

| Mode | What to expect | Account required |
| --- | --- | --- |
| Offline 5v5 | One player and nine bots. Select Recruit, Standard, or Veteran difficulty in Settings. | No |
| Guest LAN | Direct connection to a dedicated server, with bots filling unused slots. Guest matches are practice sessions. | No |
| Account session | A configured dedicated server and economy service. Matches start when ten distinct signed-in players have joined; eligible completed matches can award account progression. | Yes |

LAN and account sessions are available through **LOCAL NETWORK**. Players connect using the host's address and port. Public matchmaking and automatic server discovery are not available in this build.

### Weapons and utility

| Weapon | Class | Buy cost in match funds |
| --- | --- | ---: |
| Kestrel 9 | Semi-automatic sidearm | 0 (starting weapon) |
| Vectorline | Submachine gun | 1,100 |
| Relay AR | Assault rifle | 2,400 |
| Longwatch | Marksman rifle | 3,200 |

Each weapon has its own fire cadence, recoil, spread, magazine size, and reload timing. Frag grenades provide explosive damage, while smoke grenades obscure sightlines and help teams cross exposed routes or contest a site. Network matches use server-authoritative movement, ammunition, damage, objectives, and round results.

## Controls and settings

| Action | Keyboard and mouse | Touch controls |
| --- | --- | --- |
| Move / aim | WASD / mouse | Left joystick / right touch zone |
| Fire / reload | Left mouse button / R | FIRE / RELOAD |
| Jump / crouch | Space / Ctrl | JUMP / LOW |
| Plant / defuse | Hold E | Hold USE |
| Select weapon | 1: primary / 2: sidearm | SWAP |
| Frag / smoke | G / Q | FRAG / SMOKE |
| Buy / scoreboard | B / Tab | BUY / TEAM |
| Field menu | Escape | Pause button |

Settings include aim sensitivity, field of view, frame limit, shadow quality, 3D render scale, volume, crosshair appearance, interface text size, bot difficulty, and reduced motion. Gyroscope and controller options are also available; physical-device behavior remains under review.

The field menu pauses offline matches. Network matches continue while the menu is open. On touch devices, open the field menu's layout editor, drag the joystick or action buttons, and choose **SAVE TOUCH LAYOUT**. Use **RESET POSITIONS** to restore the defaults; button scale is adjustable in Settings.

## Progression and cosmetics

SIGHTBREAK keeps three kinds of progression separate:

| System | Purpose | Persistence |
| --- | --- | --- |
| Match funds | Purchase weapons during buy phases. | Within the current match. |
| Offline training record | Track local XP, levels, training Credits, match history, and statistics. | Saved on the device. |
| Account progression | Earn online Credits and maintain an owned cosmetic inventory. | Stored by the account service. |

Offline training and guest LAN matches do not grant online Credits or tradable items. Eligible account matches can award XP, Credits, first-match-of-the-day bonuses, and level rewards.

The current cosmetic system includes collectible **rifle finishes**, cases and keys, item inspection, owned rifle loadouts, two-sided trades, and a marketplace using earned Credits. Case probabilities are shown before opening. Cosmetic items change appearance only; they do not modify weapon performance.

The economy uses earned currency only, with no real-money purchases, cash-outs, cryptocurrency, or external marketplace integration. Detailed reward rules and provisional tuning values are in the [economy guide](docs/economy.md).

## Hosting and account setup

### Guest LAN server

From the extracted Linux package's `linux/` directory, start a server in a separate terminal:

```sh
./sightbreak.sh --headless -- --server --port=27020
```

From a source checkout, use `./scripts/godot.sh --headless -- --server --port=27020` instead. Open **LOCAL NETWORK → JOIN GUEST LAN MATCH** in each client and enter the host's address. Use `127.0.0.1` on the host computer, or the host's private LAN address from another computer or phone. UDP port **27020** must be reachable, and clients and servers should use matching game builds.

### Optional account service

The default service configuration is for local development. It requires Python 3.12+, [uv](https://docs.astral.sh/uv/), and Docker. From the repository root:

```sh
UV_CACHE_DIR="$PWD/.local/uv-cache" UV_PROJECT_ENVIRONMENT="$PWD/.venv" uv sync --project backend --frozen
backend/dev-db.sh
.venv/bin/python backend/migrate.py
backend/dev-api.sh
```

The API listens on `127.0.0.1:8080` and PostgreSQL on `127.0.0.1:55432`. Open **OPERATOR RECORD → ONLINE ACCOUNT & INVENTORY** to register or sign in. New accounts begin with zero Credits and an empty inventory.

In another terminal, start the account-enabled server:

```sh
./scripts/serve-account-match.sh
```

Choose **LOCAL NETWORK → JOIN ACCOUNT SERVER**, using the host's address and configured server ID. The launcher manages the local development server credential; credentials belong on the server and are never bundled with the client. Rewards depend on verified match eligibility and participation. Guest games, bot games, and incomplete or disqualified account matches do not create tradable rewards.

For Android account testing over USB, run `adb reverse tcp:8080 tcp:8080` and use `http://127.0.0.1:8080` as the phone's API address. This forwards the HTTP API only; the UDP game connection still needs the host's reachable LAN address.

See the [backend guide](docs/backend.md) for service configuration, [network documentation](docs/network.md) for account admission, and [protocol compatibility](docs/network.md) for matching builds. Production hosting requires additional deployment and security work.

## Development status

The current version is a playable **development alpha**. The implemented game is a subset of the [full specification](docs/SPECIFICATION.md). Public matchmaking, broader cosmetic categories, challenges, achievements, and other roadmap features remain future work.

This development build supports source exports for Linux, Android, and an unsigned iOS project. Physical Android playtesting, sustained mobile performance, and macOS/Xcode compilation remain unverified. See the [independent QA report](docs/reports/QA-0.3.md), [known limitations](docs/KNOWN_LIMITATIONS.md), [milestone roadmap](docs/MILESTONES.md), and [device testing checklist](docs/DEVICE_TESTING.md) for current evidence and remaining work.

## Building and validation

From a Linux source checkout, install the editor and native export templates, then build the desired target:

```sh
./scripts/setup.sh
./scripts/export.sh linux              # Linux executable and launcher
./scripts/setup-android.sh             # Requires OpenJDK 17 or 21 with keytool
./scripts/export.sh android            # Android debug APK
./scripts/export.sh ios                # Unsigned Xcode project
```

Each platform can be exported independently. The Linux executable and launcher are in `builds/linux/`; the Android APK is `builds/android/sightbreak-debug.apk`; the iOS project is `builds/ios/sightbreak.xcodeproj`.

The Android setup script installs SDK platform-tools. Add their `platform-tools` directory to your `PATH` to use the ADB commands above. Detailed SDK paths, signing, checksums, and export requirements are in the [native build guide](docs/builds.md).

To verify and package the complete set of development builds, export all three targets first, then run:

```sh
python3 scripts/verify_builds.py
python3 scripts/build_manifest.py package
(cd builds && sha256sum --check checksums.txt)
```

Run the maintained checks from the repository root:

```sh
./scripts/validate.sh                  # Native gameplay, UI, persistence, and networking
./scripts/validate.sh --backend        # Also PostgreSQL and account/economy checks
./scripts/test_render.sh               # Requires a graphical display
```

Backend checks require the service dependencies described above. The [independent QA report](docs/reports/QA-0.3.md) describes the validation evidence and its scope. Automated checks and export verification cover their stated scopes; physical-device results are recorded separately.

### Developer resources

- [Architecture](docs/ARCHITECTURE.md), [weapon definitions](game/scripts/gameplay/weapons.gd), and [economy configuration](backend/config/economy.json).
- [Backend and migrations](docs/backend.md), [economy design](docs/economy.md), and [network contracts](docs/network.md).
- [Independent QA and evidence](docs/reports/QA-0.3.md), [known limitations](docs/KNOWN_LIMITATIONS.md), and [development milestones](docs/MILESTONES.md).
- [Visual QA and evidence](docs/reports/QA-0.3.md), [renderer diagnostics](docs/diagnostics/README.md), and [remaining milestones](docs/MILESTONES.md).

Continue development in the existing isolated checkout; create a Git worktree only when requested. Preserve development state in commits and update evidence when behavior changes. Record untested features and device behavior accurately.
