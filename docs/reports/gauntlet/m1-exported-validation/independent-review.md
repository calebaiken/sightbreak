# Independent M1 native validation review

Prefer candidate `6a0d8d5` over baseline `561d0cb` for the two scoped corrections. The measured Linux plant/defuse approach criteria and real-X11 lifetime criteria pass independent review. The complete four-size exported layout workflow **FAILS**, so M1 and platform/release gates remain open. The largest immediate deficiency is the 1280×720 touch-off resume OCR false negative; the largest approach-source limitation is false settling under sufficiently delayed queued pulses.

Reviewer: fresh-context `/root/native_validation_critic`, with a separate read-only source check of the approach helper. Neither reviewer implemented the candidate. Comparison is an unblinded technical comparison against the actual failed controller, not a visual A/B or a shipped-game comparison.

Source under review: baseline `561d0cbba651514bfac96c50437a849d65843545`; integrated candidate `6a0d8d5d85b4fb37943903886982f51b4ed230b0`. Candidate export receipt identifies a clean source and game tree `13079ab8a3de9b18252a652ed57157e0776cf394`. I independently matched its ELF bytes to receipt SHA-256 `ef4ab16a1b7f13fe96822a102c139fb5964275701f1e92fe8bdcfacfbf29d9a4`.

## Scope and bar

I read `AGENTS.md`, the mission/progress/acceptance records, `CLAUDE.md`, parallel ownership instructions, the original Gauntlet Loop and No AI Slop skills and evaluation, the SIGHTBREAK gauntlet, and both components' predeclared criteria and retained failures. The references are the pinned 60 Hz / 5.1 m/s / 28 m/s² movement implementation and actual failed native controller output; the X11 reference is the actual destroyed-window failure reproduced with real Xvfb windows. These references support functional correctness comparison only.

## Independent checks already completed

Raw commands/results are under `builds/mission-m1/critic-native/`. Source hashes are in `source-sha256.txt`; retained artifact checks are in `retained-integrity.json`.

| Check | Result |
| --- | --- |
| Candidate real-X11 lifetime suite, isolated `:244` | Nine child cases exit 0; destroyed discovery/focus/diagnostic/geometry/close handling, unrelated/pending/wrong-resource errors, handler restoration, largest-window focus and advertised-close positive control pass. |
| Baseline matched X11 controls, isolated `:245` | Discovery and focus children exit 1 with real `BadWindow`, request 20 and 42; positive control exits 0. This is an intentional failing oracle. |
| X11 resource bounds | Candidate child cases take 0.093–0.159 s, below 10 s; fifty positive focus/diagnostic iterations take 0.018689 s, below 5 s. Baseline matched workload takes 0.026095 s. No performance improvement is inferred from these single, concurrently run tiny-window workloads. Both owned Xvfb servers are reaped; all successful child cases close fixture windows/connections. |
| Approach dynamics | Nine tests pass; all 29 successful model cases remain below 15 wall seconds, below 0.45 m endpoint error and at or below 0.05 m/s. Maximum model wall time 11.937015 s; maximum endpoint error 0.408889 m. Duplicates, moving arrival, blocked path, observation failure, round change, non-finite evidence and late read controls pass. |
| Native observation regression | Four Linux cases pass; three Windows-only cases skip. |
| Build/manifest/log regression | 24 cases pass. |
| Retained integrity | Baseline native archive, all eight window evidence files, declared historical baseline hashes and candidate ELF hash match. |

The independent check commands were:

```sh
python3 scripts/test_native_window_lifetime.py --xvfb /workspace/tools/xvfb/usr/bin/Xvfb --display :244
python3 scripts/test_native_window_lifetime.py --module builds/mission-m1/critic-native/baseline_verify_integration_export.py --xvfb /workspace/tools/xvfb/usr/bin/Xvfb --display :245 --case discovery-race --case focus-race --case positive-and-repeat
python3 scripts/test_native_approach.py -v
python3 scripts/test_native_observation.py -v
python3 scripts/test_build_manifest.py -v
```

The baseline module is the exact `git show 561d0cb:scripts/verify_integration_export.py`, hash `199ee4d0970150eee60a00c1e5a136867b58d7ef506a3242d78e94fb2a08a198`.

## Source findings

