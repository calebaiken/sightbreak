# Proposed bounded shutdown evidence contract

Status: PROPOSED — owner approval, implementation review and a separate exact-source
acquisition release are still required. No changed study or capability run is authorized.
This proposal supersedes neither old failures nor current public BLOCKED guards.

## Current constraint and provenance

The original SIGHTBREAK product request does not specify two archives or 32 MiB.
The exposed download_file tool documents a 32 MiB maximum for a Sediment-backed file.
The GitHub artifact-download tool itself documents a reusable ZIP reference but no
larger guaranteed envelope. 32 MiB per retrieved artifact is therefore our conservative
end-to-end transport guard, not a GitHub storage quota established by this task.
We have not tested a larger artifact or used another download route.

The two-archive count is this task's earlier source/admission resource rule, derived from
the QA+receipt pair and explicitly fixed in shutdown_study_retention.ARCHIVE_COUNT.
It is not a tool-documented count limit or an original user release requirement.
The unchanged four-flow/full-failure-evidence rule cannot be guaranteed inside
that pair: OCR allowed prefixes alone sum 128 MiB, other logs have no source byte
maximum, and compression/dedup cannot provide a worst-case guarantee.

## Recommended option: one quota-bounded four-trial acquisition

Run exactly four maximum attempts in order ordinary, verbose, verbose, ordinary,
using one source-bound export on one Windows host. Ordinary is engine verbosity off;
the existing offline trace remains enabled in both arms. Fresh isolated profiles,
original controls, random seeds, rendering/priority and stock gameplay remain.
Record seeds; do not force health, rounds, objective outcomes or match sequences.
No full source-suite/network/objective/full-match qualification is repeated.

The original per-flow 300-second deadline and 20-second close wait remain unchanged.
At most one 5-second failure-only owned cleanup is available to the whole collection;
it cannot become a successful close/drain or permit a replacement trial. Add a
1205-second outer acquisition ceiling that can only abort earlier. Preserve the
existing 30-minute job limit; before gameplay require enough remaining job budget
for 1205 seconds plus 120 seconds preservation and 60 seconds transfer reserve. Setup
that consumes that reserve blocks before starting the first arm.

Put all four fresh trial output/state roots in one NEW blank fixed-size 128 MiB
NTFS virtual disk. Keep export/SDK binaries outside it. Before gameplay require
its backing file ≤129 MiB, correct isolated mount and a writable fresh profile root;
unsupported privilege/API/mount/capacity blocks without an engine call. No existing
host/user volume or profile is copied. The storage mechanism needs source/pure
review and later approved capability validation; it has not run in this task.

An outer supervisor, outside the worker's owned job/volume, records a preallocated
bounded control ledger. It watches captured regular-file bytes and free space.
At 48 MiB captured bytes OR less than 16 MiB free, it stops the entire collection.
The 129 MiB backing-file ceiling is the hard storage bound if the soft monitor is
late. All trial writes, native combined logs, OCR/capture/trace/state/controller
streams must be routed inside the volume before this design can be admitted.
The ledger, fixed manifests and source/request/ownership receipts have a combined
12 MiB hard packaged limit, with ZIP headers and final status space reserved before
launch. Retained control payload must fit below that packaged limit.

On a cap, write error, metadata exhaustion or uncertain ownership, abort the active
arm, use only the single failure cleanup budget, and mark it INCONCLUSIVE_LIMIT
(or INCONCLUSIVE_OWNERSHIP). Remaining arms are NOT_RUN. They are not replaced.
Known strict leaks/warnings remain FAIL findings; collection inconclusiveness never
erases them. A limit outcome cannot satisfy gameplay, shutdown or release acceptance.

## Capture, storage and transfer bounds

