# Independent offline CI receipt audit — run 39880125007

**Outcome: the exact-source CI run failed. It is not a passed matrix, accepted development candidate, release, or production validation.** Selected successful substeps below are qualified evidence, not substitutes for either failed exported-client flow.

- CI source: `2a026e61cabee3c66334066d45e92eb3ec6c2641` (attempt 1, 2026-10-23).
- Run: <https://github.com/calebaiken/sightbreak/actions/runs/39880125007>.
- Independent audit started 2026-10-24, external directory `C:\Users\blith\AppData\Local\Temp\opencode\sol-ci-receipt-audit-20261024T085929Z`.
- Packet: `docs/reports/three-agent-evidence/development-v3/ci-attempts/run-39880125007/`.
- Full downloaded evidence: `C:\Users\blith\AppData\Local\Temp\opencode\sightbreak-v3-evidence\ci-39880125007`.

## Results and source identity

| Gate | Audit-qualified result |
| --- | --- |
| Download completeness and transport bytes | All three artifact ZIPs match the SHA-256 digests in the retained GitHub artifact metadata. All 2,680 artifact members and 34 run-log members were read completely, CRC-checked and SHA-256-hashed. No duplicate ZIP names found. |
| Frozen source | Independent Git-object calculation reproduces the game tree, both source digests, and all 362 declared validation-source files. Matrix, campaign, native/package verifier and audio restoration receipts agree on that identity and recorded clean boundaries. |
| Maintained matrix | **83 rows: 82 passed, 1 failed**. All row names/order and 81 commands match frozen inventory; all 81 top-level process receipts match their recorded exits, are complete, and report clean POSIX containment. The two final source/resource gates also match their raw JSON. |
| Separate campaign | **12/12 conditions qualify under the frozen harness**, each with ten clients and an 18-second shared measurement. Independently checked 120 client plus 12 server report/log pairs, native summaries, source boundaries, parent process receipts and failure/leak gates. |
| Adversarial audio | **10 baseline groups, 386 checks, zero baseline failures; A5/A6/A7 all caught by expected assertions.** Thirteen contained attempts, five real WAV files and their ten voice/report companions retained. Mutation hash chains and eight restored source snapshots match frozen Git bytes; four tooling hashes also match. |
| Native export verifier | Recorded completed pass: Linux menu/demo, APK metadata/signature output, iOS unsigned-project structure. Five real process receipts/raw logs agree with this limited result. |
| Packaged verifier and actual inner ZIPs | Recorded completed pass for extracted ELF and console-wrapper smoke, with two process receipts. Independently checked **three inner ZIPs, 61 members (58 payloads + three source receipts), all byte counts/hashes/POSIX regular-file modes**, and all five manifest artifact checksums. Uploaded extracted copies match the inner bytes. No executable extracted or run by this audit. |
| Exported network flow | **Failed/incomplete**: hard watchdog, **240.141 s**. Authority fire/reload substep passed, but no completed client/authority clean-exit and final unchanged-export success result. |
| Exported living-player offline flow | **Failed**, worker exit 1, **48.805 s**: actual elimination before the reload check. Not a positive-health OCR false alarm. |

Independent frozen identity (`derived/source-object-audit.json`):

```text
commit                    2a026e61cabee3c66334066d45e92eb3ec6c2641
game tree                 172704d0e82c4e74dfc35f218ab2645fd908f970
game runtime content      7561f44322a7fc35a08e67ba8b3e8dd322f46a45c03ff42e684efa988c0c2407
validation source content 4886bb4fb01b3769b98891c90bf80c28ee865b30f9e489acd6a309d3932b2407
declared validation files 362
```

The algorithms were independently reimplemented over Git blob bytes, not imported from the project: frozen `scripts/godot_process.py:166–206` and `scripts/build_manifest.py:24–48`. The source manifest distinguishes runtime inputs from test/validation inputs and records Git blob IDs and SHA-256. CI clean-before/after is recorded evidence, corroborated by matching independently calculated source bytes, not a new observation of a live runner.

## Matrix failure, including expected rejection logs

The failing row is `matrix-harness-unit`: exit 1, `logged_errors=true`, 4.576 s. Its unedited log reports **18 tests, two errors, one Windows-only skip**:

