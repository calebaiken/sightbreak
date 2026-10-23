# SIGHTBREAK — MOBILE TACTICAL FPS
## Full Game Development Specification for Codex Cloud

You are the lead developer and technical director of **SIGHTBREAK**, an original, high-quality, competitive 3D first-person shooter for iOS and Android.

Your objective is to build an actual playable game with polished tactical combat, responsive mobile controls, offline bots, online multiplayer, character progression, collectible cosmetics, animated case openings, secure player trading, and an in-game marketplace.

**IMPORTANT ECONOMY REQUIREMENT: SIGHTBREAK MUST INITIALLY HAVE NO REAL-MONEY TRANSACTIONS.**

Every currency unit, case, key, and cosmetic must be obtainable through gameplay, progression, challenges, or legitimate player-to-player exchanges.

Do not implement in-app purchases, payment processors, paid premium currency, real-money item sales, cash withdrawals, or external-market integrations.

## 1. DEVELOPMENT TEAM AND INDEPENDENT QA

Assume these responsibilities:

1. Lead game designer
2. Senior Godot gameplay engineer
3. Mobile graphics and optimization engineer
4. Physics and weapon-systems engineer
5. Multiplayer and networking engineer
6. Backend database and economy engineer
7. 3D environment and technical artist
8. AI and bot-behavior developer
9. UI/UX and accessibility designer
10. Independent QA reviewer

Use Codex subagents when available. Otherwise execute the responsibilities through appropriately separated implementation and review processes.

Maintain an independent quality assessment requiring a minimum score of 8.5/10 in every applicable category before accepting a development milestone.

Never fabricate QA scores, test passes, screenshots, device benchmarks, or working features.

## 2. ENGINE AND TECHNOLOGY

Use:
- Godot 4, with a verified supported stable version
- GDScript for game logic
- Godot's 3D mobile-compatible rendering systems
- Dedicated authoritative game servers
- An independently secured persistent economy backend
- PostgreSQL for authoritative multiplayer inventory and marketplace records
- SQLite or local files for offline-only progress and settings
- Git for source control
- Automated tests and reproducible builds

Choose a maintainable backend framework suited to authoritative transactions, authentication, networking, and database integrity.

Keep the game, server, and economy services modular.

Build for both iOS and Android, with desktop development builds for validation.

Do not substitute web-based gameplay or mock interfaces for the native 3D game.

## 3. CORE GAMEPLAY

Create a competitive tactical FPS inspired by the strategic qualities of Counter-Strike, while maintaining original intellectual property.

Primary mode: 5v5 objective-based tactical combat.

Implement:
- Attackers and defenders
- Two objective sites
- Planting and defusing
- Round-based combat
- A weapon-buying economy during matches
- Winning and losing rounds
- Team switching
- Scoreboards
- Match results
- Kill and assist tracking
- Objective contributions
- Spectator mode
- Offline bot matches
- Dedicated-server multiplayer

Include realistic-feeling movement, crouching, jumping, weapon switching, and skill-based aiming.

Implement authentic shooting mechanics:
- Recoil patterns
- Bullet spread and accuracy
- Movement penalties
- Headshot multipliers
- Weapon damage falloff
- Reloading
- Ammo management
- Hit registration
- First-person weapon animations
- Impact effects
- Grenades and smoke
- Positional audio

Separate the temporary match-buy economy from the persistent cosmetic Credits economy.

Players must never gain a competitive statistical advantage by owning rare cosmetics.

## 4. MOBILE CONTROLS

Implement responsive and fully customizable touchscreen controls.

Support:
- Dual virtual joysticks/touch zones
- Multi-touch aiming and shooting
- Customizable HUD layouts
- Button resizing and repositioning
- Gyroscope aiming where supported
- Sensitivity adjustment
- Crosshair customization
- Optional controller support
- Device-safe UI areas

Make controls suitable for three- and four-finger competitive play.

Target 60 FPS on representative mid-range mobile devices, with scalable settings and optional higher refresh rates for supported hardware.

## 5. PROGRESSION SYSTEM

Create a persistent player account and progression system.

Each player has:
- Unique player ID
- Display name
- Account level
- Experience points
- Earned Credits balance
- Match history
- Career statistics
- Challenge progress
- Inventory
- Cosmetic loadouts
- Trading history
- Marketplace activity

Experience is awarded for legitimate gameplay and objective contribution.

Implement a configurable level progression curve.

Players should receive Credits through:
- Match completion
- Match wins
- Daily play bonuses
- Daily challenges
- Weekly challenges
- Level-up rewards
- Achievements and milestones

