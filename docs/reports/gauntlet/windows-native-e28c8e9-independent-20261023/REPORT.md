# Independent actual Windows outcome at e28c8e9

**FAIL for the selected Windows qualification**, run
[39926044462](https://github.com/calebaiken/sightbreak/actions/runs/39926044462),
job `120322557935`, attempt 1, exact source
`e28c8e90b9ef2d0c766bd9152c194e3197ceba9a` on immutable ref
`codex/v1-qualify-win-e28c8e9`. The ordinary settings route leaves its declared
corridor before reaching cover. Weapon switching, settings, strict LEAVE,
settings reopen and the entire focus sequence are unreached. The separate legacy
delayed-reload diagnostic also fails its original completion wait despite its
outer workflow step reporting success.

| Actual component | Independent result |
| --- | --- |
| Maintained native source suites | PASS: 15 suites / 9,434 checks with original receipt audits |
| Ordinary exported OS input | PASS: real consumed fire/reload, four shots, final RIFLE 30/86 |
| Four-second delayed release-first input | PASS: real consumed fire/reload, four shots, final 30/86 |
| Original four-second delayed held-fire diagnostic | FAIL: original five-second reload-completion wait expires; both owned processes exit 1 |
| Living/settings route and later journey | FAIL: x = −8.6911116 exceeds the declared −8.5 boundary; later stages unreached |
| Player plant / natural device resolution / next BUY / default restart | PASS: ordinary defender defuse, player still alive at resolution |
| Player defuse / next BUY / default restart | PASS under original limits |
| Unseeded stock match / earned disk and runtime reopen | PASS: twelve rounds, 7:5 local defeat, exact 120 XP / 250 offline credits |

The single largest gap is reliable actual ordinary-control delivery to the
declared cover endpoint, with a stopped living actor inside the original corridor
and budget. The complete living settings/LEAVE/reopen/focus/normal-close journey
still has no actual pass. Static route acceptance `5820ca7` and combined source
acceptance `47c8600` retain their source-only scopes.

## Route failure and unreached coverage

The journey fails after **108.782 seconds** of its original 300-second cap.
The second-LIVE wait begins at driver time 98.625 with its unchanged shared
35-second budget. Route readiness is observed at 102.844; the route fails at
108.532, before that budget is exhausted. This is a failed corridor predicate,
not a timeout or lost living actor.

The start is ordinary round-2 stock spawn x = −4.4000001, z = −21, tick 2938,
at rest with neutral controls. All twelve retained accepted route states preserve
actor 1, deaths 1, round 2 LIVE, 100 health, team 0, SMG 30/120, focused unpaused
game and unit simulation speed. The original D/A input actions and newer native
states show actual horizontal movement. At tick 3068 the actor is stopped at
x = −8.3950014, 0.5950014 metres from the target, outside the original 0.45-metre
endpoint requirement. A later accepted stopped state is x = −6.2700005 at tick
3159. No settled target-completion receipt exists.

The rejected newer state at **tick 3211** is x = −8.6911116, z = −21, horizontal
velocity −3.7 m/s. It is **0.1911116 metres outside the corridor** and 0.8911116
metres from target x = −7.8. The actor remains alive at 100 health, with the same
identity, death count, weapon and ammunition. Independent reconstruction agrees
with the retained typed `SETTINGS_ROUTE_PRECONDITION_LOST` reason
`left_declared_clear_corridor` and binds the prior valid and rejected originals.
No death, hidden relocation, missed input or collision defect is established.
[Route audit](audit-r2/settings-route-recomputed.json).

The approach records two correction pulses, requesting 0.154589 and 0.125769 wall
seconds. The traced A-down→A-up and D-down→D-up after-call intervals are 0.500
and 0.515 seconds. Those are driver action brackets, not exact physical key or
simulation intervals. They expose actual acquisition costs absent from pure
callback models; they do not authorize a causal performance claim or any relaxed
movement criterion. A/D dispatch and actor motion are retained; the OS bitmap
samples r/d/w, so no separate A bitmap is claimed.

The reached `06c-next-round` living BUY capture passes its complete native
before/barrier/newer-after, PID, source and original shared 160-second binding,
with 135.985 seconds remaining. Original HUD images show SIDEARM 14/60 after
fire, 15/59 after reload and purchased SMG 30/120, all at 100 health. Seven native
OCR stdout calls have matching hashes/counts, complete untruncated bytes and
zero exits. Success-only numeric result fields and final controller digest are
absent because the journey fails. [Phase audit](audit-r2/phase-captures-recomputed.json)
and [OCR audit](audit-r2/journey-OCR-recomputed.json).

No `06f/06g` switch captures, field settings transaction, explicit settings
resume, strict LEAVE lookup/click, return menu, normal first-client close,
settings disk save, reopened settings process, `10` bracket or `11a/11b/11c`
focus captures exist. No typed `FOCUS_PRECONDITION_LOST` exists because focus
testing never starts. The single journey client, PID 9028, exits 1 during failure
cleanup with no recorded cleanup errors. Neither normal-close gate passes.
[Focus audit](audit-r2/focus-actual-recomputed.json).

## Separate input, objective and earned-profile results

Ordinary exported input passes in 72.219 seconds; release-first passes in 96.891
seconds. Native telemetry verifies real consumed ACKs, four shots, depletion,
reload and exact conservation to 30/86 under original commands and limits.
Original ordinary after-fire pixels still read 30/90; release-first reads 26/90.
Both completed-reload originals show 30/86. These transient screenshots do not
identify an exact authority tick or input-to-photon delay.

The legacy diagnostic retains its four-second delayed held-fire schedule and
240-second whole cap, but **fails in 113.141 seconds**. Its original completion
wait starts at 105.610 with five seconds. The timeout at 110.797 retains ammo
26/90 and reload remaining 0.266667; the following failure retains that same
incomplete sample. The first complete 30/86 authority sample occurs **106 ms
after the timeout's native wall timestamp**. The later failure observation,
final authority summary and failure PNG therefore show completed reload. They
cannot erase the expired original deadline. Real R input and reload countdown
were consumed; this does not establish missed input. The inner diagnostic exits
1, as do its client and server; the existing wrapper preserves that result while
its workflow step exits successfully. The overall qualification and the
three-schedule completeness predicate remain failed.
[Legacy failure audit](audit-r2/legacy-failure-recomputed.json).

The real player-plant fixture passes in 92.703 seconds of 180. Its endpoint error
is 0.022779 m, settled ticks 1377/1390, conservative movement bound 5.468 seconds
of 15. Interrupted E resets; final uninterrupted E consumes exactly 180 ticks,
adds one contribution and ordinary 800→1100 credits. Original images show
DEFEND THE DEVICE, DEVICE 34s and 100 health through ordinary smoke. An ordinary
defender naturally defuses; the player is still alive at 25.2098 health and
3000 credits at resolution. Next round BUY is bounded by 5.360 seconds of 12.
Both clients close normally and restart with the unchanged default profile.

Player defuse passes in 76.125 seconds of 180 after an ordinary bot plant.
Endpoint error is 0.122234 m, settled ticks 1273/1286, movement bound 2.984 seconds
of 15. The interrupted hold resets; the final hold consumes exactly 300 ticks,
one contribution and ordinary 800→3800 credits. Native pixels show DEVICE/DEFUSED,
100 health and next round BUY within 4.765 seconds of 12. Both clients close
normally and default restart compares correctly. The incomplete objective
fixtures create no earned save; these restarts are not earned disk reload.
Separate full settled input snapshots are absent beyond the retained native
tick/endpoint receipts. [Objective stages](audit-r2/objective-stages-recomputed.json).

The unseeded stock match passes twelve natural rounds and halftime with ten
actors, one completion and zero dropped events. Its 224 events span 399.466667
simulation seconds / 480.094 wall seconds, under the unchanged 1,800-second cap.
Final attack:defense is 7:5, local defeat with 0 kills / 0 assists / 11 deaths /
0 objectives. Recomputed earnings are exactly **120 XP / 250 offline credits**.
Final native profile, one history entry, parsed original saved JSON and the
distinct reopened process's initial profile/settings agree exactly. Original
result, roster, reopened training record and fresh stock HUD corroborate them;
both processes exit 0. Two ordinary bot-arm notifications and one natural device
defuse occur; the other planted round ends by elimination. This sample does not
qualify representative bot reliability or a bot-quality improvement.
[Raw recomputation](audit-r2/raw-recomputed.json).

## Source, logs, originals and review limits

Critic criteria `339f974` were committed/pushed at 08:37:01 UTC; root preregistration
`86620c3` and release `e2d9cbd` also precede dispatch at 08:38:12 UTC. GitHub binds
attempt 1, one Windows job and exact e28c8e9. No second attempt was dispatched by
this critic. [Chronology](dispatch-chronology.json).

All eight current source records bind clean source/game state. Game tree remains
`55691684d31d44f1680141954bbe530443de9d1f`; shipping content remains
`bcb872f6998ed8504c852dee354ab0acf5b6f19e58e40717267a1927e6d68a50`.
LF validation `b757d89ed21fb257822e3c9a57000641c5e9e2151c443dd1c627f766ac2b6cdf`
reconciles to native Windows
`619f452a0eda12ed87933d1399c70abf624570576a24c95f9b822c54a14d8123`
through eleven explicitly listed tracked CRLF paths. All 323 native copied game
resource hashes match. The missing success-only journey controller digest stays
false; the complete validation hash binds the frozen controller inventory.
[Source audit](audit-r2/source-Windows-recomputed.json).

All 15 native suites preserve original order, 120/30-second limits, pinned engine,
31 private native producers and owned namespace cleanup. Independent checks
recompute 186 command/producer/cleanup predicates, 4,399 gunplay predicates and
1,974 dry-primary observable predicates. Unlogged protected snapshots remain
outside that observable audit. All **133** transferred native logs, including
93 regression logs, pass the maintained full-log patterns and added standalone
`Orphan StringName:` / positive unclaimed StringName checks. The earlier a089
138-log package also passes a fresh added-pattern scan. Scanner clean booleans
alone were not accepted. [Completeness](audit-r2/runtime-completeness.json).

Both official ZIP SHA-256 digests and sizes match GitHub metadata. The bounded
receipt artifact retains 219 selected originals plus its index; every selected
original matches the full QA artifact byte for byte. The full QA artifact retains
289 files and all 70 intact PNGs. **24 originals were directly inspected** with
their exact hashes and observations recorded in [visual review](visual-review.json).
The complete decoded job log is retained in the supported connector's original
response JSON; all failure artifacts remain in the original ZIPs. Signed transfer
URLs are omitted from publication; artifact/file IDs and digests are retained.
[Transfers](supported-transfers.json).

The native executable receipt is 113,575,576 bytes, SHA-256
`481f48a05521cd3823cadc7afbcfc2e31b0e4c65649a8fa275f9611ef74261c3`.
Seven runtime receipts join that identity; native inspection records 134 embedded
PCK resources and clean headless/graphical startup. The 142,653,530-byte development
artifact exceeds the supported 32 MiB transfer cap and was not requested.
Independent executable/PCK reparse remains unqualified. This is a Godot 4.7.2 debug
export on Windows-2025Server-10.0.26100-SP0 with hosted rendering, without physical
GPU, latency, human play/listening or release-package acceptance. Original process
exit receipts and namespace cleanup do not prove a host-wide orphan scan; the
runner log only reports its cleanup phase without identified descendants.

Review R1 retained its own setup failures: the older auditor assumed a settings
save existed before route failure and indexed a success-only authority summary
in the failed diagnostic. Its seven-path CRLF expectation also omitted four
new tracked Linux/Mac fixture paths. R2 fixes those reviewer assumptions, keeps
all missing/reached-failure predicates false, and produces a deliberate nonzero
completeness verdict. No candidate source or native evidence changed.
[Reviewer corrections](REVIEWER_CORRECTIONS.md).

For the identified comparison, **a089473 is better on achieved living-journey
and legacy-diagnostic coverage**: it reaches living settings resume before its
later death and passes the legacy schedule, while this attempt fails earlier
on route delivery and independently fails that diagnostic. Both overall Windows
qualifications fail. New stock output has broader observed objective events and
retains exact earned-profile integrity, but separate hosted executions establish
no causal route, survival, timing, input, performance or bot improvement. Prior
Windows/Mac/Linux failures remain intact. No whole G1/G2/G12/G16 or RC gate closes,
and this verdict approves no retry.
