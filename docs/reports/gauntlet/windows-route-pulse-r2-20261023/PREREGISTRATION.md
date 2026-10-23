# Windows route pulse R2: per-down context fence

Source-only preregistration, before implementation. Parent handoff is
`9a3d73563e45c720aa0a3cccd48eb7d4ecd8c996`; rejected code freeze
`977633e44a61352cbf666273931021ebebfe70d9` remains immutable in history.
Independent rejection `bf47f7c9b15a5d8be8aa3dcc0f815fb3c60961f2`, preregistered
at `9329c472`, is the named comparison. Read the committed REPORT.md,
independent_controls.py and named independent-receipts.json from
`/workspace/reviews/windows-route-pulse-source/docs/reports/gauntlet/windows-route-pulse-independent-20261023`.

The two real-key-path counterexamples change foreground HWND 34 to 99 or owner
PID 12 to 99 immediately after W SendInput returns. The rejected helper then
sends D down at mock time .005 to the changed context, before detecting loss.
Releases occur but cannot undo that second down. All 93 maintained methods
passed on the rejected source. This finding concerns dispatch ordering; it
establishes no Windows latency, survival, input-consumption or route result.

Implement only the route helper's per-down fence and its pure controls. Keep
initial preflight and original after-down/after-release samples. Before each
attempted down, freshly read pinned window/PID identity, visibility, thread,
owner, foreground, all W/A/S/D bits and LMB. Accept already owned attempted keys
in the bitmap; reject any other down bit, LMB, unknown read or changed context.
Retain each check and exception in a separate in-memory receipt list. Check the
unchanged absolute deadline after the read; the original fixed hold boundary
includes all check/dispatch work and never restarts. If that boundary is
already reached, send no new down. Release every attempted key in finally,
even after context loss, unknown state, cancellation, lateness or another up
failure. Preserve receipt publication after release attempts.

The success criteria are no second down in either committed falsifier; living
real-key-path positive two-key dispatch with prior owned bits; no down after
visibility/thread/pin/input loss or late/unknown per-edge reads; all attempted
releases despite errors; complete raw check/edge/error receipts; unchanged
hold/cap and existing default-source behavior. Add real WinUI.key -> _input ->
fake User32 tests, including alias and list requests. No native call is made.

Replay the independent script unchanged to a new receipt destination and keep
its full output. Its fault hooks use IsWindowVisible read ordinals 2 and 3 for
old post-down/post-release stages. New reads necessarily shift those locations;
retain such failures and distinguish stale stage selection from the exact
focus/owner assertions. Add semantic-stage controls and ask the same independent
critic to judge the source and controls. Do not edit the critic's original
script, receipts or rejected checkout.

Run all nine maintained pure groups (93 original methods plus added cases),
AST/source preservation checks, a scripts-only genuine depth-one clone and
alias/depth-one path controls. No historical report fixture may be a maintained
test dependency. Keep the original e28 raw trace binding, x>=-8.5 corridor,
x=-7.8 target, <.45 endpoint, <=.05 speed, two later neutral observations,
actor/round/life/health/input guards and original 35-second/whole caps exact.
The separate original legacy reload timeout remains failed. Game/AI/health,
rules, seed, scenes, graphics, captures, other input schedules, CI and canonical
mission records stay unchanged. No engine/native/CI/OCR executable, services,
Apple compile, heavy aggregate or runtime retry is authorized. Builder results
are unapproved until fresh independent review and exact-source release.
