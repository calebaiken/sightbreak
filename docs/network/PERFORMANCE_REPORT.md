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