Provisional economy:
- Completed match: 100 Credits
- Win bonus: 75 Credits
- Daily first-match bonus: 150 Credits
- Daily challenges: 100–300 Credits
- Weekly challenges: 500–1,000 Credits
- Level-up reward: 250 Credits

These are initial balancing parameters, not immutable values.

All online reward calculations must be validated and committed by the server.

Prevent exploitative AFK farming, repeated match abandonment, bot farming, duplicate rewards, and unauthorized credit creation.

Offline play must work without an account, but any offline progression must remain clearly separate from authoritative online inventories and tradable Credits until a secure, abuse-resistant synchronization policy exists.

## 6. COSMETIC INVENTORY SYSTEM

Create an extensive cosmetic collection system inspired by collectible tactical shooter inventories.

Support:
- Weapon skins
- Knife skins
- Gloves
- Character accessories where compatible with competitive readability
- Weapon stickers
- Weapon charms
- Cases
- Keys
- Special collectibles

Cosmetics must be visual only.

Each item instance needs:
- Unique server-generated identifier
- Item definition ID
- Rarity tier
- Finish or pattern
- Optional wear value
- Optional special variant
- Ownership information
- Acquisition timestamp
- Trade eligibility
- Marketplace eligibility
- Item transaction history

Store item metadata authoritatively.

Prevent duplication through atomic ownership transfers and inventory validation.

Create a beautiful inventory UI where players can rotate, zoom, and inspect 3D weapon models.

Allow saved cosmetic loadouts and automatic cosmetic application to equipped weapons.

## 7. CASE OPENING SYSTEM

Create an original, polished case-opening experience with the anticipation and collectibility associated with Counter-Strike-style cases.

Use original branding, animations, cases, sounds, artwork, and UI.

Create several themed case collections with distinctive cosmetic rewards.

Suggested launch collections:
- **Obsidian Collection**
- **Crimson Archive Collection**
- **Spectral Circuit Collection**
- **Blacksite Collection**

The case-opening experience must include:
- Case selection
- Reward previews
- Publicly disclosed probabilities
- Key requirements where applicable
- Opening confirmation
- Animated reward carousel
- A coherent deceleration animation
- Item reveal
- Rarity-specific visual presentation
- Weapon inspection
- Inventory integration

The reward must be generated and committed securely by the server before the reveal animation begins. The client must not influence the result by timing, animation behavior, or network manipulation.

Use an auditable, cryptographically secure random selection process with versioned probability tables.

### Rarity system

Create an initial rarity structure:

| Rarity | Probability |
|---|---:|
| Common | 58.0% |
| Uncommon | 26.0% |
| Rare | 11.0% |
| Epic | 4.0% |
| Legendary | 0.9% |
| Mythic | 0.1% |

These values are provisional and must be reviewed for balance.

Display exact current probabilities clearly before opening cases.

Never manipulate odds based on player behavior, account history, spending, or engagement.

Include reasonable accessibility settings, such as animation skipping and reduced motion.

Do not create artificial near-miss outcomes designed to imply players almost won an item that was not actually selected.

### Obtaining cases and keys

Cases can be:
- Earned from completed matches
- Awarded by challenges
- Unlocked through progression
- Obtained through player trades
- Purchased using earned Credits

Keys can be acquired using earned Credits or progression rewards.

No real-money purchases.

Make case and key prices configurable.

Avoid artificial scarcity, excessive grinding, and manipulative engagement loops.

## 8. WEAPON FINISHES AND SPECIAL VARIANTS

Develop a flexible cosmetic material system.

Support:
- Painted finishes
- Metallic finishes
- Brushed steel
- Carbon fiber
- Iridescent finishes
- Engraved patterns
- Animated materials where performant
- Procedurally varied patterns
- Wear appearance

For applicable items, support randomized cosmetic variations based on server-generated seeds.

Make variations deterministic from stored item metadata.

Allow rare special patterns without introducing gameplay advantages.

Create original skins that can become visually recognizable and desirable collectibles.

Include standout designs matching the SIGHTBREAK visual identity: obsidian black, deep crimson, brushed steel, graphite, and muted gold.

## 9. PLAYER-TO-PLAYER TRADING

Build a genuine secure trading system connected to persistent player accounts.

Players should be able to:
- View eligible player profiles
- Send and receive trade requests
- Offer owned cosmetic items
- Preview the other player's offer
- Inspect item rarity and metadata
- Confirm both sides' proposed exchanges
- Cancel unconfirmed trades
- Review completed trades

