# SIGHTBREAK architecture

This is a native Godot 4 project. The full product request is preserved in [SPECIFICATION.md](SPECIFICATION.md). No web gameplay or payments are part of the product.

- `game/`: native client and the headless dedicated simulation. `scripts/gameplay/actor.gd` owns movement and weapon rules, `arena.gd` constructs original Relay Yard geometry, and `match.gd` owns rounds and authority. `scripts/network/` accepts constrained input and distributes authoritative state.
- `game/scripts/ui/`: touch controls, HUD, native account/inventory/economy screens and a real 3D item inspector.
- `backend/`: separate authenticated account and economy service using PostgreSQL, transactions, idempotency and item reservation. The game client never receives database credentials or privileged server keys.
- `game/scripts/profile.gd`: offline training progress saved locally. It cannot be imported into online wallets or inventory.
- `scripts/`: reproducible toolchain, validation and native export commands.

The match wallet buys equipment only for the current match. Persistent Credits obtain only visual cosmetics and cases/keys. All online currency/item changes must pass backend authorization and transactional invariants. There are no real-money conversions, payment APIs, redemption, or external marketplaces.

The procedural map, models, materials, UI icon and synthesized sounds are original project content. Compatibility rendering provides a conservative GLES3 mobile baseline; physical device frame time and thermal behavior require device testing.

The repository is already an isolated checkout. Continue work in this checkout; do not create a Git worktree unless the user asks. Preserve source changes between sessions and update the roadmap and QA report with evidence. An unverified acceptance criterion never passes by assumption.
