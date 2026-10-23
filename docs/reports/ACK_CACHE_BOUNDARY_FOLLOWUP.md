# PR21 cache-boundary artifact follow-up

## Parent-recorded review summaries

These are **summaries of parent-recorded GitHub comments, not full critic
transcripts**. Refreshed on 2026-10-22 after the server restart.

- [Outcome-only verdict, comment 6276374296](https://github.com/calebaiken/sightbreak/pull/21#issuecomment-6276374296):
  **sample-R WINS the diagnostic bar; C loses coverage.** The critic verified the
  packet checksum, 1,224/1,224 observations, 20 formerly unscored held observations,
  reconstructed snapshot-relative drift, legacy parity, maintained gates, metric
  windows, transport balance, lifecycle controls and ACK600/empty-queue recovery.
  The remaining artifact gap was that the 120-cache/481-observation bound and
  anchor-after-eviction claim had terminal receipts rather than raw insertion history.
- [Separate source verdict, comment 6276233073](https://github.com/calebaiken/sightbreak/pull/21#issuecomment-6276233073):
  **PASS for bounded observability** on runtime `0fbce120` versus frozen701.
  The helper plus five predictor additions preserve legacy execution and bounded
  local state. Coverage is of reconciled observations: accepted A→B→A snapshots
  can coalesce before a physics callback, leaving B unobserved. This limit remains.
- [Initial fallback verdict, comment 6275674040](https://github.com/calebaiken/sightbreak/pull/21#issuecomment-6275674040):
  **TIE** for the original identical J/Q packet. Its evidence and the later winning
  packet at `6d2b38dffe9c591d6cec6fc34b92bbc8d06fe008` remain unchanged.

## Narrow workload fixed before capture

Own branch `astra/prediction-reconciliation-v3` continues exact parent
`6d2b38dffe9c591d6cec6fc34b92bbc8d06fe008`. Shipping runtime stays byte-identical
to `0fbce120d8c17db58596d280f7d8401ab2aa0937`. The comparator is frozen
`701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd`.

One external native fixture performs **121 direct reconciliations**, ACK1/epoch7,
at positions `P(n) = [3 + (n-1)/32, 0.0625, -2]` metres, for `n=1..121`.
All offsets are exactly representable. A real pending command seeded at
`[3.5, 0.0625, -2]` supplies one nonzero old error (0.5 m) on the first ACK.
After that ACK, history is empty; enabled reconciliation still executes existing
correction bookkeeping. Actor positions/velocities, errors, history, sequence,
corrections, visual offsets and combat-state controls are captured after every call.

Each available diagnostic capture contains the actual observed count, retained size,
eviction/repeat/ignored counts, complete retained ordinal list, and oldest/latest
samples (including position, first anchor and both drift values). At insertion121
the required result is **120 retained, one evicted, IDs2..121, original anchor
`[3, 0.0625, -2]`, total drift3.75m, previous-snapshot delta0.03125m**. Baseline
helper absence is N/A; all121 legacy rows must compare exactly between sources.

This isolates one eviction boundary. It is not a new simulation, transport,
gameplay-accuracy, performance or longer-duration bound claim. The parent campaign
and unchanged regression suites are not part of this focused run.

## Capture and review procedure

Freeze this workload before capture. The driver verifies cached shipping bytes
against exact Git archives and the unchanged runtime, overlays the same external
fixture, then captures/waits for one official Godot process at a time. It uses
previously imported own staging caches; no editor import or shared harness runs.

```powershell
python scripts/measure_ack_cache_boundary.py `
  --baseline-game C:\Users\blith\AppData\Local\Temp\opencode\ack-observability-stages-r3\sample-C\game `
  --candidate-game C:\Users\blith\AppData\Local\Temp\opencode\ack-observability-stages-r3\sample-R\game `
  --godot C:\Users\blith\AppData\Local\Temp\opencode\godot\Godot_v4.7.2-stable_win64.exe `
  --out C:\Users\blith\AppData\Local\Temp\opencode\ack-cache-boundary-capture-new
```

The new neutral packet contains **only two raw traces and method instructions**.
Raw logs, exact source/workload hashes and author-run audit are published outside
it. Identity-bearing capture commands and the newly shuffled mapping remain in
the external `controller/` directory until the same critic freezes its follow-up
verdict. No critic is launched by this worker. PR21 remains draft; prediction
default-off, protocol6 and live rewind off remain in force.
