# Independent shutdown-contract proposal review

**R1 e73: REVISE. R2 3698: acceptable bounded option for the owner's decision.**
R2 is not implemented, runnable, capability-qualified or admitted for execution.
No study, Windows API/capability test, native helper, dispatch or CI run is approved
by this review. Exact frozen texts and hashes are retained beside this report.

The original proposal's largest deficiency was finite failure preservation: its
120-second window began only after processes stopped, while full-image preservation
was promised even if ownership/stop/detach could not be proved. That condition can
wait forever or leave an unstable/unavailable image. It also omitted part/control/
ZIP staging from peak storage. R2 repairs both contract defects and explicitly
accepts incomplete failure evidence as an inconclusive outcome. It is now honest
enough to put the resource/tradeoff decision to Caleb without waiting for an
implementation that has not been authorized. Engineering gates stay BLOCKED.

This is a reused independent reviewer slot, not a duplicate R7 review or fresh
thread. I edited this isolated report only; root proposal/originals remain intact.
The review uses frozen text, exposed tool descriptions, retained read-only receipts,
static source citations and arithmetic. No new API request, artifact download,
privilege probe, VHD creation/mount/flush, implementation test or native action ran.

## Recommended bounded option

Recommend R2's single four-slot ordinary/verbose/verbose/ordinary collection,
using one source-bound export and host, stock controls/natural outcomes and fresh
profiles. It changes the old two-artifact admission resource rule, not product
acceptance. It permits limits to end acquisition with honest incomplete coverage,
no replacement attempt and no claim that quiet closes fix the original leak.

| Proposed quantity | Bound and review result |
| --- | --- |
| Raw trial container | Fixed128MiB NTFS virtual capacity; backing≤129MiB, conditionally plausible but unqualified on the target host. |
| Outside study working files | Combined≤64MiB, including ledger, supervisor streams, parts, ZIPs, temporaries and uploader disk staging. |
| Peak logical study-owned files | 129+64=193MiB. Existing pinned SDK/export/source are separately inventoried. This is not whole-host OS allocation. |
| Image transfer | ceil(129/16)=9 raw parts maximum; eight16MiB parts plus at most1MiB at the bound. |
| Final control | ≤12MiB including intended envelopes and reserved final status; payload must be smaller. |
| Raw image plus control | ≤141MiB before any still-unaccounted part/service ZIP overhead. |
| Retrieved artifacts | ≤10, each strictly<32MiB, sum of retrieved ZIP lengths≤160MiB. |
| Envelope allowance | 160−141=19MiB aggregate headroom; this is arithmetic, not proof of a future service envelope. |
| Acquisition | ≤1205s, retaining four300s whole-flow maxima and the one aggregate failure-cleanup allowance. |
| Preservation/upload reserve | 120s from collection cutoff plus60s transfer reserve; no wait for stop to become provable before starting the clock. |
| Job/setup | 1800s job,1385s total reserve, at most415s setup when anchored to the actual remaining job budget. |

The300/20 arithmetic is confirmed by exact original source c90fedfd:
verify_offline_export.py:200/232/268 and initial/reopened waits884/1060 use the
same whole-flow deadline and min(20,remaining()). It would be wrong to add another
80 seconds for four close waits. Source hashes and precise citations are retained
in ORIGINAL_SOURCE_BINDING.json and ORIGINAL_TIMING_EVIDENCE.md.

## Required R1 repairs and how R2 resolves them

1. Anchor preservation to collection cutoff, not an event that may never occur.
   R2 ends preservation within120s even if stop/ownership/flush/detach fails;
   the one5s cleanup consumes this window rather than restarting it. Survivors or
   uncertain ownership mean INCONCLUSIVE_OWNERSHIP, no unowned signals or forced
   detach, no indefinite wait and no replacement trial.
2. Permit explicit unavailable failure coverage. R2 preserves the entire image
   when safe, otherwise all safely accessible data and a reserved partial/unread/
   unavailable/unstable coverage receipt. It no longer promises every captured
   byte will remain retrievable. Even missing control transfer is missing coverage,
   never a passing or silently truncated record.
3. Count peak working files. R2 sets193MiB logical peak with64MiB for every outside
   study write, requires serialized part staging, and forbids holding all nine
   parts locally. Generated staging can be removed only after byte/digest receipt
   verification; original volume and previous runs/failures/worktrees remain.
4. Separate packaged control from payload and final transfer from network traffic.
   R2 includes envelopes in the12MiB control cap and defines160MiB as retrieved
   ZIP lengths, not upload+download traffic. Whole-image/per-part offsets, lengths
   and hashes, exact reconstruction and required producer-shaped receipts remain
   prerequisites for complete evidence.