1. `test_dirty_source_refuses_to_launch_matrix`: `platform.platform()` probes `platform.processor`, whose call to `subprocess.check_output` is intercepted by the test's global mock; the finite `side_effect` iterator exhausts with `StopIteration`.
2. `test_inventory_keeps_existing_rows_and_adds_maintained_python_units`: another `StopIteration` reaches the final `git status` call after the same mocked subprocess surface has been consumed.

Evidence: `raw/artifact-12470739875/builds/v3-matrix/matrix-harness-unit.log`, its `.process.json`, frozen `scripts/test_validate_matrix.py:158–209`, and `scripts/validate_matrix.py:59–62,157`. The raw log, not a later repair or rerun, determines this verdict. This is a harness-unit failure; it does not by itself establish a game-runtime defect, and explaining it does not waive it.

All 83 rows and command/gate checks are enumerated in `derived/matrix-audit.json`. The nested cleanup receipt has `leaked_logs=[]`; an independent scan found no `ObjectDB...leaked` / `Leaked instance` in matrix logs. Two mixed-version server logs contain ENet `ERROR: Condition ...` output in **intentional pre-handshake incompatibility trials**. Frozen `scripts/test_protocol_compat.sh:66–102` expects these combinations not to admit, or to fail with a reason. The eight-combination `protocol/matrix.md` and actual client/server logs agree with those expected rejections. They are retained, not hidden, and are not naïvely reclassified as new runtime defects. The frozen matrix's nested gate specifically checks leaks, not an assertion that every negative-test child contains no `ERROR` text.

## Twelve-condition campaign

`scripts/run_network_campaign.py:21–40,54–62,79–118,126–143` supplies the exact condition inventory, command, source, parent exit, log and failure gates. `scripts/simulate_network.py:89–110,199–221,236–247` launches real Godot children and gates cleanup, exit/log failures and fresh authority; `game/tests/network_simulation_probe.gd:212–242` supplies the child freshness, movement and reconnect assertions. Those source files are frozen copies in this packet.

Every condition has ten clients, port `39000 + 20*index`, seed 7301, guest/account-tickets=false, render-client=-1 and reconnect delay 2 s. Each has one server and ten matching native child reports/logs, a complete clean exit-0 parent containment receipt, empty failure arrays, `shared_stop_reached=true`, equal recorded source-before/source-after, and a final campaign source gate. All final clients are connected, received/accepted at least ten snapshots with ages <750 ms, and moved >0.1 m. Server occupancy never exceeds ten or duplicates actor authority; final ten bindings have input ack >=10 and idle <750 ms. Reconnect restores each client's original actor ID. Prediction-disabled reports prediction off.

| Condition | Impairment beyond base | Max final accepted age | Minimum accepted snapshots |
| --- | --- | ---: | ---: |
| rtt-0 | added RTT 0 ms | 54 ms | 287 |
| rtt-50 | added RTT 50 ms | 38 ms | 330 |
| rtt-100 | added RTT 100 ms | 60 ms | 330 |
| rtt-150 | added RTT 150 ms | 56 ms | 325 |
| rtt-200 | added RTT 200 ms | 58 ms | 344 |
| jitter | RTT 100 ms, jitter 20 ms | 59 ms | 338 |
| loss | RTT 100 ms, loss 3% | 67 ms | 343 |
| reorder | RTT 100 ms, reorder 5% | 56 ms | 329 |
| impaired | RTT 100 ms, jitter 20 ms, loss 3%, reorder 5% | 70 ms | 318 |
| blackout | RTT 100 ms, blackout at 4 s for 2 s | 37 ms | 284 |
| reconnect | impaired + blackout + reconnect at 8 s, delay 2 s | 75 ms | 240 |
| prediction-disabled | RTT 100 ms, prediction disabled | 42 ms | 329 |

Important distinctions:

- Child wall measurements finish at or after 18 s, with stop lateness up to 44 ms; these are not exactly 18.000 s of sampled process lifetime. Proxy windows are about 22.43–23.21 s and explicitly include startup/report drain. Traffic totals are whole-proxy-lifetime payload bytes, not a pure 18-second bandwidth measurement and not full IP/ENet-overhead accounting.
- Godot's serialized large epoch differs from Python's epoch by at most **4.769 microseconds** (decimal serialization precision). All child deltas are preserved in `derived/campaign-audit.json`; numeric/byte-exact epoch identity is not claimed.
- Native child logs identify the engine, role and observed report metrics. Individual Godot PID/exit-code supervisor receipts were **not** retained. The frozen script consumes their exit status after cleanup and rejects failures; this audit independently checks all report assertions/logs and the twelve parent receipts, but cannot reconstruct an unrecorded per-child OS exit table.
- No new performance ceiling is inferred from a fixture with no such threshold. This is headless guest loopback impairment evidence, not a rendered ten-human match, public WAN/cellular trial, or continuous full-match soak.

