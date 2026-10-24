# First-displacement route correction

Status: source investigation and pure verification only. Base is exact
49ae54b0e4f5d880bdf06e4eb783a616b2dff684. Own branch is
codex/windows-reload-route-actual-20261023. No native process, export, CI,
qualification dispatch or retry is released. Pure work uses CPU 4 only.

The inspected bar is the original failed Windows run 39940242244, job
120369601915, plus the maintained 60 Hz ground-motion controls. Complete raw
paths and hashes are bound in original-bindings.json. The independent actual
critic owns the verdict. Historical e28c8e9 corridor and legacy reload-completion
failures remain failed.

## Source-supported findings

The route starts at x=-4.4000000954 in round 2, actor 1, deaths 1, alive with
100 HP and SMG 30/120. Source native_approach.py enters continuous `walk` at the
original 3.4 m distance because the optional native pulse hook is used only after
`fine` becomes true at 2.2 m. The native fine pulse is never reached in this
actual attempt. D-down is bracketed by controller wall stamps
1792752527975..1792752528025. Traced redundant steering calls and three traced
releases precede D-up at 1792752529655..1792752529708. Last accepted readback is
tick 3313, x=-8.3977794647, vx=-5.0999999046, move=[1,0]. Next readback is
x=-11.5494470596, vx=-2.2999997139 and violates unchanged xmin=-8.5. The route
never reaches its stopped endpoint. This is a controller sequencing defect;
these observations do not prove an OS delivery-latency cause or product defect.

Ordinary network input independently fails its original reload-start wait. The
raw logs contain two server disconnect notices with an intervening reconnect.
The last bound telemetry sample before firing is wall 1792752122282, ack 382;
`before_firing` reads this same sample at wall 1792752152717, 30.435 seconds
later. LMB-down at 1792752157461 falls in a native sample gap; the next sample
at 1792752161118 is unbound, ack 502. R-down at 1792752181847 follows this
unbound observation. All retained joined-actor samples show fire=false,
reload=false, shots=0, ammo=30/90. OS edges do not establish game consumption.

Production main.gd samples R from the physical input state, samples fire from
_input mouse events, and hands local intent to match.gd. A connected client sends
sequenced intent; authority consumes only a bound peer's accepted stream and
neutralizes sustained silence. actor.gd requires a non-full magazine for reload.
The fixture's reload-start timeout therefore cannot identify an R-key defect in
this attempt. Disconnect origin, actual client processing during the sample gap,
and any transport/render starvation cause remain unproved. Neither the schedules
nor product input/authority code will be altered by this component.

## Preregistered change and falsifiers

Change only the opt-in controller behavior: if an explicit native pulse callback
is supplied, choose bounded pulse-from-rest from the first displacement, using
the existing acceleration formula, rate bounds, pulse cap, release/finally,
two distinct neutral stopped ticks and original absolute deadline. Existing
callers without a callback retain their continuous coarse walk. The R2 WinUI
per-edge owner/focus/release implementation stays byte-identical. No endpoint,
corridor, life, stock weapon/ammo, rules, health, AI, timers or acceptance limits
change. This is a controller adaptation, not a product input fix.

Before editing controller source, add a meaningful delayed traced-callback plant
control using the inspected 28 m/s^2 acceleration, 5.1 m/s speed, 60 Hz ticks and
13-tick readback publication. Reproduce the old opt-in coarse-walk corridor
failure with nonzero diagnostic callback costs, then require the same model to
reach the original endpoint inside the corridor with pulse dispatch. Include
first-displacement callback use, zero fallback key-downs, endpoint/two stopped
readbacks, unchanged deadline and rejection/release on blocked path, unreadable
observation, late callback and lost identity. Simulated costs are declared stress
conditions and are not presented as a reconstruction of unobserved engine time.

Run the relevant maintained input/route/focus/capture pure groups on CPU 4 and
repeat from a fresh initialized depth-one clone with no report-tree dependency.
Retain the pre-fix failure, post-fix output, exact source diff and largest remaining
uncertainty. A separate fresh source critic and explicit root release are required
before any new native attempt; native success remains unobserved.
