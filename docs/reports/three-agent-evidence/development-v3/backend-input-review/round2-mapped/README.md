# Mapped backend assurance — compact, source-bound publication

This packet preserves the completed **qualified, narrow trade-read integration review**. It is not a new backend test run, performance execution, or production approval. The copied report and both old/new evidence layers retain their original qualifications and failures.

Start with [`audit/MAPPED_ASSURANCE_REPORT.md`](audit/MAPPED_ASSURANCE_REPORT.md), then [`audit/QUALIFIED_DECISION_LEDGER.json`](audit/QUALIFIED_DECISION_LEDGER.json). The root publication receipts concern byte preservation and source binding; they do **not** turn historical failed checks into passes.

## Source and execution references

| Reference | Exact meaning |
| --- | --- |
| `4a8e9ea73aa8b286d9f1751b0a6b485479737294` | Reviewed shipping trade-read runtime; app blob `16f33c94da490c77a8ab930b88d8fc0662f3fa4c`, raw SHA-256 `703c20b298d734395f292d4a8c5e415e55e6f35109e9a51dcb36fbcb62647441` |
| Local `88bfc51` | Main's `-x` integration commit. Publication verifies its complete resolved commit ID, the same app blob, and the recorded 4a8 cherry-pick reference; see `GIT_BINDINGS.json`. No current builder-owned working files are inspected or modified. |
| R2 **M** | Reported executed checkout/runtime `701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd`; harness `8070436f53dd98e9529e8c21ea7b0f7e3ecb6daf` |
| R2 **V** | Reported executed checkout/harness `8070436f53dd98e9529e8c21ea7b0f7e3ecb6daf`; shipping reference **4a8**, not falsely relabelled as its executed checkout |
| `866e2e1f38461fa245557c9015b6c1a1a97ad745` | Immutable raw R2 and identity-release archive |
| `8dc8e3715dcaeb99fe6e3544243ee591d68c337b` | New direct-bound test and actual-import identity harness source/workload freeze |
| `3e7ce7409322766d07afe504d97f47c5b3614875` | Completed assurance control-runner freeze; shipping app unchanged |
| `172c900795c04f9b8706c4e80d72f55927f40da1` | Raw assurance publication, including both attempts, JUnit/logs, materialization and import receipts; raw manifest `38a72cbab4948e9144040626c3793e6310e74d0d73758ab8c83b6e18867c4f8c` |

`GIT_BINDINGS.json` records **470 actual pinned Git bindings**. Each check requires successful command exits, a resolved nonempty commit ID, the requested tree entry, independently recomputed blob SHA-1, SHA-256 and byte length. Empty stdout alone is never binding evidence. These checks establish immutable object/content linkage, not original execution authenticity or certification of later working-tree changes.

Useful source locations are 8dc `backend/tests/test_trade_reads.py:88–112`, 8dc `scripts/benchmark_trade_reads.py:35–42,161–169,225–227`, and 3e `scripts/check_trade_read_assurance.py:40–94,118–234`. Those exact source snapshots and their execution receipts are copied under `audit/objects/`; they are not the builder's live source files.

## Freeze, key and order

The **entire 10-file original second Sol verdict directory** is copied unchanged under `frozen-second/`.

| Anchor | Verified SHA-256 |
| --- | --- |
| Second report | `1248f66b7b80e2acbf69595ef084b164957547497f7c40c2e56c4489847fcf3e` |
| Second `FROZEN.json` | `185d7b4cd1dacde52d8d9cc48bc35b43fde9b1453ef98a362d798e9bb9ab0f9e` |
| Second verdict ledger | `f34dec97780638ddba68a38dbf50d967000b8181eb00ad410e3060084612bc20` |
| Released R2 key, `audit/second-key-verified.json` | `28f0de31229e531e7164ce3905ae88cedcbd07ce89e62f046983000ebdecf93a` |

The original freeze is `2026-10-23T00:26:09.129364+00:00`. The completed audit's `PRE_KEY_FREEZE_VERIFIED.json` records **28 successful checks before mapping inspection**. The publication also checks freeze/report/ledger and artifact bytes before copying the already-released key. This is preservation of the earlier blind-review boundary, not a new blind verdict or trusted timestamp attestation.

## Old evidence versus new evidence

| Layer | Preserved conclusion and limit |
| --- | --- |
| Original R1 | The committed **165-pass / 1-fail** app-binding history remains unchanged. Its named newline constructions did not explain `9f94…` versus raw Git `703c…`; the then-unknown cause is not retconned. The locked `round1/` and `source-review/` archives are untouched. Exact structured copies already captured by the completed audit remain in `audit/objects/first-round/`. |
| R2 retention | The completed offline audit verified **168 received responses, 336 state arrays and 28 aggregate states** across 14 workload records. It did **not** find an original measured app-byte snapshot or original actual imported-fixture identity in R2. Matching clean labels/trees do not supply those missing captures. |
| New R3 direct-bound assurance | The completed attempt has two candidate passes and two intended mutant failures. Mutant actual bind counts **1600 / 502** fail only the new 500-bound assertion while old query ceilings still pass (**5≤8 / 4≤5**). Logs, JUnit, actual mutant bytes, patches, driver and DB-cleanup receipts are retained under `audit/objects/assurance/`. No failed earlier attempt is hidden or double-counted. |
| New actual-import controls | Actual `__file__`, resolved path and hash are captured. Matching bytes are accepted and source-side shadowing is rejected; dedicated import probes report zero intercepted DB-connect calls. This does not mean the full benchmark opens no DB: its database creation precedes the guard. Historical replays are explicitly **post hoc**, not original captures. |
| New reverse-mutant preimage | `audit/derived/attempt-2-reversed-app.py.txt` is the **new post-hoc** preimage of `9f94…`, reconstructed by reversing exactly four constants in the retained mutant. It has 510 CRLF / 21 bare LF and normalizes to the raw `703c…` app. This does not rewrite the valid R1 failure or turn it into an original R2 app capture. |

