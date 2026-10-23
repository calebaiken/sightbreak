# Read-only startup discovery before permanent input geometry

Repeat run `39906639650`, job `120260016569`, used combined source
`b2e0293a546961230afbd73e5cd2a1a307d69e94`. Source controls passed. The actual
ordinary component failed at the post-capture owned-window guard, before any
CGEvent or Deploy. Original result, full decoded log, component receipts, PNG and
the two exact downloadable archives remain here. Archive hashes match GitHub's
published artifact digests. The result extracted from the log matches original
`macos-ordinary-input/results.json`.

The first owned window and screenshot receipt agree on window 54 / PID 14158 /
`[0,25,1024,684]`. The original PNG shows the Godot splash. The later guard's
actual current rows were omitted, so the evidence does not establish whether the
window disappeared, its ID changed or its bounds changed. Private user:// logging
was observed, but ordinary gameplay was never reached. The public failure-close
request timed out, then SIGTERM removed the client; that failed close remains
failed evidence. No native gameplay acceptance follows from this attempt.

Before editing source, register this correction and these gates:

1. Keep startup discovery read-only. Within one existing 60-second menu deadline,
   inspect only the exact owned PID's visible layer-zero windows and capture each
   candidate with the unchanged read-only ScreenCaptureKit/Vision helper. Preserve
   every rejected capture and exact guard/current window rows. Godot splash pixels
   never establish menu readiness.
2. Startup candidate geometry may be replaced only before any CGEvent attempt.
   Require one exact owned window, the existing strict whole-window/chrome/Retina
   mapping, and the original menu identity at the unchanged confidence threshold.
   Keep the original 30-second first-window bound and all stage/300-second totals.
3. Use one original five-second focus budget. After focus, obtain a fresh menu
   screenshot and require the current metadata and foreground PID to agree. Only
   then pin the geometry for input. Reject every attempted CGEvent before pinning.
   Never repin after that boundary, including later gameplay or return-to-menu.
4. Preserve the requested 1280x720 command, graphics defaults, exact app/PCK,
   private/default userdata guards, read-only stock authority, gameplay schedule,
   fire/reload/frame budgets and strict teardown. Do not resize the display/window,
   lower quality/resolution, change rules or extend deadlines to rescue a run.
   Retain actual observed final geometry; the old 1024x684 splash cannot prove a
   1280x720 native frame.
5. Pure controls must cover splash then ready menu, pre-input candidate changes,
   late positive menu/focus predicates, continuous geometry churn, foreign or
   ambiguous windows, invalid mapping, missing menu, any pre-pin/post-input event,
   and every later geometry change. Existing helper/controller/path/original Mac
   tests and their mutation controls remain required. No local engine/native/OCR
   or CI repeat is released by this source plan. Fresh independent frozen-source
   and combined integration reviews precede any root-authorized repeat.
