# Offline capture phase fences

2026-10-22. Criteria recorded before implementation on own branch
`fix/offline-capture-phase-fences`, sparse worktree
`/workspace/sightbreak-capture-fences`, base `9d11f1d`. This milestone changes the
observer only. No engine, native renderer or OCR workload is authorized while
account qualification owns the CPU lane. Canonical root mission documents and
product, arena, authority and gameplay state remain untouched.

## Actual regression bar

Windows CI39728129445, source
`a8eb7eb81c74f306a9600820cb6e78f98a5e1630`, completes the functional ordinary
journey. Independent critic `native_ci_outcome_critic` inspected the original
images and retained action/event bytes. The named captures do not prove their
claimed phase:

- `06c-next-round.png` visibly shows round 1 POST and ELIMINATED / SPECTATING.
  Its SHA-256 is
  `146e4b8370b021411eb2d2ad2379e8d39f41179a04cf04f38cb9d5ac7031bf46`.
  The driver sees the Round 2 log at 162.875 seconds, then captures from 162.906
  to 163.265. The actual round 2 buy event is tick 6814, drawn frame 1142, with
  living health 100. No exact authority/frame bracket surrounds this capture.
  Later images show the living round 2 player; they do not repair this image.
- `10-reopened-loaded-settings.png` visibly shows the previous main menu.
  Its SHA-256 is
  `c72ca7c9da99aad6641c8c4f1a808d692f27133f68a0196edfd8e02b5d5b2674`.
  The loaded-profile event exists at driver 208.890 seconds; capture runs from
  208.906 to 209.093. That initial event is tick zero, frame 12, buy round 1 and
  living health 100, but its own `ui.screen` is still `menu`. The later living
  game observation is tick 909 / frame 166. The preceding serialized action
  observation belongs to the retired first process and cannot bracket this one.

Original PNG bytes and the critic's exact reconstruction are retained under
`reference/`. The complete raw official archive remains at
`/workspace/reviews/native-ci-39728129445`. The original controller SHA-256 is
`9364e7e4c8e0d33d081d0619950388aa8ea2dc0c6fcbb15ab2e30a662ec2298b`.
Driver elapsed/Unix timestamps and each native process's observer clock are
different domains; this report does not equate them or invent missing brackets.

## Preregistered criteria

1. Retain the existing Round 2 log contract. Before `06c`, also observe the same
   actual local actor alive, focused and unpaused in game screen, round 2, buy
   phase, normal simulation speed. An old dead/spectating POST observation can
   remain honest evidence while waiting; it cannot satisfy the new phase.
2. Retain the reopened initial-event stock-condition and exact saved-profile
   checks. Select the reopened trace before reading its current state. Before
   `10`, observe that process's initial actor alive, focused and unpaused in game
   screen, buy phase, round 1. The initial menu event alone cannot authorize it.
3. For each boundary, acknowledge the named context, then require at least two
   additional drawn frames with the same actor, life, phase and round. Frame
   counters must be nonnegative integers, excluding booleans, and cannot move
   backward. A stopped counter, stale observation, wrong process/trace or context
   transition must fail or remain unready; no later life may silently replace it.
4. Revalidate the expected context immediately before and with a fresh
   observation after raw capture. Pin the native process and trace path and
   revalidate exact source identity before and after capture. For `10`, also
   retain the exact loaded initial profile and disk settings equality across
   the capture. Record acknowledgment, ready, before and after states, process,
   trace, expected phase/round and deadline metadata with the raw image.
5. Share the existing absolute 160-second natural-round budget and 30-second
   reopened-profile budget with acknowledgment and frame waits. Do not add a new
   grace period, extend the 300-second whole journey or change input/event,
   objective, reload, focus, life, settings or source contracts. Keep the real
   native inputs and other capture paths unchanged.
