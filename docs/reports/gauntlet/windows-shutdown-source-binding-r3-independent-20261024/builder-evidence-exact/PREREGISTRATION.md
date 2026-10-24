# Correct the demonstrated physical source read race

Root-owned new branch codex/windows-shutdown-source-binding-r3-20261024 at
/workspace/sightbreak-windows-shutdown-source-binding-r3, exact baseb692/b6da.
Independent rejectee4f8d8a preserves same-length mutation after canonical read,
restored mtime with changed POSIXctime/current bytes. Register before edits/tests.
Old source/review/checkouts remain immutable; no native admission or retry.

Add POSIX change metadata to the same-read identity comparison and independently
read bytes again before final identity comparison. Reject differing second bytes
or changed read metadata. Retain both comparison observations, not a false claim
of atomic whole-filesystem or already-loaded-bytecode attestation. Windowsctime
is not a measured NTFSChangeTime substitute; explicitly label its stability limit.
No new WindowsAPI or process action. Simulate constantmetadata Windows-like views
and verify the demonstrated first-read mutation still rejects by the second read.
Any unsupported broader Windows guarantee stays unverified/publicBLOCKED.

Pure tests preserve exactcritic race/propagation and add changedbytes with restored
mtime, metadata-masked firstread mutation and unchanged-double-read positives.
Use real owned temporary files/Git only, no game/engine/proc/API/helpertrial/CI.
Retain existing36 controls and original outputs; compare exact old case failure.
Sourceonly freeze/fullunion/purepreflight before existing independent studycritic.

This is one narrow source component. Incomplete receipt validation, unbounded
complete retention/two32MiB outerarchives and whole-study REJECT/BLOCKED remain.
No schedule/timeout/privacy/warning/capacity or game/defaultdriver change.
