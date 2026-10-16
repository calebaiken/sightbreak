# Independent reload audio capture timing investigation

This is a read-only source investigation and external harness prototype. Shipping files and tests in the frozen baseline were not edited. The baseline checkout remained clean at `4316c58c8f5ae38ea924631fc48e4b1e7d5df873` for every recorded run. Engine: `4.7.2.stable.official.ed1daf0bf`, official full source revision `ed1daf0bf001b61586d9930840f2f1394092c079`.

## Finding

The original capture test maps captured sample index to elapsed wall time from one `clear_buffer()` call. This conversion is invalid for Godot's Dummy audio driver under scheduling delays. The original historical early-silence failure can be reproduced without changing any game or test source: suspending the original test process for 150 ms after initialization produces the same `0.06647` early peak, although the sound is scheduled normally. The original failing result remains historical evidence; this controlled experiment establishes a causally sufficient mechanism, not a recording of which OS scheduling event occurred in that historical run.

The exact engine source explains the mechanism:

- `servers/audio/audio_driver_dummy.h` sets `buffer_frames = 4096`: **92.88 ms at 44100 Hz**. The original test comment claiming 2048 frames / 46 ms is incorrect for this engine revision.
- `AudioDriverDummy::thread_func()` processes a full buffer and then always sleeps for `buffer_frames / mix_rate`. It does not compensate for elapsed processing time, preemption, or oversleep. Thus generated frame count / sample rate need not equal wall time.
- `AudioEffectCapture::get_pushed_frames()` counts frames actually written by the mixer; `clear_buffer()` advances only the read cursor. The capture itself does not stamp frames with wall times.
- The bus effects are processed in sequence. Reading one bus's counter while a mix is in flight can stamp a cue/cancel in a different block from its playback request unless the test synchronizes with `AudioServer.lock()`.
- `AudioStreamPlayer3D::play()` sets a pending playback. The actual `start_playback_stream()` happens during `NOTIFICATION_INTERNAL_PHYSICS_PROCESS`. Driving the actor's presentation from arbitrarily frequent `process_frame` yields creates an extra race with that physics handoff.

In the original failed log the first real threshold onset was at sample-clock 472 ms but play was logged at wall-clock 546 ms. Its event search started only 60 ms before play, so the reported -60 ms onset was the **search-window boundary**, not the true onset. The early-silence scan included legitimate audio from 472 ms through its presumed silent boundary at 486 ms.

## Reproductions and intermediate failures

All unsuccessful attempts are retained.

| Run | Harness | Result |
| --- | --- | --- |
| `unmodified-pause150` | Original, unchanged `res://tests/reload_audio_capture.gd`; SIGSTOP at 0.45 s after launch for 150.15 ms | Exit 1; 9 checks / 4 failures; early peak **0.06647**, first threshold onset 472 ms versus play 547 ms |
| `pause150-wall` | External instrumentation retaining original wall-coordinate math; 150.15 ms stop after capture-ready marker | Exit 1; 9 / 4 failures; early peak **0.06647** |
| `pause150-frames` | Independent cue capture-frame marks, no onset-based alignment; 150.15 ms stop | 9 / 0 failures |
| `final-isolated-cancel` | Frame marks, process-frame driving, no mixer lock; run alongside four other captures | 11 / 1 failure; cancellation peak 0.00485 after its 80 ms sample guard |
| `final-sequential-cancel-1` | Frame marks, process-frame driving, no mixer lock | 11 / 1 failure; pouch onset 126 ms after cue mark, 116 ms from median |
| `physics-loaded` | Physics-frame driving, frame marks, no mixer lock; 3 captures + 2 CPU workers | 8 / 9 runs passed; one cancellation guard failure, peak 0.00485 |
| `physics-paused` | Physics-frame driving, frame marks, no mixer lock; three scenarios per round with 150 ms stop | 8 / 9 runs passed; one cancellation guard failure |

The failure retained in the unsynchronized prototype is material. Frame-coordinate conversion alone is insufficient. No numerical tolerance was increased to make these runs pass.

## Narrow test correction and final prototype validation

The proposed correction is confined to the capture harness:

1. Clear and stamp every capture's origin while holding `AudioServer.lock()`.
2. At the existing `reload_cue` signal, stamp the independently advancing capture frame counter for the logged voice. This signal follows `play()` in the same main-thread call. The enclosing mixer lock prevents a mix from occurring between playback scheduling and the frame mark.
3. Drive the manually ticked actor after `physics_frame`, matching the 3D audio player's internal physics scheduling.
4. Hold the mixer lock only around the synchronous authority/presentation tick and its cue/cancel marks, then release it immediately. No `await` occurs while locked.
5. Use those independent frame marks for event search, the pre-first-event quiet interval, cancellation, and shot/seat overlap. Do not align a sound using its measured onset.
6. Assert that none of the captures discarded frames.

