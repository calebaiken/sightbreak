# Frozen Windows reload-completion failure — source assessment

Scope: read-only inspection, 2026-10-20. No repository edits, native processes,
reruns, threshold changes or artifact mutation were performed for this assessment.
The retained CI log is `/workspace/desktop-evidence/ci-windows-final.log`.

Frozen source: `0fb74800cffb96077069144028d113e308ef1744`.
Failure artifact: <https://github.com/calebaiken/sightbreak/actions/runs/39384250334/artifacts/12245964199>.
The uploaded ZIP digest reported by Actions is
`4b66d71f1d1ca691773ff42441c5e65aea9e3d15ab639bf90c9ea7e065aa0124`.
Its raw nested authority/client logs and screenshots were not available in this
workspace and were not inspected. Claims below separate source deductions from
unobserved failure state.

## Established evidence

- Windows native export and resource inspection completed. The CI log reports
  130 PCK resources and successful headless startup plus a rendered native menu.
- The five focused native authority/compatibility groups completed their step
  before the exported-input flow began.
- The input controller failed with `Authority reload completion`. Its control
  flow therefore saw `EXPORT_UI_RELOAD_STARTED` and then failed to see
  `EXPORT_UI_RELOAD_COMPLETED` within the existing five-second completion wait.
- This does **not** independently establish a native R-key command in the failed
  trial. The fixture also reports reload start for automatic empty-magazine
  reloads. `reload_command_seen` is checked by the final authority oracle, which
  the controller did not reach. Prior successful trials remain prior evidence.
- Comparing the relevant source between `3710c19` and this freeze finds no
  Windows input or game-runtime change. The intervening controller delta is
  Linux-only automation/session handling and result metadata. That narrows the
  changed-source hypothesis; it does not prove the failure is environmental.

## What the source rules out and leaves plausible

**Held R alone is not a reload cancellation.** In `actor.gd:635–645`, an active
reload timer decreases before the input is processed. `start_reload()` at
682–685 only starts when the timer is zero, the magazine is incomplete and the
reserve is positive. Repeated R while the timer is positive does not reset it;
a full magazine also prevents restarting it.

**Client focus loss alone cannot freeze the authority's reload.** The client
main script neutralizes its controls and opens a local overlay on focus loss.
Network matches keep running; the fixture's server actor continues its authority
tick and reload timer. Focus can affect which native events were delivered, but
is not itself evidence of server reload cancellation.

**Retained fire is a concrete plausible oracle failure.** At timer completion,
the actor fills its magazine, then can fire in the same authority tick
(`actor.gd:635–652`). The fixture samples afterward and requires both
`reload_remaining <= 0` and exactly `ammo == 30`. If fire remains held, the
post-tick state can already be 29, so no completion marker is emitted. If R is
also held, another reload can begin on the next tick. This is a source-supported
possibility, not a finding that fire actually remained held in this failure.

The controller also captures PNG `04-fire-input` **before releasing LMB**. A slow
capture lengthens the intended 0.7-second trigger hold. It could deplete the
magazine and produce an automatic reload-start marker before R is sent. Current
logs do not expose capture duration or native-button state in the Actions text.

Other unresolved possibilities include low authoritative simulation throughput
(the guard is wall time while the reload consumes simulated physics time), a
peer/round/weapon lifecycle change, or native event/focus delivery. The fixture
normally holds bots inactive and keeps a long live phase, so death or a natural
round transition is less expected; raw state is needed before excluding either.

## Next bounded diagnosis

1. Preserve this original failure. If an exact-source retry is practical, rerun
   this Windows job once at the same frozen SHA into new evidence. An eventual
   pass is an additional result, not an explanation or deletion of this failure.
2. Before changing gameplay or waits, make a separate diagnostic source freeze
   with additive, bounded fixture telemetry. Retain timestamps, authority tick,
   simulated elapsed time, actor ID/alive/weapon/ammo/reserve/reload timer,
   current `fire`/`reload`/weapon input, ACK sequence, peer binding and phase at
   shot/reload edges and at the completion timeout. A short bounded ring buffer
   flushed on failure is sufficient; no protocol or shipping telemetry is needed.
3. Record controller timestamps before/after native input and each capture;
   retain target/foreground HWND and OS LMB/R key state at those boundaries.
   Inspect `06-after-authority-reload-start.png` for an overlay, weapon change
   or actual reloading state. Emit the nested server/client log tails in CI so a
   blocked artifact download cannot hide the decisive failure state.
4. Run one matched diagnostic trial with the existing input schedule and
   unchanged exact-ammunition, protocol, native-input and clean-exit gates.
   If a second comparison is needed, release R immediately after the server
   observes the real reload command and move the firing capture after LMB-up;
   retain both schedules and their results. This is a diagnostic comparison,
   not grounds to relabel the original trial.

Do not increase the five-second threshold merely to get green, accept 29 rounds
as a reload pass, switch to authority-triggered reload, or suppress the failure.
If the raw state shows correct authority completion in simulated time but a
wall-clock overrun, select any revised deadline from retained timing evidence
and repeat qualification in a new freeze. If it shows held fire or a cancelled
reload, fix that specific cause and retain the strict full-magazine oracle.

Current status: **final frozen Windows gameplay completion FAILED / root cause
UNRESOLVED**. Native Windows export/startup evidence remains valid within its
scope. This assessment is not proof of a shipping reload defect or a new pass.
