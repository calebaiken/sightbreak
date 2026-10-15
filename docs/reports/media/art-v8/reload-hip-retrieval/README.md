# The reload, round 3: a source for the replacement, handling, sounds, grip, flash

Branch `claude/cs2-fidelity-art-production`, from `fceefa1` (art-v7). **Who has judged this:** my own measurements, and one read-only review by an agent that shares my model family (below). **Nobody has looked at it on a phone, nobody has listened to the sounds, and no human has judged any of it.** Every timing and cost is from Mesa llvmpipe under Xvfb with the Dummy audio driver. Tests prove what they measure; none of them proves it looks or sounds right.

## What changed

1. **Where the replacement comes from.** After the old magazine is let go (0.37) the empty hand goes down and to the left to a magazine pouch at the hip, **below the bottom of the frame**; the sleeve stays in the picture, swung out and up (elbow bias) so it runs down the left edge. The hand takes the replacement there (0.50), the replacement is **first drawn at that instant, in the hand, with 3 % of it inside the frame** (a test), and the hand brings it up, across and under the well. The hand is out of the picture from 0.41 to 0.60 of the reload (19 %, 0.43 s of 2.25 s); the pouch itself is not drawn. This is the brief's "carefully staged off-screen retrieval", not a visible pouch.
2. **Handling.** Every path through the clip's keys is a Catmull-Rom spline with continuous velocity and `hold` keys only at a grasp, a let-go and the seat (the v7 motion eased between keys and read as linear). The replacement rocks about its front lip (8.8° as it enters, square at the stop), the seat gives the rifle a short kick (a quarter of it with reduced motion), the swing-out is a smooth arc, and the hand's return no longer sinks a fingertip into the handguard (the fingers flare more as the hand lets go). Peak speeds: magazine 1.82 m/s, hand 2.80 m/s; peak accelerations on the clip's own 60 Hz grid: magazine 17.0 m/s², hand 41.5 m/s² (the hand's peak is its return, at 0.93) (bounds in `weapon_art_test.gd`: 2.0 and 3.0 m/s, 20 and 50 m/s²).
3. **Hands.** Extensor tendons on the back of each hand; the support-hand grasp re-tuned (roll 24.5°) so the pinky and middle fingertip stay in view; the contact review (Blender, every frame): left arm 0.0 mm into the rifle and 0.9 mm into the magazine, right arm 1.47 mm into the trigger (the trigger finger rests on it by design). **The hands are not anatomically convincing yet**: see "Not done".
4. **Sounds.** Six events of the presentation clock (unlatch, extract, pouch, land, enter, seat), each once per reload, on four separate voices of their own (`reload_audio.gd`), twelve synthesized sounds (two variants of each, alternating by reload). A cancelled reload stops what is playing and plays nothing more; weapon change, round reset and death do the same. The shot has its own player.
5. **Grip and materials.** The pistol grip is its own mesh (one more draw), with a palm swell, a flared base, three finger grooves and a recessed stippled panel on each side, in a graphite material that is darker again in the game (0.3 of its baked albedo, no fill floor). The stipple is raised dots, not the relief that read as rock. The arms got a readability floor and a rim light.
6. **Muzzle flash.** The thin straight spikes that drew the flash as a star are gone; short blast petals to each side and over the top, the lobes kept, a 40 ms light, and a puff of smoke that thins out over 0.45 s.
7. **Reduced motion.** Three variants of the rifle's roll and lift, compared in `../reduced-motion/README.md`. **The default is unchanged and the choice is open.**

## What was measured, and what each measurement does not show

