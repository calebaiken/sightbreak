# Final scoped source/binding review

**PASS for record-backed source provenance, artifact binding and journal-only recovery dataflow in the declared one-case-per-source control. No unresolved source or transformation blocker remains.**

The original blind outcome stands unchanged. Identity disclosure now binds its labels as follows:

| Frozen neutral label | Verified shipping revision | Frozen outcome |
|---|---|---|
| `Set-829261D1` | `7b6f379a3f8c809d0985a64e883cbadfdd78d135` | Supported, 1/1 exact recovery; winner |
| `Set-DB921BCA` | `701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd` | Failed, 0/1 exact recovery |

This closes the inspected-source/dataflow component of the blind verdict's strongest gap. Historical machine execution, loaded-code/cache identity and process ancestry remain record-backed rather than independently authenticated. That limit does not block this scoped acceptance or require another crash variation.

## Review boundary and preserved freeze

The parent reported public freezing at `https://github.com/calebaiken/sightbreak/pull/18#issuecomment-6382319612` before this source access. I did not fetch GitHub or depend on a newly fetched statement there. I independently rehashed my original files before source review and again during the new offline audit:

- Original `VERDICT.md`: `ce31d12d3def7e7b312ce1a44e30fc654290085796b3b0a5c2bd561e59c904af`.
- Original `independent-audit.json`: `873b727b69b44eb2dd6d9116eb13d34b86e20b268c50783cb291f617ed957f39`.

Both retain their exact bytes. This is a separate post-disclosure supplement, not a rewrite of the pre-identity verdict.

I read the permitted controller, its captured resources, referenced raw observations and immutable Git objects in the main repository. All commands were offline file/Git inspection and independent parsing/hash/comparison operations. No application, database, native client, test suite, network probe or other agent was run. No repository file was edited. Scratch copies of Git source blobs were created solely for reading; the target source and packaging programs were not imported or executed.

Citation shorthand:

- **Controller**: `C:/Users/blith/AppData/Local/Temp/opencode/journal-review-e8f9e5706e73e619/CONTROLLER`.
- **F**: `Controller/source-context/candidate-7b6f379/`; both arms' frozen driver/probe copies were verified identical.
- **R**: `docs/reports/native-journal-only-restart-evidence/r2/` in repository `C:/Users/blith/OneDrive/Documents/Default Project/sightbreak`.
- Shipping-source citations specify a revision and repository path. Line numbers refer to the Git text; the archive's CRLF conversion preserves those line numbers.

## 1. Controller, transformations and publication binding: PASS

The controller mapping matches its supplied commitment:

```text
mapping.json SHA256
4ef6ffc75a2ef410a55d576a273626c625582053aba5dc910c1e0bc3dbf19c86
```

Its source identities agree with the original summaries and the exact Git trees. The immutable source-evidence commit is `e6fc11b2c103bb45551dd065bb9131851d072d50`; the inspected publication is `0e536d94621453adba5469303908536c6e58d952`.

I independently replayed every recorded raw-to-neutral substitution from the bound Git bytes:

- **26 unchanged observation files** match byte-for-byte.
- **24 transformed observation files** reproduce their neutral bytes exactly.
- All **10 economic-stage files** remain byte-identical.
- The remaining four payloads are the two generated semantic aids, overview and README; they are distinguished from the 50 observations.
- **182 substitution records, covering 356 literal occurrences**, are accounted for. They are confined to the declared path/environment-path/source-digest aliases.

| Substitution category | Actual occurrences |
|---|---:|
| Private journal path | 8 |
| External probe path | 42 |
| Source SHA-256 values | 96 |
| OS environment paths | 132 |
| Private fixture path | 24 |
| Project path | 36 |
| Executable path | 18 |

For each replacement I checked the allowed alias, original occurrence count, replacement result and final packet digest. This is independent replay, not acceptance of `exact_transformation_replay: true`. The packaging implementation corroborates that mechanism: `Controller/build_neutral_journal_only_packet.py:24-42,66-79,81-115,154-161`; helper `build_neutral_receipt_packet.py:61-74` performs exact longest-first literal substitutions, including slash and JSON-escaped spellings. The new packager loads committed blobs and packages retained observations; it does not run a measurement.

