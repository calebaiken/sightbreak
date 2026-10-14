# Environment production

**Status: not started on this branch.** Relay Yard is still built from batched boxes (`arena.gd`) with three tiling PBR sets, as in 0.4.

## Contract with gameplay (must not change)

- **Collision:** collision shells, lane geometry, plant sites and spawn positions stay as authored in `arena.gd`.
- **Visual dressing:** it may not occlude what collision allows players to see through, and it may not open sightlines that collision blocks.
- **Readability:** wall, floor and cover surfaces must keep the contrast that the readability captures in `docs/reports` established.

## First section to produce

Bring the B-site transfer hall front (doors, columns, signage and the floor in front of it) to final quality as the first environment section:
- a modular trim sheet;
- three hero props (container door set, column base, signage frame);
- wear decals;
- a baked lightmap for the static set.

It must keep the current box collision and be measured on LOW and STANDARD against the 0.4 benchmark views.

## Budgets

| Item | Budget |
| --- | --- |
| Hero prop | ≤ 6k triangles; shares the trim atlas |
| Section draw calls | ≤ +30 over the 0.4 site view (37 draws measured in software rendering) |
| Lightmap | ≤ 1024² per section, in a format the Compatibility renderer supports |
