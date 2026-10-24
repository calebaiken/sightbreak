# Shutdown-study decision

**Proposed; no execution authorized.** Approve one later, separately reviewed
four-trial study: ordinary, verbose, verbose, ordinary. Keep the original stock
gameplay, 300-second flow, 20-second close and single 5-second failure cleanup.
No replacement trials or full qualification rerun.

Capture every trial file in a fresh, fixed 128 MiB NTFS virtual disk, with backing
file at most 129 MiB. Reserve at most 12 MiB for the outer control ledger and
manifests. Stop the collection on quota, write or ownership failures; mark the
affected trial inconclusive and remaining trials not run. Preserve the entire
written container. A limit outcome cannot pass or conceal an observed leak.

Retain up to nine 16 MiB raw-image parts and one control artifact: at most ten
artifacts, each below 32 MiB, at most 160 MiB total. The two-artifact count was
our earlier admission rule. The 32 MiB value comes from the Sediment file-download
tool, not a documented GitHub storage limit or the original product requirements.

The tradeoff is explicit: quota exhaustion can prevent complete capture and makes
the trial inconclusive. The volume may affect I/O timing. Four quiet closes would
still leave the original leak unresolved.

Implementation, Windows capability, packaging bounds and independent admission
must pass before a pushed execution release. Prepare the existing registered
workflow on an own immutable feature ref; no default-branch merge or new workflow
registration. A rejected route blocks execution.

Details and provenance: [PROPOSAL.md](PROPOSAL.md),
[TOOL_LIMIT_PROVENANCE.json](TOOL_LIMIT_PROVENANCE.json),
[DISPATCH_PROOFS.json](DISPATCH_PROOFS.json).