The approach integration changes only `move_to`'s driving method. It retains the original 15 s budget, ordinary WASD events, the 0.45 m strict radius, 0.05 m/s stopped threshold, and actual newer consumed-neutral observations. It rejects a changed actor/round/phase, a dead player, non-finite motion and decreasing ticks; duplicate ticks cannot add settling evidence. The `finally` path attempts all four key releases even after observation/deadline errors. I found no position write, game API call, timer relaxation, fixture edit, save edit, rule change or authority bypass in this component.

The X11 wrapper synchronizes while its callback is alive and restores the previous process-wide handler in `finally`. Missing-resource recovery is restricted to the expected display, target resource, error code and native request. Pending and unrelated protocol errors remain Python failures containing protocol details. Discovery/focus/diagnostics recover only from a vanished target; geometry and close continue to fail so caller cleanup runs. Focus is checked from `XGetInputFocus`; largest named-window selection, geometry bounds and advertised-close checks remain intact. The module lock serializes its own handler scopes; arbitrary third-party concurrent Xlib handler replacement and server disconnects remain outside this correction.

Native validators establish process-group ownership at launch and run cleanup in `finally`. The new wrapper lets Python reach those existing cleanup paths instead of allowing default Xlib process termination. The independent tiny-window checks establish their own native resource cleanup; actual full workflow cleanup still needs its receipts.

## Additional source limits found independently

The delegated source critic ran 216 wider route probes and 448 near-target probes. I independently reproduced its finite queued-pulse failure using the supplied movement plant; raw state and controls are in `critic-native/extended-delay-limit.json`. Start `(0,0)`, request `(0,0.46)`, simulation/wall ratio 1, input delivery delay 1.5 simulation seconds, publication lag 0.2 seconds: at wall 6.721864 s the helper returns observed error 0.086667 m and speed 0 on ticks 377/390, while the current model state is error 0.561111 m and speed 1.4 m/s. A still-pending S pulse later leaves error 1.082222 m. With publication lag zero it returns stopped, but later queued W pulses move beyond the radius.

The cause is that fine pulses have no evidence of their nonneutral input consumption before settling; their release marker is the observation tick from before issuing the pulse. Two later neutral observations can therefore precede still-queued input. This is a model defect outside the published 0/0.1/0.2 simulation-second delay envelope. No added failure was found through 1.0 s delivery; no native fixture reproduction is claimed. Actual completed native route receipts can establish those observed runs only. They cannot establish correctness under arbitrary event backlog or variable simulation rates. The pending-input risk is the largest source deficiency; future coverage should include this retained counterexample and require proof that a pulse has been consumed before final settling can accept.

Two smaller limits remain. The prior inline controller checked the radius for both settled ticks, whereas candidate accumulates neutral/stopped ticks before checking only the final radius; no grounded model false acceptance was found from that difference alone. Also the deadline is checked after observations, before acceptance, but synchronous completion logging/final key release can finish later: a callback probe observes at 14.95 s and returns at 15.05 s with a 0.1 s logging callback. This limitation preexists the helper and does not permit a snapshot first observed at/after deadline. Arrival remains horizontal-only, as in the baseline; these two flat routes do not certify airborne arrival or arbitrary collision paths.

The helper's detailed review and probes are in `builds/mission-m1/critic-helper-source/`. They are technical source/model evidence, not exported gameplay acceptance.

## Baseline native output inspected

I inspected the baseline results, action trace, events, final status, original initial-conditions screenshot, and a raw video frame at 35 seconds from the retained X11 recording. The recording is 1280×720, H.264, 5 fps, 43.8 seconds as measured by `ffprobe`; its requested capture budget was 60 seconds. The screenshot shows the ordinary buy-phase player and carried device. The video frame shows an actual live player in the deployed smoke; it cannot measure exact coordinates or keyboard latency.

The authoritative/action evidence supplies the failure: movement starts at wall 53.326 s from z=2.0. The first full-speed release at z=7.86778 coasts to z=8.80000; subsequent corrections swing back across the goal. At wall 68.364 s the controller fails, still alive at 100 HP, z=7.69833 and velocity z=−5.1 m/s. Plant/defuse is not reached. The retained baseline cleanup errors are empty. This is a real steering failure, not a dead-player or missing-window explanation.

## Candidate native plant r1 inspected

