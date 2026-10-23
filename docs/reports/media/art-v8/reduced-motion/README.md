# Reduced motion and the rifle's reload: three variants, compared

**This is a comparison, not a decision.** The project has no policy yet for what reduced motion should do to the rifle's reload, and nobody who uses the setting has looked at these. `Actor.REDUCED_RELOAD_VARIANTS` holds the three variants and `reduced_variant` selects one; **the default stays `current`** (what shipped before this round), so the build does not silently choose. What I can say is what each one costs in what the player can see.

## What the setting already does, and what the variants change

With reduced motion on, sway, walk bob and the equip swing are attenuated (as before), the old magazine does not tumble as it falls, and the seat kick is a quarter of its size. **The variants change one thing:** how much of the rifle's whole-weapon staging for a reload the player gets: the roll (clockwise, about 26° in the default) and the lift/shift that bring the support hand and the magazine into the frame (`ARMS_RELOAD_ROTATION` and `ARMS_RELOAD_OFFSET` in `actor.gd`, scaled by the variant). The hand's own motion inside the clip (it reaches, pulls, goes to the hip, comes back) is the reload and is the same in all three; so are the timing (reload duration, event phases), the sounds and the ammunition. Presentation only.

| Variant | Roll | Lift and shift of the weapon | What it is |
| --- | ---: | ---: | --- |
| `current` (default) | 25.8° | 14 cm up, 5 cm left | what shipped: a visible roll that keeps the arm in the picture |
| `calm` | 10.3° | 18 cm up, 6.5 cm left | less than half the roll, a bigger lift to compensate |
| `still` | 0° | 22 cm up, 8 cm left | no roll at all; the weapon only rises |

## What each costs (measured on the final build, `reload_visibility_test.gd --reduced --variant=<name>`, 51 poses, 1280 × 720)

Pixels each part really draws (a flat-colour identification pass; lighting-independent). The hip is the span 0.41 to 0.60 of the reload in which the hand is below the frame by design.

| | `current` | `calm` | `still` |
| --- | ---: | ---: | ---: |
| Support hand, least pixels outside the hip and the rise from it | 13,797 | **7,954** (at 0.40) | 10,621 (at 0.40) |
| Left arm out of the picture (under 1,000 px) at the hip, poses of 10 | 1 | **9** | **8** |
| Hand on the rise from the hip, least pixels | 7,150 | **2,921** | 7,166 |
| A replacement magazine drawn with under 3,000 px of its arm in the frame | 0 poses | 4 poses (last at 0.62) | 3 poses (last at 0.60) |
| Crosshair box (80 px square) free of rifle, arms and magazines | all poses | all poses | all poses |
| Rules of the test that fail | none of 15 | 5 of 15 | 2 of 15 |

`logs/visibility-<variant>.csv` has every pose and `logs/visibility-<variant>-report.txt` every rule's result. The frames: `compare-stages.jpg` (the same six ticks of all three, made by `tools/art/compare_stages.py`), and the full sequences in `../reload-hip-retrieval/sheets/reduced-*.jpg` and `clips/reduced-*.mp4` (normal and quarter speed). The rules were written after the hip existed and their thresholds are mine; a failure is a measured fact about the frame, but where the line sits is a judgment.

## What the numbers do not say, and what the pictures show

- **`current` keeps the arm in the picture while the hand is at the hip, with one pose out; the other two do not.** With less roll the sleeve that goes down to the pouch leaves the frame (8 of 10 poses for `still`, 9 of 10 for `calm`), so for about 0.3 s the player sees no part of the left arm: the retrieval reads as the hand vanishing and a magazine appearing, which is the failure the hip staging was built to avoid.
- **`still` keeps the hand visible everywhere else (its least pixel count, 10,621, is above `calm`'s) but puts the rifle high and level across the middle of the screen** for the whole reload: in `compare-stages.jpg` its barrel crosses the upper half of the frame from edge to edge at tick 36 and later. **The crosshair box is clear in all three variants (the measure is 80 px square, so it says the exact centre is free and nothing about the sightline)**, and the rifle's pixel count is 61,500 to 73,216 in `current`, 72,647 at most in `still`: the whole rifle is not covering more of the frame, it is covering a different part of it.
- **`calm` is the worst on the measures**: the roll is too small to keep the arm in and the lift is too small to keep the hand in; on the rise from the hip the hand is mostly outside the frame (2,921 px).
- **What a person with vestibular sensitivity would find acceptable is unknown.** Roll is the usual trigger for the concern; `still` removes it, at a cost in readability. Whether the whole-weapon lift (a vertical translation, 14 to 22 cm over 0.14 of the reload) matters at all is also unknown.
- Nothing here was seen by a person who uses the setting, and the sequences are llvmpipe captures at a desktop size, not a phone.

## Options for whoever decides

1. Keep `current` and say so in the setting's text (it keeps the roll, 26°).
2. Ship `still` and accept that the arm is out of the picture during the retrieval and the rifle covers more of the middle (it would need a different staging of the hand's path for reduced motion: for instance a shorter, shallower dip to the hip, which is a change to the clip and so a rebuild).
3. Offer two settings (reduce camera/sway motion; reduce reload staging) so a player can keep readability and drop the roll or the reverse.

Reproduce: `scripts/capture_reload_matrix.sh` makes the sequences; `DISPLAY=:99 scripts/godot.sh --audio-driver Dummy --rendering-method gl_compatibility --script res://tests/reload_visibility_test.gd -- --reduced --variant=still --report --csv=<absolute path>`.