## Audio: actual catches, captures and source restoration

`--only A5,A6,A7` did not narrow or skip the broad baseline. Raw baseline summaries confirm sequence (92), weapon art (179), audio (29), reload capture (14), cancel capture (11), visibility (15), reduced-motion visibility (15), finish stability (3), light separation (4), contact (24): **386 checks total**. Every baseline attempt has exit 0, one complete passing summary and clean process containment. Commands retain their original scenarios/flags; no threshold was relaxed.

| Control | Exact intentional mutation | Actual detector result |
| --- | --- | --- |
| A5 | reload voice volume changed from `-15 + LEVELS` dB to `-95` dB | exit 1; 14 checks / 6 failures, one for each missing/too-quiet event. All six CSV onsets are -1 and peaks round to zero. The retained mono PCM16 WAV is entirely zero after quantization; float diagnostic peaks are tiny, not claimed literally zero. |
| A6 | remove both weapon-change/pre-seat reload voice stops | exit 1; 11 checks / 1 failure: post-cancel peak **0.01783**, above silence threshold 0.0008, after the original 80 ms mixer allowance. Event sequence itself remains correct. |
| A7 | play an unlogged voice before `actor.start_reload()` | exit 1; 14 checks / 1 failure: early voice peak **0.03063**, above 0.0008. Independent PCM16 mono inspection finds early peak **0.0306101** before the first cue window. Scheduled event checks still pass. |

These `ERROR`/`FAIL` lines are completed expected assertion catches (`push_error` context, exactly one correct summary, exit 1), not crashes, leaks, or an accidental native error being accepted. All three containment receipts have no errors. All five WAVs parse as mono PCM16, 44,100 Hz, 135,168 or 139,264 frames; each WAV/CSV/report hash matches the attempt's capture hash. Full 90-member audio artifact contents are preserved in the packet.

The audit reconstructs each unique exact mutation anchor and sequential before/after hash from frozen bytes, and matches every `control-A*.json` edit. Eight original source/GLB hashes and four tooling hashes match Git. `raw/sources-after.json` restores all eight exactly; top-level source-before and source-after both equal the frozen clean build identity. Frozen capture thresholds remain onset 0.012, deviation 90 ms, silence 0.0008, cancel fraction 0.63 and maximum latency 120 ms.

**Limit:** only summed mono PCM16 WAVs, not the full five per-voice float sample arrays or cancel-frame counters, were retained. Consequently this audit cannot freshly recompute every per-voice onset/timing assertion or A6's exact post-cancel window from raw samples alone. The original voice CSV/report/native logs, mutation and restoration evidence support those catches. No person listened; speaker quality, physical output latency and subjective audio quality are unverified.

## Actual packages versus verifier claims

`derived/inner-package-audit.json` records each member's expected hash/bytes/mode and actual agreement. Linux has five members, Android five, iOS 51. All names are unique, target-confined, non-traversing POSIX regular files; source receipts are byte-identical to the outer export receipts and JSON-identical to the manifest/native/package verifier receipts. All uploaded extracted copies match by bytes. ELF and console wrapper have inner mode **0755**. Outer GitHub-upload file modes are not substituted for inner POSIX archive modes.

All five manifest artifacts and `checksums.txt` agree, including the actual three inner ZIP bytes, the Android APK, and Linux ELF (the latter available in the uploaded extracted copy). The manifest and `packaging.json` are byte-identical. Static independent parsing finds Linux/iOS PCK resource counts **130/130**, Android asset count **132**, the required imported rifle/arms/textures/modules, and no shipped test harnesses. The ELF header is x86-64 little-endian. Android APK library ABI inventory and retained aapt/apksigner output support arm64-v8a/x86_64, version `0.3.2-dev (5)`, min/target SDK 24/36, landscape and exported launcher alias; retained signature output reports v2/v3 verified. iOS plist/project bytes support landscape, bundle/version/build identifiers and empty unsigned development team.

