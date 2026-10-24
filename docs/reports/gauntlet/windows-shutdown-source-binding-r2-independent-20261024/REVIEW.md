# Scoped independent verdict: REJECT the remaining read-race gap

Candidate source `b6da3aecfc2d88443c5e0757a9bd9320122a1d4d`; builder handoff
`b69213b13a4503a330d283bf72565096e152f9d5`. Root built this correction; this
reviewer did not. The reused reviewer thread and shared object storage are
explicit. Initial review preregistration `e16acd68` preceded implementation or
handoff inspection and tests; concrete controls were registered at `a9d19f94`.
The whole-binding propagation check was separately registered at `fd974aec`.

The original supported static binding defect is corrected: both index flags can
no longer hide changed model/non-model bytes from the physical comparison. A
fresh same-call mutation still produces a stale successful physical receipt.
This fails the narrow registered changed-during-read criterion and requires a
separate correction. This finding does not demand an atomic whole-filesystem
snapshot or already-loaded-bytecode attestation; those are explicitly outside
the handoff's scope.

The whole study remains REJECTED/BLOCKED regardless of this component outcome.
The original incomplete-receipt success model, unbounded complete retention,
actual two-bin proof and outer-artifact wrapper bounds remain unresolved. No
native execution or admission follows.

## Supported same-call race

`physical_source_file` in `scripts/shutdown_study_retention.py:39-64` reads lstat,
then real file bytes, then lstat again. It compares device/inode/size/mtime/mode;
it omits the available POSIX ctime. The registered hook performs an actual read
of `original bytes\n`, writes different same-length bytes `changed! bytes\n`, and
restores the prior mtime before the helper's final lstat. No read result is
fabricated. Size remains15 and inode/mtime/mode stay the same, while ctime changes.

The helper returns a successful receipt for canonical SHA256
`45c0b761a6c6640319e6cddeb492718532f70161ed9174c75ca7f1158c508b2f`,
although the current file is different. The paired mutation without restoring
mtime correctly rejects. Raw inputs, before/after timestamps, current bytes and
returned receipt are in both views' `read_race_restore_mtime_True.json` controls.

The additive test repeats the same construction through full source_binding on
an exclusive temporary Git fixture, using the actual default physical helper.
The repository is clean before the call; mutation happens inside that helper
call. Full source_binding also returns BIND, with the original physical SHA256,
while current bytes differ and Git status after the call reports the changed
file. Both own and initialized-depth source views reproduce it. See
`race_propagation.py`, `own-race-propagation.json` and
`depth-race-propagation.json` for exact fixture bytes and results.

This is a concrete POSIX same-call detection gap. It is not an observed NTFS
result, a claim that future writes can be prevented, or an accusation that the
handoff promised global atomicity. A narrow fix should detect or explicitly
refuse this observed mutation using supported platform evidence. Do not infer
Windows change-time semantics from POSIX ctime; actual Windows remains unmeasured.

## What the correction gets right

The original marker under assume-unchanged now rejects on a physical mismatch.
The original plain skip-worktree case also rejects, separately retained even
when porcelain detects it first. Changed non-model files reject under both
flags in exclusive temporary Git fixtures. All required source paths must be
present; missing and leaf-symlink files reject. Owner executable-bit gain/loss
rejects on POSIX; valid ordinary/executable files bind.

The NUL parser binds exact spaces, Unicode, tabs and newline names. A disabled
optional Git filter declaration cannot redefine the frozen physical bytes; no
external filter program is run. Windows helper mode permits exact strict-UTF8
LF-to-CRLF conversion with no NUL or existing CR, records both physical and
canonical hashes, and labels NTFS executable bits unmeasured. Linux conversion,
partial conversion, invalid UTF8, NUL and existing-CR changes reject. Equal binary
bytes bind normally. These are pure helper controls, not Windows observations.

The real exact-source preflight exits2/BLOCKED and returns513 physical receipts,
execution_authorized=false. Guarded actual public collect calls none of the
owner, runtime identity reader or native driver. The fix adds no public ADMITTED
route and does not change the fixed study/retention model.

## Source and retained test evidence

`BINDINGS.json` and `BINDINGS-depth.json` directly verify all513 physical non-doc
file bytes, Git identities and POSIX owner-execute modes after the controls restore
source bytes/flags. Both source views finish clean at exact b6da3aec. The depth
repository reports shallow=true/count1; it was initialized empty and read-tree
HEAD preceded materialization. Shared Git alternates are disclosed, with no full
clone or independent object-store claim.

Compared with c90fedfd, the complete non-doc delta is only
`scripts/shutdown_study_retention.py` plus the new
`scripts/test_shutdown_source_binding.py`. All511 other original non-doc paths
remain byte/mode/blob exact. Every other original tracked path identity is also
protected. Game, default driver, workflow, old tests and old receipt reader remain
exact; the unchanged default-driver erasure test passes against its original base.
All10 actual builder manifest members match sealed Git bytes and their hashes;
exact copies, original source-freeze setup failure and preregistration are retained.

All8 new and28 maintained pure methods pass in each exact-source/depth view on
CPU4, no skips/errors. Independent23-control corpora match22 expectations and
reproduce the single race gap; full-binding propagation is separate and confirms
that gap. Original23 inputs/results remain unchanged after the additive test.
No builder source or old75de artifact was edited. Scripts, commands, exact inputs,
stdout/stderr and source receipts are retained in this directory.

Reproduce with CPU4 `python fresh_controls.py` and `python race_propagation.py`
from this report directory; environment BINDING_REVIEW_ROOT selects an exact b6da
source view and output variables keep repeats separate. The two maintained
commands are unittest discovery in scripts for test_shutdown_source_binding.py
and test_windows_shutdown_study.py. Real preflight command is
`python scripts/windows_shutdown_study.py preflight --expected-source b6da3aecfc2d88443c5e0757a9bd9320122a1d4d --output <fresh-report-path>`;
expected exit is2. These commands do not dispatch an engine or native driver.

## Comparison and limits

b6da wins the original static-byte-binding comparison: old75de's assume-unchanged
witness accepted identical identity, while this candidate rejects and reports
physical bytes for all513 paths. It also preserves all36 maintained controls.
It does not win the full narrowed correction bar because the supported same-call
race still receives a successful binding. Regression passes cannot override that
counterexample.

The largest gap within this correction is the incomplete same-call stability
check. The largest whole-study admission gap remains lossless finite complete
retention under two32MiB limits, including transport. The passed-only missing-
receipt false success from75de is unchanged and must not be treated as approved.
The old review/source/raw evidence remains intact.

No API, engine/export, version probe, native/helper trial, actual replay, CI,
Windows/Mac, codec or field-of-view activation occurred. Actual NTFS modes,
Windows line-conversion behavior and shutdown timing/ownership/leak causality
remain unverified. Any followup must be separately preregistered and frozen,
retain these falsifiers and obtain independent scoped review. Execution stays
BLOCKED throughout.
