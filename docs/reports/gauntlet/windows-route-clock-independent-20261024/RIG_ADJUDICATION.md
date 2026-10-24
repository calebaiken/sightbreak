# Independent model correction and added fault stages

Registered before the additive v2 rig is executed. Candidate remains unchanged
4cf6ac8e744603ed6af122a362036d276754cc76. The original 313-case rig and every
original outcome remain byte-exact. It reports 308 matching expectations and
five failures, not 313 passes.

Original rig SHA-256: d5a705636400525fbbeff0cbda4bdd9a25ad64ab033db65f9d7c6004dedb4375.
Original cases SHA-256: c973bd0bb28a2e46b8b61e722439ea8bc4ca7a1009e66d5e31643a9235718654.
Original summary/stdout SHA-256: 6d7c8a5aff5d405f1689867cd87b1fa64062b96bbebdf248acfc4fd6aea92cf4.

The five failures are model expectation defects, with these concrete reasons:

- Cases 225-227 deliberately make watchdog time run at twice the model sleeper's
  elapsed-time rate. Candidate correctly fails on the first budget read after
  expiry and attempts both releases. My extra assertion that failure's observed
  elapsed time could never exceed the budget ignores that a nonpreemptible
  sleeper advances this deliberately skewed clock while no code can run.
  Candidate preregistration and independent initial registration both explicitly
  disclaim preemption. Keep these skew-rate stresses as failure-detection and
  sleep-request accounting checks. Do not claim they establish an upper bound
  on an OS call or observed physical hold. Unit-rate advancing-clock cases still
  require the original operation allowance and immediate detection on return.
- Case 264 supplies -100000 on EVERY route read. There is no earlier higher
  sample, so this is a frozen negative initial epoch, not a backward step. Its
  unchanged positive absolute deadline implies a very large remaining duration;
  the harness then aborts at its read limit. This is a retained harness failure,
  not proof of a production infinite loop under the intended .2-second budget.
- Case 284 supplies -100000 on EVERY watchdog read. This is a constant initial
  epoch, with no decreasing sample. The route clock progresses and the helper
  completes correctly. Calling this a backward-read rejection test was wrong.
  Negative epochs are meaningful only with consistent relative deadlines and
  elapsed differences; the new positive epoch case supplies those consistently.

The original actual failures and source gates are not weakened. An independent
watchdog must detect operation expiry on the first returning budget read, and
every attempted owned key must receive an UP attempt even after clock failure.
No candidate code or old expectation/result file is edited.

Additive v2 methods, before execution:

1. Replace the mislabeled always-backward model with a valid first sample then
   a strictly lower second sample before any down. Preserve the original
   post-two-down backward mutations. Add a positive negative-epoch model with
   route deadline exactly epoch + original remaining and unrelated watchdog
   epoch, so its relative budget is internally consistent.
2. Keep the .5/1/2 artificial watchdog-rate cases, but judge rate-skew cases for
   immediate failure on the first returning expired read, clipped sleep
   requests and all releases. Check the hard model duration allowance only for
   unit-rate, zero-overrun calls. No elapsed expiry may return success.
3. Add true backward and NaN/+Inf/-Inf route samples at down pre-timestamp,
   down post-timestamp, sleeper return, each release pre/post timestamp and
   final completion-recording budget. Pre-down faults dispatch no down; all
   later failures attempt every owned UP and retain failure. Add equivalent
   watchdog failures at its actual returning budget-read stages: after down,
   after sleeper return and final recording. Do not pretend the helper reads
   the watchdog inside an edge when it does not.
4. Retain the first-expiry read in the independent world. If it occurs before
   releases, reject any subsequent DOWN or sleep. Require failed final status;
   permit only release/state/failed-recording work after expiry. This directly
   checks immediate handling without assuming OS-call preemption.

Run v2 in a fresh output directory. Report original failures and their
adjudication separately from v2 outcomes. No native acceptance follows.