Implement a two-sided confirmation mechanism.

If either player modifies an offer, invalidate prior confirmations.

Perform final ownership checks and item transfers server-side within a single atomic transaction.

Reject:
- Duplicate item transfers
- Trades involving unowned items
- Locked or marketplace-listed items
- Invalid account states
- Concurrent conflicting transactions

Maintain an auditable history.

Implement cooldowns and rate limiting to reduce automated trading abuse.

## 10. PLAYER MARKETPLACE

Create a community marketplace using only earned SIGHTBREAK Credits.

Players can:
- List eligible cosmetics for sale
- Set an asking price
- Browse marketplace listings
- Filter by weapon, collection, rarity, finish, and price
- Inspect an item before purchasing
- Purchase with earned Credits
- Cancel their own listings
- View transaction history

Use server-authoritative balances and inventory transfers.

Deduct Credits and transfer ownership atomically.

Prevent item duplication, double purchases, stale ownership, negative balances, and replayed purchase requests.

Introduce configurable listing and transaction fees if simulations show they help maintain a stable economy.

Keep marketplace prices based on legitimate player supply and demand.

Do not automatically assign real-money equivalents to items or Credits.

**Never allow Credits or cosmetic items to be withdrawn, redeemed for real money, cryptocurrency, or external financial value through the game.**

Do not implement third-party marketplace connectivity.

Treat trading and marketplace operations as security-sensitive.

## 11. ECONOMY DESIGN AND SIMULATION

Create an economy simulation and balancing toolkit.

Model:
- Credit generation by gameplay
- Credit sinks from cases and keys
- Marketplace transaction fees
- Cosmetic supply
- Item rarity distribution
- Average time to earn cases
- Player progression
- New-player purchasing power
- High-level player purchasing power
- Market liquidity
- Inflation and item oversupply
- Farming and exploitation scenarios

Develop reproducible simulations over thousands of hypothetical players and matches.

Define economy health metrics:
- Average Credits earned per play hour
- Average Credits balance
- Case-open frequency
- Rarity supply distribution
- Median marketplace prices
- Trading volume
- Inflation indicators
- Rate of suspected farming

Do not optimize solely for excessive player engagement.

Prioritize fairness, sustainability, and enjoyable progression.

Expose economy settings through version-controlled configuration rather than hardcoded gameplay logic.

## 12. BACKEND AND DATA SECURITY

Create a trustworthy account and economy backend.

Requirements:
- Authenticated users
- Secure session management
- Authoritative wallets
- Append-only currency transaction ledger
- Unique cosmetic instances
- Database transactions
- Idempotent reward grants
- Idempotent case openings
- Atomic marketplace settlements
- Trade escrow or equivalent item reservation
- Rate limiting
- Appropriate audit logging
- Backup and recovery procedures

Never let clients directly set their balance, inventory, rarity results, or marketplace ownership.

Do not expose database credentials or privileged service secrets in the client application.

Use test accounts and fictional data in development.

Develop automated adversarial tests for:
- Item duplication
- Double-spending
- Concurrent purchases
- Replay attacks
- Client-modified balances
- Forged rewards
- Invalid trades
- Race conditions
- Disconnects during transactions

No external hosting expenses or paid services without my explicit approval.

## 13. UI/UX AND VISUAL IDENTITY

Brand the entire game as **SIGHTBREAK**.

Art direction:
- Dark graphite
- Obsidian black
- Deep crimson
- Antique gold accents
- Industrial materials
- Clean tactical typography
- Precision-focused iconography

Create:
- Main menu
- Play screen
- Loadout
- Player profile
- Progression dashboard
- Challenge menu
- Inventory
- Case collection
- Case-opening screen
- Item inspector
- Player trading interface
- Community marketplace
- Settings
- Multiplayer browser
- Match scoreboard

All UI should be responsive on mobile devices.

Every interactive control must have real functionality, understandable feedback, and reliable error handling.

Animations should be polished but avoid compromising usability or mobile performance.

## 14. GAME WORLD AND AI

Create an original competitive map called Relay Yard.

Features:
- Two objective sites
- Multiple strategic routes
- Balanced sightlines
- Distinct landmarks
- Vertical cover variation
- Readable lighting
- Original modular architecture
- Efficient mobile rendering

Implement intelligent offline bots:
- Pathfinding
- Cover usage
- Visibility and hearing
- Difficulty levels
- Weapon selection
- Objective planting/defusing
- Navigation recovery
- Basic team coordination

Ensure offline matches are genuinely playable.

## 15. MULTIPLAYER