`atomic-frameclock.patch` is a proposed diff against the frozen baseline. `reload_audio_capture_atomic.gd` is the same minimal proposal as a standalone file. The lead integrator may adapt its CSV names and existing resource teardown changes. These files deliberately do not rewrite game audio or authoritative reload timing.

Every original numerical limit is retained: 90 ms event spread, median offset -45..120 ms, 60 ms pre-first-event guard, 80 ms post-cancel guard, the 40 ms shot search lead, amplitude thresholds, and search window lengths. Five zero-discard checks are added. The meaning of the median-offset diagnostic changes from an invalid global wall-coordinate calculation to latency in independently marked capture frames. This does not measure physical speaker output latency.

Final instrumented source: `reload_audio_clock_probe_locked.gd`, SHA-256 `861d391047bffa540f295f8778e6fba97cebf9d10cb381c4b91763a6fd9b96c8`.

| Final condition | Runs | Result |
| --- | --- | --- |
| Isolated cancellation | 1 | Passed 11 checks |
| Three simultaneous captures (reload, cancel, shot), two independent CPU workers, four rounds | 12 | **12/12 passed** |
| Three simultaneous captures (reload, cancel, shot), 150 ms whole-process suspension immediately after clear, three rounds | 9 | **9/9 passed** |

These finite samples support this orchestration correction. They do not prove that arbitrary host load can never violate a genuine timing gate. A new campaign must retain any subsequent failure.

## Negative controls

Controls replace only the test instance's audio object with a subclass, or start an extra voice from the test. Agent-owned/shipping scripts remain unchanged.

| Control | Injected defect | Final locked prototype outcome |
| --- | --- | --- |
| A5 equivalent | `play()` succeeds but voice volume is set to -95 dB | Exit 1; all six audible-event checks fail |
| A6 equivalent | `stop_all()` is a no-op during cancellation | Exit 1; post-cancel peak **0.01783**, above 0.0008 |
| Early audio | Start an unlatch voice before its cue/log, retaining normal later events | Exit 1; pre-first-event peak **0.03063**, above 0.0008 |

The actual-early-audio control matters: the correction cannot create an offset from the sound it is trying to validate, and genuine unannounced early playback is still detected. Reload-phase correctness remains covered independently by the sequence and audio scheduling tests; this capture gate observes audible samples relative to scheduling.

## Reproduction commands

From `/workspace/sightbreak-three-agent-build`:

```sh
python3 /workspace/reviews/stabilization-v2-20261016/timing/run_unmodified_pause.py
python3 /workspace/reviews/stabilization-v2-20261016/timing/run_batch.py --label NEW-loaded --cpu-workers 2 --rounds 4 --probe reload_audio_clock_probe_locked.gd
python3 /workspace/reviews/stabilization-v2-20261016/timing/run_batch.py --label NEW-paused --pause-ms 150 --rounds 3 --probe reload_audio_clock_probe_locked.gd
python3 /workspace/reviews/stabilization-v2-20261016/timing/run_probe.py --name NEW-A5 --clock frames --negative mute --probe reload_audio_clock_probe_locked.gd
python3 /workspace/reviews/stabilization-v2-20261016/timing/run_probe.py --name NEW-A6 --clock frames --scenario cancel --negative cancel-voices --probe reload_audio_clock_probe_locked.gd
python3 /workspace/reviews/stabilization-v2-20261016/timing/run_probe.py --name NEW-early --clock frames --negative early-unlogged --probe reload_audio_clock_probe_locked.gd
```

Batch and per-run metadata contain exact commands, scenario, suspension duration, source identity, probe hash, exit status, and clean-baseline status. Versioned probe files preserve each recorded hash, even where the initial command used a working prototype filename later superseded by the final prototype. `manifest.json` maps those hashes to retained source files.

Engine source was fetched read-only through the GitHub API at the exact full official commit. Source URLs:

- https://github.com/godotengine/godot/blob/ed1daf0bf001b61586d9930840f2f1394092c079/servers/audio/audio_driver_dummy.cpp
- https://github.com/godotengine/godot/blob/ed1daf0bf001b61586d9930840f2f1394092c079/servers/audio/audio_driver_dummy.h
- https://github.com/godotengine/godot/blob/ed1daf0bf001b61586d9930840f2f1394092c079/servers/audio/effects/audio_effect_capture.cpp
- https://github.com/godotengine/godot/blob/ed1daf0bf001b61586d9930840f2f1394092c079/servers/audio/audio_server.cpp
- https://github.com/godotengine/godot/blob/ed1daf0bf001b61586d9930840f2f1394092c079/scene/3d/audio_stream_player_3d.cpp

## Final maintained source review

Read-only source review of `game/tests/reload_audio_capture.gd` at frozen commit **`aee6b7396928489662eb9917c7e403a1a00a21af`**. Maintained file SHA-256: `8d37c5b390d537cb49c542f2fe49348bab3dfc9c9cc0f6e6057652bd6f798013`.

