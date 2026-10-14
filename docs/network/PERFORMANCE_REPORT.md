# Ten-client synthetic campaign

Source `85edf895c05a9c4070d19e2e96a5752ade55006b`; shipping runtime identical to d084e500. One dedicated Godot process and ten clients, eighteen seconds each, seed7301. RTT is added half in each direction. Jitter ±20 ms per direction, loss3%, reordering5% where enabled. Blackout4–6 s; explicit close/reconnect at 8 s. Prediction is deliberately enabled in the experimental fixture except the disabled comparison; shipping default remains false.

| Condition | Pass clients | Tick work p95 ms | Tick interval p95 ms | Remote delayed error p95 m | Ack error p95 m | Corrections / hard | Up / down total B/s |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| rtt-0 | 10/10 | 5.56 | 16.95 | 0.011 | 0.290 | 537 / 1 | 49293 / 119442 |
| rtt-50 | 10/10 | 6.14 | 16.82 | 0.008 | 0.287 | 473 / 0 | 51706 / 124138 |
| rtt-100 | 10/10 | 6.14 | 16.71 | 0.008 | 0.245 | 725 / 0 | 53809 / 121934 |
| rtt-150 | 10/10 | 8.22 | 17.63 | 0.008 | 0.476 | 1119 / 0 | 52586 / 120152 |
| rtt-200 | 10/10 | 10.76 | 23.14 | 0.114 | 0.340 | 931 / 0 | 52336 / 119117 |
| jitter | 10/10 | 9.42 | 19.45 | 0.008 | 0.330 | 986 / 0 | 52092 / 120618 |
| loss | 10/10 | 10.80 | 23.19 | 0.010 | 0.319 | 852 / 0 | 48126 / 111358 |
| reorder | 10/10 | 9.54 | 18.04 | 0.008 | 0.397 | 863 / 0 | 52794 / 120095 |
| impaired | 10/10 | 11.03 | 20.71 | 0.009 | 0.382 | 923 / 0 | 50594 / 119052 |
| blackout | 10/10 | 7.39 | 17.39 | 1.959 | 0.170 | 456 / 5 | 46300 / 107700 |
| reconnect | 9/10 | 10.91 | 19.63 | 2.120 | 0.340 | 493 / 7 | 36626 / 93818 |
| prediction-disabled | 10/10 | 8.92 | 19.76 | 0.011 | N/A | 0 / 0 | 51849 / 117548 |

Remote error compares visible remote rendered positions with independent60 Hz authority at the intended100 ms-delayed render timestamp, not current server time. Ack error compares saved predicted command poses with authority. Prediction-disabled ack differences are stale authority poses and are intentionally not scored as prediction accuracy. Corrections include initialization/reconnect discontinuities; counts are all ten clients combined.

Bytes/sec divides actual forwarded UDP payload bytes (including ENet framing, excluding UDP/IP headers) by the whole proxy window including startup/drain. Per-client packet, byte, drop, max-datagram and resource timelines are in each summary. This is not steady-state cellular bandwidth. Server tick work excludes other process work. CPU/RSS include measurement arrays; short runs cannot establish long-term leak freedom.

Baseline per-client up range 4773–5139B/s, down 9344–12604B/s; server CPU 3.49 s over 23.34 s, peak RSS 188.4 MiB. Maximum baseline downstream datagram 1392 bytes; 30 exceed1200 bytes. This is an MTU/tunnel risk, not observed loopback IP fragmentation.

## Reconnection follow-up and negative control

Original aggressive0.7 s close/retry:9/10 recovered in the campaign; one client ended failed. Three exact impairment repeats and a no-loss control then recovered10/10 each. Those passes do not erase the intermittent failure.

