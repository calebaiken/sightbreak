# Exact-commit recovery QA — preparation complete, blind verdict pending

**Git evidence byte bindings are verified. A new source-blind outcome packet and separate private key have been prepared. No independent native replay, blind outcome verdict, or baseline/candidate improvement claim is made.**

## Deliverables

- Source/evidence audit: `PRIVATE/SOURCE_AUDIT.md` — exact lines, concrete countercontrols, observed limits and retained failures.
- Neutral packet: `NEUTRAL/` — give only this directory to a fresh critic. `NEUTRAL/manifest.json` binds its files.
- Private identity key: `PRIVATE/KEY.json` — keep private until the critic freezes its verdict. Its mapping is intentionally absent from this report.
- Original published bytes: `PRIVATE/raw/` — all 237 objects, unmodified. `PRIVATE/rederived-raw-objects.json` binds path, Git blob ID, SHA-256 and length.
- Detailed independent re-analysis: `PRIVATE/bytebindings.json`, `PRIVATE/independent-record-reanalysis.json`, `PRIVATE/additional-record-checks.json`.
- Complete neutral inclusion/transformation/omission crosswalk: `PRIVATE/neutral-crosswalk.json` (identity-bearing; do not share with the blind critic).
- Read commands and reproducibility: `PRIVATE/commands.jsonl`, `PRIVATE/REVIEW_COMMANDS.md`; final verification/hashes are in `PRIVATE/packet-verification.json` and `FINAL_MANIFEST.json`.

## Verified scope

Exact recovery source `7b6f379a3f8c809d0985a64e883cbadfdd78d135`; source comparators `701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd` and `d2439acdd5f73df7bae5ada62ee1e3dec2cf30db`; evidence publication `49268b8702c44a6a19adfc743727f5aad2a10e8b` on the requested local remote-tracking ref. Only immutable Git objects/source evidence were used. Scoped comparator source files are identical, but the published native comparator is 701ce2c, not a separate d2439ac runtime measurement.

- **237/237** published path/blob-ID/SHA-256/length tuples re-derived, **1,863,212 raw bytes**. The inner publication manifest has 236 entries and excludes itself; its own hash is independently covered by the outer binding.
- Both exact source ZIP hashes reproduce; all **299/307** archived source-file hashes and complete path sets match. Canonical Git text and executed archive text differ by CRLF/LF on 278/286 entries; that distinction is retained. The ZIP hashes match without normalization.
- Six complete stored record sets, five SQL snapshots each, were independently re-analyzed without importing/executing the author's harness. SQL visibility/kill ordering, actual operation/ledger/audit/ownership/payment rows, full-row preservation, original request bodies, fresh per-phase sessions, journal bytes where published, and third-process economic non-mutation were checked against underlying records.
- The proxy's frozen source withholds all downstream bytes of the first purchase acknowledgement before the kill. The stored zero-byte flags are not an independent wire capture. JSON receipt equality is semantic, not raw HTTP property-order identity.

## Verified blockers / assurance limits

1. **Partial plausible 2xx confirmations can clear a receipt.** The client validates an item ID plus a few scalars, not a full success schema or echoed actor/route/key/body-hash identity. This is a source-proven P2 contract gap; no forged pinned-backend runtime response was demonstrated.
2. **A newly acquired owner guard is retained after staging errors**, even where no receipt was published and nothing was sent. This is a source-proven liveness asymmetry, not a demonstrated double-charge.
3. **An uncertain operation with no successful server receipt has no safe finite closure protocol.** Conservative recovery rejection retention is necessary under the current backend. Do not weaken it by clearing on 409/timeout.
4. **Missing runtime countercontrols:** interruption of the recovering process itself, competing-owner/stale-claim PostgreSQL interleavings, malformed-success injection, and low-price fee boundaries 1/33/34. No engine/cache binary re-hash, fresh native replay, power-loss assurance, or separately measured d2439ac outcome is available here.

The source audit found no source-diff weakening of the unchanged authentication, participant privacy, expected-price, integer-fee or authoritative economic boundaries. That statement is not a new live security certification or an unconditional recovery sign-off.

## Failures remain visible

The unchanged port-9 native oracle remains **36/37, exit 1**. Its separately executed one-URL external DNS calibration remains **37/37, exit 0**, under a changed condition. Earlier compile/SystemError, occupied-slot preflight, out-of-memory/tasklist, unavailable-resource-window and startup/barrier failures are retained. Later observations do not replace those failures. Author summary booleans and expected-outcome command flags are not counted as independent replay.

## Operating and size limits

Review used the explicitly approved Python **3.13.15**, serial standard-library offline analysis and Git read commands. No engine, DB, service, app, network oracle, GitHub comments, commits, posts, branch changes or deliberate index/worktree edits were performed. Repository state is recorded at both ends. Output writes are confined to this new external review directory.

**Concurrent workspace change:** initial HEAD was `2a026e61cabee3c66334066d45e92eb3ec6c2641` with a clean status. At verification, HEAD was `88bfc51da026be42b3dec517817459ed89630ded` and unrelated modified/untracked files were present; staged-path output was empty. This read-only agent issued no command that could make those content/HEAD changes and did not inspect, overwrite or revert that work. No unchanged-workspace claim is made. The evidence ref remained exactly pinned, and no audit input was taken from the changed working tree. See `PRIVATE/concurrent-workspace-observation.json` and the final state record.

The neutral packet is a compact derivative, not an undisclosed “raw” relabeling: original counts/events/timestamps/economic records are retained; source paths/identities/code/control arguments are withheld and JSON whitespace compacted. Existing credential redactions and provenance limits remain explicit. All original raw bytes are private and unchanged. Regenerable ~8 MB source ZIPs and non-published engine/cache/database artifacts are not bundled. The final manifest gives the exact logical payload size; the target is at most 5 MiB.

**Next action:** provide only `NEUTRAL/` and its manifest SHA-256 to a fresh critic. Freeze that critic's outcome-only assessment before disclosing any identity/source audit. This preparer must not act as that blind judge.
