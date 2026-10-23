# Animation standards

**Status:**
- **Relay AR with the rigged arms (default on this branch):** the support hand performs the reload. The 1 s `reload` clip in `relay_ar_arms.glb` is seeked by reload progress, and frame 0 is the hold.
  - The hand leaves the handguard, takes the magazine, slides it out along its well, swings it left and lets it go (it falls and lands), goes down to a magazine pouch at the hip **below the frame** (the sleeve stays in it), takes the replacement there, brings it up and across, rocks its front lip into the well, drives it home with a shudder of the rifle, and returns. Phases and events are one list (`reload_phases.gd`); `docs/reports/media/art-v8/reload-hip-retrieval/README.md` has the measurements and what they do not show.
  - The weapon moves into a held reload pose (an 11 cm lift, 5 cm toward the centre, a clockwise roll) so the hand and the whole magazine are in frame at the grab and the seat.
  - Online clients receive the reload timer at the snapshot rate (20 Hz). The pose follows a presentation clock in `actor.gd` (`_reload_clock`): it advances every visual tick and stays within 0.1 s below the authoritative timer, and it snaps to a new reload or an upward correction. It never writes the timer, ammunition or any gameplay state. At 20 Hz the clip time now changes on every visual tick, where before it changed on 1 tick in 3.
  - The trigger finger curls with the recoil kick.
- **Still transform-driven:** recoil kick, sway, walk bob, the equip dip, and every other weapon's reload (tilt plus a 0.23 m magazine drop and reseat).
- **A second magazine (rifle only):** the reload swaps two separate magazine nodes (art-v7, then art-v8 for the source of the replacement and the handling). The other weapons' reloads are still procedural.
- **Sounds:** six events of the same presentation clock (unlatch, extract, pouch, land, enter, seat), each once per reload, on four separate voices (`reload_audio.gd`); cancelling the reload stops them. The procedural weapons have a release and a seat.
- **Not authored yet:** draw, inspect and bolt release.

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
4. **Handling is velocity-continuous.** Paths through the keys of a clip are splines whose velocity is continuous; a key stops the motion only where it is marked `hold` (a grasp, a let-go, the seat). Nothing in a clip may be linear between keys, jump in speed or snap to rest: `weapon_art_test.gd` bounds the peak speed (magazine 2.0 m/s, hand 3.0 m/s) and the acceleration on the clip's own 60 Hz grid (magazine 20 m/s², hand 50 m/s²), and a build with straight lines between keys fails it (negative control N24).
5. **First-person contract.**
   - The magazine node pivots at its seated top.
   - The muzzle marker sits at the crown, and the ejection marker at the port.
   - The hands are posed per weapon from the generator's `grip_hand` and `support_hand` anchors.

## Next

1. Draw and inspect clips on the same rig. The game already seeks clips by state (`_deploy_remaining` for draw), and a clip never writes the state it reads.
2. A visible pouch. The replacement now comes from the hip, below the frame, with the sleeve going down to it; nothing in the picture shows the pouch itself.
3. A bolt release on empty reloads. It needs the empty or tactical distinction the authoritative actor already has (`ammo == 0` when the reload starts); presentation only.
4. Reduced motion: the rifle's reload staging is no longer scaled (at 0.2 the hand fell out of the frame); the procedural weapons' dip still is. `Actor.REDUCED_RELOAD_VARIANTS` holds three alternatives (`current`: the roll of about 26 degrees, the default; `calm`; `still`) and `docs/reports/media/art-v8/reduced-motion/README.md` compares them. **Which one ships is undecided**: it needs a person who uses the setting.

## Reduced motion (art-v9)

`Actor.REDUCED_RELOAD_VARIANTS` holds per-variant presentation profiles with separate controls: weapon `roll`, `lift` (translation), `recoil`, and the support hand's `clip` (`reload` or `reload_calm`). Camera shake is not used by the reload. The default is `current` (unchanged); `calm` (roll 0.4, lift 1.3, recoil 0.6, calm clip) and `still` (roll 0, lift 1.8, recoil 0.4, calm clip) pass all 15 visibility rules, `still` with thin margins. Timing, sounds, ammunition and authoritative state are identical in all variants. These are candidates for a human review; there is no comfort evidence. See `docs/reports/media/art-v9/reduced-motion/README.md`.
