# Actual Linux GLES profile capability

The single registered attempt produced usable renderer-query output, then
FAILED the original initial-LIVE wait. Source and owned cleanup checks pass.
This is the builder's measured handoff; independent raw review is pending.
The existing Linux next-buy failure and broader release gates remain open.

## Exact attempt and original failure

Root released one fresh export and one native attempt after independent source
acceptance [`8a1df18c`](https://github.com/calebaiken/sightbreak/blob/8a1df18c8bcf8fc1856ab3b1ad6f8814af7719a9/docs/reports/gauntlet/m1-linux-gles-profile-recovered/independent-review-r2/SOURCE_REVIEW.md)
at exact source `b1a131ab4790ac84371b54ee236441a66faf4125`. The controller,
game, validation and shipping identities were clean and unchanged from
preflight through export and post-run teardown. The maintained exporter passed
in 11.172328 seconds; there was no extra fixture, OCR, CPU sampler, repeat,
Docker, service or CI run.

The real controller retained Linux plant / explicit seed 42 / whole budget 180,
original 1280x720 native extent, Standard, render scale 1, cap 60, 60 Hz physics,
time scale 1 and ten stock-health actors. The controller source sets software
rendering and two Mesa workers; the actual client log identifies GL
Compatibility / Mesa llvmpipe. The normal V-Sync unsupported warning is retained.
Private export state began with only a symlink to the independently verified
template directory. The client used its ordinary fresh isolated output state.

Controller PID 9725 exited 1 after 58.715280 wrapper seconds. Its own retained
result takes 58.557768 seconds and records `Objective scenario live phase`.
The unchanged `objectives` function waits 45 seconds for initial LIVE. The
initial-capture-end to failure driver bracket is 45.075967 seconds. The last
observation remains BUY / round 1 / tick 844, elapsed 14.066667 simulation
seconds, with 0.933333 seconds left on the original 15-second BUY timer.
Plant, next buy and restart were unreached. The original 12-second next-buy
bound remains unchanged; this attempt never entered it. No deadline was
extended, and no passing gameplay result is inferred.

I viewed both original 1280x720 PNGs. The main menu shows empty device training;
the initial arena image shows a living attacker in ROUND 01 / BUY, 100 HEALTH,
DEVICE / CARRIED and the stock sidearm. These two images cannot establish LIVE,
plant, objective completion, next buy, restart or visual-quality acceptance.

## Profile capability and its limits

The actual initial argv has `--gpu-profile` at index 1, before `--`. The receipt
has only Xvfb and that client; no reopened client was reached and no external
sampler output exists. The client log contains 35 profile headers. Thirty-four
have positive named task rows; all parsed headers are finite/nonnegative and
all printed rows are finite and above 0.01 ms. This meets the preregistered
output capability condition at the measured source, pending independent review.

`Render Opaque Pass` is the largest printed named interval in all 34 row-bearing
blocks. Its reported interval averages range from 260.764 to 1,403.713 ms.
This is a coarse query interval to investigate further. It does not assign that
duration to a CPU function or establish the cause of the failed gameplay wait.
The separate header values range from 0 to 486.349 ms and use a different
statistic. The raw values, names, stdout line positions and every parsed block
are retained in [`native-recomputed.json`](native-recomputed.json).

As established from the pinned engine source before running, GLES queries are
historical and buffered; the source comment says frame minus two. Stdout can
reuse retained profiles and emits neither source-frame nor phase identities.
Named rows accumulate adjacent query differences over draw calls until more
than one host second passes; the header uses the latest retained profile's final
timestamp offset. Startup, buffering, retained profiles, reporting denominators
and threshold omissions remain part of these bytes. The reported ranges are
ranges of emitted statistics, not unique-frame timings or percentiles.

No stdout-arrival phase tagging, header/row sum, CPU-cost partition, physical
FPS, profiler/sampler overhead, causality or performance-improvement claim is
supported. The earlier sampler-on attempt and this profile-on attempt do not
form a controlled performance comparison. No product change follows from this
single diagnostic.

## Source, artifact and cleanup receipts

The engine archive and extracted editor member match the pinned hashes. The
1,281,349,702-byte template archive matches its pinned SHA-512; its Linux debug
member matches the installed template linked into private export state. Actual
export and client identify `4.7.2.stable.official.ed1daf0bf`. The fresh manifest
and read-only binary inspection verify an x86_64 ELF with an embedded Godot
4.7.2 PCK, 134 resources, compiled offline diagnostics and no shipped tests.
Exact hashes, lengths, resource names and PCK header are in
[`export-source-verified.json`](native-r1/export-source-verified.json).

The controller reports `cleanup_errors=[]`. Its failed initial client exits
SIGTERM / -15 during bounded failure cleanup; Xvfb exits 0. Initial/reopened
normal-exit fields are null because the flow did not reach those paths. A
separate post-run probe finds controller 9725, Xvfb 9770, client 9816 and both
owned child process groups absent, with display :123 socket/lock absent.
[`post-run-cleanup.json`](native-r1/post-run-cleanup.json) retains the probes and
the unchanged clean source identity. No process permission, quota, affinity,
priority, host setting or game setting changed.

[`native-r1/payload-index.json`](native-r1/payload-index.json) binds 29 archived
payloads, 1,200,024 raw bytes / 1,135,195 archived bytes. Original logs are
compressed without editing their trailing spaces; every decompressed byte/hash
matches its source. The original output directory is
`/workspace/sightbreak-linux-profile-recovered/builds/linux-gles-profile-native-r1`.
The complete ELF/PCK, generated caches, wrappers and licenses remain at their
original ignored paths, with 124 local-only file hashes/lengths inventoried.
No original output was removed. Frozen source copies, controller/export/client
logs, commands, observations, both PNGs and cleanup receipts are archived.

Recompute all archive hashes, capability rows and ordinary failure predicates
without launching an engine:

```sh
python3 docs/reports/gauntlet/m1-linux-gles-profile-recovered/native_audit.py > /tmp/linux-gles-native-audit.json
cmp /tmp/linux-gles-native-audit.json docs/reports/gauntlet/m1-linux-gles-profile-recovered/native-recomputed.json
```

The native lane is idle. Root should assign a fresh critic to the actual raw
outputs and retained ELF/PCK. The largest remaining gap is controlled attribution
beyond this historical renderer-query interval; the ordinary Linux gameplay
failure remains unresolved. No second attempt is registered or performed.
