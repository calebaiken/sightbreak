# Publication contents, omissions and integrity

This is a compact, source-backed **selection** of the completed exact-input QA bundle, not a new run or a complete source distribution. Main retains V2 bot runtime; nothing here authorizes wholesale merging `48eb058`.

## Included

- `REPORT.md` — publication decision, source-backed findings, scope and limits.
- `CHRONOLOGY.md` — neutral-assessment ordering, exact timestamps and evidence-strength caveats.
- `COMMANDS.md` — original command locations and strict-versus-adapted reproduction boundaries.
- `Build-PublishSet.ps1` — path-pinned, docs-only copy/receipt/checksum generation. Authored with patch; never runs native tests or git.
- `PACKAGING-ATTEMPTS.md` — the later docs-only restart, expected missing-directory query and packaging-script error/retry; separate from original QA failures.
- `evidence/neutral-first-assessment.md`, protocol and neutral mappings — unchanged originals, including the invalid first mapping attempt.
- `evidence/commands*.jsonl`, `runtime-*/`, `extra-*/` — unchanged receipts and raw streams for direct native controls and repeated strict/API, real-equipment, adapted-behavior and policy tests. The elimination callback has one run per tree, not an invented repeat.
- `evidence/logs/*-match-check-only.*` and `provenance/compile-receipts.json` — both direct native match compilation outputs/receipts, without a fixture.
- Native engine/import, commit-claim, ancestry, final HEAD/status and original failed-verifier status logs; source identity/hash/status manifests.
- All five authored native `.gd` fixtures, the five retained `.gd` fixtures actually rerun, original command drivers and summary-analysis script. They are archival evidence, not changes to runtime.
- `evidence/initial-attempts.md`, all `host-failures/` files, and **every historical retained-V2 `.log`** — original errors, retries, failed imports, indentation and expectation mistakes remain visible. Historical V2 logs are not represented as PR14 runs.
- `evidence/comparison-summary.json` — unchanged machine summary of native observations; no behavioral simulation.
- `provenance/source-excerpts.json` — selected line ranges with commit/path/blob/snapshot/native-byte hashes. Full source snapshots are not copied.
- `provenance/chronology.json`, `repeat-verification.json`, `publication-receipt.json` — mechanically derived chronology, captured-stream repeat checks and packaging provenance.
- `provenance/copied-files.json` — exact package-to-original mappings, bytes and hashes for unchanged payload copies.
- `provenance/omitted-files.json` — **every original payload not copied**, with its original path, bytes, hash and retained external location.
- `provenance/external-SHA256SUMS.txt` — unchanged complete original checksum ledger.

Pre-ledger mistakes have only the original narrative where raw output was never retained; no replacement raw logs were fabricated. All available raw host OOM output is copied. The unmodified initial-attempts narrative ends with broad “read-only source” wording; this means no authored source edits. The explicit later status verification records generated tracked `.import` changes and takes precedence over any implication of fully clean worktrees.

## Complete external archive

```text
C:\Users\blith\AppData\Local\Temp\opencode\sol-ai-evidence-20261019
```

- **341 hashed payload files + `SHA256SUMS.txt` = 342 files**, 2,256,625 logical bytes at publication preflight.
- Original ledger SHA256: `726e035f325d2d1f0a1f254ce35314dbdedfbed263385d4d696a4b1150933b68`.
- Original full `REPORT.md` SHA256: `d0c3de201f9489bd29d44481f3f4e824a5287c45f10204101d78540e0071f30d`.
- The packaging script verifies all 341 original payload hashes before copying, rather than trusting only a selected subset. The complete external archive is not modified.

## Raw material intentionally not copied

Full `baseline-source/` and `candidate-source/` snapshots; large whole-tree diffs, parent patch and complete source-tree listings; the 32 generated import-metadata payloads; redundant per-side summary JSON; unused historical probe/code/patch/JSON files; repeated verification logs and mostly empty recovery/status streams; original setup/verification/sealing utilities and the original full report remain external. The copied full root ledger still references some of those omitted raw paths: **a receipt reference is not a claim that its raw file is included**.

The omissions JSON is authoritative at the individual-file level. It also makes the compact set auditable against the complete external checksum ledger. Native source excerpts are derived, not a substitute for entire raw snapshots when auditing context. The original source can be recovered with the exact commit and `git show` commands provided in the excerpt records.

## Checksums and size conventions

`SHA256SUMS.txt` covers **every other included file**, including authored documents, generated receipts, copied empty streams and the copied external ledger. As with the original bundle, it cannot recursively checksum itself; its own SHA256 is supplied in the delivery response. Counts include zero-byte files; bytes are the sum of file lengths, not filesystem allocation or a compressed archive size. The packaging script emits the exact final count/bytes and verifies every payload entry after sealing.

No current native, graphical, build, mobile or network validation is implied by these document-integrity checks. No campaign was run on the dirty integration checkout. Only this fresh docs directory is written; existing V2 evidence, other V3 docs, runtime files, owner branches, commits and GitHub are outside this task's write scope.
