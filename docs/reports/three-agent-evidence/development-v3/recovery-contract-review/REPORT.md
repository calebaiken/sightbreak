# Recovery contract review — completed evidence publication

**PR18 remains held by the main session. This packet publishes completed evidence only; it is not a source change, a new execution, a release approval, or a broad recovery-safety sign-off.** No frozen program, native engine, database, service or network test was rerun while publishing. No staging, commit, push or GitHub action was performed.

## Findings supported by the completed bounded native controls

Target source is exact Git `7b6f379a3f8c809d0985a64e883cbadfdd78d135`, not dirty integration. The unchanged completed bundle is copied under [`native-controls/`](native-controls/REPORT.md).

| Finding | Actually observed | Scope boundary |
| --- | --- | --- |
| **S1: receipt predicates accept the two specified minimal bodies** | Both complete production functions at `game/scripts/ui/economy_ui.gd:597-608` were invoked verbatim in a native predicate component. Market `{"item":{"id":"unrelated"},"credits":0,"fee":0}` and case `{"item":{"id":"partial"},"roll":0,"table_version":"anything"}` each returned `true`. Three synthetic legitimate-shape positives were accepted, seventeen clearly malformed shape/type/range negatives rejected, and three integer-helper controls passed: **25 expected outcomes** total. | This is an exact native **predicate-component** test, not full EconomyUI, `_send_transaction`, client or backend execution. Fixtures are synthetic, not forged backend responses. No HTTP status or new authority contract was tested or asserted. |
| **S2: an invalid stage retains its newly acquired journal guard** | The complete unfiltered production journal was used. A (PID 12368) called `stage({})`, received **30 / ERR_INVALID_DATA**, and retained a listening guard without publishing a pending/tmp file. B (PID 16660) staged valid input at the same new canonical path and received **22 / ERR_ALREADY_IN_USE** while both PIDs were alive. After A exited, the **same B**, still alive, retried the identical input and path, received **0 / OK**, and reloaded the exact published pending dictionary. | Only the invalid-empty stage branch was executed. Oversize/unwritable branches and a full-UI path reaching invalid `{}` are not runtime claims. No private release, forced clear, weakened record, HTTP or database was used. The positive-control receipt remains intact. |

The final A/B records contain **49 unique native assertions: 36 + 13**. The 33- and 6-assertion intermediate snapshots repeat earlier assertions; they do not increase that count to 88. These controls are distinct from the older 36/37 and DNS-calibrated 37/37 native economy oracles.

Exactly two tiny Godot processes were used in that completed attempt, with resource preflights, 15-second bounds and prelaunch Windows Job Object containment. All four persisted completion JSONs match literal lines in the two actual engine logs; both process receipts are complete, exit 0, errors empty. Empty GUI stdout was not credited alone. The post-run audit confirmed both PIDs exited and all source/input/copy bindings remained exact. Publication copies the records; it does not repeat those checks as new runtime measurements.

### What remains source-only

- **Conditional receipt clearing:** `economy_ui.gd:559-563` plus `584-586` link accepted non-error bodies to resolution and clearing, conditional on `clear()` succeeding. Those methods were not invoked by the native predicate control.
- **Pre-dispatch return:** `economy_ui.gd:543-550` returns before `_send_transaction` on stage failure. This is source inference, not an independently measured HTTP/network count.
- **Other guard failure branches:** journal `86-102` has additional early returns; oversize, unwritable, failed readback and rename cases were not executed in this bounded control.
- The source auditor's broader S3 closure limitation and other unexecuted countercontrols remain in the unchanged [`source-review/PRIVATE/SOURCE_AUDIT.md`](source-review/PRIVATE/SOURCE_AUDIT.md). No uncertainty record was cleared to make a control pass.

## Frozen outcome-only verdict, then identity disclosure

The complete outcome-only verdict bundle is copied unchanged under [`neutral-verdict/`](neutral-verdict/REPORT.md). Before copying, publication verified the known frozen receipt and report:

- `FROZEN.json`: **`a94e9c716e8892fbc445fce5f4e4e3442b354ad24727081f275f31f82732aadc`**.
- `REPORT.md`: **`b2243cfd62ab8fe2b79ad39d4f3a9defc44b140c6ffe2648777346f681a7dc8b`**.

The freeze's complete artifact list and pinned `SHA256SUMS` were checked for preservation. The original verdict is not rewritten after identity disclosure. Local hash/timestamp freezing is tamper-evident, not a trusted timestamp, signed historical capture or hardware immutability.

The frozen verdict ranks **stored original-receipt recovery only**: `sample-8e3f9bc622` recovered **3/3** retained original receipts; `sample-ccaee51fd6` recovered **0/3**. **Economic integrity is a tie. Broader reliability/source safety/release readiness remain uncertain; approval is false.** Each group has one case at each price 400, 401 and 10,000,000, not repeated trials per price or a contemporaneous randomized campaign.

The user-authorized, post-freeze [`source-review/PRIVATE/KEY.json`](source-review/PRIVATE/KEY.json) maps the winning label to `7b6f379` and the other label to the measured `701ce2c` comparator. `d2439ac` is a scoped source-equivalent comparator, **not a separately measured native runtime**. Publishing the key does not turn the source critic into the blind judge or expand the original outcome verdict.