I checked **69 distinct controller-bound originals**, including all 50 observations and 19 withheld bindings, against their length/SHA-256, evidence-commit Git blob, publication-commit blob and retained file bytes. All match. This targeted binding work is separate from the parent's already-completed 101-file publication audit; that parent audit was not used as a substitute for source reasoning.

The ZIP bytes independently produce Git blob `47c02e8c41fb4e7cb650839b3969c19013095635`, which is the exact publication ZIP object. Its SHA-256 remains `7a12ec5de2b8344794c60eab1b83cc116f40de5b0cf0360e6cc0a6e84032625f`. The originally frozen neutral outcome therefore binds to these disclosed raw records without changing its evidence.

## 2. Frozen harness versus shipping source and archives: PASS

Both retained driver/probe copies are byte-identical to their Git blobs at original harness freeze **`7be70f73ec6a065849d902e7075d2b76e78bdd21`**, main cherry-pick **`9e4fd4f6e1567fbc923d145982301e54afe3d0cc`**, and publication `0e536d94`:

| Frozen component | SHA-256 |
|---|---|
| `scripts/validate_native_transaction_restart.py` | `168b2574f94a660f8fd62bf974136c6e55536e5896ea3ab08fa66e670e61885d` |
| `scripts/native_transaction_restart_probe.gd` | `f33f1c7e52206aeb3ca54f4a5dc65e07d7e859b323b3b137367d6fd926d314ff` |

Both freeze/cherry-pick commits change exactly those two scripts and `docs/reports/NATIVE_JOURNAL_ONLY_RESTART_PROTOCOL.md`. Each leaves its parent `game` and `backend` trees unchanged. I reviewed the script diff from the prior `31438cbcea6ef08a131ae312c65b94f7e3e882c3`: it adds the minimal-input capture/validation, allowlisted environment, explicit native cwd and read receipts, and moves price normalization into the send branch. It does not alter shipping production code.

The driver archives `game` and `backend` from the explicitly measured shipping revision, not from the harness checkout (`F/validate_native_transaction_restart.py:562-591`). The child receives that archived game's `--path` and cwd, while `--script` points to the external frozen probe. The harness's different game tree is therefore not silently substituted for the measured shipping UI. The six native UI/API/journal-file read digests match the shipping archive digests below.

I reproduced both complete Git ZIP archives in memory using the recorded archive arguments and checked every member against the captured source manifests:

| Shipping source | Archive files | Archive SHA-256 | Files differing from raw Git blobs only by LF -> CRLF |
|---|---:|---|---:|
| `701ce2c4` | 299 | `e059f5e213b5f1375c96200da7a2a203d5e45b087037f171bcf756170c1fbe33` | 278 |
| `7b6f379` | 307 | `2434610f47d0d7503d93cbab7155878fc886f48898c2f9fe85f6a4aaec6c9c01` | 286 |

Every archive hash and all **606 source-manifest entries** match. Every raw-Git/archive difference is exactly LF-to-CRLF conversion, with no other source difference. Direct Git-blob hashes initially differed from the recorded Windows source hashes; that apparent mismatch is explicitly resolved by the actual archive bytes, not ignored or relabeled.

| Archived production component | SHA-256 |
|---|---|
| Baseline `game/scripts/ui/economy_ui.gd` | `4dcf553e08180727f8aed9b5fd2543123f8b23d6dc63433beb33027550d2f236` |
| Candidate `game/scripts/ui/economy_ui.gd` | `310cb4e7aaf110efd6b6d8eebc221231bdb169665a3062b1bc13437af0f9a84b` |
| Both `game/scripts/ui/economy_api.gd` | `246a50de1e68137715f2e1430b6c2f5cd42761f0d64acb26032e7f8668e81e7f` |
| Candidate `game/scripts/ui/transaction_journal.gd` | `72fa6d9779e621f71d11b5686080c1c12f1f46846fe129be5004f4930a320117` |
| Both `backend/app.py` | `78816607ee70fe47ae1f1c97f48d4d2a360eebe7c0e64ac73c296dfd53fb8121` |

The baseline archive has no journal source. Both shipping revisions and the harness bind the same backend tree, `67027b4fa17674ef067c84401af76eb1524419ac`. The shipping game trees are baseline `2d2b174c2145e9755ddfc78a1369e74443fcc400` and candidate `026b711f887038a9e953b448dcad0f1208e5210b`.

