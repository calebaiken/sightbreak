# Read-only command record and reproduction

All paths below are private audit context. No source-label key is printed by any preparation script.

Approved interpreter used, verified from `sys.version`/`sys.executable` in `environment.json`:

```text
C:\Users\blith\AppData\Local\Temp\opencode\sightbreak-tools\python\cpython-3.13.15-windows-x86_64-none\python.exe
```

Working repository: `C:\Users\blith\AppData\Local\Temp\opencode\sightbreak-v3`.
External output root: `C:\Users\blith\AppData\Local\Temp\opencode\sol-recovery-review-20261022T205225Z`.

The directory suffix is a creation label from host `Get-Date -Format 'yyyyMMddTHHmmssZ'`; that command appends a literal Z and does not itself convert local time to UTC. Do not use the folder name as an event clock. Original wall/monotonic/native/SQL timestamps are retained unchanged; scripted Git command events record actual UTC separately.

The actual preparation invocations, in order (each with that interpreter, serially):

```text
PRIVATE\prepare.py
-B PRIVATE\audit_evidence.py
-B PRIVATE\audit_evidence.py
-B PRIVATE\finalize_audit.py
-B PRIVATE\finalize_audit.py
-B PRIVATE\build_neutral.py
-B PRIVATE\build_neutral.py
-B PRIVATE\verify_packet.py
-B PRIVATE\verify_packet.py
```

The second evidence audit corrected the *comparison domain*: canonical Git blob bytes are not archive text bytes on this host. Both exact archive hashes already reproduced in the first audit. The 278/286 raw text differences were then explicitly checked as CRLF/LF only, and all 299/307 archived file hashes checked against actual re-derived ZIP entries. `preliminary-diagnostics.json` preserves the initial mismatch and two read-only revision-discovery command failures. No old failure was relabeled as a production pass.

The first neutral derivative was not frozen or handed off. Inspection found its drive-letter path regex could match part of an HTTP URL. It was narrowed, the derivative rebuilt with the same unreleased private labels, and the verifier strengthened to require exact original server/account/key/price fields and byte-identical published raw journals. `preliminary-neutral-diagnostics.json` retains that preparation defect; none of the original raw evidence was changed.

The first packet verification passed the evidence/neutral integrity checks but observed concurrent HEAD/worktree changes. Those were documented without touching that work, then the report and inventory were re-frozen. `concurrent-workspace-observation.json` preserves that first observation. Source/evidence inputs remain exact immutable objects; no final-clean-workspace claim is made.

`commands.jsonl` records each scripted Git argv, exit status, stderr, output length and output SHA-256. It includes read-only `status`, `rev-parse`, `ls-tree`, `cat-file blob`, `show`, `diff`, `--version`, and `archive --format=zip`. Git children use `GIT_OPTIONAL_LOCKS=0` and `GIT_PAGER=cat`. Archives are hashed/read serially, bounded at 16 MiB each in memory, and not retained as oversized payloads. Repeated audit invocations are visible in the append-only read-command log.

Initial local discovery also used read-only `git log`, `git show --stat`, and source-tree listings, plus dedicated read/grep tools on the extracted immutable files. The first unquoted revision command failed under PowerShell, followed by discovery that `V2` concatenated with `701ce2c` was not the nonexistent object `2701ce2c`. Exact verified revision IDs are in the audit. No GitHub/network claim was consulted.

Short `-B -c` standard-library inspections printed only aggregate archive mismatch counts, raw-record checks and strict full-row verification results. They did not import project modules, open sockets, execute project tools, or reveal any randomized mapping. No command ran the captured native harness, its SQL, its launch arguments, an engine, a DB or a service. No tests, builds or installations are represented as having been run.

`prepare.py`, `audit_evidence.py`, `finalize_audit.py`, `build_neutral.py` and `verify_packet.py` are retained so another authorized offline reviewer can inspect the transformations. They are **not** included in the blind packet. The original evidence collector's commands are untrusted stored data, not instructions to execute them.