The maintained fixture now calls the real disconnect handler and defaults to its2 s retry delay; `--reconnect-delay 0.7` retains the original stress case. Exact clean source 47a350da951131e478fa63bc27f578fdacd2ce37: the normal2 s impaired reconnect recovered10/10. A second scenario moves blackout to 7.8–9.3 s around explicit close at 8 s, with 100 ms RTT and no additional loss/jitter: **only5/10 recovered within22 s**. Two clients received “No slot is available for this account; disconnected players retain their slots for60 seconds.” Three remained connecting. The other five reclaimed their original actor IDs around17.9 s. Failed clients had no accepted snapshot for14.6–15.4 s.

This is a confirmed full-capacity reconnect reliability blocker. Attribution as a PR1 versus Codex regression remains UNVERIFIED: the prior foundation also has a ten-transport cap and occupied-token guard, but a matched baseline reproduction has not been run. The original one-client failure had no diagnostic notification history; do not assert an identical cause without evidence.

Source review finds an occupied resume-token actor is not reclaimable while its old peer binding lives; bounded ENet capacity can delay arrival before application admission. Preserve ownership and preflight ticket rules. Follow-up should introduce bounded backoff for explicitly transient old-session/capacity rejection and generation-safe old-binding retirement after validated identity, with a separate protocol contract if rejection codes change. Do not grant duplicate authority or consume tickets on rejected retries.

A terminal-blackout negative control correctly failed both clients even though one still displayed connected: accepted snapshots were14.2 s old. This validates that the harness does not mistake a connection label or stale packets for progress.

Reproduce with `scripts/run_network_campaign.py --only reconnect --out <dir>` (default2 s), or `scripts/simulate_network.py --clients 10 --seconds 22 --rtt-ms 100 --blackout-at 7.8 --blackout-seconds 1.5 --reconnect-at 8 --out <dir>` using spaces between options and values. Raw command arrays and summaries are versioned; durations are finite fixtures, not a sustained soak or cellular trace.

## Matched rendering comparison

Exact baseline PR1=227d6c8; combined production graphics=d084e500 (instrumentation6c34758). Same camera, standard preset,1280×720,24 samples per view ×3runs, CPU0,1/LP_NUM_THREADS=2. The later98ff57c HUD change is absent from this scene-only fixture and changes no measured render source. Values are medians of run medians, not GPU timings or phone FPS.

| View | PR1→combined draws | Rendered primitives | Median wall frame ms | Texture residency |
| --- | --- | --- | --- | --- |
| Approach, weapon visible |152→154|78,274→111,352|447.422→558.426 (+24.8%)|55,942,068→61,538,676 bytes|
| Site, weapon visible |45→47|40,522→73,600|401.768→509.083 (+26.7%)|same|
| Overview, weapon hidden |166→166|75,674→75,674|388.768→392.567 (+1.0%)|same|
| Operators, weapon hidden |138→138|75,024→75,024|428.248→433.757 (+1.3%)|same|

The viewmodel adds2 draws,33,078 primitives and 5,596,608 bytes (5.34 MiB) tracked texture residency. Native actor/cosmetic lifecycle tests plateau without new GL leaks; cache residency is not an isolated allocation measurement. Site p95 reaches648.101 ms in one run; individual distributions are retained.

Eight-scenario profiling ran three times with 24 samples after 8warmups: empty yard, authored idle, fixed reload pose, six static smoke clouds, live ten-actor bots, active inspection, partial case opening, and 20 synthetic marketplace listings. Counters are final-frame samples. Authored idle30 draws/73,554 primitives; smoke72/94,506. Timings vary1.9–5.3× across runs and are diagnostic ranges, not tight estimates. Inspection/case panels are only250×240/260×240; case sampled progress≈0.05–0.625, not full reveal. Reload holds a pose and excludes repeated animation seek; ten-actor bots face a wall, not ten visible combatants. Synthetic cosmetic fixtures make no backend transactions. These limits are in the independent graphics assessment.

Three-round weapon benchmark: no weapon23 draws/37,452 primitives, procedural28/40,476, static hands30/72,682, rig30/73,554. Static hands have a confirmed projection defect, so their timing is not equal-quality evidence. Raw per-round medians are retained (original tool sorted them; chronological round identity is unavailable).

