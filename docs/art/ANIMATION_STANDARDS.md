# Animation standards

**Status:**
- **Relay AR with the rigged arms (default on this branch):** the support hand performs the reload. The 1 s `reload` clip in `relay_ar_arms.glb` is seeked by reload progress, and frame 0 is the hold.
  - The hand leaves the handguard, takes the magazine, follows it down its well and back, seats it with a short push and returns.
  - The weapon moves into a held reload pose (an 11 cm lift, 5 cm toward the centre, a clockwise roll) so the hand and the whole magazine are in frame at the grab and the seat.
  - Online clients receive the reload timer at the snapshot rate (20 Hz). The pose follows a presentation clock in `actor.gd` (`_reload_clock`): it advances every visual tick and stays within 0.1 s below the authoritative timer, and it snaps to a new reload or an upward correction. It never writes the timer, ammunition or any gameplay state. At 20 Hz the clip time now changes on every visual tick, where before it changed on 1 tick in 3.
  - The trigger finger curls with the recoil kick.
- **Still transform-driven:** recoil kick, sway, walk bob, the equip dip, and every other weapon's reload (tilt plus a 0.23 m magazine drop and reseat).
- **Not authored yet:** draw, inspect, bolt release and a second magazine. The same magazine is pulled and reseated.

Evidence is under `docs/reports/media/art-v3/`:
- `motion/`: `5100b3e`, the hand and magazine below the frame;
- `staged-reload/`: the current staging.

Each sequence is a frame-by-frame capture from `game/tests/weapon_motion_capture.gd`.

## Rules

1. **Animation never drives gameplay.**
   - Fire cadence, reload duration, deploy time and recoil values come from `weapons.gd` and the authoritative actor.
   - Clips are timed to them, never the reverse.
   - A clip that cannot fit the gameplay timing is shortened, not the timing lengthened.
2. **Reduced motion is respected.** When the player enables reduced motion, cosmetic sway and equip motion are attenuated (asserted in `actor_test.gd`). New clips must provide the same attenuation.
3. **Readable silhouettes.** Reload and inspect poses must not hide the crosshair area or the HUD's ammunition block.
4. **First-person contract.**
   - The magazine node pivots at its seated top.
   - The muzzle marker sits at the crown, and the ejection marker at the port.
   - The hands are posed per weapon from the generator's `grip_hand` and `support_hand` anchors.

## Next

1. Draw and inspect clips on the same rig. The game already seeks clips by state (`_deploy_remaining` for draw), and a clip never writes the state it reads.
2. A second magazine, so the reload is a swap rather than a reseat.
3. A bolt release on empty reloads. It needs the empty or tactical distinction the authoritative actor already has (`ammo == 0` when the reload starts); presentation only.
4. Reduced motion: the reload pose is scaled by 0.2 like the old tilt. Check that the hand still reads with it.
