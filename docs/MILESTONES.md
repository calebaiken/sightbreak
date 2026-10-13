# Development milestones

The initial source state contained only a README. This implementation establishes a playable native alpha with substantial offline, network and economy foundations. The specification's quality gate remains **at least 8.5/10 in every applicable category**, backed by independent evidence. Implemented functionality is not automatic milestone acceptance. No full phase is accepted while its applicable physical-device, security or quality criteria remain unverified.

| Phase | Implemented development scope | Remaining acceptance work |
| --- | --- | --- |
| 1 Foundation | Pinned native Godot toolchain, menu/settings, player controller, architecture, scripts, tests | Independent quality gate and device startup/lifecycle |
| 2 Combat | Four weapons, damage/headshots/recoil/spread/reload, grenades/smoke, touch/controller/gyro code, 3D arena and bots | Physical input feel, production weapon/character animation and all-device stability |
| 3 Offline | Full 5v5 round loop, two sites, planting/defusing, match funds, side switch, scoreboard, results, spectator and local training records | Human balance, full-session play and device soak; bots use simple tactics |
| 4 Online | Dedicated authoritative ENet, input filtering, snapshots/interpolation, reconnect, account tickets, trusted result bridge, server lobby reset | Encrypted production transport, broader anti-cheat, prediction/lag compensation, loss/jitter/10-human tests |
| 5 Progression/inventory | Authenticated accounts, XP/levels, match/daily-first/level rewards, authoritative wallets/instances, persistent rifle loadouts | Daily/weekly challenges, achievements, complete career/profile/history UX and anti-farming review |
| 6 Cases/cosmetics | Four collections, exact probabilities, CSPRNG draw committed before carousel, skip/reduced motion, procedural finishes and native 3D inspection | Expanded knife/glove/sticker/charm/accessory assets; physical-device polish |
| 7 Trading/market | Two-sided revision confirmations, atomic ownership exchange, marketplace debit/fee/transfer, reservation/replay/race tests | Complete filters/history/profile UX, pagination, trade expiry, lost-response recovery UX and load/security review |
| 8 Production | Original procedural yard/models/sound, shader finishes, compatible renderer, quality controls, instance batching | Production art/audio/animation, device performance/thermal profiling and optimization |
| 9 Release | Native Linux and Android debug exports, iOS configuration, reproducible checks and independent QA record | Physical Android/iOS evidence, secure public deployment review, accessibility/balance and release acceptance |

## Next development session

1. Begin with `docs/reports/QA.md` and reproduce unresolved findings before adding features. Run only relevant regressions while editing; run the aggregate before publishing a build.
2. Install the actual debug APK on representative midrange Android hardware and complete the QA device checklist. Collect device/OS/build hash, p95/p99 frame times, a full match and long-session thermal/memory behavior. macOS/Xcode/iPhone validation is a separate platform prerequisite.
3. Exercise ten real account users through full matches and rewards. Preserve privacy-safe identity/activity evidence; verify rejoin, ineligible abandonment, network loss, result retries and lobby reset. Synthetic fixture success is not human anti-farming evidence.
4. Finish configurable daily/weekly challenges, achievements and career/history screens from authoritative match records, with idempotent grants and adversarial tests.
5. Expand cosmetic definitions and original assets only after the visual-only loadout invariant remains tested. Finish multi-field market discovery/history and recoverable pending transaction UX.
6. Profile and improve predicted movement, bounded lag compensation and encrypted authenticated transport before public competitive play. Keep privileged services isolated and never add financial features.

## Session state

- Source and reproducible scripts live in the repository; generated exports, local keys, caches and logs are ignored.
- Local test PostgreSQL and API run only for development. Start using `backend/dev-db.sh`, migrate explicitly, then `backend/dev-api.sh`; processes do not survive an environment snapshot.
- The installer pins and verifies Godot 4.7.2. Android toolchain setup and export instructions are in `docs/builds.md`.
- Automated fixtures are fictional and distinct from player progress. Never import local training saves into online inventory or wallets.
