# Character production

**Status: not started on this branch.** Operators are still the procedural primitive bodies from 0.3/0.4 (articulated knees and arms, sphere helmets). This document fixes the standard the first authored operator must meet, so the work can start without re-deciding it.

## Contract with gameplay (must not change)

- **Hit volumes:** the head and helmet ellipsoids from `SBActor.HEAD_VOLUMES`, and the body as the 0.3 movement capsule (r 0.31 m, h 1.8/1.25 m, cut at the torso top).
  - A visual model must fit these volumes rather than move them.
  - Any change to hit volumes needs its own documented compatibility review and is outside this initiative.
- **Node roles read by the actor:**
  - body root;
  - legs, knees and arms (articulated);
  - head;
  - `world_muzzle` (third-person muzzle flash);
  - team colour parameters.
- **Crouch:** the drawn body must stay inside the crouched capsule and helmet volumes.

## Production standard

- **Pipeline:** a generator script in `tools/art/` (same conventions as the Relay AR), with a skeleton exported in glTF for the existing articulated motions.
- **Budgets:** ≤ 18k triangles at LOD0, ≤ 6k at LOD1 and ≤ 2k at LOD2; a 1024² body atlas plus a 512² gear atlas. Team identity comes from material parameters, not separate textures.
- **Readability tests:**
  - silhouette captures at 10, 25 and 45 m on LOW and STANDARD;
  - team identification in sun and shade;
  - no part may visually exceed the hit volumes by more than 1 cm.