The completed `plant-candidate-r1` receipt passes on the clean candidate/ELF above in 125.128560 wall seconds under the original 180 s whole-flow limit. I recomputed an upper bound of 9.320547 s for movement from the preceding smoke-fuse observation to movement completion. Final requested `(-15,8)` error is 0.244443 m, horizontal speed 0, and both native movement keys and mouse are released. The ordinary E hold spans exactly 180 authoritative ticks / 3 simulation seconds. The native player plants, gains the objective contribution/funds, the device is naturally defused, the next buy round appears, and the restarted menu/settings/profile comparison is equal. All three owned process groups are absent when independently checked; all exit codes are zero and cleanup errors are empty. This is an objective slice and restart check, not a complete-match earned-progression qualification.

I inspected the original approach and completed-objective screenshots, the raw video at 50 seconds, both native logs and full action/result data. The images show the live player in ordinary smoke, the HOLD E prompt, then the armed-device timer and 1100 funds; they do not provide coordinate/tick proof. Logs show pinned Godot 4.7.2/Mesa llvmpipe and the allowed V-Sync warning, with no other error or leak output. The video is 60 s / 5 fps / 1280×720; it is evidence of rendered output, not physical input latency.

The retained neutral-snapshot proof is incomplete for r1. The controller reports settled ticks 1234/1247 after final release tick 1208, but the external retention file begins at tick 1650. I verified all 61 raw snapshot hashes; neither settled tick exists in it. The 54 later snapshots in the same round stay neutral/stopped at the same 0.244443 m error, so they support later stability but cannot retrospectively prove the two completion ticks. Root was informed and a rerun with retention active before launch is required for this criterion. Recomputed raw result: `critic-native/plant-r1-recomputed.json`. I have not promoted the missing exact-tick evidence to verified.

The coordinator's completed broad `validate.sh` log reports success at `.local/validation/run-as4Oaj`; I inspected its completion and relevant regression output. That run is coordinator-executed, distinct from my independently rerun focused checks. It does not close the missing native evidence or documented bot objective/physical-platform gates.

## Candidate native plant r2 exact-tick proof

The repeated same-source plant run resolves r1's retention gap. `critic-native/plant-r2-independent-checks.json` recomputes 12 checks and all pass. I verified all 188 retained raw snapshot hashes, source and ELF identity, original budgets, exact objective duration, restart equality and clean native ownership. Movement takes at most 9.107351 wall seconds from the preceding observation. Both exact settled ticks 1234/1247 are later than release tick 1208, in the same live round with a living 100 HP actor, `time_scale=1`, consumed movement `[0,0]`, zero horizontal speed and 0.244443 m error. Both satisfy the baseline's stronger two-in-radius interpretation too. Eighty-five later same-round snapshots remain neutral/stopped/inside for 18.2 simulation seconds; no late queued pulse is observed on this run.

The objective hold is 180 ticks / 3 simulation seconds; whole flow is 124.299489 s. All three processes exit zero, cleanup errors are empty, and independently checked owned process groups are absent. Original r2 hold/next-round screenshots and native logs were inspected. The hold bar, ordinary next buy round and normal player HUD are present. This verifies the measured plant route and objective slice on Linux software rendering, with the source queue-delay limitation stated above.

## Candidate native defuse r1 exact-tick proof

`critic-native/defuse-r1-independent-checks.json` recomputes the same 12 checks and all pass. All 169 raw snapshot hashes match. Both exact settled ticks 1403/1416 are later than release tick 1377, in the same live round with a living 100 HP actor, normal time scale, consumed movement `[0,0]`, zero horizontal speed and 0.035549 m error from requested `(-17,9)`. Movement takes at most 12.543367 wall seconds, within the original 15 s. Fifty-four later same-round snapshots stay neutral/stopped/inside for 11.483333 simulation seconds.

The player actually moves 3.035549 m, reaches an independent bot's planted device, resets an interrupted interaction, and defuses with an uninterrupted 300-tick / 5-simulation-second E hold. The authoritative trace independently places the final input start at tick 1513 and completion at 1813. Contribution rises 0→1; credits reflect the objective and ordinary round award. The next buy round and equal restart observation pass. Whole flow is 103.392275 s; all native process exit codes are zero, cleanup errors are empty and independently checked owned groups are absent. I inspected both logs and original approach/completion screenshots: the ordinary HOLD E NEAR THE DEVICE prompt becomes DEVICE / DEFUSED and the scored post round. This verifies the measured defuse route and objective slice, with the documented broader queue-delay limit.

## Completed exported layouts and outstanding failure

