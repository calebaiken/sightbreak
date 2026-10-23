# Independent authority-order review

**Verdict: accept the bounded correction. Candidate d593d7b is better than frozen 6a0d8d5.** Product actor/match source is unchanged from 470fad5; d593d7b strengthens the oracle and corrects the performance fixture. No blocking gameplay, authority, or privacy regression was found within this review. This does not close general competitive fairness, network qualification, or any physical-device gate.

The candidate removes the reproduced first-processed winner in 32/32 mirrored simultaneous lethal duels and uses a common post-movement/crouch pose for every shot. It preserves one death/reward per victim and living front-actor shielding throughout the batch. Baseline reversed winners with Dictionary insertion order and hit targets at an earlier pose in one order.

This was a source correctness comparison with known identities, not a blinded comparison. I made no implementation edits and did not change the builder worktree. Full source reasoning and the changed signal/RPC path are in [SOURCE_REVIEW.md](SOURCE_REVIEW.md).

## Reproduction and regressions

Independent detached candidate `d593d7b14b5838d2904a9a35547611e5a08cdf81` and baseline `6a0d8d5d85b4fb37943903886982f51b4ed230b0` used pinned Godot 4.7.2, identical final oracle SHA256 `87e79a6baa19475fbb0c7cf2567d39a26c7b93efc585ff052cd0f2d37f002277`, and fresh per-command state directories. Exact commands, working directories, exits, durations, and log hashes are retained in `*.receipt.json`; [run_review.py](run_review.py) reproduces the runs.

- Final candidate: **178 checks, zero failures, exit 0**. Final baseline: **178 checks, 152 intentional failures, exit 1**. Baseline failures remain failed oracle evidence.
- The original 162-check runs independently reproduced the same result. Review found that the original pair comparison omitted positions. One initial pair had a 78 µm floor-settling residue; all 16 pairs were within 0.1 mm. The revised harness explicitly checks that tolerance and retains the original raw records.
- Eleven maintained groups independently passed on both product sources: actor, hit feedback, weapon integrity, hit history, match, state privacy, movement prediction, input lifecycle, input stream, bot AI regression, and real bot lifecycle.
- Independent [28-check probe](critic_authority_negative.gd) passed both builds: single movement advance, ammunition/cooldown/reload/deploy, held semiauto, four outage edge latches, utility release/hold, capped actual damage, one death/kill/reward, credit ceiling, and corpse inactivity. Its rejected first fixture iteration and diagnosis remain in [FIXTURE_FAILURES.md](FIXTURE_FAILURES.md).
- Real bot lifecycle passed on both; differing scores and one candidate plant are functional observations, not balance evidence.
- Builder's full maintained `validate.sh` completion log was inspected and copied as `builder-full-validate-470fad5.txt`; it has no error signature. That full run is builder evidence, not my full-suite rerun. Skips include rendering checks without DISPLAY, absent backend Python drift check, and native Windows-only checks. Gameplay source matches the final reviewed candidate; the revised 178-check oracle was independently rerun.

Deferred shooter feedback still routes only to the active peer owning that shooter. Impact/shot visibility filters, public elimination feed, reliable hit/elimination paths, protocol 6, prediction opt-in, and the absence of live rewind remain intact. Already-dead targets are skipped before another damage/death/reward. There are no new RPCs, serialized hit queues, or client hit claims. This is a regression check of the changed phase, not a claim of ten-client impairment qualification.

## Performance evidence and corrections

The initial claimed sustained-fire benchmark was invalid: my instrumented original fixture recorded 900 shots in firing sample 0, then **zero shots in samples 1–6**, with ammunition and reserve exhausted. Those logs and old source remain here. Old depleted-trigger medians cannot establish sustained firing overhead; the initial reported >25% increase remains historical evidence, without a proven cause.

The revised fixture supplies benchmark-only ammunition, compensates recoil in identical input generation outside the timer, and counts real shot/damage events. Every active 2,000-tick sample independently recorded 3,170–3,180 shots and exactly as many damage events on both builds. Both benchmark runs passed 14 assertions. No production weapon data was changed.

| Independent revised pair | Baseline median / p95 of sample means | Candidate median / p95 of sample means |
| --- | --- | --- |
| Ten actors idle | 249.42 / 254.95 µs | 247.22 / 254.94 µs |
| Ten actors active | 480.22 / 494.52 µs | 475.68 / 484.92 µs |

The candidate median differences are about -0.9% in each condition; this shared-host pair supports no speed-up claim and does not reproduce a >25% regression. P95 is the maximum/nearest-rank p95 of seven sample means, not individual-tick tail latency.

The same independently instrumented script, SHA256 `bd3c205675c6daa6840b04a381c1878cfaef8748514b4a8e8f12fe8a5f22c9bd`, ran on both sources. Runtime observations show fixed active node count 448, audio node count 60, resource count 69, effect pools 24/40/12, and message-buffer high-water 4,096 bytes. Packed active samples temporarily raise object count to 8,686–9,626; two process frames outside the timer return it to about 2,346 each sample. This rules out cumulative node/object/resource/message-buffer growth in these seven samples. Post-flush static memory rises about 0.53 MB while the fixture retains 22,700 shot records; the correlation is consistent with fixture records, but allocator attribution was not isolated. This is not a general leak qualification.

No presentation suppression was used. Timed blocks still include deferred audio/playback allocation; sample-boundary cleanup runs outside the timers. These are narrow headless authority-call costs in a packed manual loop, not rendered frame cost, hardware FPS, input latency, or steady frame pacing. Raw counters, per-sample costs and calculations are in [reviewed-benchmark-summary.json](reviewed-benchmark-summary.json).

## Largest remaining deficiency and unsupported gates

**Multiattacker attribution remains order dependent.** In the shield fixture, actor 1 gets the only kill/reward in forward order and actor 2 in reverse order. Later contacts at the dead victim also lose contribution and hit feedback. Health, shielding, death count and total reward agree. This needs an explicit competitive policy; the current correction does not certify all order invariance.

The existing attacker-first simultaneous full-team wipe result remains, and accepted trades make that policy more reachable. Utility detonation damage and sequential `move_and_slide` contact resolution remain outside the batch. Equal-distance overlapping trace volumes, network delay/sub-tick fairness, bot/human balance, human feel, external title parity, rendered performance, and unavailable native devices remain unsupported by this benchmark.

Static native CI registration review also passes: adding `authority_order` to root `run_native_regressions.py`'s SUITES causes its default argparse list to run `res://tests/authority_order_test.gd`, with existing exit/log enforcement and timeout. The desktop workflow already calls that helper with defaults. The precise patch is retained as [native-suite-registration.patch](native-suite-registration.patch); applying/running it is root's separate integration step, not a claim of native Windows/macOS execution here.

Review ended after this bounded source/correctness/performance check. No reviewer engine process remains running. All source, output and failed-fixture evidence is retained; SHA256SUMS indexes top-level review artifacts.
