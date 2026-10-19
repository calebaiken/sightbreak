# Blinded native visual comparison

Independent critic: inspect **only this `blind` directory** before recording your judgement. Do not inspect parent directories, source, Git history, process logs, or private mappings.

## Conditions

Two anonymous sources were rendered by the same official native Windows engine, OpenGL compatibility renderer, 1280×720 viewport, fixed 60 Hz simulation, same camera, same rifle, same lighting view, local reload authority, Dummy audio, no post-reload firing. Both projects were completely imported before testing. Actual image dimensions were verified.

- Sequence 01: sunlit, normal motion.
- Sequence 02: sunlit, reduced motion, calm variant.
- Sequence 03: shade, normal motion.

## Files and blinding

Start with the six PNGs in `contact-sheets/`: matched chronological pickup and return/ready frames. A/B source identity is consistent across both sheets **within one sequence**, but may change between sequences.

`pairs/sequenceNN/pairN.png` is a lossless side-by-side pair, A left / B right. `pairN_A.png` and `pairN_B.png` are full native 1280×720 lossless images without tags or metadata. Same-name JPEGs are convenient equivalents. Each still pair's A/B order is randomized independently; do not carry A/B identity from sheets to stills or across still pairs. `index.json` maps neutral pair numbers to ticks.

The `strip_A.jpg` / `strip_B.jpg` filmstrips use the same consistent identity as that sequence's contact sheets. Every source was simulated for all 153 ticks with 13 predetermined native images saved using the unchanged harness's --only option. Comparison ticks were fixed before any output was viewed. No source has been scored by the preparer.

## Critic task — before unblinding

Record A, B, tie, or inconclusive **per sequence** for the coherent contact sheets, with concrete visible reasons and tick references. Consider hand/magazine attachment and grip, pickup/entry continuity, forearm/wrist anatomy, silhouette and material readability under each light, return-to-ready stability, and any regressions. Still images cannot establish full real-time motion; explicitly state that limitation. If a sheet hides detail, inspect native still pairs and report those by their own pair IDs, not by the sheet's identity. Do not infer source identity or use presumed newer-is-better reasoning. Freeze your response before anyone opens the private mapping.

Separate automated test outcomes and performance information are intentionally absent from this packet.
