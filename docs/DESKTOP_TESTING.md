# Native desktop alpha acceptance checklist

Record OS/architecture, engine, exact source SHA/game tree, source and artifact
hashes, commands/actual exit codes, raw failures, logs and unedited screenshots.
Use a new evidence directory and frozen clean commit for every attempt. The
`Desktop playability P1` workflow and scripts are development gates; unexecuted
platforms remain **UNVERIFIED**. Headless startup is not graphical acceptance.

Current exact-source results and retained failures are in the
[playability report](reports/DESKTOP_PLAYABILITY_REPORT.md); the
[parent delivery report](reports/DESKTOP_ALPHA_REPORT.md) retains its historical
scope. Desktop/mobile touch selection is now explicit. Simulated touchscreen and
controller capability tests are separate from physical input-device qualification.

For objectives and newly earned ordinary-match training, run separate fresh
attempts against the selected exported package:

```sh
python scripts/verify_offline_match.py --target linux --scenario plant --seed 42 --display :107 --timeout 180 --output /absolute/new/plant
python scripts/verify_offline_match.py --target linux --scenario defuse --seed 42 --display :108 --timeout 180 --output /absolute/new/defuse
python scripts/verify_offline_match.py --target linux --scenario full-match --display :109 --timeout 1800 --output /absolute/new/full-match
```

On native Windows use `--target windows`; Win32 input requires no Xvfb. Automated
macOS gameplay remains unimplemented. Windows hosted CI explicitly selects
`--hosted-render-priority below-normal` for owned offline game processes; default
manual invocation inherits priority. Disclose that scheduling adjustment and its
actual class receipts separately from shipped game behavior or performance. `--executable` accepts an extracted native
entry point only when its bytes match the original clean export receipt.

Plant/defuse declare initial debug/offline spawns, side and seed before physics;
ten stock living actors, equipment, AI, combat, collision and timers remain active.
Require actual movement from outside interaction range, out-of-range/interrupted-E
negative controls, uninterrupted 3/5-second **simulation** holds measured from
consumed input to authoritative completion, local contribution, ordinary objective
resolution, next round and normal restart. Read-only authority observations do
not replace rendered phase/role evidence. Retain legitimate combat deaths and
automation overshoot failures; do not change health or winners to pass.

`full-match` forbids `--seed`, retaining stock spawns/teams/randomness and
`time_scale=1`. Require one normal result, ten-player scoreboard, exactly one new
history entry and earned offline XP/Credits actually loaded in a reopened client.
Preserving an unchanged profile alone is insufficient. The 1800-second watchdog
is a bounded trial, not a guarantee for every possible match. No save/result API
injection is allowed. Offline training cannot authorize account rewards.

Layouts request 960×540, 1280×720, 1920×1080 and 1280×800. Capture generation,
independent original-image review, physical high DPI and performance are separate
gates. Preserve each attempt and its exact source when later attempts succeed.

| Area | Required evidence |
| --- | --- |
| Windows | AMD64 PE, icon/version/PCK inspection; native Windows rendered startup and input; clean normal close |
| Linux | x86_64 ELF, executable launcher/PCK inspection; extracted ZIP launch; X11 and Wayland separately where available |
| macOS | Universal 2 slices, plist/icon/PCK/modes/signature; native Intel and Apple Silicon execution separately |
| Offline | Menu → 5v5 → live living player → real move/aim/fire/reload; positive health and conserved ammunition |
| Round flow | Buy/switch/utility; authoritative plant/defuse or documented round completion; distinguish fixture controls from actual exported objectives |
| UI/display | Tab roster, field menu/settings, pointer capture/release, focus loss/explicit resume; 960×540, 1280×720, 1920×1080, 1280×800; text scaling/DPI and three window modes |
| Persistence | Change a setting through real UI, normal close/reopen, compare saved offline scope/settings/training; completed-match progress separately |
| Multiplayer | Matched protocol 6 peers, authoritative ammo/movement/damage, private snapshots, reconnect; mixed-OS compatibility separately |
| Packaging | Exact export/verifier commit, clean source/tooling, all payload hashes/modes, notices; extracted entry-point execution |
| Stability | Actual root exit, strict nested error/leak scan, bounded cleanup; retain every failed attempt |

After selecting and exporting the native target ([commands](builds.md)):

```sh
python scripts/verify_builds.py --targets linux --graphical
python scripts/verify_integration_export.py --target linux --visit-armory --reload-mode keyboard --timeout 240 --output builds/native-network-attempt-1
python scripts/verify_offline_export.py --display :102 --timeout 300 --output builds/native-offline-attempt-1
```

Linux UI controllers require Xvfb/X11/XTest, Pillow and Tesseract; set `XVFB_BIN`
if Xvfb is not on PATH. Screenshots use native X11 pixels. Windows uses the same
network controller with `--target windows`, Pillow, Win32 native input and raw
client-area screenshots. It does not need Xvfb. macOS graphical menu startup is
available through the verifier; automated macOS gameplay input is unimplemented.
Do not turn that missing coverage into a pass.

The real exported network client connects to an explicitly synthetic local guest
authority fixture with a practice rifle. Its ammo/reload assertions are server
observations. The fixture is excluded from exports, grants no account rewards
and establishes neither internet transport security nor an offline full match.
Offline screenshots require independent inspection in addition to positive-health
OCR; ambiguous/blank/dead HUD results fail. A frame-count exit is only an optional
premature-exit control; successful input flows use normal OS window close.

Run the maintained `scripts/validate.sh`, backend tests with an isolated PostgreSQL
database, and relevant protocol/load campaigns. Keep prior failures and skipped
groups explicit. Physical input feel, controller hardware, audio listening,
complete human matches, mobile regression and each applicable 8.5 quality gate
require their own independent evidence. Never claim Steam Deck Verified from CI.