| Item | Proposed maximum | Enforcement/meaning |
| --- | --- | --- |
| Whole trial evidence container | 129 MiB backing file | Fresh fixed virtual disk, verified before gameplay; filesystem capacity enforces a hard bound |
| Soft stop | 48 MiB captured data or <16 MiB free | Early stop; does not rely on polling preventing every full-volume error |
| Control/source/manifest envelope | 12 MiB retained | Preallocated/bounded ledger with reserved final status; exhaustion is inconclusive |
| Native acquisition | 1205 seconds | Includes four original flow budgets and the one failure-only cleanup; earlier abort allowed |
| Artifact preservation | 120 seconds after owned processes stop | Cannot extend gameplay/close or turn forced cleanup into success |
| Volume parts | Up to 9 parts, each ≤16 MiB | Raw byte ranges, no compression assumption; complete image reconstructs byte-exact |
| Control artifact | One ≤12 MiB ZIP | Entire bounded ledger/manifests; STORED packaging with measured headers |
| Retrieved artifacts | At most 10, each <32 MiB | Changes the old TWO count; retain the per-file transport guard |
| Total transfer guard | 160 MiB | Check actual uploaded metadata and returned bytes/digests; unexpected service envelope is a blocker |

129 MiB takes at most 9 sixteen-MiB parts. Raw image plus control is ≤141 MiB;
source-derived client ZIP bounds and explicit 160 MiB aggregate leave headroom,
without assuming compression. The exact uploader/client/service envelope must be
independently verified before admission; an unproved bound remains BLOCKED.
No old large game EXE/PCK artifact is split or transferred by this proposal.

## Complete evidence and limit semantics

After normal completion/verified cleanup, flush and detach the owned volume, split
its entire backing file and retain every part with byte offsets/sizes/SHA256 plus
whole-image SHA256. This preserves every captured file, including partial files,
unknown names and filesystem state; it does not suffix-filter or trim logs.
Keep source/EXE/PCK hashes and both initial seed records. Full trial validation
still requires all producer-shaped mandatory logs/captures/OCR/trace/profile/PID/
close evidence and strict original failure rules.

If the volume fills, a producer write can fail and some intended output may never
be captured. We explicitly do NOT call that complete evidence. Preserve the entire
already-written container and ledger, mark missing/unread/failed-write coverage,
and return inconclusive. Likewise failed flush/detach, incomplete upload, mismatched
parts or an unavailable artifact prevents complete-evidence success. No silently
truncated prefix becomes a passing record. No native retry follows a limit.

This is the requested tradeoff: bounded storage/transfer with honest inconclusive
limit outcomes replaces the old impossible guarantee of every unbounded failure
byte. The new volume can affect I/O and leak timing; record this confound. Four
quiet closes still mean non-reproduction, never a fix of run `40080238905`.

## Dispatch route and authorization boundaries

Read-only GitHub metadata confirms default branch main/public repository, active
registered workflow `390221868` at .github/workflows/desktop-alpha.yml, and prior
run `40089125575` event=`workflow_dispatch` at feature ref
`qualifier/windows-route-clock-4cf6ac8e-20261024`, SHA
`4cf6ac8e744603ed6af122a362036d276754cc76`. The workflow file currently returns
404 at main. No default-branch modification/merge or new
workflow registration is authorized or proposed.

Supported route to prepare is a reviewed dispatch-only study mode at that SAME
registered workflow path on a new immutable own development ref, preserving all
existing modes. One exact workflow-ID/ref/input request may occur only after
owner approves this contract, independent source/admission review and pushed root
release. The prior run is evidence that feature-ref dispatch worked, not a promise
that GitHub will accept a new mode. If GitHub refuses the exact reviewed route,
report BLOCKED; do not fall back to full qualification, change payload/ref, retry,
modify main, register through a merge or use an alternate workflow without fresh
authorization. No dispatch test has been made.

## Approval requested

Approve preparation and one later separately admitted four-trial study under this
quota/inconclusive contract, including up to 10 artifacts below 32 MiB (160 MiB total),
while preserving original gameplay/close/cleanup rules and no default-branch change.
Approval of this contract alone does not release execution: implementation,
Windows capability/source checks, artifact bounds and independent admission must
still pass. Otherwise retain the existing BLOCKED study; source repairs continue.
