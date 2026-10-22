# Mac focus observer iteration

Declared before implementation, 2026-10-22. Actual ARM run 39729489971 at
`3b97a00` compiled the capture helper successfully, launched game PID 3996 and
failed the unchanged five-second foreground guard. The last recorded foreground
PID was 3721. No event was posted, no capture helper was invoked and no OS PNG
exists. The preflight's PID 3571/window 35 is a different process. Selected game
window geometry and activation return were not retained, so the cause is open.

The inspected public NSRunningApplication SDK header describes time-varying
properties as persisting until the next turn of the main run loop. This is a
concrete observer risk in a Python sleep/poll loop, not proof of this failure's
cause. The next native run must expose the actual request and sample sequence.

1. Retain the exact newly selected exported PID/window ID/bounds immediately,
   before activation or capture. Never reuse the previous preflight's window as
   this client's identity. Preserve source/export/profile and cleanup gates.
2. Keep one existing public `activateWithOptions:` request. Record its options,
   return value and pre-request observations. Process the controller's main run
   loop through public CoreFoundation default mode and retain each bounded
   before/pump/after sample. Record exact NSWorkspace foreground PID and only
   the target application's active/hidden/terminated/finished-launch/policy
   properties. Do not retain unrelated application names or windows.
3. Keep the five-second focus deadline and exact foreground PID condition.
   Neither request success, target active state, run-loop processing, a visible
   window nor window order is focus proof. Never accept a sample after the
   deadline. No forced activation, private/alternate identity or new requesting
   API is introduced. Native data must distinguish a refreshed observer from a
   genuinely unfulfilled activation; source controls cannot establish the cause.
4. Before activation, allow one separately scoped read-only ScreenCaptureKit
   capture of the same exact owned background window. Require the helper's own
   permission and all existing geometry/pixel guards. It may independently
   establish capture permission/geometry; it is not focus or navigation proof.
   Its failure is retained, then focus diagnostics still run without events.
   No event may follow a failed background capture. Foreground menu captures
   and all existing text/target/neutral/source/profile guards remain mandatory.
5. Retain zero-event failures truthfully. Preserve normal AppKit termination,
   owned-only group cleanup and held-control release. No unknown profile/cache
   data is deleted. No AppleScript, TCC change, prompting, security bypass,
   guessed chrome offset or input retry is allowed.
6. No game/art/protocol/economy, existing timeout, Windows/Linux or other native
   workflow gate changes. No local engine or OCR work while M1 owns that lane.
   Only milestone evidence/HANDOFF docs change. Fresh source critic must review
   before root dispatch; a fresh native critic must inspect actual samples,
   permission/geometry PNGs and cleanup before any acceptance.
