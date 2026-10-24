# Concrete independent models, registered before execution

Frozen source is 4cf6ac8e744603ed6af122a362036d276754cc76, base
7101350e5d0a2f6e4afb9a913b5b1bcf2107857a. Initial preregistration SHA-256
67c3b248eda5cdb5dae7918b5bb3dc38f824f0601258fb34e6b1ecab2f9c504a
is unchanged. Reviewer thread reuse and initial sparse materialization failure
are explicit in PREREGISTRATION.md and SETUP_FAILURE.md. New own reviewer HEAD
bd208eac contains reports only; source is still the exact frozen candidate.

Interface inspection is complete. No maintained or independent test has run.
Production differences are inside WinUI.key_pulse only; second changed non-doc
path is test_native_route_pulse.py. Compare every one of 508 paths outside docs/
by Git mode/blob and every selected working byte against frozen Git before and
after checks. Compile the exact key_pulse AST from candidate/base into a class
with ctypes and time names supplied; execute it only on independent fake User32
and key functions. Do not instantiate WinUI, call native APIs or import the
builder's mocks into independent models. Retain helper AST/source identities.

The independent world stores rational model time, held-key state, calls, sleep
requests and ownership checks. Route clock = route epoch plus a quantized model
delta; watchdog = unrelated epoch plus its own elapsed model delta. Sleeper
advances separate model time by ceil(request * wake ratio / 100 ns) * 100 ns.
This declared timer resolution/clock family is a counterexample model, not a
measurement or reconstruction of actual Windows timing.

Registered cases and expectations:

- Positive coarse/fine matrix: route quanta continuous, .001, .015625, .0625,
  .25; phases zero, 1/8, 1/2 and 7/8 quantum; route epochs 0, 767.968 and 2**40;
  requests .0004, .015625, .12567175974707734 and 2.5; original remaining budget
  4 seconds. Complete before unchanged deadline, fixed H, all up attempts and
  neutral final state. Every sleep is positive and no greater than H minus the
  same-clock before sample and remaining watchdog duration. State and dispatch
  costs are zero in this basic matrix.
- Fine/coarse genuine early wakes: ratios 1/3 and 2/3, quantized/continuous clocks,
  unrelated watchdog epochs -10000, 0 and 1000000. Reach the same fixed target
  through positive residuals; do not slide H or require a single sleeper call.
- State/dispatch costs: initial/pre-down/post-down/read/release work advances
  model time. Preflight cost precedes H; per-key dispatch/state costs consume H.
  Passing cases retain fixed H, shorter residuals and original watchdog budget.
  Costs that exhaust H or original deadline must fail and release all attempts.
- Frozen route clock: advancing watchdog with elapsed rates .5, 1 and 2 and
  unrelated epochs. Requested duration .03, original remaining .2. Fail only
  within original remaining elapsed watchdog budget, with each sleeper clipped
  to its remaining allowance; release every attempted key. The model rates are
  artificial and prove elapsed-domain accounting, not a physical duration bound.
- No arbitrary short watchdog: freeze route temporarily past the requested .03
  pulse while watchdog elapsed is still below original .2 remaining, then resume
  route progression. The helper must remain eligible to reach unchanged H.
- Deadlines: requested .125 with original remaining .125 or .08; first sleeper
  overshoot; expensive release/state work. Equality, clipping to the deadline or
  completing/releases after it remain failures, with all attempted ups.
- Input validation: negative/zero/over-2.5/nonfinite/boolean durations, nonfinite/
  boolean deadlines and invalid/opposing/duplicate key lists. Fail before downs
  and do not dispatch invalid sleeps. Exactly 2.5 remains admitted with room.
- Clock/watchdog faults: NaN, infinities, booleans, nonnumeric, backward, OSError,
  KeyboardInterrupt and SystemExit before dispatch and after two down attempts.
  Pre-down faults dispatch no downs; post-down faults attempt both ups, retain
  failure and never label timing-invalid release evidence successful.
- Faults from sleeper, state checks, down and up operations, including partial
  two-key downs: retain exception and attempt every previously attempted owned
  up even when another up fails or a timestamp fails. A release-call failure is
  not proof of physical key release. Ownership, visibility, focus or physical
  nonneutral changes before either down reject the down.
- Base comparison uses exact old helper and identical admitted model inputs.
  Preserve at least one valid fine-sleeper/coarse-clock model rejected by old
  source and admitted by candidate. Old real runs are not rerun or promoted.

Harness safety guards may abort unexpectedly nonterminating synthetic cases;
that abort is a retained failure, never an implementation retry allowance or
passing evidence. After models, run the maintained 41 pulse methods and the
builder-declared 194-method pure regression groups using explicit Python/bash
commands only. Existing pure macos_menu tests are regressions; there is no Mac
artifact/file-handling review or native work. Retain source-bound output and
skips without treating method counts as acceptance.

If practical, initialize a separate depth-one Git source view with candidate
commit plus source trees/blobs, no parent, remote or alternate, and repeat
independent models and focused maintained pulse methods there. This is local
object transfer, not a fresh network clone. A source-only decision remains
bounded by the original unmeasured actual clock samples, nonpreemptible calls,
physical input/game consumption and unresolved old shutdown failures.