| Measurement | Result | Does **not** show |
| --- | --- | --- |
| `reload_sequence_test.gd` (headless, 92 checks) | identity, paths on axis, rock-in, first draw off screen, grip, event timing under four timers, reduced motion, authority, edge paths | whether any of it looks like a reload |
| `weapon_art_test.gd` (167) | contract, budgets, speeds and accelerations on the 60 Hz grid, at 69 % and 75 % the magazine's *top face* is under the well and entering | that the motion feels weighted |
| `reload_visibility_test.gd` (native, 4 runs: sunlit, backlight, shade, reduced) | pixels each part draws, from a flat-colour pass: outside the hip and the rise the hand shows at least 13,797 px, the thumb at least 247 px, three fingertips at least 100 px (the second-best finger is 102 px at its lowest) whenever a magazine is held; at the hip the sleeve at least 9,903 px; on the rise the hand at least 7,673 px with the magazine in full view | contrast, legibility, anatomy; **lighting-independent by construction** (all four views print the same counts). The rules for the hip and the rise were written after the hip existed, from what the clip does; their thresholds are not independent of it |
| `scripts/test_reload_contact.py` (24) | per-digit gaps to the magazine, the opposition of the thumb, penetration of both arms | whether a grasp that touches everywhere looks like a hand |
| `reload_audio_test.gd` (29) | each event once and in order under four timers, two reloads in a row, corrections, four sounds on one tick on four voices, a fifth takes one, shot and seat together, cancel by weapon change, reload cut short, round reset, SMG | what anything sounds like |
| `reload_audio_capture.gd` (real time, `AudioEffectCapture` on a bus per voice, 9 + 6 + 10 checks) | the six sounds are in the mix on their own voices at their times to within 90 ms of the run's offset; nothing sounds before the first event; after a cancel (90 ms into the landing) every reload voice is silent 80 ms later; a shot and the seat clunk are both in the mix | **the Dummy driver mixes in 46 ms chunks, so single sounds land 13 to 71 ms after `play()`; this is not the latency of a phone**, and the capture cannot tell a good sound from a bad one. `audio/` has the mix WAVs and spectrograms |
| `viewmodel_light_probe.gd` (native) | median luma by part in four lightings (table below) | how it looks |
| `reload_perf_probe.gd` | triangles, draw calls, `tick_visual` microseconds, texture bytes | any device cost |
| Negative controls (`scripts/reload_negative_controls.py`) | see "Controls" | defects nobody thought to inject |

### Luma by part, grab pose (0 to 255, sRGB, median of the part's visible pixels; `logs/light-probe-after.txt` has every pose)

| | sun | backlight | shade | dark interior (simulated) |
| --- | ---: | ---: | ---: | ---: |
| magazine | 136 | 57 | 53 | 32 |
| gloves | 89 | 38 | 33 | 20 |
| sleeves | 112 | 42 | 40 | 23 |
| pistol grip | 51 | 27 | 28 | 15 |
| rifle body | 52 | 30 | 32 | 22 |

