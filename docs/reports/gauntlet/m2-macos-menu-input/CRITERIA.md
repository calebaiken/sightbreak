# Native ARM Mac menu input

Declared before implementation on 2026-10-22. Baseline is the bounded preflight
at source `e7718ee`, actual ARM run 39727011693, job 119653125533. Its step
metadata says success; raw permission/source/window evidence has not yet been
independently accepted. No event delivery is inferred from that metadata.
The inspected production flow is `main.gd` Settings navigation and Escape's
ordinary `screen != menu` return path. Neither operation saves a profile.

1. Freeze clean source and its real Mac export. Require a successful same-source
   preflight receipt with posting/capture permission true, exact artifact hash
   and observed owned window; independently accepted prior ARM evidence must
   precede dispatch. Recheck current permission in the actual event controller
   and screen-capture helper. Denial is an exact external blocker. No requests,
   TCC edits, private APIs, AppleScript or alternative security identity fallback.
2. Guard canonical native player-profile and temporary entries absent before
   launch and immediately before every input transaction. Block existing
   entries without reading/deleting them. Use ordinary exported launch with
   supported window flags and evidence log path. Record native cache/directory
   effects; never delete unknown files. Preserve runtime rules and shipping art.
3. Select only the exported child PID's visible layer-zero main window. Public
   AppKit activation must result in the exact target frontmost PID. Before each
   down event, verify foreground PID, stable exact window ID/bounds and neutral
   control baseline. An activation return value alone is insufficient.
4. Capture that exact window with supported ScreenCaptureKit after the helper's
   own non-requesting screen-access preflight. Retain original PNGs and native
   metadata. Require matching CoreGraphics/SCWindow bounds in global points,
   filter content size, point-to-pixel scale and returned pixel dimensions.
   Reject unknown chrome/DPI geometry before input; no guessed titlebar offset.
5. Use Vision on those original pixels. Initial and returned menus require
   visible TACTICAL OPERATIONS and one exact SETTINGS target; Settings requires
   FIELD SETTINGS. Match confidence at least 0.8. Convert its normalized
   bottom-left box into the same full-window global points. Recheck bounds
   immediately before the single Settings click. No save control is clicked.
6. Post only an ordinary pointer move/click and an Escape press/release through
   public CoreGraphics events. Observe actual combined-session button/key state
   down then up, plus foreground PID and pointer coordinates. A void post call
   never proves delivery. Screenshots must show menu → FIELD SETTINGS → menu.
   Fresh independent image/native-output review is required for acceptance.
7. Bound the whole journey and each helper call. Finally release only controls
   this driver recorded as held, then request ordinary app termination through
   public AppKit and reap only owned groups if needed. Verify no owned process
   remains and player-profile entries remain absent. Revalidate source/export.
   Catchable cancellation is covered; hard kill/concurrent human input is not
   claimed safe or qualified by these receipts.
8. Linux source controls establish readiness only. Source needs an independent
   critic before actual ARM dispatch. Keep all existing Windows/Linux input,
   default Mac startup/source, Intel and iOS gates unchanged. This narrow menu
   proof cannot pass movement, aim, firing, full offline play, physical-device
   performance or human play. No local engine or OCR workload is authorized
   while root owns validation. Update only milestone HANDOFF/evidence files.
