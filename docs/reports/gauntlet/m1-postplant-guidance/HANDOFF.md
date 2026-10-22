# Post-plant role guidance

2026-10-22. Builder branch `investigate/offline-plant-role-guidance`, sparse
worktree `/workspace/sightbreak-plant-guidance`, base `a8eb7eb`. This checkpoint
contains read-only findings and criteria declared before product changes. No
Godot, OCR or native workload has run in this investigation. Canonical mission
files are untouched.

## Reference and observed failure

Reference: actual Linux CI39725980732, frozen `872a576`. Raw receipts are under
`/workspace/reviews/native-ci-39725980732/receipts/evidence/offline-plant`.
The original failure remains `Actual attacker HUD restores post-plant role
guidance`, total 66.262 seconds.

The ordinary player interaction succeeds: input starts tick 1321 and the armed
notification occurs tick 1501, exactly 180 simulation ticks / 3.0 simulation
seconds. Contribution increases by one and credits increase 800 to 1100. The
completed capture is living at tick 1520, frame 193, health 100. Subsequent combat
notices arrive at simulation times 25.217, 29.750, 30.417, 30.550 and 32.683. The
fourth is the local player's death at tick 1833. At failure, tick 1988, the round
is still live and the device planted; the player is dead and the status is another
elimination notice. No actual PNG from this attempt is present in the bounded
receipt directory, so these are authority/UI-text findings, not a pixel review.

Clock limit: the trace's `elapsed` is match physics time. Notification expiry
uses `main.elapsed`, incremented by `_process(delta)`. The existing receipt does
not expose that UI clock or its expiry metadata. Simulation gaps must not be
presented as measured UI-clock quiet periods.

## Existing contract and defect

`hud_objective_hint_test.gd` exercises the actual `_process` label for the
attacker, defender, carrier, dropped/planted device, waiting, buy, post, completed
and spectator cases. It also preserves one unexpired notification and restores
the correct role after that notification expires. It does not exercise a
notification flood or establish a maximum role-guidance outage under combat.

Every `show_notification` call replaces status text and sets expiry to the
current UI clock plus five seconds. Thus any sequence arriving before expiry can
renew suppression indefinitely. Elimination messages also have a separate typed
`elimination_reported` signal and dedicated kill feed. This is a product priority
gap consistent with the failed run, rather than an objective-authority failure.
The source-level starvation counterexample still requires actual engine proof.

The observer has a separate diagnostic weakness: its 15-second predicate keeps
requesting attacker-only text after the actual player dies. A prompt, specific
death/context failure is appropriate; it cannot turn that failed gate into a pass.

## Preregistered scope and measured gates

1. In an operational live round with a planted device, select the current role
   hint on the next processed HUD frame and retain it after every processed frame
   while ordinary combat notices continue. This applies to living attackers,
   living defenders and eliminated spectators, in desktop and touch mode.
2. Source benchmark: use the existing frozen HUD fixture, with no gameplay tick
   advanced. Replay the retained combat messages and a 20-second UI-clock flood
   at 0.25-second intervals. Compare the baseline actual `_process` label with
   the candidate. Record every wrong/missing role frame. No quiet period may be
   required by the candidate. This is a declared UI fixture, not gameplay proof.
3. Preserve the isolated five-second notification behavior outside that urgent
   planted phase, including the existing carrier test. Preserve waiting, buy,
   post-round and completed-operation behavior and correct E/USE wording.
4. Critical connection/recovery feedback takes priority over tactical guidance
   and must survive ordinary notices, including after the ordinary five-second
   expiry. Use existing typed connection state and a presentation-only stored
   notice set by connection callbacks; do not classify freeform/translated text
   or player names. Clear obsolete critical feedback on a successful welcome.
   Keep RPC signatures, protocol 6, recovery policy and all network deadlines.
5. Add negatives for disconnected/reconnecting/failed clients under a notification
   flood, recovery to connected, dead actors never receiving attacker guidance,
   phase changes, and an ordinary isolated live notification. Preserve fixture
   ownership/cleanup and zero progression writes.
6. Strengthen the native observer to fail promptly with the actual life/actor/
   round/objective context reason. Do not extend its original 15 seconds or alter
   its required exact attacker guidance. Retain source, frame and life guards.
7. Run the exact exported plant scenario after a source freeze: real OS input,
   ordinary 180-tick plant and economy award, then actual living post-plant role
   guidance and its rendered capture under the original budgets. No pause,
   invulnerability, injection, teleport, timer or game-speed workaround.
8. A separate critic must inspect the actual notification-flood baseline/candidate
   outputs and the exact exported plant gate, including negatives. The builder
   cannot approve this correction. Failed iterations remain retained.

## Proposed smallest implementation

Change status selection only for the urgent live/planted phase. Retain the
existing notification expiry elsewhere. Read a presentation-only
`connection_notice` recorded by the existing connection callbacks, so ordinary
RPC notices cannot overwrite a failure/recovery reason. Use the existing typed
connection state to decide whether that critical reason is active; clear it on
welcome. This does not change authoritative gameplay or transport messages.

Touch ownership is coordinated: its builder changes input-mode synchronization,
HUD margins/footer and kill-feed refitting, with no changes to status priority,
`objective_hint`, `show_notification` or `_fit_status_line`. This correction will
not edit those touch/feed functions. The required art-v9 hands log fixture path
is included in the sparse checkout for eventual broad validation. No canonical
mission files will be changed by this branch.

Next: implement this bounded scope, then request a focused/native CPU window.
Touch builder/critic currently own the execution lane. Runtime verification and
independent acceptance are pending.

## Integrated source checkpoint

The criteria commit is preserved from the investigation branch as `aedb7e6`.
The implementation branch is now `fix/postplant-guidance-priority`, worktree
`/workspace/sightbreak-postplant-priority`, based on integrated source `93ec98b`.
This includes the accepted touch synchronization and feed refitting. Those
functions are unchanged by this candidate; its main-controller diff only changes
status selection. The original investigation branch and unexecuted prototype
remain recoverable, without rewriting either history.

The candidate adds a presentation-only connection reason at the existing typed
callbacks, clears it on successful hosting/welcome, and selects the current role
on each processed operational live/planted HUD frame. It retains ordinary
notification expiry outside that phase. Its observer reports actual death or
context loss before accepting the existing exact role predicate, then checks
the original living actor/round/objective again after the rendered capture.
The 15-second role deadline and all gameplay/input timers are unchanged.

The baseline comparison will load `93ec98b`'s actual main controller through the
fixture's existing `--baseline-source` option. Both sides use the candidate's
same frozen match fixture and declared typed connection fields. This isolates
the status selector; it is not a whole-product gameplay comparison. The source
benchmark also exercises the actual successful welcome callback with a valid
frozen snapshot and checks waiting, buy, post and completion after the flood.

The next exported plant run will retain a genuine, silent X11 recording from
the validator's own fresh Xvfb display, alongside original screenshots and
authority/input receipts. Record the recorder command, timestamps and hashes;
retain its output even if the gate fails. This adds capture load under the
unchanged original budgets. The video is qualitative evidence, with no audio,
speaker-listening, frame-rate or latency qualification. No native or engine run
has yet been performed on this candidate.