5. Treat uncontrolled writing and packaging as blockers. R2 requires complete
   study write routing, bounded supervisor output and every uploader/temp write
   accounted without relying on a timely poll. It explicitly blocks unknown staging,
   uncontrolled cache/log paths or an unproved client/service envelope.
6. Keep owner approval separate from dispatch admission. R2 requests preparation
   plus one later separately admitted acquisition. Same registered workflow/path
   and immutable own ref only; no main merge, new registration, changed request,
   alternate workflow or retry after a refused reviewed request.

These are contract repairs, not verified implementation claims. Frozen R1 and
its old approval summary stay intact; frozen R2 explicitly supersedes differing
R1 wording. No additional blocking prose repair was found for this owner decision.

## Engineering prerequisites remain unresolved

A fixed128MiB NTFS volume is a plausible design, not a verified runner capability.
The format must be pinned: classic fixed VHD and VHDX can have different overhead.
Verify exact byte capacity/backing ceiling, unique fresh mount, privileges, usable
free space, cleanup ownership and flush/detach behavior under a separately approved
capability/source plan. No existing host volume/profile may be touched or copied.
Do not infer those properties from the word fixed or from normal Windows support.

The outside64MiB ceiling needs source-derived enforcement for every writer,
including uploader intermediates and supervisor diagnostics. One-at-a-time must
mean one current part/packaging operation, with all simultaneous raw-control and
ZIP copies counted. A polling threshold alone cannot guarantee that hard cap.
A feasible implementation could partition the64MiB workspace into bounded slots;
its actual producer/client bounds must fit. No such mechanism is implemented or
proved by this proposal review. Unavoidable uncontrolled study-owned output leaves
the design BLOCKED; host OS/service effects are outside the193MiB logical-file claim.

The service ZIP boundary is also unproved. Deterministic single-member names,
client/action versions, STORED packaging and all header/extra/envelope bytes need
source-derived bounds before admission. All returned archives must fit both the
strict32MiB per-file policy and160MiB total. The exposed32MiB limit belongs to
Sediment download_file, not a proven GitHub quota. Retained artifact12558603152,
24419997 bytes/digest5622ca…, corroborates one past complete ZIP transfer; it does
not prove future envelope bounds. Oversize/unavailable/mismatched transfer is an
incomplete outcome, not permission to split another original artifact or change routes.

The metadata proves an active registered workflow and a past feature-ref dispatch.
The same frozen receipt also shows the workflow file404 at main. That evidence
cannot guarantee a new study-mode/ref request will be accepted. Exact route
eligibility remains unresolved, with no dispatch test performed. Owner resource
approval does not authorize modifying main or trying fallback workflow/payloads.

Deadlines are limits and failure classifications, not proof that a blocking OS
operation is preemptible. Future supervisor/source review must bound the whole
collection/cleanup/preservation behavior and leave unresolved stop/image coverage
inconclusive. It must not reset budgets inside nested per-process waits.

## Complete evidence and findings

All four slots must finish the original required actions/strict gates with complete
mandatory producer evidence, safe stable-image capture, exact reconstruction and
complete bounded transfer before claiming complete quiet-close non-reproduction.
A recorded leak/warning remains a FAIL finding even if another limit makes overall
coverage incomplete. Fully captured failure evidence can be complete evidence;
it is still a failed trial. An incomplete or unavailable image cannot establish
shutdown/gameplay/release acceptance. Four quiet closes still do not fix the old
three-object leak. New volume I/O remains a recorded confound.

## Pasteable owner-decision wording

Approve preparation and at most one later separately admitted four-slot
ordinary/verbose/verbose/ordinary collection under R2:193MiB study-owned logical
peak (129MiB container plus64MiB outside working space), final control≤12MiB,
up to9 image parts plus1 control, each retrieved ZIP<32MiB and total≤160MiB.
Keep original300s whole flows/min(20,remaining()) closes, one5s failure cleanup,
1205s acquisition,120s cutoff-anchored preservation,60s transfer reserve and30min
job. Limits/survivors/unavailable evidence mean explicit inconclusive coverage,
known FAIL findings persist, and no replacement/retry or original deletion occurs.
This decision alone releases no capability/native/CI/dispatch execution: exact
implementation, Windows capability, write-routing, packaging/service bounds,
source and independent admission must pass before a pushed execution release.
An unavailable registered route remains BLOCKED, with no default-branch change
or unauthorized fallback.
