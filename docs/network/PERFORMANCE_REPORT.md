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

Frozen checkout `/workspace/sightbreak-movement-qa`, Godot4.7.2 Linux x86_64, headless, 60Hz physics, max render callbacks60Hz, real dedicated server and two guest clients, 14-second scripted client fixture. Loopback UDP impairment is added RTT, not measured cellular latency. The repeated runs below use the same committed source. Seed7301; impaired adds100ms RTT, ±20ms jitter, 3% loss, 5% reordering. Source and fixture intentionally include corner, crouch and jump motion; no physical-device evidence.

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