This audit did **not** rerun ELF, wrappers, SDK tools, signature cryptography, native tests or a database. Native CI process receipts/raw logs corroborate the original Linux menu/demo and extracted menu/wrapper passes. APK cryptographic validity is a retained-tool-output result, not a new offline cryptographic verification. Receipt-reported extracted filesystem modes are distinguished from independently inspected ZIP modes.

## Exported-client failures are not promoted

### Network

`raw/artifact-12470681259/v3-export-network/results.json` remains `passed=false`, `stage=watchdog-start`, `status=incomplete`. The watchdog controller hash matches frozen `verify_integration_export.py`; its complete process receipt has exit 1 and a timeout error, with POSIX cleanup reported verified. Raw watchdog output records the hard deadline including cleanup.

The authority subreceipt and server log genuinely show join/ack (largest ack 95), six shots, ammo low 24, native reload command and completion to ammo 30. This is a **substep pass only**. Visual review shows `07-after-authority-reload-completion.png` still displaying `RELOADING 0.6s`, whereas `08-settled.png` displays `RIFLE 30 / 84`, `100 HEALTH`. Capture filenames refer to authority/controller timing, not proof of instantaneous rendered completion. Source `verify_integration_export.py:314–329` itself requires visual review and then native close, both exits, log checks and unchanged-export checks. A final overall success receipt never arrived. Evidence cannot prove the exact stalled function or justify changing the failed flow to passed.

### Offline

The raw 05 screenshot shows `100 HEALTH`, `SIDEARM 14 / 60`; the raw 06 screenshot shows **`ELIMINATED · SPECTATING` and `RELOADING 0.1s`**, also in saved OCR stdout/crops. The traceback reaches `parse_hud_text` from `verify_offline_export.py:180` and rejects that eliminated state. It is real rendered death, not merely an OCR false negative. The frozen controller hash and exported ELF digest match their exact source/artifact records. This proves a retained failed attempt, not a successful living-player reload, movement/fire acceptance, menu-return or final clean-exit/source-restoration flow.

## Workspace protection and concurrent changes

The local checkout was already dirty and at `88bfc51da026be42b3dec517817459ed89630ded`, not the CI source. Before packet publication it moved concurrently to `456d9bef0e3c388aa3696df43a874cc721c76e61`; index/ref hashes changed, and these four outside-scope paths changed/appeared:

```text
docs/network/ACK_SNAPSHOT_DIAGNOSTICS.md
game/scripts/network/ack_snapshot_diagnostics.gd
game/scripts/network/ack_snapshot_diagnostics.gd.uid
game/scripts/network/movement_prediction.gd
```

This happened while the audit had written **nothing inside the repository**. No attempted rollback, repair, owner-branch operation, index update, staging or commit was made. All CI analysis used frozen Git objects, never current working scripts. The exact before/pre-publication/final snapshots and status files remain external; the packet's `derived/workspace-read-only-audit.json` summarizes their hashes and actual differences. **A globally clean or invariant local checkout is not claimed.** Final publication verification separately records any further concurrent delta rather than silently attributing it to the audit or suppressing it.

During packet assembly, another snapshot observed **1,031 differing or newly visible outside-packet paths**: 1,029 additions/visibility changes plus modifications to the owner progress report and parent evidence `.gitignore`. The additions include the separately owned `ci-repair-followup`, snapshot-observability and input-boundary packets. HEAD, index and refs were stable between that pre-publication snapshot and assembly snapshot. Their full differing-path/hash records remain external; only a compact summary and hashed full references are included here. None of those owner files was written or repaired by this audit. Changes in ignore visibility are not proof that every newly visible file was newly created.

## Publication, integrity and exact omissions

The packet is capped at **12 MiB total logical file bytes, including its SHA-256 ledger**. `PACKAGE.json` records final payload categories/counts/bytes; `SHA256SUMS.txt` covers every packet file except itself, and its own SHA-256 is returned in external `FINAL_VERIFICATION.json`. Every published file is reread and hashed; preserved archive selections are also re-compared with original ZIP members. Nested `.gitattributes` disables text normalization, and nested `.gitignore` permits preserved logs/builds paths. The packet is not staged. No old packet was overwritten.