### Failures and gates are not waived

- The original native economy oracle remains **36/37, native exit 1: failed**.
- The externally altered reserved-`.invalid` DNS calibration remains **37/37, native exit 0: a separate condition**, not a replacement pass for the original oracle or a between-sample improvement.
- Earlier compile, resource, occupied-slot, startup/barrier, diagnostic and audit-tooling failures remain classified in the frozen verdict and source audit. Later successes do not erase them.
- The missing-engine attempt under [`blocked-attempt/`](blocked-attempt/BLOCKED.md) remains blocked before any native launch. Its complete original ledgers and compact failure records are retained; omitted duplicate bytes are explicit in `OMISSIONS.json`.
- Neither 3/3 receipt recovery nor the integrity tie closes interruption of the **recovering** process, interrupted clear/replay, competing-owner/stale-claim PostgreSQL interleavings, actual malformed-success injection, wrong-scope recovery, low-price fee boundaries, power-loss/server-crash assurance, or full recovery coverage. No correctly rendered uncertain UI state is established by the retained outcome packet.
- **Human/UI and real-device gates are not waived.** This evidence does not approve release or resolve PR18; the main session independently reviews and decides source-PR feedback.

## Packet layout and omissions

| Path | Published content |
| --- | --- |
| `native-controls/` | Entire completed exact-7b bundle: report, pre-import manifest/input hashes/provenance, exact extracted functions, unfiltered journal, probe/config/driver/supervisor, four native JSONs, engine/stdout logs, process receipts, timeline, post-run audit, retained positive receipt and complete original ledgers. |
| `blocked-attempt/` | Compact old missing-engine failure, original driver/notes/failure results, complete original ledgers, post-failure source manifest and diagnostics. Duplicate source/module/probe/config/supervisor bytes are omitted only with exact original paths, lengths and hashes. |
| `neutral-verdict/` | Complete frozen outcome-only verdict, including unchanged programs as inert provenance, raw verifier output, judgments, attempts, full input ledgers, checksum list and freeze receipt. None was reexecuted. |
| `source-review/` | Original report, complete final ledger, full neutral outcome packet, source-auditor `PRIVATE/SOURCE_AUDIT.md` and `PRIVATE/KEY.json`, binding/record analyses, full raw-object and source ledgers, transformation/omission crosswalk and publication metadata. |
| `engine-restoration/` | The already completed local restoration receipt and official checksum list, hash-bound by the native calibration provenance. No binary is bundled or run. |
| `PUBLICATION_LEDGER.json` | Complete copied/generated file ledger with destination hashes and source-root/relative-path mappings. It excludes itself and the final checksum list to avoid circular hashes. |
| `OMISSIONS.json` | Exhaustive per-file omissions from the four source bundles, plus explicit external runtime/archive reference limits. Original external ledgers remain copied unchanged. |
| `COPY_VERIFICATION.json` | File-copy/hash preservation, frozen pins, complete external-ledger checks, scoped attribute/ignore checks, counts, and size-cap receipt. Publication checks are byte/metadata checks, not test reruns. |
| `SHA256SUMS` | Final packet hashes including the publication ledger; excludes itself. Its hash is returned separately. |
| `publication-history/` | Retained publication-only aggregate-counter failure and the initial copy receipt; not an application/test failure or another native attempt. |

The 237 original raw publication objects and bulk canonical source directory are deliberately not duplicated. Their complete path/blob-ID/length/SHA-256 ledger and original final inventory are retained, as are the full neutral derivative inputs. The source auditor's bulky command transcript and preparation/verifier programs are also omitted with per-file hashes; the completed results are retained. Source ZIPs and engine/cache/database runtime trees were never part of the compact source-review payload and are not silently implied present.

The native engine executable's frozen SHA-256 is `ab1824f85bfd8e0e4128182c000c4003a3e042245b2967848d089b2a04b22424`. Its binary and the approved Python runtime are external, explicitly omitted references, not publication-stage executable revalidation claims. Exact production blob/source hashes remain in `native-controls/pre-import-manifest.json` and the original source ledgers.

**Publication metadata correction:** the first file-copy command caught a final size-accounting mismatch because a PowerShell aggregate did not sum ordered-dictionary keys. All 272 copied files were already byte-identical and the actual tree was below the cap; no frozen artifact was wrong or changed. The initial copy receipt, exact error, original metadata hashes and zero-counter deltas are retained under `publication-history/`, along with a subsequent read-only hash-helper alias collision that wrote no files. Only newly authored publication counters, ledger and checksum metadata were corrected, then checked directly against filesystem lengths. No frozen program or runtime test was reexecuted.

Only this new `recovery-contract-review/**` subtree is written. Its scoped `.gitattributes` disables text, filter, ident and encoding transformations; its scoped `.gitignore` permits retained logs without changing ancestor rules. Every copied file is checked against its source bytes/hash before and after copying. The complete subtree is capped at **3 MiB**; exact counts/bytes and all omissions are recorded rather than silently dropping evidence. Other active packet subtrees and owner/runtime files are untouched.
