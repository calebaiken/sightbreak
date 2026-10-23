# PR21 cache-boundary artifact follow-up

**Source-bound critic review is complete:** outcome-only boundary **PASS**, then
post-unblind capture/API-binding **PASS**. The existing controller files are now
publicly archived against their prior hash commitments. PR21 is ready for **Sol
integration review**, remains draft, and is not claimed integrated.

## Parent-recorded review summaries

These are **summaries of parent-recorded GitHub comments, not full critic
transcripts**. The closure chronology below uses the comments' GitHub UTC timestamps.

- [Outcome-only boundary PASS, comment 6354593942](https://github.com/calebaiken/sightbreak/pull/21#issuecomment-6354593942),
  frozen **2026-10-23 00:42:29 UTC before identity/source access**: the same critic
  checked both 121-row traces, ZIP/CRC/JSON integrity, every insertion's arithmetic,
  the 120→121 boundary, retained IDs2–121, original anchor, 3.75m total drift,
  0.03125m previous delta and all legacy parity. The raw insertion-history gap is
  closed; M's absent helper is N/A.
- [Post-unblind capture/API-binding PASS, comment 6354660494](https://github.com/calebaiken/sightbreak/pull/21#issuecomment-6354660494),
  recorded **2026-10-23 00:47:32 UTC after the frozen outcome PASS**: the same critic
  opened the existing controller/source records and verified M→frozen701 and
  T→capture workload `b4b3db04`, shipping content `0fbce120`. ZIP/captured/published
  trace bytes agree, as do native log hashes, exit0 and 242/484 checks. Three
  workload-file hashes match Git. The fixture actually invokes `predict` and
  `reconcile` and reads helper counts/IDs/samples rather than exporting expected
  formulas as outcomes. The critic reconstructed all **124 baseline / 125
  candidate** shipping-manifest entries, accounted for LF→CRLF representation,
  and checked the recorded before/after identity checks. No blocking discrepancy.
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
it. Identity-bearing commands and the shuffled mapping were withheld in the
external `controller/` directory until the same critic froze the outcome-only
verdict. They were inspected afterwards and are now archived under
[`ack-cache-boundary-v3/controller/`](ack-cache-boundary-v3/controller/README.md).
PR21 remains draft; prediction default-off, protocol6 and live rewind off remain
in force.

## Captured result

The workload was committed and pushed **before capture** at
`b4b3db044fc762fbb5c9eb69da8713b316fdb496`, directly after parent `6d2b38df`.
The first capture completed both short serial native invocations successfully;
the subsequent server restart did not require repeating them.

| Insertion | Observed count | Retained size | Evictions | Retained IDs | Original anchor | Drift from original anchor |
| --- | ---: | ---: | ---: | --- | --- | ---: |
| 1 | 1 | 1 | 0 | 1 | `[3, 0.0625, -2]` | 0 m |
| 120 | 120 | 120 | 0 | 1–120 | `[3, 0.0625, -2]` | 3.71875 m |
| 121 | 121 | 120 | 1 | 2–121 | `[3, 0.0625, -2]` | **3.75 m** |

The raw trace contains **every insertion**, not just these three boundary rows.
At insertion121 the received/latest position is `[6.75, 0.0625, -2]`, the oldest
retained position is `[3.03125, 0.0625, -2]`, and the previous-snapshot delta is
**0.03125 m**. Both oldest and latest retained samples still reference the original
anchor. Exact arithmetic checks pass; no tolerance or rounding hides a discrepancy.

All **121 legacy rows compare exactly** between frozen701 and the unchanged
diagnostic runtime. In particular, the old error series remains `[0.5]` after
every insertion; history stays empty after ACK1; positions, velocities, sequence,
correction records/counts, visual offsets and combat-state controls match.
Baseline cache assertions are **N/A because the helper is absent**, not a new
baseline regression or failed old gate.

Native assertions passed: baseline **242**, diagnostic runtime **484**, both with
zero failures, zero exit codes and no script/resource-leak errors in captured
logs. Assertion count is not the improvement metric: the added artifact supplies
the missing raw evidence for an already reviewed runtime boundary. The previous
six-condition campaign and maintained gates were not rerun.

### Exact provenance

| Item | SHA256 / revision |
| --- | --- |
| Frozen external workload | `b4b3db044fc762fbb5c9eb69da8713b316fdb496` |
| Original raw evidence/report | `d5c738d367f3ba80f3cfc679e104a009d0a72183` |
| Native fixture SHA256 | `33ea6a44b45120ad11baa8ee46bad31dcca9b4a3fc7ae89a2419a7795deb4518` |
| Driver SHA256 | `a179632642e80dd8ac2e68155bef9723aa0f63398308531f36b10d59ec616e31` |
| Shared slice-local capture utility SHA256 | `95a72a5125ff59619fadf8801c665a000a36895800d8424a458852bed36c60d5` |
| Official Godot 4.7.2 binary SHA256 | `ab1824f85bfd8e0e4128182c000c4003a3e042245b2967848d089b2a04b22424` |
| Neutral trace ZIP SHA256 | `70a15c1f330c7e9e51bf50fc52673243dd3cbe62dd030acdc60081eba6443517` |

The capture records the driver's cached-shipping comparison against exact Git
archives before running, unchanged-shipping check afterwards, and candidate
comparison against `0fbce120`. Native fixture and driver hashes match their frozen
Git blobs. The post-unblind critic reviewed this capture/API chain.
[Raw traces, logs, source receipt and audit](ack-cache-boundary-v3/README.md).

### Frozen review chronology and controller release

1. Workload `b4b3db04` was frozen before capture. Evidence `d5c738d3` published the
   trace packet and `publication-audit.json` commitments while withholding the key.
2. Outcome-only **PASS** was publicly frozen at **00:42:29 UTC**, before identity
   access. The neutral packet was the only review input at this stage.
3. The same critic then read the existing controller/source records. Capture/API
   provenance **PASS** was publicly recorded at **00:47:32 UTC**. The parent
   comments explicitly attest to this ordering; these are not full transcripts.
4. This docs/evidence-only closure copies the **exact existing** controller files
   into Git, without normalization, and verifies them against the commitments
   already committed at `d5c738d3`. It performs no new capture or test run.

| Released label | Captured source revision | Shipping runtime reference |
| --- | --- | --- |
| M | `701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd` | `701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd` |
| T | `b4b3db044fc762fbb5c9eb69da8713b316fdb496` | `0fbce120d8c17db58596d280f7d8401ab2aa0937` |

Both sources used the same frozen external workload `b4b3db04`. The existing
imported stages and full native command lines are retained verbatim in the capture.

| Exact released file | Previously committed SHA256 |
| --- | --- |
| [controller/mapping.json](ack-cache-boundary-v3/controller/mapping.json) | `bb9e66d695b9d079fc5b55c99ba985aee4133052e55245b1de0315aeca7483b5` |
| [controller/capture.json](ack-cache-boundary-v3/controller/capture.json) | `68aefbc9a5b3f0d397078b144f5e40993fdbe2e183a8154dcb1eecb488e393b2` |

[Release receipt](ack-cache-boundary-v3/controller/release-receipt.json) binds the
archive to the prior commitment blob and both public verdict anchors. Scoped
`-text` attributes preserve copied bytes; [checksums](ack-cache-boundary-v3/checksums.json)
bind the released files. The initial TIE, earlier R win and all original neutral
packet hashes remain distinct and unchanged.

### Provenance limits and integration status

**Machine execution and historical filesystem measurements remain author-run
attestations, not authenticated process attestation.** Byte/source/API binding
review supports the recorded capture chain; it does not establish independently
authenticated historical process execution. The window trace isolates one eviction
boundary with empty replay history after ACK1, and observes reconciliations rather
than coalesced wire packets. It does not establish gameplay accuracy, consumption
time, performance, ENet behavior or prediction activation.

The source-bound review task is complete. Shipping stays `0fbce120`, the measured
workload stays `b4b3db04`, and original evidence stays `d5c738d3`. PR21 is **ready for
Sol integration review**, not integrated. Draft/default-off/protocol6/rewind-off
remain in force.