The initial assembly's size gate stopped before ledger finalization because the unexpectedly large concurrent-workspace delta expanded its generated summary. Finalization replaces only that audit-authored generated summary with compact hashed external references; original selected receipts, failures, logs, source bytes and media are unchanged. `PUBLICATION_FINALIZATION.json` records this bounded-publication adjustment. The final packet is measured and checked again, with no historical packet or failed-run verdict overwritten.

- `raw/`: canonical original artifact member names, byte-preserving receipts, all audio raw controls/captures, matrix logs/process gates, each campaign summary and every native child log, failing flow logs/OCR and selected raw screenshots, plus individual job-step logs.
- `transport/`: byte-preserving downloaded run/jobs/artifact/collection metadata, original collection checksums and receipt indexes. All 27 collector-selected receipts are independently checked and included under canonical archive-member paths. The historical 0.3.0 fixture manifest is labelled by its actual nested location, not mistaken for current-source build proof.
- `frozen/`: selected exact Git-object workflow/probe/verifier/harness sources, plus the contact fixture and source manifests.
- `derived/`: independently generated matrix, campaign, audio, inner-package, provenance/flow, source and workspace audits. These are derived analyses, not altered original receipts.
- `EXTERNAL_INVENTORY.json`: **every member of all four external ZIPs**, size/SHA-256/mode, exact published path or omission reason and full external archive reference. Full binaries, APKs, static libraries, caches, DB files, full trajectory JSON and complete ZIPs remain external. Nothing executable was extracted by this audit. Large per-client/server JSON was read and audited in memory; per-child hashes and scalar gates are published instead of roughly 100 MB of trajectories.
- Selected failure screenshots are unedited PNGs, not the separately supplied `flow-screens-20261024` derivatives. Unselected menu/requisition/fire timing PNGs remain individually named/hashed in the external inventory. All actual failed verdicts and raw failure logs remain in the packet.
- Twelve parent campaign stdout logs are byte-identical to their included condition summaries and omitted as duplicates; three aggregate run-log concatenations duplicate the included individual job-step files and remain externally referenced. No failure is omitted by this deduplication.

Artifact links and independently matched digests:

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| [12470739875 — validation](https://github.com/calebaiken/sightbreak/actions/runs/39880125007/artifacts/12470739875) | 88,023,940 | `06497a564fd04ed13c10a0c92a323b4f0c1ed223017298f924ee751e5d16488a` |
| [12470681259 — development](https://github.com/calebaiken/sightbreak/actions/runs/39880125007/artifacts/12470681259) | 522,826,604 | `531a83b8407fdea9e26579a3df6fdefd0ad1e77dd461aee549073082a03ebe00` |
| [12470965068 — audio controls](https://github.com/calebaiken/sightbreak/actions/runs/39880125007/artifacts/12470965068) | 215,325 | `b0d7719a389bbbb270659563ee256ee441c583f74d9b5af40d852314baa12917` |

External `run-logs.zip`: `4c57d3d183e157a48d724167d41ec2ddecb1039e030fb29f0690bd48d20c3f15`. Unlike the three artifacts, the run-log ZIP has no separately retained published GitHub transport digest; its local hash is not presented as one. Retained artifact metadata says expiry 2026-11-06; no online availability/expiry check was performed.

## Hard gaps and audit limits

1. Exact-source full matrix **still failed**; neither a successful later repair nor a current local commit rewrites that result.
2. Both attempted exported-client overall flows **still failed**. There is no accepted dev-candidate/fire-reload-clean-exit result from those attempts.
3. Physical Android/iOS installation, real touch/gyro, sustained device/GPU performance, hardware/cellular behavior, macOS/Xcode compilation/signing, and continuous full-match/human gunplay quality gates remain **unverified**. Linux llvmpipe/Xvfb, dummy audio and unsigned/debug packaging do not substitute for them.
4. No native jobs, database, network/GitHub calls, executable extraction, project imports, or commits were performed. The approved CPython parser and read-only Git commands were the only audit computation path; tool path/hash is recorded in provenance.
5. Offline checks corroborate retained downloaded metadata and actual bytes. They cannot independently authenticate remote GitHub history or re-observe CI execution. Individual native campaign exit receipts and full per-voice float captures are absent, as disclosed above. Concurrent local changes prevent a global workspace-invariance claim.

**Acceptance remains withheld.** This is a bounded, independently checked evidence packet for a failed historical CI attempt, with qualified substep findings and explicit remaining gates.