## 3. Raw config/read/environment bindings: PASS, with explicit secret-redaction limit

For **all six launches**, I checked the original source-labelled records rather than their neutral placeholders:

1. The prelaunch input record equals the timeline `native_inputs_prepared` record and precedes the corresponding `native_started`/`native_finished` records.
2. The native `fixture_read` digest, length, key list, mode and PID agree with that launch.
3. The actual native probe/UI/API/journal-file hash map equals the prelaunch map excluding its driver-only entry, and each value equals the frozen harness or measured shipping archive.
4. The redacted fixture's retained original-file SHA-256 and the full unneutralized environment's sorted compact-JSON SHA-256 recompute exactly.
5. The full environment contains exactly the 15 declared Windows housekeeping keys plus `SIGHTBREAK_RECEIPT_FIXTURE`; it excludes `DATABASE_URL` and other inherited application variables. Full argv is only executable, headless/verbose flags, archived project path and frozen probe path. The original purchase identifiers/fields are absent from these full values.
6. All four restart configs contain exactly `{url,journal,mode,username,password,owner}` with `mode: "retry"`; no purchase path, payload, listing/item/seller/key, price or expected result is present.

| Arm | Native PIDs: send / recovery / second restart | Private retry digest, both restarts |
|---|---|---|
| Candidate | 20004 / 1700 / 22640 | `b579890c1d7cbf7ddf30fe9485b32d70372583c68d1424ba73ef0ed8c4e78c33` |
| Baseline | 23852 / 28396 / 13500 | `baf7f9d638e37be2fe5581a9f3c98afc8aad8c8e874570be3f857d287e1bd1b2` |

Raw environment digests are candidate `f1202ff522071ffdc7acede7c65480223e3d5482cfda4101ce8ab8df9e89cd52` and baseline `8ad3fdbe949e6324b94168e80dbdc6335536bfaf96f77dcbda84d4cb2f3aefc2`. These now independently recompute because their original path values have been disclosed. This closes the neutral packet's path/environment substitution limit.

Source mechanism: `F/validate_native_transaction_restart.py:41-44,361-394,424-431,458-467` constructs a fresh six-key retry dictionary, truncates the same supplied file via `write_text`, reads and hashes it, writes only a redacted evidence copy, then launches with the captured environment/argv/cwd. The original transaction remains in driver memory for checks. `--expect-recovered` influences final acceptance at lines 640-642, not the child inputs or returned receipt.

**The original secret-bearing configs are not retained at their recorded paths.** Both `sightbreak-receipt-mbdiizus/run-1-fixture.json` and `sightbreak-receipt-7y9bqtyb/run-1-fixture.json`, their `seeded-private.json` files and extracted project directories are absent now. The code explicitly removes the seeded file before native launch (lines 597-608), unlinks the case fixture in `finally` (512), and encloses the private directory in `TemporaryDirectory` (581).

The source-labelled redacted configs are 633 bytes for send and 300 for retry; native/prelaunch private lengths are 670 and 337. Their **37-byte difference** exactly matches a 47-character generated synthetic password replaced by the 10-character `[REDACTED]`. The additional neutral journal-path substitution yields the previously reviewed 565/232-byte neutral files. Password generation is independent random seeding at lines 288-301; it does not encode the later purchase key or result.

Nevertheless, the discarded random password cannot be reconstructed, so I cannot independently rehash the original private 337-byte file. Plaintext bearer-token hashes are likewise not recomputable from redacted tokens. The private hashes remain matching recorder/native-reader bindings, corroborated by inspected source, rather than independently re-created secret bytes. No attempt was made to invent or recover those secrets. This bounded secrecy limit survives acceptance.

## 4. Actual recovery dataflow: PASS

### Frozen probe

`F/native_transaction_restart_probe.gd:15-30` reads exactly the file named by `SIGHTBREAK_RECEIPT_FIXTURE`, parses that text, hashes the same text and enforces the six-key retry shape before constructing the UI. `31-39` changes only the journal location, then adds the UI to the tree and captures its already-loaded pending state. `43-49` uses the normal login path and requires the configured owner and a nonempty fresh token.

