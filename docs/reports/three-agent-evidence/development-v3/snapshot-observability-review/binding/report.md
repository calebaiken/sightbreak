# Post-freeze source/capture binding review

## Recommendation

**Accept the source/hash binding for the narrow additive-observability result, subject to the unsigned historical-execution and reconciliation/coalescing limits below.** Sample-T maps to the candidate, whose measured production shipping sources match shipping revision `0fbce120d8c17db58596d280f7d8401ab2aa0937` under the explicitly demonstrated newline transformations. Sample-M maps to the V2 baseline. The prior diagnostic-information win / captured-legacy-output tie is unchanged.

This is a source-level and artifact-level binding pass, **not independent authentication that the historical engine actually loaded those files**, a gameplay-accuracy result, permission to enable prediction, or release/integration approval. The existing default-off prediction and non-rewound live-shot paths remain unchanged.

The original outcome-only review at `sol-snapshot-neutral-verdict-20261023T005224059323Z` is left completely unchanged. Its report, machine judgments, ledger, freeze receipt, and all 20 ledger-covered artifacts were hash-verified before this review's conclusion and are rechecked at finalization. Its recorded freeze instant remains `2026-10-23T00:58:57.663009+00:00`. No identity material was added to that directory.

## Pins and independently verified commitments

| Role | Exact Git revision / tree |
| --- | --- |
| Docs closure | `37924d1531029b7429ee9289a266a497388001b4` |
| Original outcome packet / controller commitments | `d5c738d367f3ba80f3cfc679e104a009d0a72183` |
| Measured harness | `b4b3db044fc762fbb5c9eb69da8713b316fdb496` |
| Shipping candidate | `0fbce120d8c17db58596d280f7d8401ab2aa0937` |
| V2 baseline | `701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd` |
| Harness, shipping, and closure `game/scripts` tree | `3111af5423d229b9b04b958de9588c4ab537c1ee` |

The released controller files were read directly from the closure's Git blobs:

- `controller/mapping.json`: 60 bytes, SHA-256 `bb9e66d695b9d079fc5b55c99ba985aee4133052e55245b1de0315aeca7483b5`.
- `controller/capture.json`: 31,031 bytes, SHA-256 `68aefbc9a5b3f0d397078b144f5e40993fdbe2e183a8154dcb1eecb488e393b2`.
- Both exactly match the commitments in the **original** `publication-audit.json`, not just the later release receipt. That original commitment blob has SHA-256 `590976fd2abe89cd12e14572e94d5183c4f91fd26aab2239590e4e2a975926ce` and is unchanged at the closure.
- The controller files are absent from the original evidence tree, as expected for withheld keys. The three original-path `cat-file` attempts exited 128 with their exact errors retained; they are expected absence observations, not binding failures.
- Mapping is exactly `sample-M -> baseline`, `sample-T -> candidate`. Capture run roles, source revisions, and trace hashes agree with that mapping.
- Both Git ZIP blobs, at the original commit and the closure, are byte-identical to the external ZIP actually reviewed before unblinding: SHA-256 `70a15c1f330c7e9e51bf50fc52673243dd3cbe62dd030acdc60081eba6443517`. Every member also matches the original review's untouched raw member capture. The two payloads' independently computed Git blob IDs match the adjacent trace blobs in both evidence trees.
- The relevant original and closure checksum entries match the actual bytes. Checksum scope is explicit in `auditraw/04-binding-result.json`; author audit content, native log content, controller README, and other unneeded receipts were not opened. Capture log hashes agree with the committed checksum strings, but this is not an independent log-content or execution validation.

The closure introduces only README/checksum changes and the controller release within the scoped evidence directory. `game`, `scripts`, and `server` have **no source delta from the measured harness to the closure**. No branch-tip or mutable worktree source was substituted for the supplied revisions.

The owner's README/release receipt contains other parent-recorded review summaries. Those conclusions were not used as proof, their links were not followed, and their review chronology is not attributed to this independent Sol freeze.

## Actual probe and exporter paths

The three original harness source commitments are exact raw Git SHA-256 matches:

| Source | SHA-256 |
| --- | --- |
| `game/tests/ack_cache_boundary_probe.gd` | `33ea6a44b45120ad11baa8ee46bad31dcca9b4a3fc7ae89a2419a7795deb4518` |
| `scripts/measure_ack_cache_boundary.py` | `a179632642e80dd8ac2e68155bef9723aa0f63398308531f36b10d59ec616e31` |
| `scripts/measure_prediction_timeline.py` | `95a72a5125ff59619fadf8801c665a000a36895800d8424a458852bed36c60d5` |

Source citations below refer to the captured Git blobs under `objects/harness/` and `objects/shipping/`, not working-directory files.

### Probe invokes production objects; observations are not substituted expectations

At harness probe lines 39–59, the probe creates `SBActor` and `SBMovementPrediction`, resets the actor at anchor plus 0.5 m, and calls production `predict(..., EPOCH, false)` to seed a pending command. It then calls production `actor.apply_snapshot(...)` and `predictor.reconcile(...)` for each input.