The original Sol source controls remain **UNEXECUTED**. Copied completed offline-audit programs are evidence, not rerun instructions. Earlier target/PG/pytest receipts describe retained **Python 3.12.14** executions; publication uses approved **CPython 3.13.15 only for standard-library file/hash collection and read-only Git**.

No full-backend, general-latency, monetary/write, memory, unbounded-history, concurrent-load, device/human, deployment or production gate is claimed. R2's eight monetary/history tables are empty and balances are zero. Its snapshots prove retained **net row equality within the captured intervals**, not transient no-write behavior or all authoritative contracts.

## Compact selection and complete external references

The completed external audit remains unchanged at:

`C:\Users\blith\AppData\Local\Temp\opencode\sol-backend-mapped-assurance-20261023T005138Z`

Its full **611-file / 6,605,076-byte payload manifest** is copied exactly as `audit/SHA256SUMS.txt`, SHA-256:

`048276d1fcb0fe2dc52485b9d730e109669e5902ffca5f79c38cb089d7068750`

That inner manifest is the **complete external bundle index**, not a claim that every indexed path is present in this compact packet. All 611 originals were hash-checked before selection and again after restart.

- **526 original audit payload files** are copied unchanged. All root reports/programs/ledgers, all `objects/` source/assurance receipts, both derived app files and selected raw captures are present.
- **85 original files / 3,262,041 bytes are omitted locally**. `OMISSIONS.json` lists every name, size, hash, full external path and available same-hash alias. This selection changes no original source bundle.
- `RESPONSE_STATE_INDEX.json` indexes the original response/canonical/expected/state artifact files with exact Git commit/path/blob/hash and local/external capture references.
- Bounded raw representatives cover complete `(1,2)` received/canonical/expected bodies and before/after states, plus all 12 item-heavy `(40,20)` before/after state arrays, both roles. Shared/tiny captures may cover additional cases. Large `(40,20)` response bodies remain external rather than duplicated locally.
- `audit/RETENTION_WORKLOAD_LEDGER.json` and `audit/SOURCE_HASHES.json` retain the full 14-workload and source/capture index. Complete original raw payloads remain addressable through the external bundle and pinned 866 Git references.
- `COPY_LEDGER.json` lists **537 exact copied files**: 526 audit payloads, the complete external manifest and all 10 frozen second-verdict files.

The active selection is `COMPACT_COLLECTION_PLAN.json`. The earlier larger plan is retained as planning history, not represented as the final selection.

## Failures, restart recovery and byte preservation

The packet preserves the completed audit's two negative checks from the earlier materialization-confounded attempt, its partial historical replay failure, and the first archive's 165/1 history. Publication success does not reclassify any of them.

A shell-startup exit 6 and an interrupted collection are recorded in `publication-raw/`. On restart, byte checks rejected zero-filled publication copies; all original 611 audit files still matched their frozen hashes. No non-identical copy was accepted or silently overwritten.

- `resume-failure.json` and `resume2-failure.json` retain the refusals.
- `publication-raw/interrupted-zero-copies.zip` losslessly retains 122 damaged publication copies; `BULK_INTERRUPTED_COPY_RECOVERY.json` records their exact decoded hashes and sizes.
- `publication-raw/planning-and-restart-history.zip` losslessly retains the initial plan/validation and the separately observed zero-filled source-index copy; `PUBLICATION_HISTORY_INDEX.json` records exact decoded hashes and filenames.
- **Only temporary publication history and damaged-copy bytes are compressed. No copied completed-audit, verdict, source, log, JUnit or execution receipt is compressed or transformed.** Restored source copies are independently hash-verified; future writes were explicitly flushed.

Nested `.gitattributes` disables text/filter/ident/encoding transformations. Nested `.gitignore` keeps raw logs and copied programs visible. `COLLECTION_COMMANDS.json` / `SEAL_COMMANDS.json` retain publication Git argv, exits and raw stdout/stderr references. No target modules, original audit programs, tests, PG, native programs or services were rerun for publication; no commit, push, GitHub action, source/index edit, progress/index update or write outside this directory was made.

## Final verification

The **root `PUBLISHED_SHA256SUMS.txt`** covers every published file recursively except itself, including all inner original manifests, failure archives and metadata. Its returned digest is the outer anchor; there is no self-hash assertion. `verify_packet.py` is a read-only standard-library/Git verifier for the compact publication; it does not execute copied programs or tests.

`PUBLICATION_VALIDATION.json` and `PUBLICATION_RECEIPT.json` distinguish publication integrity from historical qualification. Main may inspect/stage/commit this directory in its next freeze; nothing here modifies or supersedes the locked first-round/source-review archives or the builder-owned test/harness sources.