The decisive branch is at **51-58**:

- Send mode alone normalizes `config.payload.expected_price` and passes `config.path/config.payload` to `_perform`.
- Retry mode calls **`await ui._retry_pending()` with no arguments**.

The previous unconditional fixture-price read is removed from retry mode. The probe neither assigns `ui.pending_transaction` from config nor injects a receipt, payload or expected result on recovery. This source reasoning addresses the causal-input concern directly.

### Candidate shipping UI and journal

At `7b6f379:game/scripts/ui/economy_ui.gd:65-77`, `_ready()` populates `pending_transaction` from `transaction_journal.load_pending()`. The probe's journal-path assignment happens before this startup load. Authentication refreshes account/inventory data but does not build or replace the pending transaction (`355-382,407-453`).

The initial `_perform` stages the keyed transaction **before** dispatch (`529-552`). The journal validates the six-field transaction, writes it to a same-directory temporary file, flushes/closes, verifies bytes, renames, and verifies published bytes (`transaction_journal.gd:76-111`). The staged record contains replay inputs, not the eventual full result.

On restart, `transaction_journal.gd:51-74` reads/validates the journal and restores integer method/price types. UI `_retry_pending` (`504-527`) copies that loaded record, requires matching original owner/server and a nonempty authenticated token, and claims it. The journal's `claim` (`34-44`) reacquires ownership and rereads the file, rejecting a changed record. Dispatch then uses exactly **`pending.path`, `pending.payload`, `pending.message`, `pending.method`** (`economy_ui.gd:523`).

`_send_transaction` (`554-582`) returns the actual API result; subsequent `_refresh()` does not replace that return value with an inventory/account reconstruction. A successful validated receipt clears the claimed journal. The next startup has no nonempty pending record, so `_retry_pending` returns `{}` without dispatch (`504-506`).

Thus journal-only here has a precise meaning: **the original transaction inputs come from the staged journal; the original result comes from server-side Operation replay**. It does not claim that the journal itself stores the completed response.

### Baseline absence control

At `701ce2c4:game/scripts/ui/economy_ui.gd:47,62-72,495-531`, pending state begins empty and has no persistent journal implementation/startup load. `_perform` can save only in-memory pending state after an uncertain API result; the killed process is still awaiting that response. Fresh-start `_retry_pending` returns `{}` immediately because pending state is empty. This explains the frozen 0/1 outcome and the refreshed inventory without a recovered receipt.

### Real HTTP and PostgreSQL replay, not probe-supplied result

`game/scripts/ui/economy_api.gd:47-79` serializes the supplied payload, sends it through a real `HTTPRequest`, and returns its parsed response. It does not synthesize the expected transaction result.

The frozen proxy forwards the incoming raw body and authentication token to the backend, reads the actual upstream response and records it (`F/validate_native_transaction_restart.py:166-198`). Only the first purchase response is held and discarded (`199-209`); a recovery request is forwarded upstream and its new upstream response delivered normally (`210-217`). The held response is used as the driver's comparison oracle, not substituted as a fake native response.

The unchanged backend authenticates from Session rows (`7b6f379:backend/app.py:61-67`), issues a new session on login (`177-200`), and enters a PostgreSQL transaction with the existing advisory lock (`44-48`). `market_buy` checks Operation replay **before** attempting another settlement (`279-297`). The replay key is owner/route/idempotency UUID, and the stored request hash must match (`127-141`); success returns the stored full response. Independent SQL snapshots use a new repeatable-read, read-only connection (`F/validate_native_transaction_restart.py:114-128`). These sources agree with the already-frozen original request/receipt/session/economic observations.

## 5. Prior source closure: explicitly reused bound only

I read `docs/reports/native-pg-restart-evidence/source-binding/source-binding-completion.json` (current SHA-256 `46c1372312f850df23483f1cc85553bb66c198ef0435974bd320f87db1219b1b`) and its README. I reuse that prior closure only as a bound on the identical shipping revisions/backend and its disclosed cache/ancestry limitations.

I independently checked the new frozen harness, its change from `31438cbc`, all new six-launch bindings, the new mapping transformations and both complete source archives here. The prior three-price campaign supplies no additional cases or execution proof for this new run. Its source archive hashes agree with the independently reproduced hashes; the new causal-input evidence is the new two-case capture.

