# Shutdown-study decision

**Proposed R2; no execution authorized.** Approve one later, separately reviewed
four-trial study: ordinary, verbose, verbose, ordinary. Keep the original stock
gameplay, 300-second flow, 20-second close and single 5-second failure cleanup.
No replacement trials or full qualification rerun.

Capture trial files in a fresh fixed 128 MiB NTFS virtual disk, backing file at
most 129 MiB. Cap all outside study staging/control at 64 MiB: **193 MiB peak**,
excluding the pinned SDK/export. Stop at 48 MiB captured or under 16 MiB free.
Quota, write or ownership failure makes the trial inconclusive; no replacement.

Retain up to nine 16 MiB raw-image parts and one control artifact: at most ten
artifacts, each below 32 MiB, at most 160 MiB of retrieved ZIP bytes. The two-artifact count was
our earlier admission rule. The 32 MiB value comes from the Sediment file-download
tool, not a documented GitHub storage limit or the original product requirements.

Preservation ends within 120 seconds of collection cutoff, even if stop/detach
fails; transfer has 60 seconds. Retain the entire image when safe. Otherwise record
partial or unavailable evidence and an inconclusive result. **That loss of capture
is the explicit tradeoff**; it cannot pass or conceal known leaks. The volume may
affect I/O timing; four quiet closes leave the original leak unresolved.

Hard enforcement, write routing, Windows capability, client/service ZIP bounds and independent admission
must pass before a pushed execution release. Prepare the existing registered
workflow on an own immutable feature ref; no default-branch merge or new workflow
registration. A rejected route blocks execution.

Contract: [REVISION_R2.md](REVISION_R2.md). Original proposal and provenance: [PROPOSAL.md](PROPOSAL.md),
[TOOL_LIMIT_PROVENANCE.json](TOOL_LIMIT_PROVENANCE.json),
[DISPATCH_PROOFS.json](DISPATCH_PROOFS.json).
