# Acquisition source review: REJECT

Exact reviewed source is `c7145cd48eb6d91246b526e5dc1fb5aaa655246d`.
Do not release either native block from this freeze. This is an independent
source and pure/mock verdict; no engine, import, native signal or service ran.
The accepted game candidate and its earlier independent review are unchanged.

The strongest deficiency is the unbounded final receipt/journal write after
the whole clock is stopped. `run_acquisition.py:597–607` clears ITIMER_REAL,
records `wall_seconds` and determines success before writing
`overall.receipt.json` and the claim journal. There is no elapsed-time check
after either write. A successful candidate at 239 seconds whose overall
receipt takes two seconds returns `passed: true` at 241 seconds, retains
`wall_seconds: 239.0` and writes the success journal. The captured alarm at the
write boundary is zero. This violates the declared 240-second whole bound,
which explicitly includes normal finalization. The same code finalizes the
480-second regression block. A hung final write also has no bounded emergency
alarm. This is a source defect, not a claim that a filesystem stall occurred.

Two additional pure counterexamples remain:

* `Runner.native()` records phase wall time at line 391 before reading/hashing
  streams, writing classification output and writing its receipt. Its cap test
  uses that earlier value. The independent control gives the phase receipt a
  121-second completion under a 120-second cap; it returns without error with
  `passed: true`. The only final check at line 416 re-arms the whole clock.
  Source must account for the declared phase scope consistently and measure
  the recorded duration through the work it claims to include.
* `completed_suite()` accepts a squad success line alongside an explicit
  `BOT_SQUAD_FAILURE` line. The shared strict scanner does not classify that
  prefix as an error, and the squad completion function only counts the exact
  successful result line. The mocked regression block therefore passes all
  ten stages with the contradiction present. The frozen suite normally ties
  failures to a nonzero exit and result count; this challenge does not claim
  it has produced contradictory output. It exposes a gap in the wrapper's
  preregistered rule that an extra failure stays failed. Check all result and
  explicit failure records, including contradictory extra result lines.

The unchanged builder suite passes 25 methods with no skips. The independent
suite runs six methods: three controls pass and three safety assertions fail,
with raw streams retained. The first run used a 241-second final write from
zero elapsed; the second uses the tighter 239 + 2 second boundary above.
Both failed outputs remain. `replay-witnesses.json` retains the second run's
exact commands, state contracts, event order, reports and counterexamples.
The tests replace process/signal/clock effects; no child native process is
created and no actual Linux signal is sent.

Provenance checks pass. All 36 hashes from the wrapper and accepted-candidate
manifests match exact Git blobs. Accepted candidate manifest bytes and the
`game`/`scripts` tree identities equal `1b7ebc7`. The reviewed wrapper, builder
tests, strict scanner, native producer source and retained observation helper
bytes match the exact target. These details are in `source-binding.json`.

The successful independent candidate control uses four native calls in order:
producer before, editor/import, maintained candidate, producer after. Caps
are 30/120/120/30 seconds, and the candidate audit precedes producer after.
The regression control uses ten calls with one import, three maintained suites
in AI/dry/symmetry order and distinct XDG state directories per suite. The
argv prefix is the pinned engine plus `--headless --audio-driver Dummy --path`;
the import suffix is `--editor --import`; the candidate suffix is
`--script res://tests/bot_exhausted_primary_test.gd`. The controls preserve a
fixture HOME and do not execute the engine. Producer commands use the accepted
native PROBE literal and retain actual receipt validation in `run()`.

Source inspection and pure controls support the following narrower facts:
exclusive same-HEAD/block claims reject a new output path; fixed block
definitions remain separate; tracked project bytes are mechanically copied
against Git blobs and SHA-256; preparation distinguishes the permitted added
derived-test UID from original-byte equality; prepared non-cache contents
are fixed; producer identity rejects foreign userdata/project/settings and
known profile/diagnostic leftovers; complete stdout/stderr classification
retains ObjectDB and typed leak warnings; import, suite, source and authority
audit failures stop later native stages. A strict failed candidate can receive
only the separate pure diagnostic audit. Original failure preservation and
the registration/PIDfd/fallback paths have passing mocked builder controls.

Cleanup remains limited to observed stable identities, ancestry and anchored
session members. Escaped, unobserved descendants remain explicitly outside
the evidence. Actual PIDfd availability/signaling, registration races,
shutdown, generated UID behavior, parser/import readiness, private native
userdata and performance were not exercised. The original audio leak failures
remain failures. Selection behavior, exported gameplay, full matches and
release gates remain unqualified.

Before another source review, retain these falsifiers, correct the deadline
and contradictory-result paths, freeze the new exact source and demonstrate
normal success plus slow overall/journal writes, slow phase finalization,
interruptions and write failures without a false success or lost first failure.
Root must separately release candidate and regression runtime after independent
source acceptance. The builder cannot approve that release.
