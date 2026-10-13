# SIGHTBREAK

A native **Godot 4.7.2** tactical FPS development build for desktop, Android and future iOS export. Fight a 5v5 offline match in the original Relay Yard, or connect to a dedicated server. The separate PostgreSQL economy supports authenticated accounts, earned Credits, collectible rifle finishes, cases, two-sided trades and marketplace purchases.

**No real-money transactions.** There are no payments, premium purchases, withdrawals, cryptocurrency or external marketplaces. Offline training progress never becomes tradable online value.

This is a playable **development alpha**, not the finished release in the [full specification](docs/SPECIFICATION.md). Independent QA has not accepted the required 8.5/10 milestone gates; physical mobile usability, sustained device performance and production security remain unverified. Read the [QA evidence](docs/reports/QA.md), [known limitations](docs/KNOWN_LIMITATIONS.md) and [milestone roadmap](docs/MILESTONES.md).

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
| Fire / reload | Left mouse / R | FIRE / LOAD |
| Jump / crouch | Space / Ctrl | JUMP / LOW |
| Plant / defuse | Hold E | Hold USE |
| Weapons | 1 primary / 2 sidearm | SWAP |
| Frag / smoke | G / Q | FRAG / SMOKE |
| Buy / roster | B / Tab | BUY / TEAM |
| Menu | Escape | Pause button |

Settings include sensitivity, FOV, frame cap, shadow quality, volume, crosshair size/color, gyro, controller input and reduced motion. During a match, the field menu opens the touch HUD editor. Drag button positions and press **SAVE TOUCH LAYOUT**; button scale is adjustable in settings. Physical gyro/controller behavior still needs device review.

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
./scripts/test_render.sh               # Requires display; currently flags known GL teardown failure
.venv/bin/python scripts/test_account_network.py  # Real account-ticket admission tests
./scripts/export.sh linux
./scripts/setup-android.sh
./scripts/export.sh android
```

Optional live native account checks: set `ECONOMY_UI_TEST_URL=http://127.0.0.1:8080` when running `game/tests/economy_ui_test.gd`. Tests use fictional accounts. `backend/bridge_fixture.py` and `scripts/test_reward_bridge.py` exercise the real reward adapter with an explicitly synthetic match fixture against an isolated database; this is not a ten-human match or mobile benchmark.

Outputs are `builds/linux/sightbreak.x86_64` and `builds/android/sightbreak-debug.apk`. Android is a debug-signed development package, API 24+, target API 36. Export and signature verification do not establish device behavior. iOS export settings are included, but an installable iPhone build requires macOS, Xcode, Apple signing and physical testing. Detailed commands and provenance: [builds.md](docs/builds.md).

## Continue development

- [Architecture](docs/ARCHITECTURE.md), [weapons](game/scripts/gameplay/weapons.gd), [economy configuration](backend/config/economy.json).
- [Backend/API/migrations/backup](docs/backend.md), [economy simulation report](docs/economy.md), [network protocol](docs/network.md).
- [Milestones and next work](docs/MILESTONES.md), [independent QA](docs/reports/QA.md), [known limitations](docs/KNOWN_LIMITATIONS.md).

Use this existing isolated checkout. Do not create a Git worktree unless requested. Preserve development state in commits and update evidence when behavior changes. Never mark untested device behavior, scores, screenshots or features as passed.