Shipping `movement_prediction.gd` lines 26–44 sanitizes that real command with `SBInputStream.sanitize`, assigns sequence 1, and appends its recorded actor position even though the seed call disables movement advancement. `input_stream.gd` lines 43–59 accepts this finite zero-move/zero-look command. The first ACK therefore finds the pending sequence-1 record; reconciliation lines 63–69 compute its position error and remove it. `actor.gd` lines 574–585 and 1232–1238 establish the reset/current-position behavior used by this fixture.

The subsequent probe loop has **no intervening await or physics step**. It is 121 direct reconciliations, not 121 independently timed authority snapshots, and its supplied positions/ACK/epoch are deliberate fixture inputs. It does not exercise an actual server command-consumption path or leave surviving commands to replay.

Probe lines 64–83 read actual helper counters, the actual `samples` ID list, deep-copied oldest/latest sample dictionaries, actor state, and actual legacy predictor fields. `encode` recursively converts vectors/arrays/dictionaries without replacing observed values with expected geometry. Assertions at lines 60–75 compare actual values with expectations, but do not assign the diagnostic/legacy results. Missing helper output is exported as `null` / `not_available_not_applicable`.

The predictor preloads the shipping helper and calls `snapshot_diagnostics.observe(...)` at reconciliation entry (shipping `movement_prediction.gd` lines 5–6, 52–54). The production script tree is identical between harness and shipping; the probe is not invoking a separate Python model or a test-only reconciliation implementation.

### Exporter preserves emitted trace bytes

`measure_ack_cache_boundary.py` lines 89–127 checks the selected Git shipping file hashes against the staged shipping hashes, installs the committed fixture only under `tests/`, records the exact engine invocation, records pre/post shipping equality, and hashes the emitted JSON. Lines 134–147 add those emitted files to the ZIP with `packet.write`, without reserializing their rows.

The driver's expectation-derived `audit()` function (lines 28–71) only asserts against loaded rows and returns a **separate** audit summary. It does not synthesize or overwrite either trace. Header and input fields remain fixture-generated, but the diagnostic/legacy outcome fields come from the objects being exercised.

The helper functions imported from `measure_prediction_timeline.py` were read, not executed. `shipping()` excludes `.godot` and `tests`; `execute()` records a return code and a decoded stdout-plus-stderr log. Its log is not a signed, raw multiplexed engine stream. No reviewed exporter, probe, or game code was imported or run in this review.

## Shipping bytes: exact comparisons and only demonstrated newline conversion

Every reported shipping path is accounted for against the corresponding Git tree, including assets and project files. The candidate's complete non-test `game/` blob map is identical to the shipping revision's map. Git blob IDs and raw byte lengths were independently recomputed for all captured objects.

| Source | Reported files | Raw Git SHA matches | Exact LF→CRLF-only matches | Unexplained |
| --- | ---: | ---: | ---: | ---: |
| V2 baseline | 124 | 21 | 103 | 0 |
| Candidate / shipping | 125 | 21 | 104 | 0 |

For the newline-only cases, the raw blob must be strict UTF-8, contain no NUL and **no CR**, and `SHA256(raw.replace(b'\n', b'\r\n'))` must exactly equal the reported measured hash. No whitespace, formatting, token, encoding, or semantic normalization is accepted. The historical filesystem measurement is still the author's attestation; the independent fact is the exact match between the committed digest and this explicitly reconstructed byte sequence.

Examples:

| File | Raw Git SHA-256 | Reported measured SHA-256 (exact CRLF expansion) |
| --- | --- | --- |
| V2 `movement_prediction.gd` | `3d3da91d04e4430d0d2f51675caf00b33596eecb9d187672eb0a8a793d4ceee3` | `f3a7f92570a6a57574f5af8bdecaf6f6ddccd39d72227d80f3424e94b8bd6d8f` |
| Candidate `movement_prediction.gd` | `d63fa55a3b9bf89c34e058d294e61bd82c57135515bdff7da7322e66bebbace4` | `9cc042de2c1f43bc00b9e878e6cc3bda475b251fb366545785a2039f91ccb565` |
| Candidate helper | `9a5c90b3dd26885ba8fbe58d712006e641cf069abf7f8278720a6b7a9459951f` | `83459fa8e3cf977d30ab7b8af65b383c510a0f42060993c284038c1d52fba346` |

`shipping-source-hashes.json` contains all 249 per-source path comparisons, Git blob IDs, raw/reconstructed/reported hashes, newline counts, and raw-object locations. There are 126 unique source blobs totaling 9,096,541 bytes.

## Production semantics and preserved behavior

### Real 120-entry retention, epoch scope, and first-observed anchors

The shipping helper's `MAX_SAMPLES` is actually **120** (line 4), closing the original ZIP-only capacity-declaration gap at source level. It appends a dictionary and then pops the oldest if size exceeds the limit (lines 54–62). Thus completed calls retain at most 120 samples; the append can temporarily make 121. This is not a measured allocation-peak or cost bound.

