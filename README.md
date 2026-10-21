# SIGHTBREAK 0.3.3-dev

A native **Godot 4.7.2** tactical FPS development build for desktop, Android and unsigned iOS project export. Fight a 5v5 offline match in the original Relay Yard, or connect to a dedicated server. The separate PostgreSQL economy supports authenticated accounts, earned Credits, collectible rifle finishes, cases, two-sided trades and marketplace purchases.

**No real-money transactions.** There are no payments, premium purchases, withdrawals, cryptocurrency or external marketplaces. Offline training progress never becomes tradable online value.

This is a playable **development alpha**, not the finished release in the [full specification](docs/SPECIFICATION.md). Historical whole-game visual QA scored the earlier pass **8.1/10**, below the required 8.5/10 milestone gate; physical mobile usability, sustained device performance and production security remain unverified. Read the [0.3 independent QA evidence](docs/reports/QA-0.3.md), [known limitations](docs/KNOWN_LIMITATIONS.md) and [milestone roadmap](docs/MILESTONES.md).

## Desktop alpha continuation

Windows x86_64, Linux x86_64 and macOS Universal 2 now have independently selected
native export/verification/package commands. [Build and run instructions](docs/builds.md)
include platform prerequisites, exact-source receipts and clean-attempt rules.
The [desktop checklist](docs/DESKTOP_TESTING.md) separates native gameplay from
cross-export inspection; [Steam readiness](docs/STEAM_RELEASE_READINESS.md) is
preparation only. This branch starts from frozen V2 runtime; it does not merge
unfinished V3, bot or graphics changes. Quality and untested-platform gates remain open.

The [desktop delivery report](docs/reports/DESKTOP_ALPHA_REPORT.md) records frozen
source `0fb7480`, five inspected packages, real Linux offline/restart and Windows
network-input passes, and macOS Apple Silicon startup. Intel macOS graphical
startup failed; the original Windows reload timeout remains an intermittent issue.
These results do not establish complete desktop or Steam release acceptance.

## Competitive engineering stack (development only)