The prior review recorded a then-present Godot binary matching SHA-256 `ab1824f85bfd8e0e4128182c000c4003a3e042245b2967848d089b2a04b22424`. Both new raw summaries record that same digest/version. **The executable is now absent at the recorded path**, so this follow-up does not claim a new direct binary rehash or independent historical executable attestation.

## 6. Preserved negative findings and strongest remaining gap

1. **Baseline recovery still fails.** Its `authoritative_pass`, `complete_result` and `stable_journal_at_kill` flags are common settlement/stability checks, not receipt-recovery acceptance. The source explicitly calculates `recovered` from separate recovery checks (`F/validate_native_transaction_restart.py:332-358,483-503`). Stable absence is not a surviving journal; refreshed account/inventory is not an exact receipt. The original negative verdict is preserved.
2. **Journal absence wording needs a source-level precision note.** `journal_snapshot` sets `exists=bool(raw)` (`131-138`), so that wrapper alone cannot distinguish a missing file from an existing zero-byte file. The baseline has no journal implementation, and in either interpretation it has no recoverable transaction. This clarification does not change the 0/1 outcome. The candidate's nonempty 303-byte raw journal is directly retained and unaffected by this ambiguity.
3. **Historical cache payloads are not retained in these capture records.** Each 62-entry copied-cache manifest and same-game-tree identity is bound. The historical extracted directory is gone. This does not independently reconstruct the cache or prove which cached/preloaded code the native process executed. A source hash measured after the probe's static preload is still a file measurement, not loaded-code attestation.
4. **PID identity within each native launch is consistent; upstream process ancestry is not independently captured.** The source/records show these different launcher and worker identifiers:

   | Arm | Wrapper-launched driver PID / timeline harness PID | Service launcher PID / logged server worker PID |
   |---|---|---|
   | Baseline | 9004 / 20728 | 11864 / 12004 |
   | Candidate | 22072 / 23504 | 22940 / 25140 |

   Sources: `R/launch.json`, arm `summary.json`, `run-1/timeline.jsonl`, and `service.stdout.txt:1`. The capture contains no independent ancestry record establishing those parent/worker relationships. I neither silently equate the PIDs nor treat the missing ancestry attestation as evidence of a different transaction outcome.
5. **Secret-bearing config bytes and plaintext tokens cannot be independently reconstructed.** Their current absence and redaction are explicit above. Source and cross-process hash/key/length records support the supplied-input boundary without pretending those secrets were inspected.
6. **Recorded cleanliness, source-unchanged flags and actual execution history depend on the recorder.** The complete source archives, actual read receipts, unneutralized input records and inspected dataflow now align. They are not a hostile-process sandbox, exhaustive filesystem access trace or independent machine witness. The native test remains a headless direct-method stable postcommit/held-response termination case.

**Strongest remaining gap:** unauthenticated historical machine/cache/loaded-code execution and launcher-to-worker ancestry, including the now-unavailable executable at its recorded path. There is no remaining unexplained source-byte, transformation or inspected recovery-dataflow mismatch. Under the declared record-backed causal-control scope, those attestation limitations are retained limits, not an actual acceptance blocker.

**Final scoped decision: PASS.** Candidate shipping `7b6f379` remains the supported 1/1 winner over unchanged baseline `701ce2c4` at 0/1. The journal-only supplied-input control and its inspected-source explanation are accepted. No additional variation is required solely to cover a different crash window, power-loss condition, production environment or UI qualification.

## Saved independent audit

All new review files are outside the repository at:

```text
C:\Users\blith\AppData\Local\Temp\opencode\independent-journal-source-561fde2e90934fdbb1863eebfe3a68d8
```

`source-binding-audit.json` is 13,452 bytes, SHA-256:

```text
ef0d0f2f0d727956039bfe7b9d0e5fe6c73f762b264cfa586b3b1379d1c19d4f
```

`audit_source_bindings.py` is the independent offline audit implementation; it does not import or execute target code. The accompanying `sha256.json` pins this exact review, the audit, the audit script and the five scratch Git-source copies. Final artifact hashes are supplied with delivery for byte-for-byte archival. The original blind verdict and JSON audit remain in their original scratch directory with their original hashes and read-only flags.