`clear()` resets epoch, counters, samples, ACK, and both anchor vectors (lines 16–25). `begin_epoch()` rejects negative/older epochs and clears history on a new epoch (27–34). `observe()` rejects invalid ACK/position values and regressed ACKs; same-ACK samples share `_first_position`, while a changed ACK starts a new first-observed anchor (36–50). Eviction never rebases that anchor. Previous-snapshot delta is computed only for a repeated ACK; a new ACK receives `null` (54–64). These are source semantics, not newly executed transition tests.

### Important coverage limit: reconciled observations, not every accepted wire snapshot

`match.gd` validates a received snapshot and pushes it through the ordered snapshot buffer (1095–1100). For the local actor, each accepted state **replaces a single `_pending_reconciliation` dictionary** (1137–1142). The next client physics tick applies/reconciles that one pending state and clears the slot (206–211, 771–784). Only that reconciliation calls the helper.

Consequently, several accepted local wire snapshots before one physics tick can collapse to one diagnostic observation. The first reconciled position can differ from the first accepted wire position for an ACK. The helper does not provide accepted-wire-snapshot coverage, arrival timestamps, packet-level completeness, or a server consumption-time anchor.

ACK provenance further supports this distinction: `state_privacy.gd` lines 156–159 copies `_last_input_sequence` into `move_ack`; `match.gd` lines 240–267 advances the last sequence only when a command is popped, while held controls may continue stepping during gaps. Same ACK can therefore accompany changing authoritative positions. The fixed-ACK fixture is diagnostic geometry, not proof of pure replay error or zero authority motion.

### Legacy fields, defaults, protocol, and live shots

Only two non-test shipping paths differ from V2: the added helper and `movement_prediction.gd`. Removing **only the five exact added diagnostic lines** from the latter restores the complete V2 file byte-for-byte: preload, helper instance, reset clear, predict epoch notification, and reconcile observation. The original pending/error/correction/replay/smoothing code, packet fields, and thresholds are unchanged. The frozen trace's exact captured legacy parity remains the runtime-outcome evidence for this narrow fixture.

All other shipping files are identical Git blobs, including match, actor, input stream, snapshot schema/buffer, privacy, and movement step. `server/` also has the same tree ID at V2 and shipping.

- `match.gd:13` keeps protocol **6**.
- `match.gd:61,104–106` keeps prediction **default false**, enabled only through the existing option/command-line opt-in.
- **Default-off prediction does not disable the new helper.** Its observation call precedes the predictor's `if not enabled` return. Retention is bounded, but the added CPU/allocation cost, including with prediction off, has not been measured.
- Hit-history recording remains opt-in false (`match.gd:277–279`). A full shipping-GDScript reference scan finds only creation and optional recording for `_hit_history`; it does not feed live shots. `actor.gd:724–785` still traces current world/actor volumes. This change adds no live rewind or lag compensation.

## Remaining limits and audit accounting

The code and hashes support binding to a plausible, production-API-based capture procedure. They cannot prove the historical process was genuine, that the recorded engine version/hash was actually used, that a class cache resolved the intended classes, that cached/compiled resources matched the loaded scripts, or that the reported pre/post staged hashes were honestly measured. Engine and class-cache hashes in the capture are unsigned declarations; neither the engine nor staging/cache files were inspected or launched. No claim of authenticated process attestation is made.

The source shows how a genuine pending command is seeded, improving on the original ZIP-only view; **the recorded post-insertion pending histories remain empty**, and nonempty surviving replay/server consumption is still untested. Wider workloads, repeated wraps, invalid-input behavior, epoch/ACK transitions at runtime, memory allocation peak, performance, transport/coalescing outcomes, physics-time behavior, and gunplay remain unverified.

Final independent binding checks: **830 passed, zero failures**. The first local verifier attempt had one false positive because a substring count for `_hit_history` also counted the option key `record_hit_history`. The corrected exact-identifier check passes; the initial verifier, failed result/exit, and correction note are preserved in `auditraw/04-first-attempt-*` and `04-reviewer-test-correction.json`. No reviewed source or runtime was edited to obtain the pass.

All repository content was read through recorded `ls-tree`, `cat-file`, `rev-parse`, or Git-object-to-Git-object diff commands. Exact argv, stdout bytes, stderr bytes, exit codes, and hashes are retained per command; external diff/textconv hooks were disabled. The only execution was approved isolated CPython 3.13.15 and read-only Git commands. No Godot/native workload, DB, network/GitHub call, service, fetch, runtime edit, worktree/index edit, or commit occurred.

The new report, machine judgments, all source/object hashes, command index, audit records, old-freeze preservation check, and final UTC marker are bound by the new `SHA256-LEDGER.json` and `FINAL-RECEIPT.json`. This is a separate post-freeze record; it does not modify or supersede the outcome-only freeze.
