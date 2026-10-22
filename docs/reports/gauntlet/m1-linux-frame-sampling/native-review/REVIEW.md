# Independent native diagnostic verdict

Accept the instrumented receipt as valid diagnostic evidence at exact source
`8afe0cc6b4c9051d3649a82bbcb4c8de8f947f9c`. The original Linux next-buy gate
**FAILS**, recorded at 132.300578 controller seconds. The complete attempt,
including cleanup, takes 132.337244 seconds. Its terminal observation remains
POST / round 1, tick 2625, with 0.383333 seconds on the simulation timer. Natural
next buy and restart are unreached. Earlier failed attempts remain failures.

The new evidence supports repeated physics catch-up saturation across BUY,
LIVE and POST. It narrows the next profiling target toward software presentation
work: sampled process maxima are hundreds of milliseconds, physics-step maxima
are a few milliseconds, and categorized llvmpipe workers consume most measured
client CPU. It does not identify an expensive function, prove every frame
saturated, establish a renderer fix or close gameplay/performance acceptance.

## Source, engine and raw integrity

The independent preflight observed clean exact source, validation SHA-256
`b88317bf83633858eb02ca8a771be4eeec68e453c270a12fa91ae2375a42a73d`, game tree
`4510bbb4ee295f96b6e9245aeb253288611bf1ee`, and shipping-content SHA-256
`f61d63f00b841cf243af747d8d198f164167f115d2b1bc04a1619bd548cdaa50`. The three
changed runtime/controller files match the accepted source hashes. Independent
post-run inspection observes identical clean source before the builder's later
documentation/archive commit. Source and pure-review files remain unchanged.

Independent hashing verifies the cached editor archive against its pinned
SHA-512 and its extracted member against the observed editor binary. Actual
export, fixture and client logs identify `4.7.2.stable.official.ed1daf0bf`.
The 84,232,632-byte ELF matches manifest SHA-256
`4f914edf046db5a4edff06aa165b70edf0c6e82ba70e7a411d4a577f4caf2189`.
Independent parsing finds an x86_64 ELF, a 4.7.2 PCK with 134 resources, the
compiled offline diagnostic and no shipped test directory. The original binary
remains in the builder's `builds/linux`; the retained raw archive binds its hash
and size but does not contain a portable binary copy.

The frozen [native-r1](../native-r1/payload-index.json) archive, committed as
`c0bf287062c79c40659324f4aa55b06586cab0b6`, has 33 payload files / 3,607,695 bytes.
All hashes/sizes and original runtime bytes match;
there are no unindexed files. Its index SHA-256 is
`002a01a91b1da23733574c1f514adaa954bd2a75ff326eeab1ac657abe216463`.
Archived runtime source copies match Git's exact `8afe0cc` blobs. Running the
independent recomputation on the archive reproduces the original phase results
and next-buy bracket. See [archive-verification.json](archive-verification.json),
[recomputed.json](recomputed.json), and [live-recomputed.json](live-recomputed.json).

The first preflight compared an editor binary hash with the archive hash and
stopped before engine execution. Its failure is retained. The corrected check
uses the archive member. Actual order was maintained import/export, then the
existing source fixture (60 checks / 0 failures in 0.867 seconds), then one plant.
This differs from the handoff's fixture-first plan and is recorded plainly.

## Original conditions and native result

The unchanged controller runs Linux plant / seed 42 with `--timeout 180` and the
sampler opt-in. The source review proves all existing controller statements and
deadlines unchanged after removing only the new opt-in statements. The actual
Xvfb command selects 1280x720; runtime profile/readbacks retain Standard, scale
1, cap 60, 60 Hz physics, time scale 1 and jitter fix 0.5. The native log selects
Mesa llvmpipe. The sampler reads DISPLAY `:122`, `LIBGL_ALWAYS_SOFTWARE=1` and
`LP_NUM_THREADS=2`. Recorded commands are only Xvfb and the client, with no
recorder command or MP4 output.

The original controller records legitimate plant, interrupted-input reset,
smoke deployment and living post-plant guidance as partial checks, followed by
natural defender defuse. I inspected the original 1280x720 PNGs directly:
[06b](../native-r1/native-plant/06b-postplant-role-guidance.png) shows LIVE / YOU
ATTACK, 100 HEALTH, device time and `DEFEND THE DEVICE`;
[07](../native-r1/native-plant/07-objective-round-resolved.png) shows POST / DEVICE
DEFUSED, defender score 1 and ELIMINATED / SPECTATING. These observations do not
supply full gameplay or visual-quality acceptance. No OCR was used.