I independently inspected the completed `layout-candidate-r1` report, per-case receipts, actual capture and OCR-original hashes, native process exits/groups, source/ELF identity, relevant OCR TSVs, and original images. All 21 declared capture hashes/dimensions and every retained OCR-original hash match. The clean source remains `6a0d8d5`, with `exact_source_unchanged=true`. All owned process groups are absent after cleanup. The original `--touch-toggle` option is present; the validator intentionally applies it only at 1280×720.

| Native size | Actual result | Wall seconds | Cleanup |
| --- | --- | ---: | --- |
| 960×540 | Five stages pass | 48.120924 | Clean; menu/live exit 0 |
| 1280×720 | FAIL after touch HUD opt-in, while confirming desktop HUD after opt-out | 78.013105 | Live session requires SIGTERM; failure remains failed |
| 1920×1080 | Five stages pass | 101.241735 | Clean; menu/live exit 0 |
| 1280×800 | Five stages pass | 61.801757 | Clean; menu/live exit 0 |

The configured whole timeout was 600 s, whereas the original default is 520 s. Actual total was 289.346288 s, below both; each unchanged 120 s case budget was met. No increased timeout is needed to explain the observed three successful cases. The total workflow remains `capture_generation_passed=false`.

The 1280×720 exception is `Rendered UI OCR confirmation exceeded its wall budget`, not Xlib `BadWindow`. Its final successful raw capture, `06-touch-hud-opt-in.png`, visibly shows the native touch HUD. The later `keyboard-hud-check-35-ocr-original.png` visibly shows the resumed normal HUD and footer labels with no touch overlay. The saved profile and controller action show touch off persisted; OCR TSVs 32–34 recognize HEALTH but miss all of TAB/ROSTER/ESC, garbling the small footer. `rendered_hud(False)` still requires those exact recognized words, so it correctly remains a failed automated qualification rather than silently substituting read-only state for rendered proof. The native client is then terminated during failure cleanup, reported as `live-layout: forced cleanup or descendant after root exit`; Xvfb and all child groups are reaped. Native logs contain only the allowed V-Sync warning, with no engine error/leak.

I viewed raw 960×540 menu/roster/settings; 1280×720 touch HUD and final failing keyboard HUD; 1920×1080 live HUD/roster; and 1280×800 menu/settings. These contain the expected actual screens, not blank or wrong-window captures. The 1280×800 letterboxing is visible in the preserved native image. This functional inspection does not grade appearance, accessibility, every UI path or game quality. Raw recomputation: `critic-native/layout-r1-independent-checks.json`.

The scoped lifetime correction passes: both fatal baseline races are independently reproduced; the candidate survives the same real operations, propagates unrelated errors, restores the previous handler and reaches normal Python cleanup. The actual four-size run continues through its failed 1280 case and produces the two later cases, so the original fatal exit is corrected. Complete layout-workflow acceptance is withheld until the OCR recognition defect is corrected and the original rendered touch-off condition passes on a new source-bound run. The error must not be waived by removing TAB/ROSTER/ESC requirements, accepting only state flags, or labeling the visible restored screenshot as a passed automatic workflow.

## Final limits and blockers

- **Current actual blocker:** 1280×720 rendered touch-off HUD confirmation still fails. Exact evidence is the per-case result, keyboard HUD originals/TSVs and cleanup receipt above. The missing `07-keyboard-mouse-restored.png` stage and normal live close must be obtained on a successful source-bound rerun.
- **Approach hardening finding:** unacknowledged pending pulses can defeat actual arrival at 1.5 simulation-second delivery delay. The retained finite counterexample blocks any arbitrary-latency or universal-controller claim. The bounded plant/defuse runs, exact two-tick proofs and observed postarrival stability pass for the conditions actually run; they do not fix or disprove that counterexample.
- **Broader product gates:** these objective slices and restart equality do not establish a complete offline match, earned full-match progression after restart, ordinary bot objective reliability, Windows/macOS execution, physical-device responsiveness/performance, human playtesting or release readiness. Those require their own actual evidence. No CS2 parity, visual polish rating, security penetration assessment or full G1/G11 gate is accepted here.

The product/validator source was not edited by this critic. Independent source hashes, raw tests, exact-tick recomputation, initial-rule/protocol/default-prediction checks, the original brief and integrity manifest are retained under `builds/mission-m1/critic-native/`; delegated source probes are under `critic-helper-source/`. No numerical quality score is self-assigned.