**Verdict: accepted by independent source review for the audio-capture clock/synchronization correction.** No new engine process was started and no frozen-checkout file was edited during this review. Native acceptance of this maintained commit belongs to its separately running regression campaign and maintained negative controls; the earlier 21/21 result remains specific to the external locked prototype.

The final diff from `reload_audio_capture_atomic.gd` contains only these relevant adaptations, all acceptable:

- The retry loop around initial clear/counter sampling is removed. This is equivalent while `AudioServer.lock()` holds: the mixer cannot push another block between `clear_buffer()` and `get_pushed_frames()`.
- The engine comment correctly states 4096 frames / approximately 93 ms at 44.1 kHz. The original 90 ms limit remains.
- CSV columns distinguish the cue's wall timestamp from cue/onset capture frame indices. The synthetic wall-clock onset is removed; it was diagnostic-only and no longer participates in validation.
- The test queues its world for deletion, removes its temporary buses, and drains the mixer for 0.5 seconds before exit. This cleanup happens after captured samples have been checked and written, so it cannot hide a captured-audio assertion failure. It preserves exit status from `failures`.

Lock review: the initial clear/mark lock and each synchronous tick lock are balanced. No `await` occurs while either lock is held. Both authority branches converge on `tick_visual()` then `AudioServer.unlock()`. The cue callback executes synchronously from the tick's `_fire_reload_cue()`; that method calls audio `play()` immediately before emitting `reload_cue`, so the shared capture-frame mark and play call cannot straddle a mixer operation. `start_reload()` itself only starts the reload timer and does not emit an unlocked cue. Cancellation frame marks and the stop-producing weapon switch are inside the same lock. Shot frame marking and `play()` are also inside the tick/cue lock. Initialization and manual actor stepping await `physics_frame`, preserving the validated handoff to the 3D audio player's internal physics processing.

Assertion audit: original 90 ms event deviation, strict median range `>-45` and `<120` ms, peak `>0.02`, onset presence, 60 ms early guard, 80 ms cancellation guard, silence `<0.0008`, 40 ms shot lead, 250 ms shot window, 60 ms event search lead, 400 ms search tail, 0.012 onset level, and `max(10% peak, 0.004)` onset threshold are all unchanged. Expected event order, cancellation event subset, and shot/seat dual presence remain checked. Five per-capture zero-discard assertions remain added. Every scheduling mark is independent of the measured sound onset.

No additional blocking source finding was identified in this diff. This verdict does not certify listening quality, physical audio output latency, arbitrary-load determinism, or resource-clean native exit; those require the corresponding retained runtime evidence.

## Residual maintained baseline failure and ten serial reruns

A later maintained negative-control invocation at `aee6b7396928489662eb9917c7e403a1a00a21af` reported **`audio capture (cancel) FAILED` during its unmodified baseline**. Its summary is preserved at `/workspace/reviews/stabilization-v2-20261016/audio-maintained-negative-controls.txt`. The wrapper did not retain that subprocess's raw output, so it is unknown whether the failed item was the 80 ms silence guard, another timing assertion, or a script error. The wrapper classifies a test as FAILED for a nonzero summary failure count or a script error; this result cannot simply be attributed to an ignored ObjectDB warning. Its subsequent mutated controls were not reached and must not be described as accepted by that invocation.

In response, this reviewer ran **ten serial, unmodified cancellation captures** directly from the clean maintained controls checkout. Every process used the exact maintained file hash `8d37c5b390d537cb49c542f2fe49348bab3dfc9c9cc0f6e6057652bd6f798013`; source `aee6b7396928489662eb9917c7e403a1a00a21af` and clean status were checked after every run. Only one reviewer audio process ran at a time; no added CPU workers were started. The lead's separate full regression campaign was running on the host, so this was not a controlled idle-host measurement.

**Observed result: 10/10 passed, 11 assertions each, zero script/errors/leak diagnostics in their retained raw logs.** All ten post-cancel silence peaks were `0.00000`. Event offsets from the median ranged from `-8` to `23` ms, within the unchanged 90 ms bound. Raw process logs, per-event CSV files, WAV captures, commands, timings, and source checks are under `timing/maintained-serial/`; the machine-readable aggregate is `timing/maintained-serial/summary.json`.

The failure incidence in this new sample is **0/10**, not an estimated universal probability of zero. The earlier maintained wrapper baseline failure remains **unresolved intermittent evidence**, because its detail was discarded. Neither the external prototype's 21/21 result nor these ten passes establishes which assertion failed in that prior invocation. The independent source-acceptance verdict above remains limited to the clock conversion and synchronization implementation; an unrestricted deterministic cancellation claim is not accepted. Retain the failed invocation and any new campaign failure, preserve raw subprocess output on future failures, and keep every original tolerance.

No sources were edited for these reruns and no additional engine process remains running from this review.
