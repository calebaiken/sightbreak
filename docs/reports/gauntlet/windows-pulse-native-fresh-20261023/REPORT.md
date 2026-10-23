# Independent actual Windows qualification at 49ae54b0

**FAIL for the selected Windows qualification.** Run
[39940242244](https://github.com/calebaiken/sightbreak/actions/runs/39940242244),
job `120369601915`, attempt 1, executes exact
`49ae54b0e4f5d880bdf06e4eb783a616b2dff684` on immutable
`codex/v1-qualify-win-49ae54b0`. Ordinary undelayed exported input fails its
reload-start wait with zero observed authority fire/reload consumption. The
living settings route leaves the original corridor during coarse movement,
before the new fine pulse executes. Settings, LEAVE/reopen and focus remain
UNREACHED. No retry is approved by this review.

| Actual component | Independent outcome |
| --- | --- |
| Native source regressions | PASS: 16 suites / 29,550 checks, 50 Godot invocations, 33 native producer probes |
| Workflow pure controls | PASS: 49 methods across the five original groups |
| Ordinary undelayed exported input | FAIL: original reload-start wait expires; zero observed shots/fire/reload |
| Four-second delayed release-first input | PASS: four consumed shots, reload, final RIFLE 30/86 |
| Four-second delayed legacy held-fire diagnostic | PASS: seven consumed shots, reload, final RIFLE 30/83, inner exit 0 |
| Living settings route | FAIL: live actor crosses xmin=-8.5 at x=-11.5494471; no fine pulse or stopped endpoint |
| Actual player plant / natural resolution / next BUY / default restart | PASS under the original interaction conditions; player is dead by the natural defuse resolution |
| Actual player defuse / next BUY / default restart | PASS under original limits |
| Unseeded stock match / earned disk and runtime reopen | PASS: eleven rounds, 4:7 local victory, exact 120 XP / 325 offline credits |

The single largest remaining gap is reliable ordinary-control delivery through
the coarse approach and release to the stopped living cover endpoint within
the unchanged corridor and shared deadline. This attempt cannot qualify the new
fine-pulse implementation because that path never executes. The independent
ordinary exported-input failure also remains a release blocker.

## Living route failure and missing later coverage

The journey fails after 105.703 seconds of the original 300-second flow cap.
The second-LIVE wait begins at driver time 97.812 with its original shared
35-second budget. The route starts from stock x=-4.4000001, z=-21, stopped and
neutral, tick 3170. All seven accepted raw route states preserve actor 1,
deaths 1, team 0, round 2 LIVE, 100 health, SMG 30/120, focused unpaused game
and unit simulation speed. No endpoint-completion receipt exists.

The last accepted state is tick 3313, x=-8.3977795, horizontal velocity -5.10 m/s.
It is moving and 0.5977795 m from target x=-7.8, so it fails the original stopped
endpoint requirement. The rejected newer state at tick 3352 is x=-11.5494471,
z=-21, velocity -2.30 m/s, still alive at 100 health with the same identity,
death count, weapon and ammunition. It is 3.0494471 m outside the declared
corridor and 3.7494471 m from the target. The independent reconstruction agrees
with the original typed `SETTINGS_ROUTE_PRECONDITION_LOST` reason
`left_declared_clear_corridor`. This is a corridor failure before budget expiry.
[Raw state reconstruction](audit-r2/settings-route-recomputed.json).

There are zero `native_pulses` and no pulse-before/pulse-after events. The new
`WinUI.key_pulse` and its per-down guards remain runtime UNREACHED. Coarse D-down
after-call is recorded at 103.078 seconds, with repeated D-down after-calls at
103.609 and 104.203. D-up after-call is 104.765, then the settle-begin record at
104.859 refers to tick 3313. These are driver/API and OS-state brackets, not
exact physical hold intervals or a causal latency measurement. The unchanged
coarse path and its original observations require investigation before another
source proposal. [Pulse absence](audit-r2/route-pulses-recomputed.json).

Original pixels corroborate earlier living SIDEARM 14/60 after fire, 15/59
after reload, round-2 BUY and purchased SMG 30/120 at 100 health. The reached
`06c-next-round` phase capture passes its original before/barrier/newer-after,
source, owning process and shared-budget checks. No completed route image,
weapon-switch captures, field settings transaction, explicit settings resume,
strict LEAVE lookup/click, return menu, normal first close, settings save,
reopened settings process or focus capture exists. No typed focus failure is
claimed because focus testing never begins. The single failed journey client
exits 1 during failure cleanup; normal-close gates remain false.
[Phase audit](audit-r2/phase-captures-recomputed.json) and
[focus audit](audit-r2/focus-actual-recomputed.json).

## Ordinary input failure and separate delayed schedules

Ordinary undelayed input fails after 187.828 seconds, within its 240-second cap.
The original ten-second `Authority confirms reload start` wait expires. Its
failed native telemetry retains 117 samples, including 44 joined-actor samples:
all show zero shots, no fire input, no reload input, RIFLE 30/90 and zero reload
countdown. The success-only `authority.json` is absent and stays unqualified.
Both owned client/server processes exit 1; cleanup records no errors.

The actual native client log records disconnect, reconnect and a second joined
session. The server records two `Operator disconnected; bot taking over`
notices. Last retained peer-bound sample is wall timestamp 1792752122282,
tick 3195, ACK 382; the following sampled unbound state is 1792752161118,
tick 3225, ACK 502. Actual LMB-down timestamp 1792752157461 lies inside that
38.836-second observation gap. R-down timestamp 1792752181847 follows the
unbound sample. OS bitmaps show real LMB/R state changes, but these do not prove
game consumption. The three original fire/after-fire/failure PNGs are byte
identical and show 30/90. The exact disconnect time and underlying cause remain
unresolved; no missed-input, latency or causal source regression is established.
[Independent failure facts](audit-r2/ordinary-failure-recomputed.json).

Release-first passes in 147.125 seconds with four shots and exact 30/86 final
ammunition. Legacy delayed held-fire passes in 73.344 seconds with seven shots,
exact 30/83 and inner diagnostic exit 0. Both preserve actual consumed ACKs,
reload input/start/countdown/completion, original waits and normal exits.
Their five-second completion waits finish within 2.312 and 4.500 driver seconds,
respectively. Transient fire images still show 30/90; later originals corroborate
depletion/reload/completion without exact image-to-authority tick binding.
These two bounded passes cannot replace the failed ordinary schedule.
[All three original schedules](audit-r2/input-schedules-recomputed.json) and
[authority recomputation](audit-r2/raw-recomputed.json).

## Objectives and earned training

Player plant passes in 92.782 seconds of 180. Its stopped endpoint error is
0.389998 m under the original 0.45 m tolerance, with settled ticks 1247/1260 and
4.078 seconds under the original 15-second movement bound. Interrupted E resets;
the final uninterrupted E consumes exactly 180 ticks, one contribution and
ordinary 800-to-1100 credits. The planted-role observation and original capture
preserve the same living attacker at 100 health with `DEFEND THE DEVICE`.
An ordinary defender naturally defuses. By resolution, the player is dead at
0 health and the original image shows ELIMINATED/SPECTATING. The original
controller requires life for the action and planted-role capture, and genuine
device resolution afterward; it does not require survival through resolution.
No living-through-resolution result is claimed. Next BUY returns the same local
ID at 100 health within 5.016 seconds of the original 12-second bound.

Player defuse passes in 81.781 seconds of 180 after an ordinary bot plant.
Endpoint error is 0.020552 m, settled ticks 1325/1338, conservative movement bound
5.391 seconds of 15. Interrupted E resets; the final hold consumes exactly
300 ticks, one contribution and ordinary 800-to-3800 credits. Both objective
fixtures reach next BUY, close normally and reopen unchanged default profiles.
They create no earned save. Full separate settled-input snapshots are not retained
beyond the native tick/endpoint receipts.
[Original objective stage checks](audit-r2/objective-stages-recomputed.json).

The stock match completes eleven natural rounds and halftime with ten actors,
one completion and zero dropped events. Its 198 events span 382.95 simulation
seconds and 466.219 wall seconds under the original 1,800-second cap. Final
attack:defense is 4:7, local victory with 0 kills / 0 assists / 9 deaths /
0 objectives. Recomputed earnings are exactly 120 XP / 325 offline credits.
One history entry, original saved JSON and the distinct reopened process's
loaded profile/settings agree exactly. The original result, roster, reopened
training record and fresh stock HUD corroborate them. Both processes exit 0.
Two planted-state events and two natural device defuses are observed. This
single unseeded match does not qualify representative bot reliability or a
bot-quality improvement. [Full-match reconstruction](audit-r2/raw-recomputed.json).

## Source, strict logs, originals and limitations

Preregistration `80b635f2`, exact combined-source acceptance `97714ae6` and root
release `ab7eaebc` precede dispatch/run creation. GitHub binds attempt 1, one
Windows job and exact 49ae54b0; independent remote-ref readback agrees.
[Chronology](dispatch-chronology.json). No new dispatch or native engine was
executed by this critic. Review commands use CPU 4; only this report directory
is changed in the critic's own branch.

All 16 native suites pass 29,550 checks, including 20,116 exhausted-primary
checks. Independent audit reconstructs 1,268 emitted exhausted-primary rows /
75,890 predicates, 1,974 dry-primary predicates and 4,399 gunplay predicates.
The native runner preserves all 50 Godot invocations, 33 producer records,
original 120/30-second limits, private native userdata identity, unchanged
source/copy inventories and owned cleanup. Its 199 command/producer assertions
pass. The five workflow pure groups execute 24+5+7+5+8 methods, all passing.
The prior source critic's pure/shallow proof remains separate; this job is not
a new full maintained aggregate.

All eight source records reconcile to clean exact source, game tree
`1632ae1175028665ddb4cb72e0afba56f723de5d`, shipping content digest
`d5bcec25d5fa488ae3e1bbbaaf82091a3e0493b984615af94df650a550b94515`
and native validation digest
`f4603f73bddc81032daca8aa7a2488d8adba4561d2622ffc98cfd9b51f058383`.
All 327 native copied game-resource hashes match. Exact Git Windows checkout
filters independently explain thirteen CRLF paths, including the new strict-log
fixture metadata. The failed journey's success-only controller digest is absent
and remains false; the complete validation inventory binds its source bytes.
[Source reconstruction](audit-r2/source-Windows-recomputed.json) and
[independent filter proof](windows-filter-reconstruction.json).

Every one of 137 transferred native logs, including 97 regression logs, passes
the complete exact source matcher and the added orphan/positive-unclaimed
StringName checks. No tail excerpt or clean-log flag substitutes for the full
streams. Scoped process exit and private namespace cleanup receipts verify;
normal failure cleanup does not qualify normal close, and runner cleanup text
does not prove a host-wide orphan scan. Historical audio leaks remain unresolved.
[Deliberately failing overall completeness audit](audit-r2/runtime-completeness.json).

Both official ZIP sizes/digests match GitHub metadata. All 224 selected original
receipts match the complete 293-file QA artifact byte for byte; all 69 original
PNGs decode and pass integrity checks. Thirty-one originals were directly
inspected, with hashes and observations in [visual review](visual-review.json).
Both original ZIPs, complete original job-log response and all failed-stage
evidence remain retained. Signed transfer URLs are omitted from publication.
[Transfers](supported-transfers.json). The review's initial CRLF and missing
success-only-summary setup failures remain in audit R1; R2 changes only the
reviewers' assumptions. [Corrections](REVIEWER_CORRECTIONS.md).

The native EXE receipt is 113,575,912 bytes, SHA-256
`eaadf9cc5f1d126bb53c3d709701d552f3cea74fa6f048edcabf953e6c56ecd7`,
joined by seven runtime receipts. Native inspection records 134 embedded PCK
resources and clean headless/graphical startup. The 141,138,061-byte development
artifact exceeds the supported 32 MiB cap and was not requested. Independent
EXE/PCK reparse remains unqualified. This is a Godot 4.7.2 debug export on hosted
Windows with ANGLE/Microsoft Basic Render Driver; no physical GPU/input/audio,
human play, release package or Steam acceptance follows.

For the preregistered regression comparison, **e28c8e9 is better on achieved
ordinary-input and fine-route coverage**: its ordinary input passes and its route
reaches fine corrections, while this attempt fails ordinary input and leaves the
corridor before the new fine path. This attempt separately wins the observed
legacy diagnostic. Both overall Windows qualifications fail. The runs are
unpaired hosted executions and establish no causal timing, input, survival,
performance or bot improvement. All original deadlines, health/life/corridor
guards and human/physical/CS2/Steam/whole-release gates remain unchanged.
