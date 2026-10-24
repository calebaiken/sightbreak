# Physical source read-race correction: source-only handoff

Frozen sourceebc1a94133d4d73c3a553d528986c8fc40c740a9 on
codex/windows-shutdown-source-binding-r3-20261024, own checkout
/workspace/sightbreak-windows-shutdown-source-binding-r3. Preregef2032dc precedes
edits/tests. Original b6da/b692 and independent rejectee4f8d8a remain unchanged.
Reuse the existing independent study critic; no fresh thread or builder approval.

The physical verifier now compares st_ctime_ns with its existing identity/size/
mtime/mode observations, reads bytes twice, and rejects changed second bytes or
metadata. Thus the demonstrated first-read canonical→same-length changedbytes→
restoredmtime case cannot produce a binding. The second read also rejects that
first-read mutation when the metadata view is deliberately held constant in a
pure Windows-like model. It does not establish atomic whole-filesystem or loaded
bytecode attestation. Windows NTFS ChangeTime remains explicitly unmeasured;
st_ctime_ns is not claimed to substitute for that native guarantee. No WindowsAPI
or platform observation was run or silently treated as passing.

Pure-r1 passes39 methods (11 physical controls+28 existing), no errors/skips,
0.715756033s outer subprocess/CPU4. New controls exercise the actual restoredmtime
mutation, constantmetadata/secondbytes detection and explicit Windows observation
scope; original hidden-index/byte/mode/symlink/race/Unicode/lineending controls
remain. Real exact-source preflight exits2/BLOCKED,513 physical files each double
read and execution_authorized=false. Full raw JSON/stdout/stderr retained.
This preflight performs source/Git reads only, never WindowsOwner/driver/engine.

Full513 non-doc modes/blobs/physical hashes match; exactly verifier/test change,
511 protected paths remain exact. Game/defaultdriver/workflow/receiptreader,
capacity/timeouts/privacy/strict warnings and four fixed arms are unchanged.

Independent review must replay the exact prior race and fresh source controls
before bounded acceptance. Windows checkout/change-time runtime remains unverified;
no native acquisition can follow from a source result. Whole study is still
REJECTED/BLOCKED for incomplete-receipt false success and no finite complete
evidence bound under two32MiB archives, including outer wrapper overhead.
No public ADMITTED path, dispatch, retry or evidence omission is introduced.
