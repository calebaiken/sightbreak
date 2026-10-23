# Route-only pulse handoff, unapproved source candidate

Source freeze `977633e44a61352cbf666273931021ebebfe70d9`, base
`e28c8e90b9ef2d0c766bd9152c194e3197ceba9a`, own branch
`codex/windows-route-pulse-e28-20261023`, worktree
`/workspace/sightbreak-windows-route-pulse`. Preregistration `31ce9354` precedes
implementation. This builder cannot approve the freeze. No actual retry ran.

## Original evidence and corrected hypothesis

Final independent actual review `2020cfa9082fd68a46282a4e25b2f82549a2812d`
and original run 39926044462 / job 120322557935 remain failed. The route has the
same living actor at 100 health, last stopped x=-6.2700005 at tick 3159, then
rejects x=-8.6911116 / vx=-3.7 at tick 3211 outside the original x>=-8.5 corridor.
No settings/reopen/focus coverage was reached and no missed input is established.

| Original request | Driver selected-key after-call bracket |
| ---: | ---: |
| 0.1545885467 s | A-down→A-up 0.500 s |
| 0.1257692308 s | D-down→D-up 0.515 s |

`original-failed-trace.json` binds the original results/actions and retains full
route states, rejected state, all selected pulse edge rows and the separate
legacy failure. Its recomputation is byte-exact. These driver brackets do not
identify exact physical key edges. Original OS diagnostics sample r/d/w; an
independent A bitmap is unavailable. No physical hold interval or cause is inferred.

The startup hypothesis is explicitly corrected: WinUI already calls ctypes /
SendInput in process and starts no per-key helper process. The inspected fine
path performs four traced WASD steering calls and four traced release calls.
Their OS diagnostics and actions.json writes occur between the selected edges.
This is known controller work to investigate; source inspection alone does not
attribute the actual corridor failure or establish a performance improvement.

The legacy delayed-reload diagnostic separately expires its original completion
wait. Later completed authority state and workflow success do not erase that
failure. This candidate changes no default legacy schedule, reload limit or
result interpretation; the original legacy result remains false here.

## Narrow candidate behavior

Only Windows settings-route fine corrections opt into the new `WinUI.key_pulse`
operation. One controller method dispatches selected ordinary down edges, sleeps
within the requested window/original absolute deadline, and attempts every
owned up edge in `finally`. It invokes the existing in-process key method for
each edge; it does not claim a single atomic SendInput call across a sleep.
There are no trace/file writes or unrelated WASD edges between selected edges.

The operation retains before/after monotonic brackets around each delegated
native key call and OS read, requested hold/deadline, all A/S/D/W states, LMB,
foreground, window owner/visibility and errors. These remain in memory until
release attempts finish. The controller then publishes the complete receipt in
its normal actions trace and result, including failures. Window/PID are pinned
within the operation and checked before/after dispatch. Unknown/non-neutral
external controls prevent a down edge and are never claimed as owned releases.

The hold boundary starts before the first down-call bracket. Mapping/API costs
consume that window; the helper does not start a fresh requested sleep after
dispatch. Expired pre-reads, exhausted dispatch windows, sleep errors/interrupts,
release errors and successful calls/reads that return after the original cap
all fail. Release attempts remain mandatory after expiry. SendInput return and
OS bitmap snapshots still do not prove game consumption or physical latency.

The optional approach hook leaves the exact old default branch available.
Default/Linux approaches, coarse motion and normal traced callbacks are unchanged.
The route still requires its original corridor/ground bounds, target, <.45 m
endpoint, <=.05 m/s speed, two later neutral observations, same actor/life/round,
valid positive health, weapon/ammunition and original 35-second/whole caps.
Post-pulse native observations remain necessary before endpoint acceptance.

## Pure checks and next gate

The new group has 14 mocked OS/clock methods covering edge/state receipts,
partial dispatch, sleep failure/interrupt, all-key release attempts, up failure,
pre-edge expiry, dispatch-cost consumption, late successful up/sleep/OS reads,
fresh owner/focus/pin, external A, invalid requests, post-release trace retention,
optional-hook route completion and late callback rejection. Six full mocked
receipts are retained in `pure-pulse-receipts.json`; they are declared inputs,
not native timing evidence.

All nine short pure groups pass: 93 discovered methods, with the original three
native-Windows reader skips. Command/log hashes and source binding are in
`pure-checks.json`. No tests or new hashing ran during the Linux measurement
hold; checks began only after root released that lane.

`source-preservation.json` verifies exact AST equivalence after removing only
the new WinUI method, optional fine-pulse branch/forwarding and Windows route
callback. All existing key methods and input schedules, route guards, captures,
HUD/settings/focus assertions and caps remain unchanged. Game, CI, toolchain
and focus helper bytes are unchanged. The local aggregate script adds one pure
test command; no aggregate engine suite ran.

No engine/import/native/CI/OCR executable/service/Apple compile/heavy work,
nested agent, canonical root edit or runtime retry occurred. The largest
remaining gap is actual source-bound ordinary delivery and stopped living cover
completion within the unchanged corridor/cap, followed by the still-unreached
settings/LEAVE/reopen/focus journey. Require a fresh independent source critic
and exact combined-source approval before any actual acquisition. No survival,
input-latency, performance or broader release acceptance is claimed.
