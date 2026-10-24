# Blocked before native launch

Target: `7b6f379a3f8c809d0985a64e883cbadfdd78d135`.

**Neither S1 nor S2 has a native reproduction result from this attempt.** The specified Godot executable does not exist:

`C:\Users\blith\AppData\Local\Temp\opencode\godot\Godot_v4.7.2-stable_win64.exe`

The driver failed while hashing that executable, before creating the pre-import manifest, importing the supervisor, running its launch preflight, or launching any Godot process. `results.json` preserves the exact exception. `raw/timeline.json` is empty. No engine log or native completion JSON exists. The two signal files were written by unconditional harness finalization, not by a running native probe, and are not evidence of either control.

Read-only local searches found no Godot executable under the user profile (including hidden paths), and no matching 4.7.2 installation/archive under the approved OpenCode temporary root. No download or version substitution was attempted.

## Verified source binding, not native results

- `source/economy_ui.gd` is the exact Git blob `c482c553264781db2a66a373ab4e4496fb59531a`, SHA-256 `a6580d176216af48c447eacaf3d293d7862fb8af0f56db7a4a3b9fd4398f450b`.
- `project/transaction_journal.gd` is the complete unfiltered Git blob `cbac7a494f14c88127196c848a3f874892e7b94c`, SHA-256 `3a7e060f7d5c3a65f4b983edf3c56d008cb070a8948bdcb128681bd4ce562d03`.
- `project/receipt_predicates.gd` prefixes only `extends RefCounted` plus a blank line to the complete production region `economy_ui.gd:597-608`. The production region's SHA-256 is `d03956cc6edf8fad989827bfa6b7f69dbca0247d484f6156b4d12e41f0ea521b`; wrapper SHA-256 is `60b5006ed7336c3755321fccb5b25069b1c975f1300a95fadd3619b978daa347`.

## S1 source observation / pending controls

`game/scripts/ui/economy_ui.gd:597-608` checks nonempty string `item.id`, then integer/range checks and a nonempty string `table_version` for cases. Source inspection indicates these exact bodies satisfy those predicates:

- Market path: `{"item":{"id":"unrelated"},"credits":0,"fee":0}`.
- Case path: `{"item":{"id":"partial"},"roll":0,"table_version":"anything"}`.

The prepared probe includes these two cases, three synthetic legitimate-shape positives, seventeen clearly malformed negatives, and three direct integer-helper controls. **All 25 remain NOT RUN.** No HTTP status was produced or tested. No backend response was forged. These are not assertions of any invented authority contract.

At lines 559-563, a pending success result is replaced only if the predicate rejects it; lines 584-586 resolve a result without `_error`. Therefore receipt clearing for an accepted body follows only conditionally by source logic, including `clear()` succeeding. `_send_transaction`, `_receipt_resolved`, and `clear` were not invoked.

## S2 source observation / pending controls

`game/scripts/ui/transaction_journal.gd:76-90` acquires first (77), then returns for invalid data (82-84), oversize data (86-87), or open failure (88-90), without releasing the newly acquired guard. The source has later early returns through line 102 as well. `claim()` separately tracks prior ownership and releases on its own failure (34-43); `stage()` does not use that pattern.

The prepared two-process control was: A stages `{}` and remains alive without a pending file; B's valid stage at the same new path should be blocked; after A exits, the same B retries successfully and leaves its published receipt intact. **A invalid stage, B blocked stage, and B positive retry all remain NOT RUN.** Oversize/unwritable branches were never planned as executed controls and remain source-only observations.

`game/scripts/ui/economy_ui.gd:543-550` returns before `_send_transaction` on stage failure. That is source inference only. No independently measured network count is available.

## Scope and preservation

- Zero native Godot launches; no listeners or pending receipts were created.
- No owner-source edits, DB access, service changes, GitHub operations, commits, full game/assets/Match/export/campaign launch, or private API aliases.
- Existing dirty owner integration was not used for the production components. Captured Git status before/after the failed attempt is identical.
- Failure records and prepared harness are retained unchanged. `blocked-source-manifest.json` records post-failure byte/hash verification; it must not be mistaken for a successful pre-import engine manifest.
- No broad recovery-safety or performance conclusion is supported.

A corrected local path to the requested official Godot 4.7.2 executable is required to continue. A fresh evidence directory is necessary because this failed attempt already has immutable receipts and finalization signals.
