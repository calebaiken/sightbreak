# Animation standards

**Status:** the first-person motion is still transform-driven in `actor.gd` and is unchanged by the authored rifle:
- recoil kick;
- sway;
- walk bob;
- equip dip;
- reload tilt with the magazine dropping 0.24 m and reseating.

No skeletal or authored clip animation exists yet.

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

An articulated hand rig with finger chains matching `relay_ar_hands.py`'s joints, used for reload (magazine swap with the support hand) and inspect. It is played by a small clip player that reads `reload_remaining` and `_deploy_remaining` and never writes them.
