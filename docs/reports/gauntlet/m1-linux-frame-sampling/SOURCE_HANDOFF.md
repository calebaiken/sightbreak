# Linux frame sampling source handoff

Builder branch `diagnostic/linux-frame-sampling`, worktree
`/workspace/sightbreak-linux-frame-sampling`, base `9616f52`. Criteria `e71e5d4`
precede the source change. This is ready for independent source review, with no
builder acceptance or native-runtime verdict. Root retains the aggregate lane;
this branch has run no engine, native game, OCR, service, export or CI.

The game diff adds one readback dictionary inside the existing admitted offline
debug `_snapshot`. It reads physics/frame settings and counters, engine monitor
maxima and viewport/output texture dimensions. Existing calls, sampling/event
cadence and disk-write paths remain unchanged. The readback has begin/end
microsecond timestamps to expose its own collection interval. Internal 3D target
size is explicitly unavailable; output texture dimensions are labeled separately.

The controller adds `--linux-frame-diagnostics`, accepted only for native Linux
plant, seed 42 and `--timeout 180`. The original native command, 1280×720 display,
llvmpipe/two workers, profile defaults and twelve-second next-round wait retain
their source. Without the flag, it creates no sampler. With the flag, one owned
thread reads the initial client PID once per second for at most 180 seconds.
Its lifetime never follows a reopened client. The existing process cleanup stops
the original client; bounded sampler joining records any surviving worker.

The sampler records raw process/thread CPU ticks and SC_CLK_TCK, allowed affinity,
available cgroup-v2 target/ancestor quota and throttle counters, and wall/monotonic
read timestamps. It checks the owned Popen object's status and process start
identity before/after each collection. Uncertain rows are discarded. Per-thread
enumeration stops at 128 entries and reports truncation. Each file read has a
size bound. Cgroup v1, absent/denied files, missing stat fields and invalid paths
remain explicitly unavailable. Ancestor counters may include other processes;
they cannot be attributed wholly to this client.

Each CPU row also retains a strictly typed whitelist from the existing offline
plant status file. That external one-second read preserves engine-window values
which would otherwise be overwritten in `status.json`; it adds no engine writes.
Actor, profile, account and arbitrary nested fields are excluded. The header
serializes only DISPLAY, LIBGL_ALWAYS_SOFTWARE and LP_NUM_THREADS. Arbitrary thread
names are reduced to client-main, llvmpipe-name or other categories. Counter
exceptions retain a static reason/type and errno, without echoing input contents.

`sampling_completed` means the bounded worker wrote samples and stopped without
an output/worker error. Individual counter availability remains separate, and
this field gives no product or performance acceptance. The original validator's
`passed` result and its exact failed stage remain separate from sampler status.

## API evidence and interpretation

[API_EVIDENCE.json](API_EVIDENCE.json) records pinned Godot 4.7.2 source/doc URLs,
hashes and excerpts for every new engine getter/monitor, including Time's
microsecond clock. The Engine XML bytes also match commit `ed1daf0bf`.
`main/main.cpp` publishes process and physics **maxima** at the engine's roughly
one-second statistics refresh. Process time includes callbacks, renderer sync and
draw. Physics time is the largest individual step. These observations can lag
collection, do not partition a frame's wall time and are not GPU timings. Initial
monitor zeros do not establish zero rendering/physics cost.

The documented default catch-up limit is eight, matching the earlier observed
eight-tick/drawn-frame ratio. The next run must still read the actual limit;
documentation does not replace the native readback. A different native limit,
tick/process ratio or process/drawn relationship changes the hypothesis.

## Pure controls already executed

```sh
python3 scripts/test_linux_frame_sampler.py -v
python3 scripts/test_offline_role_guidance.py -v
python3 scripts/test_offline_capture_fences.py -v
git diff --check
```

The final source controls pass 18 sampler/option tests, four existing life/role
controls and 15 existing capture-fence tests. They use synthetic proc/cgroup trees
and an inert fake process, with the OS affinity getter mocked. No real client or
unowned PID is sampled. The one-second cadence control uses one short worker
interval; all other workers exit or are explicitly joined. Tests cover privacy,
PID disappearance/reuse before and after collection, unavailable counters,
bounded threads/duration, unsafe/symlinked cgroups, fresh output, full disk errors,
explicit stop, original default arguments and restricted diagnostic arguments.
Logs and their index remain in [pure-controls](pure-controls/).

The first test invocation used `/workspace/sightbreak/.venv/bin/python` and
failed importing the existing validator's Pillow dependency; its other 14 cases
passed. That failed log is retained as `run-1.log`. System `python3` has Pillow
12.3.0 and runs all controls. `run-2.log` is the intermediate 16-case pass;
`run-3.log` belongs to the final 18-case source. Earlier logs are not relabeled as
final-source results.

## Next native gate, not yet authorized for execution

After clean source freeze, independent source acceptance and root's lane release,
run the existing offline-diagnostics source fixture first on the pinned engine.
Then export this exact clean source and use its manifest-bound native executable
for one original Linux plant attempt with the sampler flag. Use fresh output,
isolated profile/display and no recorder. A representative validator command is:

```sh
python3 scripts/verify_offline_match.py --target linux --scenario plant \
  --timeout 180 --linux-frame-diagnostics --display :122 \
  --xvfb /workspace/tools/xvfb/usr/bin/Xvfb \
  --output "$PWD/.local/linux-frame-sampling/native-r1"
```

The selected `builds/linux/sightbreak.x86_64` must first exist and match the new
source-bound manifest; no older binary can supply these new readbacks. Before
execution, recheck display availability and root's lane coordination. Retain raw
source/artifact/controller identities, original stage results, every sampler row,
cleanup and failed outputs. Actual engine parsing, getter availability, monitor
values and sampling overhead remain unverified until that run. No timeout,
physics, quality or scheduling change is authorized by this proposal.

The largest remaining gap is the absence of this same-attempt Linux native
receipt. Coarse maxima and CPU counters will narrow the next profiling question;
they cannot alone identify a costly function. External physical-GPU pacing and
the release performance gate remain open. Arena, PR26 map content and canonical
mission files are unchanged.
