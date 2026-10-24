# Bounded V2 clock/helper decision

Exact proposal `7686aac41440ece6bf84369663c27dc1790008fc`; clock draft SHA256
`9bcd688d6ed1fa774ec3e9006e7eda9b31d78321d2dd303aa60ec40a4efbac61`.
Existing independent critic thread reused. Preregistration `5c95bcba` precedes
proposal inspection; concrete controls `ef17a788` and exact test source `df59ae15`
precede execution. Production source, fixtures and tests were not edited here.

**The five-site helper architecture is supported; the exact clock draft needs
one small revision before application.** This permits no compiler, future data,
source-positive model score, production reader, or study/native execution.

## Supported helper seam

The exact patch changes only the declared construction sites: import the fixture
clock, create one clock per four-arm collection, read healthy-query timestamps
from it, pass it explicitly to the synthetic writer, and replace only the study
module's `time` attribute during the entire collector call. It does not patch
standard-library time globally. Reads do not advance the synthetic clock, and
equal samples preserve the source's before/callback/query/finish ordering.

The old fake Owner, all 28 test bodies/113 assertions, identity/fault code,
`original_query` position, accounting, callback and cleanup code remain exact
outside those five replacements. Healthy-query enrichment still follows the
original query, so its failures and survivor rows retain their effect. The same
clock remains active through final/failure paths; it is neither reset per trial
nor advanced to manufacture a successful query.

The controlled extraction verifies one clock shared by four fake writer calls
and their queries, pure reads, facade restoration on success/exception, retained
failed-arm artifact/partial result and no future success-writer call for that
arm. The original identity-read schedule remains present in the helper AST; the
eight reads in the four-arm control are the fake collector's declared schedule,
not an independently measured production collector score. Only the original
pure Owner and reconstructed helper functions were compiled with a fake study
and fake fixture module. No R2 reader or actual collector was imported/executed.

Application still requires a corrected clock and its explicit fixture consumer;
the compiler/call and staged outputs remain separately withheld. No broad helper,
Owner, assertion or input-normalization changes are covered by this decision.

## Required clock correction

Seven of eight controls pass; one assertion fails, with **zero errors/skips**.
Normal bounded advances, integer-ns bookkeeping, distinct perf/monotonic origins,
wall-only steps, invalid ordinary input rejection and the helper seam pass.

The draft's `advance()` commits `self.now_ns` before projecting its return value.
Starting fresh, integer `10**308` seconds is accepted and its reads remain
finite. A second identical finite integer advance raises
`OverflowError: integer division result too large for a float` **after updating
the stored state**. The clock is left beyond the finite-read range. This is an
interface/exception-atomicity boundary control, explicitly not a plausible
300-second study schedule, current production failure, or native concern.

Compute candidate nanoseconds and validate its finite monotonic/perf projections
before assigning state, with controlled rejection and unchanged state on every
invalid/overflow path. An explicitly supported safe schedule range checked
atomically is another acceptable narrow design. Preserve the exact rejected
draft and original failure, preregister and freeze the amended draft before its
controlled replay, and retain all original eight controls. This small correction
does not justify changing source flow budgets, clocks in archived actual data, or
any test's expected failure.

## Boundaries still withheld

The V2 macro inventory addresses the omissions identified in 2904 at an
architectural level. It is not a completed source operation/state graph. The
finished compiler must separately preserve persistent held keys, required and
conditional observations, direct release scopes, the complete focus sequence,
typed receipt relationships, and a valid declared Windows route/pulse branch.
Its clock must advance at those operations, not repair previously recorded
owner/close timestamps after the fact. Stage future outputs: a launch/fault
cannot already have successful captures or final traces from later operations.
Preserve the raw empty-output guard, unknown original artifact and partial bytes.

Clock seam controls prove no native physics, rendering, input delivery, finite
retention, complete historical history or Windows qualification. The three
previously permitted construction changes and original 0f/67a/63021 evidence
remain separate. Public collection stays **BLOCKED**; math review is cancelled
here. No native, API, SDK, proc, signal, helper process, CI or capability trial ran.

Winner: explicit shared clock and source ordering over compressed constructor
runtime, with atomic finite-read validation required. Largest remaining gap:
the unfinished independently adjudicated operation/data compiler, including
declared route receipts and failure-stage publication. The raw eight-method
output, exact reconstructed helper and state transition are retained in
`pure-r1`; this decision does not replace them with a passing result.
