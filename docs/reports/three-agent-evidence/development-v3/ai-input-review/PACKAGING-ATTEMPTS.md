# Docs-only packaging attempts

This supplements the **unchanged original QA failures** in `evidence/initial-attempts.md`, `evidence/host-failures/`, the retained historical logs, and native error streams. None of the events below ran Godot or changed runtime/owner branches.

1. Before authoring files, the target directory was checked and did not exist. A read-only `Get-Item ... -ErrorAction SilentlyContinue` existence query returned exit 1 because the expected fresh directory was absent. This is not a native test failure.
2. The server restarted after initial inventory reads, before this publication directory was authored. Resumed work checked that the destination was still fresh; completed native QA was not repeated.
3. The first invocation of the newly authored packaging script exited 1 while constructing source excerpts. Verified evidence copies and some derived provenance JSON had already been written **inside this directory only**. No original evidence was overwritten. Tool-reported error excerpt (not a separately captured raw stderr file):

   ```text
   Build-PublishSet.ps1:164
   if ($range[1] -gt $lines.Count) { ... }
   Unable to index into an object of type "System.Int32".
   ```

   Exact invocation, from `C:\Users\blith\AppData\Local\Temp\opencode\sightbreak-v3`, foreground timeout 120000 ms:

   ```powershell
   & 'C:\Users\blith\AppData\Local\Temp\opencode\sightbreak-v3\docs\reports\three-agent-evidence\development-v3\ai-input-review\Build-PublishSet.ps1'
   ```

   Cause: PowerShell flattened the two single-range array literals for the small arena/weapon extracts. The fix reboxes a flat integer pair before iteration. The copied evidence bytes were not changed or deleted; the safe retry verifies existing copies against their original hashes and regenerates only this task's derived receipts/checksum ledger.

4. The next invocation, with the same command/cwd/timeout, reached provenance aggregation and exited 1 at original line 196:

   ```text
   $copied.ToArray() | Measure-Object bytes -Sum
   Cannot process argument because the value of argument "bytes" is not valid.
   ```

   Cause: `Measure-Object` did not resolve a key of an ordered dictionary as a property. The fix explicitly extracts each `bytes` key before summation, for both copied and omitted inventories. Existing verified copies, receipts and source excerpts were preserved; no native command was launched.

The final packaging/verification result is reported by the delivery response and `provenance/publication-receipt.json`. Document-integrity checks are not native gameplay acceptance.
