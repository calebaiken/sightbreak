# Development milestones

The initial source state contained only a README. This implementation establishes a playable native alpha with substantial offline, network and economy foundations. The specification's quality gate remains **at least 8.5/10 in every applicable category**, backed by independent evidence. Implemented functionality is not automatic milestone acceptance. No full phase is accepted while its applicable physical-device, security or quality criteria remain unverified.

| Phase | Implemented development scope | Remaining acceptance work |
| --- | --- | --- |
| 1 Foundation | Pinned native Godot toolchain, menu/settings, player controller, architecture, scripts, tests | Independent quality gate and device startup/lifecycle |
| 2 Combat | Four weapons, damage/headshots/recoil/spread/reload, grenades/smoke, distinct gunshots, staged reload/sway, replicated recoil, touch/controller/gyro code, 3D arena and bots | Physical input feel, production weapon/character animation and all-device stability |
| 3 Offline | Full 5v5 round loop, two sites, planting/defusing, match funds, side switch, scoreboard, results, spectator and local training records | Human balance and device soak; unforced full bot matches now pass including halftime and final result |
| 4 Online | Dedicated authoritative ENet, input filtering, snapshots/interpolation, reconnect, account tickets, trusted result bridge, server lobby reset | Encrypted production transport, broader anti-cheat, prediction/lag compensation, loss/jitter/10-human tests |
| 5 Progression/inventory | Authenticated accounts, XP/levels, match/daily-first/level rewards, authoritative wallets/instances, persistent rifle loadouts | Daily/weekly challenges, achievements, complete career/profile/history UX and anti-farming review |
| 6 Cases/cosmetics | Four collections, exact probabilities, CSPRNG draw committed before carousel, skip/reduced motion, procedural finishes and native 3D inspection | Expanded knife/glove/sticker/charm/accessory assets; physical-device polish |
| 7 Trading/market | Two-sided revision confirmations, atomic ownership exchange, marketplace debit/fee/transfer, reservation/replay/race tests | Complete filters/history/profile UX, pagination, trade expiry, durable app-restart recovery and load/security review; same-session lost-response retry implemented |
| 8 Production | Original procedural yard/models/sound, shader finishes, compatible renderer, quality controls, instance batching | Production art/audio/animation, device performance/thermal profiling and optimization |
| 9 Release | Native Linux/Android debug exports, unsigned iOS Xcode project, source-bound artifact manifests, reproducible checks and independent QA record | Physical Android/iOS evidence, secure public deployment review, accessibility/balance and release acceptance |

## Stabilization follow-up

The second development pass preserves the existing gameplay/economy architecture. The renderer failure now has a standalone engine reproduction, a shared-sky mitigation, and passing actual rendered demo/repeated-session checks. Synthetic input and landscape coverage were expanded; full natural bot matches exercise buying, combat, planting, halftime and one final result. Gunplay, environment surfaces, case inspection and safe pending-transaction retries have received focused polish. See the dated QA follow-up for independent measurements and scoped scores; these are not global milestone acceptance.

## 0.3.0-dev visual and mobile milestone

The existing systems continue from `4f21dc14ef73c3d620f095065ab89a0035ddd1f2`.

- Implemented: Relay Yard architecture/material pass; shared weapon geometry and articulated operator presentation; staged combat animation and pooled impact/casing effects; authority-confirmed network hit/impact feedback; compact mobile HUD and maximum-scale layout corrections; native hinged case and sharpened item/knife-reference inspection; inventory/market filters.
- Verified evidence: fixed-view native before/after captures, independent seven-category visual review, maintained gameplay/network/PostgreSQL/HTTP economy regressions, full bot matches and repeated native resource cleanup. Exact counts, scores and unresolved gates are in [QA-0.3](reports/QA-0.3.md).
- Measured: reproducible fixed-camera software-rendering counters and frame samples. These are development diagnostics and never mobile FPS or thermal evidence.
- Delivery: versioned Android debug package, Linux development export and unsigned iOS project, with source and payload hashes. Exact verified versions and paths are in [builds](builds.md).
- Incomplete: the visual gate (**8.1/10** aggregate; geometry/materials/lighting/models/effects below 8.5), every physical-device gate, human gunplay/balance assessment and production transport/security review. The native knife reference is not an owned item or an expanded reward catalog.

## Next development session

1. Begin with `docs/reports/QA-0.3.md`, `docs/KNOWN_LIMITATIONS.md` and `docs/DEVICE_TESTING.md`. Preserve the now-passing actual renderer/lifecycle checks and full regression aggregate. Do not reintroduce per-scene sky allocation without retesting the maintained Godot reproduction.
2. Continue the native screenshot loop on the weakest categories: authored character anatomy/hand integration, surface variation at believable scale, lighting/contact depth and less spherical smoke. Preserve the matched cameras and independent scoring. Current art increases standard rendering cost; profile LOD, shadow participation and batch/geometry budgets before adding detail.
3. Install the actual debug APK on representative midrange Android hardware and complete the QA device checklist. Collect device/OS/build hash, p95/p99 frame times, a full match and long-session thermal/memory behavior. macOS/Xcode/iPhone validation is a separate platform prerequisite.
4. Exercise ten real account users through full matches and rewards. Preserve privacy-safe identity/activity evidence; verify rejoin, ineligible abandonment, network loss, result retries and lobby reset. Synthetic fixture success is not human anti-farming evidence.
5. Finish configurable daily/weekly challenges, achievements and career/history screens from authoritative match records, with idempotent grants and adversarial tests.
6. Expand cosmetic definitions and original assets only after the visual-only loadout invariant remains tested. Finish multi-field market discovery/history and recoverable pending transaction UX.
7. Profile and improve predicted movement, bounded lag compensation and encrypted authenticated transport before public competitive play. Keep privileged services isolated and never add financial features.

## Session state

- Source and reproducible scripts live in the repository; generated exports, local keys, caches and transient logs are ignored. Curated QA logs/screenshots and manifest evidence are tracked under `docs/reports/`.
- Local test PostgreSQL and API run only for development. Start using `backend/dev-db.sh`, migrate explicitly, then `backend/dev-api.sh`; processes do not survive an environment snapshot.
- The installer pins and verifies Godot 4.7.2. Android toolchain setup and export instructions are in `docs/builds.md`.
- Automated fixtures are fictional and distinct from player progress. Never import local training saves into online inventory or wallets.