| Action bracket | Driver seconds | Observed ticks | Observed draws |
| --- | ---: | ---: | ---: |
| Initial match capture to failure | 120.227044 | 2,600 | 325 |
| Resolved capture to original next-buy failure | 12.053808 | 247 | 31 |

The POST bracket advances 4.116667 simulated seconds. Its original twelve-second
deadline remains failed. Action-associated engine observations may precede their
actions; the clocks are not equated. The positive terminal timer does not show a
failed `_begin_round` call or authorize a timer change.

## Sampler and timing interpretation

I independently observed client PID 137048 / start tick 3158785, its exported
executable and controller parent 137004 while alive. Xvfb PID 137043 also belongs
to that controller. The sampler header and all 132 process CPU records retain
that start identity. CPU units are SC_CLK_TCK=100. No process discovery was used.

The worker writes 132 samples within its 179.615404-second maximum, which is the
remaining portion of the original 180-second controller budget. Spacing is
1.000720–1.007352 seconds, with no catch-up bursts. It finishes with
`controller_stop`, error null and `thread_alive=false`. Early menu observations
produce nine explicit FileNotFoundError frame fields; 123 frame fields are
available afterward. Threads range from 1 to 16, below the 128 bound, without
truncation. Thread names are reduced to the three allowed roles. The environment,
sample and offline frame key whitelists pass; no actor/account/profile payload
is copied into the sampler file.

Actual frame fields are finite numbers with ordered read timestamps. All retain
limit 8, requested settings, 1280x720 visible/output texture size and unavailable
internal 3D target size. The source-verified monitor labels remain maxima over
roughly one-second engine windows. Runtime values do not turn these into
per-frame samples or a complete CPU/GPU partition.

| Consecutive sampled phase | Sampler seconds | Ticks / process frames | Process / draws | Process maxima range, s | Physics-step maxima range, s |
| --- | ---: | ---: | ---: | ---: | ---: |
| BUY | 38.062 | 896 / 112 = 8.000 | 112 / 112 | 0.315297–0.398210 | 0.000211–0.005699 |
| LIVE | 70.097 | 1,417 / 177 = 8.00565 | 177 / 177 | 0.272059–0.474042 | 0.001261–0.004981 |
| POST | 12.019 | 247 / 31 = 7.96774 | 31 / 31 | 0.377541–0.429270 | 0.001295–0.003494 |

The slightly above-eight aggregate ratio can occur because observation endpoints
fall within physics batches. Across the valid external interval, process CPU is
237.23 seconds over 122.180 sampler seconds (1.942 CPU-seconds per wall second).
Stable categorized thread deltas are 224.17 CPU seconds for llvmpipe workers,
10.45 for the main thread and 2.55 for other threads. These counters measure CPU
execution, not a function profile or complete scheduler-wait breakdown.

Readable cgroup-v2 root counters expose a quota of 400,000 microseconds per
100,000-microsecond period, with five allowed CPUs. Over the complete sampled
interval, `nr_throttled` and `throttled_usec` both increase by zero. Root cgroup
usage can include other processes; this supplies no client-only attribution or
proof against every source of descheduling.

Snapshot getter brackets are 11–39 microseconds; external read brackets are
0.365–2.527 milliseconds. They exclude surrounding observer/guard, serialization,
flush and header work. There is no matched instrumented-versus-uninstrumented
run, so total measurement overhead is not established.

## Cleanup and remaining gap

The native failure cleanup records client exit -15 and Xvfb exit 0, with no
cleanup errors. Independent post-run reads find all 20 declared owned PID/TID
entries absent, including controller/export/fixture wrappers and every sampled
client thread. The `:122` socket is absent. The stopped controller and recorded
worker join support actual sampler termination. This check inspects only known
owned identities, without signals or a system process sweep; it is not a claim
about unrelated host resources.

The largest remaining gap is cost attribution within the software-rendering
path and a matched measurement of overhead. The evidence supports a separately
reviewed unchanged-camera renderer profile as the next experiment. It does not
authorize lowering quality, modifying the arena, changing physics/time/FPS or
extending acceptance deadlines. Windows 976x549 ANGLE software remains an
unmatched reference. Physical-GPU pacing, sustained device performance, full
Linux playability and the broader release gates stay open.

The independent audit passes 31 native receipt predicates and seven archive
predicates. Reproduce with `audit_native.py --native <native-r1/native-plant>` and
`audit_archive.py --archive <native-r1> --builder <original builder worktree>`.
No engine, native game, OCR, service, export or CI was run by this critic.