6. Pure controls must reject the actual initial-menu profile event and original
   old-round POST context; test one-frame/stalled/backward/invalid counters,
   stale and foreign process context, actor/life/focus/pause/round/phase/speed
   loss, settings mismatch and expiry of the original shared deadline. A
   declared two-frame state sequence may prove observer logic only. It cannot
   prove that real pixels show the named phase.
7. Freeze source and request a fresh independent critic. After account releases
   the engine lane, run an exact-source native slice under the existing budgets
   and retain its complete original images, action/state/frame brackets and
   failures. Independent inspection must find a living round 2 buy HUD in `06c`
   and the reopened living game HUD in `10`; full journey qualification remains
   open if either changed boundary is unreached or pixels disagree.

The current source only waits for a log line at `06c` and for the initial loaded
event at `10`, then captures immediately. Existing fire/reload/settings paths
already demonstrate a two-drawn-frame fence; this milestone will reuse that
observation mechanism at these two boundaries. Product rendering is not changed.

Next: implement and run pure negative controls. Native proof and independent
acceptance are pending; account retains the engine lane.

## Candidate source and pure controls

The candidate changes `verify_offline_export.py` and registers a pure observer
test in maintained validation. It adds a capture transaction at only these two
boundaries. The existing Round 2 log and loaded-profile checks remain. Their
original 160-second and 30-second absolute budgets now also contain the named
phase acknowledgment, two drawn frames, fresh before/after observations and
binding checks; no new grace period is added.

Each receipt retains expected actor/round/phase, native PID, trace directory,
source identity, acknowledgment, ready, immediately-before and fresh-after
states, and remaining original budget. Source/PID/trace binding is checked before
acknowledgment and on both sides of capture. At restart the trace switches to
the reopened process before any state query; its initial event and disk profile
are read again around capture and must equal the originally accepted loaded
event and saved settings. A failed transaction retains the raw image and partial
receipt without calling it accepted evidence. Other native input/capture paths
and all product files are unchanged.

`scripts/fixtures/offline_capture_observations.json` contains extracted actual
event objects from this Windows run, with source/run and original event-file
hashes. Its old POST/dead and initial menu objects remain unchanged by tests.
Declared mutations model subsequent frames and negative context changes only;
they never enter a game process or modify authority.

Thirteen pure test groups pass, including actual old-context rejection,
one-frame/stalled/backward/invalid counters, fresh-wall requirements, life/actor/
phase/focus/pause/speed loss before and after capture, source/PID/trace/profile
races, and expiry of the original shared deadlines. Five strict caption controls
also pass. Native-observation controls pass four cases and skip three cases that
require Windows. Raw Python logs and exact command/hash receipts are in round 1.
No Godot, rendering, OCR or native workload ran for this candidate. Pure controls
do not qualify the named pixels; independent source review and a later exact
native slice remain required.

## Rejected source iteration and correction

Fresh critic `/root/offline_journey_builder/capture_phase_critic` rejected the
first frozen candidate `aaa1929`, despite its 13 passing test groups. An
intermediate unready sample could advance one frame and then regress to the
acknowledgment counter, after which later frames still authorized capture. The
same gap applied to simulation ticks. A second scheduling counterexample showed
that a status published during the pre-capture source/profile check could later
serve as the only nominal post-capture observation. The original candidate and
its incomplete passing controls remain in history and round 1; no native run or
pixel acceptance belongs to it.

The revision checks frame, physics and observer counters against every previous
validated sample, including unready samples, and retains the rejected pair on a
regression. After the screenshot it reads a named-context observation barrier,
then requires a strictly newer publication beyond that barrier before accepting
the post-capture state. This prevents one state already available before the
screenshot from being the sole after proof. All waits still share the original
160-second or 30-second absolute deadline.

Fifteen pure groups now pass, including the critic's intermediate frame/tick
rollback, an observer-clock rollback, and a buffered pre-capture state followed
by no new publication. Round 2 retains the exact revised command and raw output.
These remain declared scheduling controls, not a native pixel result. Independent
reevaluation and actual native captures are pending; account still owns the lane.
