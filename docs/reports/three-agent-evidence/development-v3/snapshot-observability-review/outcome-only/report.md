# Independent outcome-only verdict: same-ACK cache boundary

## Outcome

**Narrow diagnostic-information win: sample-T. Exact captured legacy/nondiagnostic-output tie: sample-M and sample-T. No release approval or gameplay-accuracy conclusion.**

Sample-T satisfies the supplied 120-entry retention/first-eviction bar in every supplied row. Sample-M has no helper output: its cache-boundary correctness is **N/A, not a failure**. It loses only the availability-of-diagnostic-information comparison. Neither neutral label is mapped to a source identity.

This is a fresh review of the supplied ZIP bytes, not acceptance of the producer's `checks`/`failures` summaries. The independent verifier passed **8,367 checks, zero failures**, with exit 0. All 242 supplied JSON rows were examined programmatically, not just selected endpoints.

## Evidence pin and isolation

- Input actually read: `C:\Users\blith\AppData\Local\Temp\opencode\ack-cache-boundary-neutral-r1\blind-traces.zip` (11,660 bytes).
- SHA-256: `70a15c1f330c7e9e51bf50fc52673243dd3cbe62dd030acdc60081eba6443517`, exactly the requested digest.
- The requester associates these bytes with `docs/reports/ack-cache-boundary-v3/blind-traces.zip` at commit `d5c738d367f3ba80f3cfc679e104a009d0a72183`. **That repository/commit association was not independently inspected.** The verified pin is the actual external ZIP digest.
- Three ZIP members, unique names, successful `testzip()`, independently recomputed CRC-32 and uncompressed sizes. Both JSON documents decode strictly, with no duplicate object keys or nonfinite/nonstandard numeric constants; each has 121 rows, ordinals exactly 1 through 121.
- Actual interpreter: CPython **3.13.15**, approved absolute executable, isolated `-I` mode; standard library only, serial offline work. No engine, DB, network, service, GitHub, git, source, or index operation.
- Input-content reads were ZIP-only; reviewer-created artifacts were also read for verification. An initial listing of the approved input container exposed only `blind-traces.zip`. One reviewer-created shell stdout file was read to recover the new output-directory name. No other external reports, commands, mappings, parent/branch contents, comments, or identity metadata were inspected.
- The key/map remains unopened. **Unopened identity material is not a claim of perfect blinding:** helper availability makes the behavioral variants distinguishable, and may permit inference by someone already familiar with the implementation. No such source-identity inference is asserted here.

## Verified observations