Fresh empty `.godot` import at 6c34758:7.141 s wall,779,052 KiB peak child RSS,53imported files. Existing toolchain/global caches remain; this does not measure native shader compilation, device load time or asset streaming.

## Native ten-client timing correction

The first trial failed because renderer startup delayed one process while the server used an earlier local deadline. Preserve `network-native` as failed harness evidence. The corrected fixture waits for all clients to accept a snapshot, publishes a common start atomically, maps it once to each process's monotonic clock, records boundary lateness, writes reports atomically, and retains networking peers until all reports complete. Final<750 ms accepted-snapshot freshness gates are unchanged. Network traffic spans the entire proxy lifetime, with measurement/startup explicitly separated.

The failed trial also shows a production limitation: reconnect's engine-delta2 s timer took6.384 s wall under very slow software frames. No phone conclusion or gameplay timer change follows. Final corrected native trial at `60cf125`: all ten clients pass (one native, nine headless),100 ms added RTT, prediction disabled, shared25 s. Server work p95=9.223 ms and interval p95=17.136 ms. Native wall callback p50/p95=288.899/475.282 ms; start/stop lateness30/102 ms;87 intervals. Whole proxy lifetime44.409 s includes12.558 s startup and report/exit drain. Native scene counters12 draws/36,944 primitives, not ten visible authored rifles. Accepted snapshots489–500 per client; final accepted ages0.036–0.337 s. All raw counters and trajectories are retained.


# Historical measurements before combined preview

# Network performance evidence

These are Linux cloud CPU and synthetic process measurements. They are not phone, cellular-network, GPU, battery or thermal measurements.

## Privacy development fixture

Command: `./scripts/godot.sh --headless --script res://tests/network_profile.gd`.
Environment: Godot 4.7.2 official, Linux x86_64. Fixed Relay Yard initial ten actors; 120 batches, each projecting/serializing for ten recipients. Observed on the Phase B development tree:

| Metric | Observed |
| --- | ---: |
| Full shared snapshot compressed payload | 670 bytes |
| Shared encoding p50 / p95 | 215 / 301 µs |
| Ten authorized encodings p50 / p95 / max | 2,624 / 5,422 / 7,002 µs |
| Authorized payload mean / max | 685.5 / 691 bytes |
| Static ray queries across 120 batches | 12,000 |

Privacy does not necessarily reduce compressed size: repeated private values compress well in the uniform spawn fixture, while authorization adds a relevance field and separate encodings. These values exclude ENet/IP headers, utilities, combat, moving actors and transmission. They do not establish ten-client tick stability. The harness is checked in so final commits can be measured again.

Two real loopback clients additionally recompressed received snapshot dictionaries (including reliable welcome dictionaries), with reconnect; see `NETWORK_PRIVACY` in the network logs. These are payload-size proxies, not wire-byte measurements. Short probes running alongside other tests are correctness checks, not reliable latency/throughput benchmarks.

## Baseline timing defect

The independent reviewer exercised 600 authoritative 1/60 s steps: only 150 snapshot sends occurred over ten simulated seconds. The intended 20 Hz timer actually sends at 15 Hz because of a positive floating-point residue. Integer simulation-tick scheduling is required in the movement milestone. Do not describe the baseline as measured 20 Hz.

Mobile frame pacing, sustained memory/thermal behavior, actual transport overhead, adverse-network latency/loss and ten-client soak remain unverified here.

## Interpolation matrix

Tested implementation/harness: `167f83c974268f202d84cb99953aa2f4707b2d0d`. Two real headless Godot clients and a dedicated server; 14-second scripted client motion, 60 Hz independent server reference. Each proxy adds half the configured RTT in each direction. The impaired run adds 100 ms RTT, ±20 ms per-direction jitter, 3% random loss and 5% extra-delay reordering. Seed 7301. All six runs exited zero.