Codex draft PRs [3](https://github.com/calebaiken/sightbreak/pull/3) → [4](https://github.com/calebaiken/sightbreak/pull/4) → [5](https://github.com/calebaiken/sightbreak/pull/5) → [6](https://github.com/calebaiken/sightbreak/pull/6) → [7](https://github.com/calebaiken/sightbreak/pull/7) → [8](https://github.com/calebaiken/sightbreak/pull/8) depend on corrected Claude PR1. They add recipient state privacy, continuous remote interpolation, **opt-in** local prediction, bounded peer admission and durable result recovery. Protocol6 requires matched client/server builds. Historical hit-volume recording is diagnostic only; live lag compensation is incomplete. The isolated integration preview combines Claude's graphics PR2 with this stack; its source branch and assets are untouched.

Read [current engineering QA](docs/reports/CODEX_NETWORK_QA.md), [network contracts](docs/network/NETWORK_ARCHITECTURE.md), [parallel integration instructions](docs/engineering/PARALLEL_WORK.md) and [build validation](docs/network/BUILD_VALIDATION.md). Unicode feed clipping is fixed. New custom-status layout oscillation, adverse full-capacity reconnect and the weapon/arms visual gate remain open; no full8.5 or production acceptance is claimed. Git branches/PRs are reviewable work, not authorization to merge.

## Combined development preview

[Integration report](docs/reports/COMBINED_INTEGRATION_REPORT.md) · [draft PR9](https://github.com/calebaiken/sightbreak/pull/9) · [evidence](docs/reports/integration-evidence/README.md)

Exact export source: `60cf125bb2c05606e71a4a68482d31ec26dc69bb`. Refreshed suite47/47 groups and native ten-client common-window test pass; adversarial custom-HUD and close-loss reconnect fail. Independent authored weapon/arms visual slice is5.5/10, below8.5; it is distinct from the historical whole-game score. Android debug APK, Linux executable and unsigned iOS project have source-bound manifests/checksums. Device/Xcode validation is unverified. Keep prediction opt-in and live rewind disabled. **Request changes; development preview only.**

## Play locally

From this repository, on Linux x86_64 with a graphical desktop:

```sh
./scripts/setup.sh             # Verified Godot editor and native export templates
./scripts/godot.sh             # Start the native game
```

Choose **DEPLOY / OFFLINE 5 v 5**. No account or backend is needed. The first round starts with a sidearm and 800 match funds; buy better equipment in later rounds. Attackers carry a device to either marked site; hold Use to plant. Defenders hold Use near the planted device to defuse. Teams switch sides after six rounds; first to seven wins, or 6–6 draws at regulation. Dead players spectate teammates.

| Action | Desktop | Mobile |
| --- | --- | --- |
| Move / aim | WASD / mouse | Left joystick / right touch zone |
| Fire / reload | Left mouse / R | FIRE / RELOAD |
| Jump / crouch | Space / Ctrl | JUMP / LOW |
| Plant / defuse | Hold E | Hold USE |
| Weapons | 1 primary / 2 sidearm | SWAP |
| Frag / smoke | G / Q | FRAG / SMOKE |
| Buy / roster | B / Tab | BUY / TEAM |
| Menu | Escape | Pause button |

Settings include sensitivity, FOV, frame cap, shadow quality, 3D render scale (50–100 %; the HUD stays at native resolution), volume, crosshair size/color, interface text size, gyro, controller input and reduced motion. The offline field menu pauses training; network matches keep running. During a match, the field menu opens the touch HUD editor. Drag the joystick or action buttons and press **SAVE TOUCH LAYOUT**; use **RESET POSITIONS** to restore defaults. Button scale is adjustable in settings. Touch input is canceled on focus loss, and simulated mouse events cannot fire the weapon. Physical gyro/controller behavior still needs device review.

## 0.3 visual and mobile milestone

This continues the committed 0.2 alpha. Relay Yard now has framed industrial architecture, fitted cargo, crane structure, service details and original surface maps. Shared beveled weapon models, articulated operators, staged reload/equip motion and bounded muzzle/impact/casing effects improve native combat presentation. Server-confirmed hit and impact feedback reaches network clients without changing damage authority.

The landscape HUD uses compact fading edges, centered score/reticle, vector controls and safe-area layout. Enlarged default controls clear each other at tablet and wide phone ratios. Cases use an original hinged 3D hardcase and committed-item reveal; the sharper demand-rendered inspector supports rotation/zoom and an explicitly **unowned knife reference**. Inventory and market filtering preserve existing authoritative transactions. No knife reward, payment or client-minted value was added.

The screenshot-driven review found and corrected floating rooftop equipment, obscured signage, overly bright operator materials, foam-like smoke and missing knife geometry. See the [independent visual rubric and evidence](docs/reports/QA-0.3.md), [world changes](docs/reports/WORLD-0.3.md), [mobile captures](docs/reports/media/v03-mobile/README.md), [cosmetic comparisons](docs/reports/media/v03-cosmetics/README.md) and [measured rendering costs](docs/reports/PERFORMANCE-0.3.md).

Repeated native match/inspection teardown checks preserve the shared-sky fix for the two original GL errors; see the [diagnostic reproduction](docs/diagnostics/README.md). Local tests and software-rendered images establish their stated scopes. Physical mobile comfort, GPU performance, thermals, battery use, human balance and production security remain open release gates.

## Test on a connected Android phone

```sh
adb install -r builds/android/sightbreak-debug.apk
adb shell am start -n com.sightbreak.game/com.godot.game.GodotAppLauncher
# Optional: reach the host economy API over USB without exposing it on the LAN.
adb reverse tcp:8080 tcp:8080
```

Start with **DEPLOY** offline. For USB economy testing, leave the phone's API address at `http://127.0.0.1:8080` and run the host API as described below. USB TCP reversal does not tunnel UDP game traffic; guest network play needs the dedicated server's reachable private LAN address. Record device/OS, build hash, settings, touch behavior, a full match and background/resume using the [device checklist](docs/DEVICE_TESTING.md). No physical device is attached to this cloud session.

## Accounts and dedicated play

For the economy API, Python 3.12+, uv and Docker are required:

```sh
UV_CACHE_DIR="$PWD/.local/uv-cache" UV_PROJECT_ENVIRONMENT="$PWD/.venv" uv sync --project backend --frozen
backend/dev-db.sh
.venv/bin/python backend/migrate.py
backend/dev-api.sh
```

The API binds `127.0.0.1:8080`; PostgreSQL binds `127.0.0.1:55432`. The launcher creates an ignored local development server key with restricted file permissions. No privileged key is embedded in the game. Register in **OPERATOR → ONLINE ACCOUNT & INVENTORY**. New accounts have zero Credits/items; owned loadouts and inventories come from the backend.

Start a guest practice server in another terminal:

```sh
./scripts/godot.sh --headless -- --server --port=27020
```

Or start an authenticated local development server:

```sh
./scripts/serve-account-match.sh
```

Open **LOCAL NETWORK**, enter the host address, and choose guest or account join. Authenticated servers wait for ten distinct account identities and exclude bots. The game requests a short-lived one-use ticket through the logged-in economy connection; the server consumes it to bind identity. Eligible complete matches submit server-calculated activity/results for backend-calculated rewards. Disconnects, short matches and insufficient activity do not mint tradable rewards. Guest/bot games remain practice only. Read the exact boundaries and tests in [network.md](docs/network.md) and [backend.md](docs/backend.md).

This is local development infrastructure. ENet traffic is not encrypted and no production hosting/matchmaking has been deployed. Keep database and privileged services private; see the documented release gates before public hosting. The prototype PostgreSQL password is intentionally public for loopback development only.

## Validation and exports

```sh
./scripts/validate.sh                  # Native gameplay, UI, offline persistence and two-client LAN
./scripts/validate.sh --backend        # Also isolated PostgreSQL adversarial tests and simulation
./scripts/test_render.sh               # Requires display; demo + repeated scene cleanup regression
.venv/bin/python scripts/test_account_network.py  # Real account-ticket admission tests
./scripts/export.sh linux
./scripts/setup-android.sh
./scripts/export.sh android
./scripts/export.sh ios                # Unsigned Xcode project; no IPA on Linux
python3 scripts/verify_builds.py
python3 scripts/build_manifest.py package
```

Optional live native account checks: set `ECONOMY_UI_TEST_URL=http://127.0.0.1:8080` when running `game/tests/economy_ui_test.gd`. Tests use fictional accounts. `backend/bridge_fixture.py` and `scripts/test_reward_bridge.py` exercise the real reward adapter with an explicitly synthetic match fixture against an isolated database; this is not a ten-human match or mobile benchmark.

Outputs are `builds/linux/sightbreak.x86_64` and `builds/android/sightbreak-debug.apk`. Android is a debug-signed development package, API 24+, target API 36. Export and signature verification do not establish device behavior. The unsigned Xcode project is exported to `builds/ios/sightbreak.xcodeproj`; an installable iPhone build requires macOS, Xcode, Apple signing and physical testing. Detailed commands and provenance: [builds.md](docs/builds.md).

## Continue development

- [Architecture](docs/ARCHITECTURE.md), [weapons](game/scripts/gameplay/weapons.gd), [economy configuration](backend/config/economy.json).
- [Backend/API/migrations/backup](docs/backend.md), [economy simulation report](docs/economy.md), [network protocol](docs/network.md).
- [Milestones and next work](docs/MILESTONES.md), [independent QA](docs/reports/QA-0.3.md), [known limitations](docs/KNOWN_LIMITATIONS.md).

Use this existing isolated checkout. Do not create a Git worktree unless requested. Preserve development state in commits and update evidence when behavior changes. Never mark untested device behavior, scores, screenshots or features as passed.
