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

## Actual source and native results

Frozen implementation: `3c4d921ffc31d849d1a70d095a31d9845307f963`.
The criteria preceded it. All runtime results below belong to this exact source,
not to the later evidence commit. `export-source.json` binds the Linux package;
both native runs use executable SHA-256
`0be9a93015afea6bc979edcad9bd8f77b4b5b377079876cd5a55f68849ba6741`.

The actual Godot frozen-fixture comparison reproduces starvation in the baseline
selector. Across desktop and touch, each side has 1,458 role samples from the
preregistered flood. Baseline `93ec98b` misses all 1,458; candidate misses zero.
The complete fixture reports 1,535 checks: baseline fails 1,492, candidate fails
zero. The extra baseline failures are typed critical-message and recovery-role
checks. Both fixture runs stay at gameplay tick zero, write no progression,
remove their owned native directory and restore the caller's original directory.
These are HUD-selector results, not objective-authority or rendered-layout proof.

Eight focused source suites pass without engine errors: match 75, reconnect
policy 21, independent reconnect 24, resume admission 13, resume alias 23 and main
42 checks, plus the actual ENet lost-welcome and authentication-loss fixtures.
Four Python observation controls pass. Replaying the original CI's actual final
dead observation now rejects it with its tick 1988, round 1, planted, actor 1,
alive false and health zero in the diagnostic; it does not pass that old gate.
Original status bytes and their hash are retained in round 1.

Two external recorder setup failures also remain. Round 1 stopped before a
display or recorder started because this environment omits the Linux
`/proc/<pid>/task/<pid>/children` file. Round 2 stopped at the validator's argument
check because Xvfb is installed outside PATH. The final one-off recorder verifies
the actual PPid and exact command of the validator-owned fresh display and passes
the installed Xvfb path explicitly. Neither setup failure is a gameplay result.

| Exact exported plant run | Recorded round 3 | No-recorder round 4 |
| --- | --- | --- |
| Whole result | FAIL, 130.871 seconds | FAIL, 129.636 seconds |
| Ordinary plant | 180 ticks / 3.0 simulation seconds | 180 ticks / 3.0 simulation seconds |
| Contribution / funds | +1 / 800 to 1100 | +1 / 800 to 1100 |
| Living rendered role capture | PASS | PASS |
| Natural objective resolution | Defenders defuse | Defenders defuse |
| Blocking failure | Original 12-second next-round wait | Original 12-second next-round wait |
| Final state | Post, round 1, 0.65 seconds left | Post, round 1, 0.65 seconds left |
| Cleanup errors | None | None |

Both runs preserve the complete original gate, including its 180-second total,
15-second role guidance, 12-second next-round, ordinary objective and interaction
deadlines. Both complete the changed living role-guidance slice and then fail
later. Neither reaches the next-round, restart or persistence checks; the full
plant journey remains failed. No budget, predicate, seed, timer or game state was
changed for the retry. Round 4 has fresh output, user directory and display;
two contemporaneous process inventories show no ffmpeg process.

The next-round trajectory is measured directly in `native-comparison.json`.
After the resolved capture ends, the driver waits 12.053 seconds in each run;
the associated match observations advance 247 ticks / 4.1167 simulation seconds.
Both final observations are tick 2625, elapsed 43.75, post, defused, with a
0.65-second post-round timer. The driver and match clocks remain distinct. These
two sequential observations do not establish a causal performance effect from
the recorder. The same next-round failure persists without recording load.

The complete original silent video is
`round-3/native-plant-silent.mp4`, SHA-256
`9527ba7f05d288c1545ea8dbc3723a83d5e19774118af099119fb6c7b0dfb7cc`.
It is a 7,961,368-byte H.264 file with one 1280 by 720 video stream, 1,304 frames,
10 Hz declared capture and 130.400 seconds duration. There is no audio stream.
The external recorder's wall lifetime is slightly longer; its original commands,
ownership, timestamps, ffmpeg log and ffprobe output are retained separately.
The video remains qualitative evidence, not a device frame-rate or latency test.

Every native top-level input/result/process log, trace and original screenshot is
retained in rounds 3 and 4. Generated shader and platform state caches are omitted
from this report; no authority or input receipt is omitted. `sha256.txt` indexes
the retained payloads. The 87 other main-controller function bodies, including
touch/feed helpers, and 72 other match function bodies, including RPC/snapshot,
authority and objective functions, match integrated `93ec98b` byte for byte.
`source-equivalence.json` records the hashes and its precise function scope.

Fresh critic `/root/postplant_guidance_critic` independently recomputed the flood
counts and raw log hashes, inspected the original role/resolution PNGs and the
complete MP4's stream/hash plus seven extracted frames, and ran 24 additional
actual connection-callback, snapshot-epoch and life/objective transition controls
with the inherited private fixture. That probe reports 1,559 checks, no failures,
tick zero and restored cleanup. Its separate report/verdict is pending; the
builder makes no acceptance decision here.

The largest remaining deficiency is the unchanged full native next-round gate,
followed by the unreached restart checks and an exact-source Windows rerun.
The engine/CPU lane has been released to the account qualification. No further
runtime is running for this branch. Canonical mission documents remain untouched.

## Graphics configuration and source-only diagnosis

The exact executed controller explicitly assigns `LIBGL_ALWAYS_SOFTWARE=1` and
`LP_NUM_THREADS=2` to the client environment in both native runs. Its recorded
SHA-256 matches the frozen controller bytes; both original client logs identify
Mesa llvmpipe through GL Compatibility. Both recorded client commands omit fixed
frame-rate and physics-override flags, and both final observations retain
`time_scale=1`. No separate OS readback of the child's complete environment was
retained. Round 4's outer-process snapshot has `LP_NUM_THREADS=null`; that is not
the client selection, because the controller subsequently sets it explicitly.
`selected-graphics-configuration.json` preserves the source fragment, hashes,
actual commands and renderer lines. Default unrestricted llvmpipe threads is
therefore not supported as an explanation for these runs.

For a bounded source comparison, `9f730dc` is the named parent of the frozen
Relay AR graphics integration `0345a18`. This is an explicit pre-integration
anchor, not a repository tag named pre-M6. Between that anchor and `3c4d921`,
the entire arena and referenced sky/material assets are unchanged. The existing
graphics-selection block in `apply_settings`, from its FPS selection through
MSAA, render scale, shadow and detail choices, is byte-identical. The function
adds display/pointer synchronization before that block. Project GL Compatibility,
MSAA and 60 Hz physics settings are unchanged; the project diff changes version
and unfocused-joypad policy. Main-controller changes cover menu/economy UI,
focus/input, diagnostic hooks, objective guidance, touch-mode synchronization
and feed refitting. Exact hashes and the main/project diff are retained in
`pre-integration-source-comparison.json` and `pre-integration-main-arena.diff`.
This inspection does not establish the timing cost of any UI change or a
performance regression; that would require matched runtime trials. No additional
runtime is authorized or running for this diagnosis.