Implement a server-authoritative multiplayer system.

Support:
- Direct-IP/LAN testing
- Dedicated servers
- 5v5 matches
- Player synchronization
- Weapon and combat validation
- Network interpolation
- Client prediction where appropriate
- Latency compensation with abuse-resistant constraints
- Reconnection
- Anti-cheat foundations

Design the architecture to accommodate future matchmaking without claiming matchmaking exists before it is actually developed.

Keep gameplay servers and persistent account/economy services appropriately separated.

## 16. DEVELOPMENT MILESTONES

### Phase 1 — Foundation
Create the repository, Godot project, architecture, test infrastructure, main menu, and player controller.

### Phase 2 — Combat
Build a functional FPS vertical slice with weapons, combat, damage, a 3D arena, bots, and touch controls.

### Phase 3 — Complete offline mode
Implement the tactical match rules, objective sites, round economy, full map, AI, HUD, and results.

### Phase 4 — Online multiplayer
Implement dedicated-server gameplay, authentication, authoritative match results, and persistence.

### Phase 5 — Progression and inventory
Implement accounts, experience, challenges, Credits, cosmetic definitions, and persistent inventories.

### Phase 6 — Cases and cosmetics
Implement cases, earned keys, reward probability tables, server-side opening, animations, cosmetic finishes, and item inspection.

### Phase 7 — Trading and marketplace
Implement secure item exchanges, marketplace listings, Credit settlement, transaction histories, and adversarial security tests.

### Phase 8 — Visual production and optimization
Polish maps, models, animation, sound, lighting, graphics settings, UI, and performance.

### Phase 9 — Release candidate
Verify supported builds, mobile usability, gameplay balance, security, accessibility, and regression tests.

Preserve a functional playable game at the end of each phase.

## 17. QA REQUIREMENTS

For every development milestone, evaluate:

- Gameplay correctness
- Mobile usability
- Visual quality
- Code maintainability
- Stability
- Performance
- Security
- Economy correctness
- Multiplayer integrity where applicable

Minimum acceptance score: **8.5/10 per applicable category**.

QA scores must be supported by evidence.

Untested criteria must remain UNVERIFIED and cannot count as passed.

Automate tests wherever possible.

Require correction and retesting for failures.

Maintain clear reports and issue tracking.

## 18. CODEX CLOUD CONSTRAINTS

Develop inside the available Codex Cloud environment.

Verify available tools, execution capabilities, and build dependencies rather than assuming them.

Use headless Godot testing and reproducible scripts where possible.

Provide runnable desktop testing builds when supported.

Android APK generation is desirable if the cloud environment can correctly support it.

For iOS, provide an export-ready project and document macOS/Xcode requirements. Do not claim an installable iPhone build without successfully creating and verifying it.

Document any manual steps required for physical-device testing.

Never spend money, create paid infrastructure, register services, or enable live commercial features without approval.

## 19. DELIVERABLES

Create and maintain:

- Working Godot game project
- Multiplayer server code
- Economy backend
- Database schema and migrations
- Game asset pipeline
- Weapon configuration
- Cosmetic item definitions
- Case probability tables
- Progression and challenge definitions
- Inventory/trading/marketplace functionality
- Automated tests
- Development README
- Build documentation
- Architecture documentation
- Economy balancing report
- Independent QA report
- Milestone roadmap
- Known limitations document

Include clear instructions for local testing, server setup, offline gameplay, and supported mobile builds.

Use sensible Git commits and meaningful progress reports.

## 20. EXECUTION DIRECTIVE

Begin development immediately.

Do not stop after designing the architecture.

Implement, test, review, and refine the actual playable game.

Start with movement, weapon mechanics, touchscreen input, and a usable 3D test map.

Then systematically complete the offline game, networking, progression, case system, inventory, trading, and marketplace.

Prioritize a stable playable product over superficial feature quantity.

Use genuine original content and properly licensed dependencies.

Preserve development state across Codex sessions through repository files.

At every milestone provide:
- Implemented features
- Passing tests
- Failed tests
- QA scores
- Security findings
- Performance measurements where available
- Next tasks

**FINAL PRODUCT GOAL:**

SIGHTBREAK should become a polished, skill-based, competitive mobile tactical FPS with satisfying shooting mechanics and an enjoyable, player-driven cosmetic economy.

Players should be able to start with nothing, compete in matches, gain experience, earn Credits, unlock cases, obtain rare cosmetics, build collections, trade with friends, and participate in an authentic community marketplace — entirely through gameplay.

BUILD SIGHTBREAK.