Against the round before (`logs/light-probe-before-this-round.txt`): the gloves in the dark interior went from 15.5 to 20 (the target was 20), and the grip, which had the same median as the gloves in sun (91 against 89), is now at 0.57 of them in sun, 0.84 in shade and 0.76 in the dark. **The glove-to-sleeve gap did not improve** (0.79 in sun, 0.83 in shade, 0.88 in the dark: the arms' fill floor lifts both). "Dark interior" is the shade view with the sun at 8 % and the ambient light at 30 %, not an interior: the sky is still bright in the frame.

### Cost (`logs/perf-probe.txt`, baseline `logs/perf-probe-baseline-fceefa1.txt`)

Triangles: grip 1,976, rifle nodes in the first-person scene 26,182 + arms 9,180 + flash 209 + smoke 240. Draw calls 31 ready, 34 mid-reload, 34 on a flash frame (30, 33, 32 at `fceefa1`). `tick_visual` through a reload: median 14 µs, p95 42 µs, max 93 µs (13, 23, 66 before: the audio scheduling). Frame times on llvmpipe sit at 170 to 193 ms in every state and **the differences between states are inside the run-to-run spread** (the baseline's ready state measured 171 ms, this build's 185 ms in one run and 190 ms in another: I do not claim a cost for the grip's extra draw). Texture bytes unchanged at 5.59 MB (S3TC; ETC2 the same).

## Defects found while doing this (and not hidden)

- A 11.6 mm "penetration" of a hand that had not moved: a BVH rebuilt every frame picked a different nearest face once in 61 frames (fixed: one BVH in the magazine's own space). Then a 17 mm "penetration" a fingertip beside the handguard: the nearest-face sign is wrong at a convex edge (fixed: the sign is confirmed by ray parity).
- After the rifle's rebuild three visibility rules failed: the pinky dipped to 90 px at one pose, the middle fingertip to 77 px at another, and the hand on the rise was 5,575 px. I retuned the grasp (roll 25 to 24.5°) and the carry and elbow paths until they passed on a 0.01 grid. **That is tuning to the measure.** The margins are thin (pinky 115 px, middle 102 px against a floor of 100).
- A fill floor I first tried for the dark interior made the arms a flat grey with no glove, sleeve or form (seen in a frame, not in the numbers: the numbers looked fine). Retuned until the frame looked right.
- The grip's baked graphite had the same median luma as the gloves; only the probe found it.
- The visibility test did not quit when a `--csv` path was relative (a failed write left it running for 30 minutes); fixed.
- **Five of the 30 negative controls were missed on the first run.** Three named a test that cannot see that defect (wrong lists), one was redundant (two independent cancel paths), and one was a real gap: the cancel capture cancelled when every sound was almost over, so a build that never stopped its voices passed. Fixed (the cancel now comes 90 ms into the landing, whose second bounce is 190 ms after it starts; the sound's second bounce was moved later for it).

## Controls

(first full run: `logs/negative-controls.log`, 25 of 30 caught; the final run is described below)

FINAL_CONTROLS

## Not done, and what I would do next, in order

1. **The hands are still not convincing.** The support hand reads as a glove around a stick, the grip hand as three blobs on the grip; there are tendons now and nothing else new. At gameplay size they read; at close size (see `frames/`) the fingers are sausages without joint definition. Real work here is the finger geometry and a stronger glove detail pass in `relay_ar_arms.py`, and it changes every number above, so it needs the whole loop again.
2. A visible pouch, or at least a visible sleeve for the whole hip trip in the reduced-motion variants.
3. The glove-to-sleeve value gap in shade and in the dark.
4. A listening review of the sounds, a human review of the sequences, and any look at all on a phone. The sounds are my synthesis, not a design anyone has judged.
5. A decision on reduced motion (`../reduced-motion/README.md`).
6. Competitive sightlines: I did not measure how much of the middle of the screen the rifle covers during a reload; the reload still lifts and rolls the whole weapon as before (the crosshair area is not clear during the lift).

## Evidence in this folder

- `sheets/<name>.jpg`: labelled contact sheets of real-time 60 Hz sequences (the reload and the first shots after it): `sunlit`, `backlight`, `shade`, `dark-interior`, `sunlit-wide-20x9` (1600 × 720), `sunlit-tall-4x3` (960 × 720), `reduced-current|calm|still`. **The viewport sizes are real (each `logs/viewport-*.txt` records the size the PNGs have) but the wide and tall ones are simulations of other aspect ratios, not a statement that the project ships them.** The project keeps 16:9.
- `clips/<name>.mp4` and `<name>-quarter-speed.mp4`; `frames/*.jpg` the stage ticks at full size; `logs/frames-*.csv` per tick (progress, which magazine is held, cues).
- `logs/`: `clip_contact.csv` (+ the hash of the GLB it was made for), `visibility-*.csv`, `light-probe-*.txt`, `perf-probe*.txt`, `negative-controls.log`.
- `audio/`: `mix_*.wav` (the sum of the five buses), `spectrogram_*.png`, per-voice onsets `voices_*.csv`, `report_*.txt`.
- Reproduce: `scripts/capture_reload_matrix.sh`, `scripts/validate.sh`, `scripts/reload_negative_controls.py`; the commands are in `docs/art/ASSET_PIPELINE.md`.
