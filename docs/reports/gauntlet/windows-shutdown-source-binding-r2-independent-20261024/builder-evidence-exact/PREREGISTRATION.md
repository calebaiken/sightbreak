# Bind physical source before blocked shutdown preflight

New root-owned branch codex/windows-shutdown-source-binding-r2-20261024 at
/workspace/sightbreak-windows-shutdown-source-binding-r2, base239fa222/c90fedfd.
Independent reject75ddeb26 proves hidden materialized source mutation can pass
Gitshow/status binding. Register before edits/tests. Existing study critic will
review this bounded component; no fresh thread or builder approval.

Implement physical identity verification for every tracked non-doc source path,
not only five model files. Read expected bytes/mode from the exact frozen Git tree,
then require actual regular bytes and supported physical modes to agree. Do not
trust assume-unchanged, skip-worktree, Gitstatus, working attributes or computed
actual hashes without comparison to the expected blob. Missing/symlinked/changed
source fails. Materialize all source in this new own checkout. Windows ordinary
LF-to-CRLF text checkout conversion may be explicitly accounted for as a recorded
raw-vs-canonical distinction, with strict UTF8/noNUL/noexistingCR checks; no general
normalization, mode-equivalence or arbitrary filter/smudge command is allowed.
Windows filesystem executable-mode unavailability must be recorded, never called
measured Linux mode parity. All canonical modes remain pinned to Git.

Pure controls use temporary owned Git repositories/files, no native/API/engine/
CI/helpertrial. Cover clean source, assume-unchanged+skip-worktree hidden edits,
non-model runtime edits, missing/symlink/mode mutation, binary/UTF8/CRLF exactness
and source race. Preserve initial actual failed model binding and exact original
source. Re-run appropriate existing pure controls; bind full non-doc composition.

This addresses ONE rejected group only. Incomplete receipts can still false-pass
inside the old pure orchestration seam and need a separate evidence-contract fix.
Whole study stays REJECTED/BLOCKED. Keep fixed four arms, original300/20 timing,
single failure-only5s cleanup, two32MiB archives, strict privacy/log/source guards.
The unbounded complete retention/public BLOCKED gate cannot be changed or bypassed.
No dispatch, acquisition, version probe or native retry/admission is authorized.
