# Independent M5 dry-weapon source review

Verdict: **PASS for one bounded unchanged-baseline fixture run** at
`b0635964c6b819ed41a9568afdb0b5068c3d5577`. This does not approve a product
change or establish a runtime pass. This is an identified-source comparison,
not a blind comparison. No engine, export, CI or service was run by this critic.

The bar is the actual published decision and action implementation at
`917b143ba4e4b0d9644a7a0ddeee1dd64c139682`. I read AGENTS, the mission/acceptance
and recovery instructions, CLAUDE, ownership notes, BARS, both original quality
skills, No AI Slop's eval, the project gauntlet, the preregistration and the
fixture. The receipt records exact file hashes. All three inspected production
files are byte-identical between baseline and fixture freeze; no production
script changed.

## The defect exists in the inspected source

`bot_ai.gd:631` promises primary ammunition availability, but lines 632–636
request the first owned rifle, marksman or SMG whenever the active weapon is a
sidearm and no target is acquired. The condition does not read ammo. At
`actor.gd:698` the outgoing active fields are saved, and a recorded primary
`Vector2i(0, 0)` restores zero clip and reserve. `start_reload` at line 692
refuses to start a reload with no reserve. A subsequent no-target decision
therefore requests reload again. This is a real known-dry return/reload loop in
the baseline, independent of any historical timeout explanation.

For a loaded sidearm and recorded dry rifle, source predicts one dry equip then
seven ineffective reload requests in each eight-step idle sequence. Alternating
visibility predicts the same on easy, and eight switches/four dry equips on
normal and hard. These are predictions awaiting native records, not measured
results. Native baseline must actually demonstrate the preregistered defect
before a production edit proceeds; an unrelated fixture failure cannot serve
as that demonstration.

## Fixture and observation oracle

The only actor override is `can_see`; it controls visibility and does not select
weapons or consume inputs. `match._bot_input` delegates to production
`SBBotAI.compute_bot_input`, and every sequence step calls the actual
`SBActor.tick_authority_actions`. The authority action implementation equips the
requested owned weapon and uses production reload logic. The replacement bot
does not connect the match's damage/hit callbacks, but its shot signal is
observed and the fixture deliberately keeps each sighting shorter than the
smallest profile reaction delay. This tests decision/equip/reload correctness,
not perception, movement, hit adjudication or full objective execution.

The fixture covers each primary's known dry, clip-positive, reserve-positive and
missing holstered state on every difficulty. Ownership, skip-dry selection,
unknown-first priority, all-dry inventory and active stale-cache cases are
present. Its total-ammo helper correctly counts live active fields and only
holstered ammo-store entries. The actor's equip fallback supplies definition
ammo when a holstered entry is missing; treating that absence as dry would
break the unknown cases.

Close fallback controls retain normal/hard empty-clip behavior with zero or
positive reserve, easy behavior, the 20 m boundary, loaded clips, an unowned
sidearm and an interacting defuser. An interacting sidearm holder with usable
primary retains the existing return request. The proposed product boundary is
one no-target primary-return loop; none of these controls authorizes changes
to fallback, reload or objective policy. Existing bot AI and squad-symmetry
regressions remain required for the candidate.

Before/after deep snapshots cover the preregistered weapon, ammo, reserve,
reload/deploy timers, cooldowns, inventory, ammo store, credits, health and utility
counts. Decision calls cannot silently mutate these values and still satisfy
the in-engine comparisons. Sequence ammo, weapon and reload records allow
independent recomputation of the defect and the bounded candidate improvement.
The fixture should emit 84 cases, 48 steps and 590 checks; all are source-derived
expectations. Native totals and individual outputs must be inspected.

The largest observation gap is that JSON output omits full protected snapshots
and the per-case inventory/ammo-store inputs. Raw logs alone cannot independently
recompute every deep authority-state comparison. Those predicates currently
depend on the reviewed in-engine assertions plus exact-source binding. Retain
this limit if the bytes stay frozen; add snapshot output as a registered new
fixture iteration before the baseline if complete raw recomputation is required.
This gap does not prevent observing the actual dry equip/reload/fallback defect.

Priority coverage is also finite: there is no explicit all-three-known-loaded
case or both-rifle-and-marksman-dry/usable-SMG case. The requested narrow patch
must retain the literal priority list, and the candidate source review must
reject broader selection changes that the current examples could miss.

## Runtime and cleanup boundary

The fixture has fixed loops, disables the match physics tick, queues the match
for deletion, waits one process frame and exits nonzero on any recorded failure.
It opens an offline match and never requests a service or listener. Those facts
bound its intended work; they do not establish a wall-time bound or cleanup
after an engine/setup failure. The preregistration's bare commands are requests
for root-coordinated execution, not a reviewed process supervisor.

Root must run the fixed source with an explicit wall deadline, private state and
retained stdout/stderr/exit/source receipts, own its process group/descendants,
and retain a terminal cleanup observation even when the engine fails. The
editor-import exit 0 is setup evidence only. Missing result markers, parser
errors, an unexplained timeout or residual owned processes cannot be accepted
as baseline or candidate gameplay evidence. No cleanup pass is claimed here.

The native baseline must remain a retained failing artifact. After its actual
defect is verified, freeze the narrow candidate, run the same fixture bytes and
required regressions, and compare every recorded decision and sequence against
the declared gates. A result counter or a score alone cannot close this milestone.
