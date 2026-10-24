# Revised decision contract R2

Status: PROPOSED, awaiting owner decision. This incorporates the independent
proposal-review findings; it does not approve implementation, capabilities or
execution. The exact first proposal remains in commit
`e73a5a2bf7baa13aec2490d8b9ad0c261d6d0963`. All old failures remain unchanged.
Where this revision differs, these explicit limits supersede R1's wording.

## Trial and deadline contract

At most four attempts, ordinary → verbose → verbose → ordinary, on one source-bound
export and Windows host. Preserve stock controls, fresh isolated profiles, natural
seeds, renderer, priority and all original gameplay guards. Ordinary disables only
engine verbosity; the existing offline trace is present in both arms. No full
qualification rerun, forced outcomes, padding, replacement trials or native retry.

Each flow retains its whole 300-second deadline. Its close wait is at most
`min(20, remaining())`, inside that deadline, not an extra 20 seconds. Static source
is `c90fedfd56a09bd0ba13cce5565ccd160891c3fb`,
`scripts/verify_offline_export.py`: deadline at line232, remaining at268, reopened
close at1060. One failure-only 5-second owned cleanup is available to the entire
collection. It cannot become normal close or a second cleanup budget.

Acquisition has a 1,205-second ceiling. Preservation starts at the first collection
cutoff: normal completion, stop decision or deadline, whichever occurs first. It
ends within 120 seconds of that cutoff, even if ownership, stop, flush or detach
cannot be proved. Failure cleanup consumes that window rather than delaying its
start. Transfer then has at most 60 seconds. Keep the original 30-minute job limit;
before the first engine require at least 1,385 seconds remaining, including all
three reserves. Setup overrun blocks before gameplay. A service or preservation
timeout is inconclusive, never an extension or retry.

## Storage and capture contract

All trial writes must use a new blank fixed 128 MiB NTFS volume whose complete
backing file is at most 129 MiB. Stop at 48 MiB captured regular-file bytes or
under 16 MiB free; filesystem capacity remains the hard bound if polling is late.
All game profiles, logs, OCR, traces, captures and trial controller streams must
route there. A known uncontrolled cache/log/output path blocks admission.

All study-owned files outside that volume, including the outer supervisor's
stdout/stderr, preallocated ledger, manifests, source receipts, raw parts, ZIPs,
temporary files and uploader disk staging, have a combined **64 MiB hard ceiling**.
The peak study-owned logical-file budget is therefore **193 MiB**, not 141 MiB.
The separately pinned SDK/export and existing source checkout are outside this
budget and must be inventoried separately. This is not a bound on the whole host
OS, service storage or network traffic.

Final control artifact has a 12 MiB limit including its intended ZIP envelopes.
Reserve bounded final-status/error space before launching. Use one-at-a-time part
staging and verified transfer; keeping all parts locally at once is not allowed
under the 64 MiB budget. A transferred generated staging file may be removed only
after byte/digest receipt verification; the complete original volume remains.
Never delete previous runs, original failure records or source worktrees.

The implementation must account for every temporary/disk write and enforce these
limits without assuming a timely polling callback. Unknown uploader staging or
unbounded supervisor diagnostics block admission. No guessed compression ratio
or unbounded diagnostic spill is permitted.

## Preservation, transfer and outcomes

When stop and ownership are verified, flush/detach and retain the entire backing
file, including unknown/partial files and filesystem state. Split it into at most
nine raw byte ranges of at most 16 MiB. Keep offsets, lengths, per-part and complete
image hashes. Retain the complete control artifact. Successful evidence requires
every required producer-shaped receipt, original strict checks, all image parts,
exact reconstruction and complete transfer.

At most ten retrieved artifacts: nine image parts and one control. Each retrieved
ZIP must be below 32 MiB; the sum of retrieved ZIP lengths is at most **160 MiB**.
This is a retrieved-byte budget, not total bidirectional network traffic. The
client's single-file STORED envelope needs a source-derived finite bound. Any
unproved service envelope remains an admission blocker; a successful old artifact
transfer does not prove a universal bound. Metadata/size/digest mismatch stops
transfer and marks it incomplete. No alternate route or extra artifact follows.

On write/quota/metadata failure, stop the collection; the affected trial is
INCONCLUSIVE_LIMIT and remaining trials NOT_RUN. On uncertain ownership or a
survivor, use only the one original owned cleanup budget, mark
INCONCLUSIVE_OWNERSHIP, and do not signal unowned processes or force a detach.
Do not wait indefinitely for preservation to become safe. At the fixed cutoff,
retain all safely accessible evidence and a reserved control receipt describing
partial, unread, unavailable or unstable image coverage. Such an image is not
complete evidence. If even control transfer fails, report the exact missing
coverage; do not claim that all captured bytes remain retrievable.

This explicitly accepts partial/unavailable failure evidence as an inconclusive
outcome in place of the impossible guarantee of retaining every unbounded failure
byte. It never permits a truncated success. Known warnings/leaks stay FAIL findings
inside an inconclusive collection. Four quiet closes still mean non-reproduction;
the original three-object leak remains unresolved. New volume I/O is a confound.

## Decision and dispatch boundary

Requested decision: approve this bounded/inconclusive contract for preparation
and one later separately admitted acquisition. Pending engineering prerequisites
are hard storage enforcement, complete write routing, finite client/service ZIP
bounds, Windows volume capability, receipt correctness, exact source and independent
admission. No changed study or capability run occurs before owner approval.

Reuse registered workflow390221868 at `.github/workflows/desktop-alpha.yml` on an
immutable own feature ref, preserving existing modes. Prior feature-ref dispatch
is evidence for this preparation route, not a guarantee of acceptance. No main
change, merge or new registration. A rejected reviewed request blocks execution;
no different workflow, payload, ref or retry follows without fresh authorization.
