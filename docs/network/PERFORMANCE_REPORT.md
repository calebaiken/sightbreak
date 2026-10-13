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
