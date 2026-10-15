# art-v9 final record: matched captures, validation, review

Branch `claude/cs2-fidelity-art-production`, PR #2. Verified starting head `57f6464`. **Everything here is my own measurement on Mesa llvmpipe (GL Compatibility), plus one read-only review by an agent of my own model family (`independent-review.md`, kept verbatim). No human has looked at these frames or clips, nobody listened to the audio, and nothing was seen on a phone.**

## Matched captures (same camera, size, lighting and 60 Hz timing; the reload's timing is identical in both)

- `before-after-sunlit.jpg`, `before-after-shade.jpg`, `before-after-backlight.jpg`: `57f6464` (top) against the final head (bottom), ticks 0, 14, 36, 58, 82, 98, 118, 136 (idle, reach, extraction, hip, carry, insertion, return, first shot).
- `hands-closeups-before-after-2560.jpg`: crops of 2560 × 1440 captures at ticks 0, 14, 98, 118.
- The per-tick PNG sequences (183 frames per view) were not committed (size); the sheets, the CSV of what the actor did on each tick (`frames.csv` in the capture directories) and `../reduced-motion/video/*.mp4` (4 variants at 60 Hz and quarter speed) are. Aspect ratios other than 16:9 were not re-captured this round; the earlier 20:9 and 4:3 captures (art-v8) are simulated and are not the shipped aspect policy.

## Validation at the final head

`scripts/validate.sh` exits 0 (`validate-final.log` is the run before the last test addition; `validate-final-2.log` the final one): 175 weapon-art, 92 sequence, 29 audio, 9 and 6 real-time audio captures, 24 contact, 15 visibility (default view), the rifle finish-stability probe in sun, shade and with a skin, the 12-check light separation test, and the networking suite. `negative-controls-README.md` has the control run: 35 controls, all caught after one harness defect of mine was fixed.

## Performance (`perf/perf-probe.txt`, against `art-v8` `perf-probe.txt`)

Arms 9,180 → 9,268 triangles (+88; budget 10,000), draw calls unchanged (31 ready, 34 mid-reload and flash), texture memory unchanged (5,592,824 bytes), `Actor.tick_visual` median 14 → 12 µs in a reload (p95 43 → 35). The llvmpipe frame times in the file (about 150–165 ms against 170–187 ms) are not comparable between the two runs (different host load) and say nothing about a phone; I make no performance claim beyond "no added draw calls or textures, 88 more triangles". One shader uniform pair was added (`viewmodel_roughness`, `viewmodel_specular`); the fragment cost of one `max` and a conditional is not measured on a GPU.

## What the review found, and what I did about it

See `independent-review.md` for the full text. Findings I confirm from my own numbers (receiver median in sun at the ready 54.5 → 69.7: the roughness floor and the metal fill floor trade the sheen for stability; the receiver and handguard are level in value; shade and backlight separation did not improve; the hip pop is 20 % of the magazine against under 5 % before; the grip hand is still pale in sun) are listed as open in `docs/art/VISUAL_QA.md`. One finding led to a change: the stability test measured only luma, so it could not see a hue shift; it now also asserts the receiver's (r − b) / luma stays within 0.06 of its first value in sun (before the fix the shift was 0.094, after 0.034; the reverted-floor defect gives 0.077 and fails it). It is not asserted in shade, where the same number moves 0.08–0.09 before and after because the receiver turns bluer as it faces the sky. It does not measure whether the steady olive is "beige" to a viewer; that remains a human call.

## Not claimed

That the hands are anatomically convincing, that the glove-to-sleeve gap in shade or the dark improved, that the reduced-motion variants are more comfortable, that any sound sounds right, or that any of this holds on a phone's GPU.
