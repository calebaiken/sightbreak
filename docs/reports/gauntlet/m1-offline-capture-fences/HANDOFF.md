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