| Condition | Render error p95 (m) | Authority work p95 (µs) | Upstream UDP payload total (bytes) | Downstream UDP payload total (bytes) |
| --- | ---: | ---: | ---: | ---: |
| rtt-0 | 0.00703 | 1113 | 95258 | 441616 |
| rtt-50 | 0.00670 | 1308 | 94304 | 438249 |
| rtt-100 | 0.00670 | 1206 | 93158 | 435699 |
| rtt-150 | 0.00670 | 1416 | 91728 | 431507 |
| rtt-200 | 0.00741 | 1137 | 90926 | 429486 |
| impaired | 0.00670 | 1287 | 88312 | 415340 |

Rendered error is evaluated at the intended delayed server timestamp, not at current server time. All runs had median received tick gap 3. UDP counts come from actual forwarded datagrams, include ENet framing, and exclude UDP/IP headers. Totals span startup/teardown as well as gameplay; they are not a normalized steady-state bandwidth claim. Tick work covers the authority function, not all process overhead. Raw summaries, trajectories, CPU/RSS samples and logs: `/workspace/reviews/competitive-interpolation-groundtruth/`.

The earlier `competitive-interpolation-matrix/` run used 20 Hz reference samples and is only a self-consistency check; it is superseded by the 60 Hz ground-truth run. Independent review caught this measurement weakness. Physical devices, end-to-end input latency and ten-client load are not established by these results.

## Opt-in prediction comparison — exact source `d1b94bc`

Frozen checkout `/workspace/sightbreak-movement-qa`, Godot4.7.2 Linux x86_64, headless, 60 Hz physics, max render callbacks60 Hz, real dedicated server and two guest clients, 14-second scripted client fixture. Loopback UDP impairment is added RTT, not measured cellular latency. The repeated runs below use the same committed source. Seed7301; impaired adds100 ms RTT, ±20 ms jitter, 3% loss, 5% reordering. Source and fixture intentionally include corner, crouch and jump motion; no physical-device evidence.

| Condition | First horizontal motion, clients, ms | p95 ack position difference, m | Corrections / hard | Up / down UDP payload B/s, combined |
| --- | --- | --- | --- | --- |
| rtt-0 | 16.7, 16.7 | 0.597 | 49 / 0 | 10144.7 / 27170.6 |
| rtt-50 | 28.9, 26.9 | 0.609 | 50 / 0 | 11043.7 / 27050.8 |
| rtt-100 | 16.7, 24.1 | 0.524 | 42 / 0 | 11499.9 / 26748.1 |
| rtt-150 | 33.3, 33.3 | 0.524 | 45 / 0 | 11364.9 / 26671.9 |
| rtt-200 | 25.1, 33.3 | 0.382 | 129 / 0 | 11315.0 / 26676.6 |
| impaired | 33.3, 25.1 | 0.482 | 135 / 0 | 11091.5 / 26216.5 |
| no-prediction | 229.0, 225.1 | 1.020 | 0 / 0 | 11541.9 / 26843.2 |

First motion is the first sampled horizontal displacement exceeding1cm after the fixture sets movement, including process/frame scheduling. It is **not** touch-to-photon latency. Ack differences compare stored command states with subsequent authority snapshots; collision/contact disagreement and held-input gap steps contribute. The no-prediction column measures delayed authority-only states, not prediction accuracy. Zero hard corrections (>2m) does not establish smoothness; observed ~0.4–0.6m p95 prediction divergence is why independent review requires prediction opt-in.

All seven runs had no process/logged-error failures. Continuous remote interpolation remains enabled. Traffic totals include connection setup and ENet payload overhead, exclude UDP/IP headers, and are divided by each actual whole proxy window (including server drain), not assumed steady-state throughput. Full summary JSONs with durations, packet counts, CPU seconds, peak RSS, tick distributions and render errors are [versioned evidence](../reports/evidence/movement-d1b94bc/). CPU/RSS include this fixture's in-memory measurement arrays; they do not prove long-term leak freedom. Same-host reviewer/test activity can affect wall-time peaks; no mobile GPU or battery conclusion follows.