The full raw per-insertion rows are present in `sample-M.json` and `sample-T.json`, not merely final counters. Untouched uncompressed member bytes are captured as `auditraw/entry-001.bin` and `auditraw/entry-002.bin`; the member manifest records their names and hashes. JSON row number *n* means ordinal *n* (the verifier's labels are 1-based).

### Inputs and semantic anchors

Across both traces, all 121 inputs exactly match:

`P(n) = [3 + (n - 1)/32, 0.0625, -2]`, for `n = 1..121`.

Every adjacent spatial step is exactly `1/32 = 0.03125 m`. ACK is fixed at 1 and epoch at 7. These are **observation ordinals and spatial separations, not elapsed-time samples or command-consumption events**.

For every available latest and oldest diagnostic sample, the verifier independently reconstructed its position, ordinal, ACK/epoch, original anchor, first-observation drift, prior-observation delta, repeat flag, and prediction-enabled flag. It additionally compared every oldest sample with the matching historical latest sample.

- Original anchor remains `[3, 0.0625, -2]`, explicitly labelled `first_observed_snapshot_not_consumption`.
- First sample: zero first-anchor drift, previous delta `null`, repeated ACK `false`.
- Samples 2 through 121: first-anchor drift `(n-1)/32`, previous-observation delta `0.03125`, repeated ACK `true`.
- Prediction is enabled throughout; the traces do not test prediction-disabled behavior.

### Capacity and eviction

**120 is the supplied review capacity and the ZIP README's boundary expectation.** There is no explicit cache-capacity field in these JSON documents; no actual API capacity declaration or source constant is independently verified.

For every available row *n*, the full raw retained-ID list—not just its endpoints—equals `max(1,n-119)..n`, in order, with no duplicate/gap. Observed count is *n*, retained size `min(n,120)`, eviction count `max(n-120,0)`, repeats `n-1`, ignored 0, and retained plus evicted equals observed. Consecutive windows add exactly the new ordinal and remove only the expected old ordinal.

| Insertion | Observed | Retained | Evicted | Retained IDs | Latest first-anchor drift | Previous delta |
| ---: | ---: | ---: | ---: | --- | ---: | ---: |
| 1 | 1 | 1 | 0 | 1 | 0 | null |
| 2 | 2 | 2 | 0 | 1..2 | 0.03125 | 0.03125 |
| 119 | 119 | 119 | 0 | 1..119 | 3.6875 | 0.03125 |
| 120 | 120 | 120 | 0 | 1..120 | 3.71875 | 0.03125 |
| 121 | 121 | 120 | 1 | 2..121 | 3.75 | 0.03125 |

At insertion 121, exactly ordinal 1 leaves the retained window. Oldest retained sample is ordinal 2 at `[3.03125, 0.0625, -2]`; latest is ordinal 121 at `[6.75, 0.0625, -2]`. Both still carry the original first-observation anchor. Latest-to-original distance is **3.75 m**; latest-to-oldest-retained distance would instead be **3.71875 m**. The recorded first-anchor drift therefore does not silently rebase to the sliding-window oldest observation. The recorded previous delta remains **0.03125 m**, not either cumulative distance.

No early eviction, off-by-one window, missing ID, or first-anchor reset appears in the supplied available-helper rows. This is evidence for the one tested first-eviction boundary, not proof of arbitrary future insertions or internal memory allocation bounds.

### Exact legacy and nondiagnostic parity

All **121/121** complete `legacy` objects match with strict JSON value types and zero numeric tolerance. For each row, every top-level field other than `diagnostic` also matches (**121/121** projections). Additionally, the original UTF-8 value spans for `ack`, `epoch`, `insertion`, `legacy`, and `received_position` are byte-for-byte identical between traces; the complete legacy-object serialization itself matches. This is not a claim that the whole documents match: diagnostics, diagnostic status, and producer check counts differ.

The 15 captured legacy fields include current/previous position, velocity, visual offset, pending history, sequence/epoch, correction counts, error samples, large-correction records, and health/ammo/crouch/jump state. On every row:

- Error samples remain exactly `[0.5]`, and the single recorded large-correction object remains unchanged. Its original previous position `[3.5, 0.0625, -2]` is exactly 0.5 m from authority `[3, 0.0625, -2]`.
- The legacy `corrections` counter advances from 1 through 121; `hard_corrections` stays zero. Unchanged error history is **not** absence of reconciliation processing.
- Pending history is always `[]`, sequence is 1, and positions track the supplied lattice. The README's assertion about a real pre-first-row pending command is not independently established by a pre-consumption/replay trace.
- Smoothing/visual-offset values match exactly between traces, but this comparison does not validate an independent physical/smoothing model. Binary-exact arithmetic applies to the chosen position/diagnostic lattice, not to an idealized claim that exported visual smoothing values equal mathematical 0.35 exactly.

Sample-M's diagnostic is `null` on all 121 rows, consistent with `not_available_not_applicable`. It supplies no capacity, eviction, or anchor assertions to fail; those checks are N/A for M. Its captured legacy behavior still participates fully in the parity tie.

## Criticism and explicit gaps

1. **Actual API/source binding and provenance remain pending.** Digest/CRC/JSON/arithmetic establish which bytes were reviewed and their internal consistency, not that they were emitted by a particular runtime/API, source revision, genuine pending-command replay, or engine build. The in-ZIP engine/version strings and producer pass counts are unverified self-reports. No actual capture was rerun.
2. **Empty recorded replay history is a material limitation.** Every post-insertion `pending` list is empty and the recorded correction's pending count is zero. No surviving-command replay, multi-command ordering, nonempty history, or ACK-to-consumption mapping is tested. The nonzero initial legacy error avoids an all-zero comparison but does not close that gap.
3. **Fixed ACK/epoch only.** No ACK advancement/regression, epoch transition/reset, repeated-ACK run break, invalid snapshot, multi-client history, prediction-disabled path, or helper runtime failure is exercised. Absence in M is not evidence of failure-handling correctness.
4. **Only one first eviction.** No insertion 122 or later, second wrap, long run, mixed workloads, capacity changes, repeated key reuse, concurrent activity, or reset-after-eviction coverage. Reported retained count does not bound allocation peak, temporary overshoot, object retention, bytes used, CPU cost, or memory growth elsewhere.
5. **No temporal/transport conclusion.** There are no arrival timestamps or consumption timestamps; no transport, packet loss/reordering, snapshot coalescing, snapshot scheduling, latency, physics-time, host/client, or server-motion accuracy conclusion follows. A spatial 1/32 m step is not a measured time step. Same ACK does not imply no changing authoritative position.
6. **No gunplay/gameplay accuracy or release approval.** Additional drift observability is not reduced prediction error, better hit registration, correct weapon/ammo behavior in play, or movement/physics correctness. Health/ammo equality in this fixture is not a gameplay test.
7. **Parity is bounded to what was captured.** All captured nondiagnostic row fields agree; unlogged state, side effects, allocation behavior, and all wider workloads remain unverified. CRC integrity is not a signature of trustworthy capture provenance.

## Frozen deliverables

- `verify_zip.py`: executable independent verifier, no engine or source dependencies.
- `auditraw/01-zip-audit.json`, `02-structure.json`, `03-independent-result.json`, `03-independent-checks.jsonl`, untouched member captures, and stage exit receipts.
- `machine-judgments.json`: neutral win/tie/N/A and gap decisions.
- `FROZENUTC.txt`: actual UTC freeze instant; no identity/source inspection occurred before it or is authorized by this report.
- `SHA256-LEDGER.json`: hashes of the input ZIP and all included output artifacts; excludes only itself and its receipt to avoid self-reference.
- `FREEZE-RECEIPT.json`: binds the ledger, report, machine judgments, and UTC marker; its own SHA-256 is returned to the requesting session.

The outcome was written before freezing, with the source/key still unopened. Freeze means a timestamped content-hash snapshot, not a filesystem write lock, cryptographic attestation, or permission to promote a release.
