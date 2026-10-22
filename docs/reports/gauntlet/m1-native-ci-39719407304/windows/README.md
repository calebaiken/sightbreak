# Windows native outcome review

Run 39719407304, job 119629141365, frozen source `0ca125dfba637868e6e8e9772ff9c40400413e32`. The Windows job is **FAILED**. Ten native source suites, OS input/reload, player plant/defuse and a complete earned-profile match pass independent raw-receipt checks. The ordinary offline journey fails after settings resume because the player has died. Settings restart and native focus recovery were not reached. No complete G1 or Windows release acceptance follows.

## Provenance and transfer

Official bounded receipts artifact 12400854422 is 2,380,749 bytes, SHA256 `e6829d015b6763a110b87d8f6623f5a0a21ab466b668b116bdcd6794d433158e`. Its inner `qa-receipts.zip` is SHA256 `4e64573bbd12a53b7ef8441d1cd09bde9b5400242f915790b794b01bea88a381`. Official full QA artifact 12401276651 is 22,375,714 bytes, SHA256 `884b6397eb57dbaf75ea3ee481abbc546f581094dd024f2cd0b0993836f2c541`. Both were transferred through the supported connector and Sediment download tool, matched to GitHub's official digest, and safely extracted. All 170 selected raw receipts match the index and the full QA copy byte-for-byte. The latter retains 77 actual PNGs.

The raw scenario receipts identify clean source 0ca125d, game tree `782c26464631f86ad63ddab9de36a969d4e44534`, content SHA256 `f8a849b90df3ff214037cace7bc32c0c7b5e184911558b424b0a6c0f798db781`, validation SHA256 `982057ffe78de32a2795e61c48137d5b094461ec1ea74c62d8add55b22fb13a5`, and pinned Godot `4.7.2.stable.official.ed1daf0bf`. The executable hash in receipts is `a60c182555beca798f9ee113dc1a92e40f3696395c40c012aa0b14f7729eff4d`; the compiled binary was not independently transferred. Later documentation HEADs do not re-attest this binary.

`windows-job.log` preserves the connector's decoded UTF-8 content, including 17,623 CRLF endings. Its companion raw JSON response is retained. These are decoded connector log bytes, not an original GitHub log ZIP. No reconstruction from stdout substitutes for the downloaded raw QA receipts.

## Actual ordinary-journey failure

The prior 6a Windows failure was an ammunition OCR false negative at `07d-explicit-resume`. The new run fails at that same capture boundary for a different, truthful reason: `HUD analysis requires the actual living, focused offline player`. The guard is doing its job. The overall flow ends after 100.437 seconds.

- The preceding primary-HUD resume sample is tick 3246, health 70.2791296386719, alive, in live round 2, with SMG 30/120. Its driver action occurs at 90.562 seconds.
- The actual `07c-settings-changed.png` visibly shows FIELD SETTINGS with 040 HEALTH beneath the overlay. The persisted sensitivity is 0.0051.
- Driver Escape down/up occurs at 98.515/98.890 seconds. The native trace records death at tick 3272, elapsed 54.5333333333315, `wall_msec=98419`, drawn frame 748, with health 0 and deaths 2. Native and driver clocks have different origins.
- The actual `07d-explicit-resume.png` visibly shows ELIMINATED / SPECTATING and SMG 30/120. Capture begins at driver 99.921 seconds and ends at 100.203; the guard fails at 100.250. The last observation remains dead at tick 3350, focused and unpaused.

`windows-failure-reconstruction.json` retains decisive actions verbatim, exact raw state samples, image paths/hashes and the separate-clock limit. No exact screenshot-to-simulation-tick identity is asserted. The independent reconstruction proposes no implementation. The Windows restart and native focus-recovery block remain unverified by this run.

## Passing slices

All ten maintained native source suites exit 0 with clean native logs. Engine-produced before/after paths identify ten distinct owned per-suite directories; every before-state is fresh. Actual produced-file hashes match the retained raw files; original/copy resource preservation and owned namespace/project cleanup pass. Authority order reports 178 checks, input 36, menu focus 30 and diagnostics 60, all with zero failures. A comparison to the frozen review worktree matches 296/297 original resource hashes directly; the sole difference, `tests/fixtures/backend_world.json`, matches exactly after the normal Windows CRLF checkout conversion. This explains a platform checkout difference, not resource mutation during the tests.

The ordinary exported keyboard/pointer fixture passes in 83.578 seconds. Its source-engine loopback authority observes four shots, magazine depletion to 26, a real reload input, and final 30/86 ammunition with correct conservation, positive acknowledgments and clean native exits. The four-second delayed release-first control passes in 55.031 seconds. The original delayed legacy schedule also passes in this run, with actual diagnostic exit 0 and 60.032 seconds. The wrapper step's success alone was not used to infer that diagnostic outcome. These fixtures do not measure authoritative movement displacement or physical input-to-photon latency.

Player objective fixtures preserve the declared initial spawns/side/seeds and unchanged stock rules. Plant takes exactly 180 consumed-input ticks / 3 simulation seconds, and defuse 300 ticks / 5 seconds, with one uninterrupted consumed-E edge and one objective contribution each. Interrupted-hold resets, natural round resolution, restart and clean exits pass. Plant/defuse wall times are 82.891/67.422 seconds. Movement endpoint errors are 0.232221/0.377232 metres, stopped speeds satisfy the existing bound, and conservative wall upper bounds are 5.219/3.109 seconds under the original 15-second gate. Two distinct settled tick identifiers are retained; exact raw snapshots of both settled input samples are not, so that detail remains receipt-supported rather than independently reconstructed from per-tick snapshots.

The complete stock match records 194 raw events, ten natural rounds, halftime swap, ten unique actors split five per side, one local human and one completion with zero dropped events. Final score is 3:7 and correctly means local victory after the side swap. Formula recomputation gives 120 XP and 325 offline training credits; the completed event, actual saved JSON, restarted process initial profile and result receipt agree exactly. It takes 443.416667 simulation seconds / 503.594 wall seconds. The scripted human has zero kills, assists and objectives and ten deaths. One raw planted-state event appears in round 10, followed by a defuse resolution. This is one observed bot objective sequence, not a reliability sample or a closure of F1.

I viewed the actual completed-match/scoreboard, plant completion, defuse completion, native reload-completed and decisive settings/resume failure images. The completed UI visibly agrees with victory 03:07, ten rounds, +120 XP/+325 credits. This is functional output review, not a presentation score or human playtest.

The largest remaining Windows deficiency is the failed full ordinary journey. A living, focused player must survive the observation/input sequence through settings restart and native focus recovery under the existing budgets. An implementation fix and a new actual Windows run need separate independent review.
