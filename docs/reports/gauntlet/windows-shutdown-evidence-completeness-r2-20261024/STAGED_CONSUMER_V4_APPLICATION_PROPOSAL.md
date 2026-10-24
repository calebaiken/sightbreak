# Additive V4 ownership proposal, before execution/application

This replaces only the consumer file in the held V3 application recipe. V3 stays
exact160e1726 at297373e2; all386 sealed7b043c53 members/10061463 bytes were checked
against the critic's manifest. Ten bounded selected source/results/failure files
are retained in critic-r2-staged-v3; the complete originals remain in the critic's
owned view. The original eight families pass; its five fresh guards have two
retained assertion failures. This proposal has only been parsed as syntax and
compared as AST; the builder has not imported, executed or applied it.

## Proposed application, still held

Use STAGED_CONSUMER_V4_PROPOSAL.py instead of V3 under the same private-writer/
public-wrapper recipe. Keep the exact approved V2B clock and unchanged five-site
helper seam conditional on this consumer's approval. Keep the three permitted
fixture literals and two permitted new30 adapters exactly as already recorded.
No further actual helper/test/source change follows from this proposal alone.

The exact V4 SHA256 is8d80d399f0fefb2fdd92de016a106bbdec89f2dbe523ec226b100a9af3531ffb.
The only changed class methods are __init__, put, close_owned and the finalization
part of run, plus the added read-only verify_namespace method. The new registry
stores references to the same owned records, so modeled closure wrappers remain
visible to both metadata ownership and lifetime cleanup.

## Lifecycle correction and finite-observation limit

A new record is allocated before exclusive open. Immediately after successful
open, its stream is registered in opened, then in owned, before initial fstat.
An identity failure therefore leaves a tracked partial file whose close is still
attempted. Metadata identity remains None until measured. Reusing that incomplete
record cannot authorize an overwrite; the ordinary identity guard fails. A failed
open does not invent an owned handle or a known prior file preimage. Every
registered record is closed even if its metadata was never validated or another
close raises, with the existing first-cause/chained-error policy unchanged.

After each completed byte/descriptor/path readback, verify_namespace compares the
root and every registered parent directory against its earlier device/inode/type
observation before updating the owned record. It only uses lstat: it cannot make
a missing directory, follow a symlink, adopt a new directory or repair a replaced
namespace. The same verification runs after all normal close attempts and before
successful run return. A replacement root with a hardlink to the retained file
therefore cannot qualify merely because file bytes/inodes agree. Failure keeps
the actual replacement/marker/moved object and the previous preimage policy.

These are bounded checks on fresh synthetic data. Changes after the final
observation, atomicity, NTFS/loaded code, actual OS/input/physics and unseen native
histories remain unmeasured. No source budget, waits, notifications, input/route,
callback, capture, warning policy or arm order changes. The independent critic
must replay its exact V3 guards, old eight families and registered new boundary
controls against this frozen file before permission to apply it.

The87ce sibling-originals contract/construction remains a separate held group.
No original-stream completeness claim, reader/source acceptance, real collector
or actual69-method run is made here. Public collection and all owner study/
capability, native/API/SDK/process/helper/CI and207-row replay remain BLOCKED.
