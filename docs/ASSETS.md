# Asset pipeline and provenance

Relay Yard, modular industrial structures, character silhouettes, first-person guns/arms, icon, cosmetic shader and synthesized audio were authored for this repository. No Counter-Strike names, art, audio, maps or external marketplace content are included.

- `game/scripts/gameplay/arena.gd`: procedural geometry, collision, sites, route markings, skyline, lighting and material batching. Change geometry and navigation together; retain the arena/actor regression checks.
- `game/scripts/gameplay/actor.gd`: procedural character/gun assembly, first-person animation, impact/shot feedback and material-only cosmetic application.
- `game/scripts/gameplay/utility.gd`: grenades and smoke. Visual replicas never apply client-authoritative damage.
- `game/scripts/ui/item_inspector.gd`: native `SubViewport` with procedural item representation, drag/zoom controls and deterministic metadata finish. It is not a photographic image or production asset pack.
- `game/scripts/ui/case_reveal.gd`: neutral sealed-panel carousel with a server-committed final result. Neighboring cards do not fabricate rare near misses.
- `game/assets/icon.svg`: original project mark.
- Gunshot/hurt/explosion streams are synthesized in code; there are no third-party audio files.

Godot and export-template license notices are retained in `docs/GODOT-LICENSE.txt` and `docs/GODOT-COPYRIGHT.txt` and copied into native build outputs by the export script. Python dependency versions/hashes are locked in `backend/uv.lock`; retain their upstream licenses for redistribution. Tool downloads and verification sources are recorded in `docs/toolchain-provenance.md`.

Future production assets should be imported as glTF with explicit scale, collision and LOD budgets. Record author/source/license alongside every added external asset; use properly licensed originals and preserve attribution. Device budgets must be measured rather than inferred from desktop or software-render output.
