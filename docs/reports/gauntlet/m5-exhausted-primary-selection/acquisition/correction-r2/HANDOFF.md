# R2 publication correction handoff

Status: source/pure candidate for fresh independent review. Runtime is held.
The builder cannot approve this wrapper. Rejected `c7145cd` and review
`b8ccf8f` remain rejected, with their exact originals and raw failures retained
by `PRESERVED_EVIDENCE.json`. Preregistration `2671fa6` preceded this correction.
Correction code is pushed at `d941cc355fbb089f80ccb09f7873fbfe8143c159` on
`codex/m5-exhausted-primary-selection-20261023`; this report commit only adds
source binding and recoverable pure evidence.

## Exact scope

`../run_acquisition.py` now checks every required receipt/journal write and
readback under its original deadline. Phase publication uses the smaller
phase/whole deadline. Overall publication uses the original 240-second
candidate cap or separate 480-second regression cap. Successful final source,
state and engine verification no longer receives a five-second allowance or
disables the whole alarm before publication. A single non-resetting five-second
allowance is failure-only; it cannot publish success or resume normal work.
Late, interrupted, mismatched or failed publication is terminal, demotes the
required artifacts where the allowance permits, and preserves the first failure.
No native recovery command or adaptive retry is added.

Complete stdout and stderr are considered together for suite completion.
Explicit AI, dry-weapon or squad failure records reject even beside success.
The complete relevant result inventory must contain exactly the existing
successful result; extra, contradictory and malformed result records reject.
The existing strict `native_log.failed()` gate still sees both original streams,
including warnings and typed shutdown leaks.

`../test_acquisition.py` only adapts the existing failure-allowance control to
the explicit failure-only API. `test_publication.py` adds focused mocked timing,
I/O, interruption, result-inventory and first-failure controls.
`replay_independent.py` injects the corrected wrapper into the reviewer's exact
retained six-test source, verified by SHA-256, without editing that source or
its original failed evidence.

Accepted game/scripts source, the 23-hash candidate manifest, the common
benchmark and maintained 1,268-row candidate are unchanged from `1b7ebc7`.
No game, test policy, weapon, audio, protocol, profile, native command, phase
cap, block order or one-shot claim policy changed in this correction.

## Observed pure results

`pure-checks/receipt.json` records exact commands, starts, exits, durations and
source hashes at code commit `d941cc3`. All three commands exit zero:

- Existing builder controls: 25 methods pass.
- New publication controls: 10 methods pass, including parameterized 240/480 s
  writes/readbacks and 120 s phase classification/publication boundaries.
- Unchanged reviewer controls: six methods pass. This is a builder replay,
  not a new independent verdict.

The reviewer's original late-overall witness now fails: the first overall
write starts at 239 s with a 1 s alarm and finishes at 241 s; failure-only
demotion finishes at 243 s with returned wall duration 243 s and `passed=false`.
The phase-write witness returns `passed=false` at 121 s under its 120 s cap.
The explicit squad-failure witness returns `passed=false` despite the success
marker. Successful candidate/regression controls still use exactly four/ten
mocked native stages and preserve audit-before-after-producer order.
Their full replay data are retained in
`pure-checks/independent/replay-witnesses.json`.

No engine, native import, GDScript compilation, real native signal, service or
CI operation ran. Mocked controls are not native output or runtime acceptance.

## Reading the publication contract

A stored receipt cannot contain the completion time of its own future write
and readback. Stored `wall_seconds_before_publication` is explicitly scoped as
a snapshot. Phase `wall_seconds` and readback confirmations are retained in
the later overall report. The overall report's final `wall_seconds`, confirmed
readbacks and `publication_confirmed` appear in the returned report/terminal
wrapper summary after required I/O. A successful acquisition requires confirmed
overall receipt and claim-journal readbacks plus zero wrapper exit. A tentative
`passed=true` file by itself is not success evidence. Failure to publish or
confirm recovery remains a failed wrapper result even if an earlier tentative
artifact could not be demoted.

## Remaining limits and next boundary

Fresh exact-source review is required before root may release runtime. Keep
the original 240/480 s whole and 120/30 s phase caps, one-shot claim and staged
private-state contract from `../PREREGISTRATION.md`. Use the exact reviewed
clean own HEAD as `--expected-head`; the final report commit is identified in
the handoff message rather than guessed here.

The accepted observation helper's polling/escaping/reparenting limits remain;
this wrapper does not prove arbitrary descendant cleanup. The original
baseline and verbose ObjectDB/audio shutdown failures remain open, with owner
and cause unproved. No selection runtime, full-match, balance, rendered,
perception or objective acceptance follows from these pure results.
