# Acquisition publication correction

The exact `c7145cd48eb6d91246b526e5dc1fb5aaa655246d` wrapper is REJECTED by
independent review `b8ccf8f` (review preregistration `c81a8c9`). It is not
qualified to run. `PRESERVED_EVIDENCE.json` binds retained original wrapper,
reviewer controls, rejection, raw failed output and replay witnesses to their
immutable Git bytes before this correction. Prior source/receipts stay intact.

This source/pure-only R2 changes only acquisition wrapper, its mocked controls
and this report. Game/tests/policy, prior raw evidence, phase caps, 240-second
candidate whole cap and separate 480-second regression cap remain unchanged.
No engine, native, import, GDScript compile, CI, service or nested agent runs.
The builder cannot approve the result; fresh exact-source review is required.

The three retained witnesses must all reject after correction: a successful
candidate at 239 s followed by a 2 s overall write; a phase receipt finishing
at 121 s under its 120 s cap; and explicit `BOT_SQUAD_FAILURE` alongside the
success marker. Existing successful four/ten-stage controls must still pass.

## Registered correction

Keep the normal deadline armed through stream reads/hashes, classification,
receipt/journal writes and their final readbacks. Bound each native phase's
normal publication by the smaller phase/whole deadline. Bound overall receipt,
claim-journal publication and all final readbacks by the original whole
deadline. Check monotonic time after each I/O operation, including readbacks;
an alarm alone is not the postcondition. No elapsed-time snapshot taken before
publication may serve as proof that publication completed within its cap.

Use a small shared checked-publication helper. It writes stable snapshot values,
reads back the required artifacts, verifies their contents and checks the
same original deadline after every operation. Normal success is returned only
after the entire required publication/readback set passes. The whole alarm
is cleared/restored only after that validation. Any late write, readback,
interrupt, I/O error, or contradictory completion record makes the phase/block
terminally failed. There is no adaptive native retry and no second normal
success-publication attempt.

Emergency publication is failure-only. It may preserve/demote failed receipts
and the claim journal under one bounded five-second receipt allowance; it may
never change failure back to success or grant normal work extra time. Preserve
the first native/strict/source failure if publication also fails. Missing or
unconfirmed receipt/journal publication cannot be treated as a pass. Acquisition
success requires both confirmed artifacts and zero wrapper exit; a lone
tentative success file is insufficient. No engine is launched in recovery.

Timing fields will distinguish measured time before an artifact's own
publication from the returned duration after its final readbacks. A phase's
post-publication duration can be persisted in the later overall report. The
overall report cannot contain its own future readback time; its pre-publication
measurement will be named/scoped explicitly, while the returned report and
terminal wrapper summary carry the measured final completion duration. Both
the stored snapshot's publication and the final returned duration must satisfy
the original whole cap for success. Failed recovery timing stays visibly
outside normal-success evidence.

Reject explicit AI/dry/squad failure prefixes in complete stdout/stderr even
beside a success marker. Parse the complete relevant result-record inventory,
requiring exactly the declared successful result and no contradictory extra
or malformed result. Preserve the existing counts/mode and source fixtures.

## Pure validation and handoff

Replay the reviewer's unchanged six tests against the new wrapper, retaining
their source hash and outputs separately from original failures. Add focused
mocked boundaries for slow overall writes, slow journal writes, slow final
readbacks, phase classification/receipt/readback costs, exact successful
publication, interrupted/failed publication, and failure-only recovery. Cover
both 240/480-second whole caps, contradiction/extra result rejection and first
failure preservation. No mocked result counts as native evidence.

Retain all new commands/exits/streams, new exact wrapper/test hashes and final
source freeze. Keep the accepted candidate manifest and game/scripts tree
identical to `1b7ebc7`. Root coordinates re-review and any later runtime release.
