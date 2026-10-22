# Independent source review: rejected before ARM dispatch

Subject: `ecb30708e9b6d3765bcbe342c5887dd25f4a4cf0`, compared with
`e38ec3c`. Reviewed 2026-10-22. This review covers the declared criteria,
preflight, seven observer controls and six added workflow lines. The reviewer
ran Linux controls only: no Mac host, native export, engine workload, CI
dispatch, permission request or input event.

**REJECT for the next actual ARM run under the current criteria.** Two source
paths contradict the declared privacy and native-user-directory guarantees.
Neither finding requires changing the game or native input code.

1. `scripts/probe_macos_input.py:141` hashes only
   `offline_training.json` and its `.tmp`; lines 201–207 launch the export with
   its default native `user://` directory and no log override. The pinned
   Godot 4.7.2 source ensures that directory exists and enables desktop file
   logging to `user://logs/godot.log`, with rotation. The project does not
   override file logging. Thus `profile_unchanged: true` can coexist with writes
   to the native user directory, contradicting criterion 5's claim that this
   launch does not edit that directory. Use the supported `--log-file` override
   into the evidence directory and state the narrower, verifiable profile-file
   guarantee; account for runtime directory/cache side effects. Do not claim
   complete native-directory immutability from the current two-file inventory.
   [Pinned-engine source excerpts](godot-file-logging-source.txt) retain the
   source URL, response hash and relevant lines.
2. Existing profiles are allowed through to `--smoke --capture`.
   `game/scripts/main.gd:92` loads the native profile; the unchanged main menu
   renders `profile.data.display_name` at line 383 and includes the training
   record card at line 455. Its original PNG can therefore retain profile
   contents despite criterion 3. Hashing the profile does not protect the PNG.
   Reject any existing profile or temporary profile entry before launch,
   without opening, deleting, moving or redirecting it. The absence check must
   include dangling symlinks and other entry types. Then verify the relevant
   profile entries remain absent after the owned process is gone.

The CoreGraphics/CoreFoundation ctypes signatures are consistent with the
Darwin arm64 ABI on source inspection: CGFloat is double, CGRect is four
doubles, IDs/options are 32-bit, CFIndex is signed long, CFOptionFlags is
unsigned long, and CF objects use pointer-sized results. The declared Boolean
results fit the one-byte ctypes Boolean. Framework symbol lookup fails closed
if any required symbol is missing. Linux structure sizes are 16/16/32 bytes;
this does not establish symbol availability or native calling behavior.

All inspected native calls query permissions, displays, window metadata or
combined-session key/button state. The candidate contains no permission
request, event construction/posting, AppleScript, TCC mutation or obsolete OS
screenshot call. Its zero-event/request fields are source declarations, not
runtime tracing. `CGWindowListCopyWindowInfo` obtains global metadata in memory,
but only exact-child-PID layer-zero IDs, bounds and on-screen flags reach the
report. Window names, unrelated windows and control focus are not retained.

The clean source receipt, full export payload receipt and executable hash are
checked before launch; source and export validation repeat afterward. The
engine version check is the existing pinned-toolchain version check, not an
independent native architecture attestation. Actual ARM execution must confirm
that identity and all native API results.

The native child receives a new session. Cleanup signals only its process group
and reports whether that group remains. The packaged actual Linux child control
passes. An additional exited-leader/live-descendant control sent TERM then KILL
and truthfully returned `owned_group_gone: false`; the controller subsequently
waited its own descendant and verified the group gone. Because `wait()` returns
immediately when the leader has already exited, cleanup does not wait for
descendant disappearance between those signals or after KILL. This is
conservative failure, not false readiness. A short bounded group-disappearance
poll would improve the receipt; the supplied single-child control does not
cover that case.

The [frozen controls](controls.txt) pass all seven packaged checks and five
additional fully mocked status/finalization checks. Denied posting retains the
external blocker; profile drift, a remaining owned group, source drift and an
export mutation all override readiness with `FAILED`. The reproducible
[review harness](review_controls.py) loads the exact reviewed source from Git,
so later worktree edits do not change these checks. One earlier supplemental
reviewer harness failed because its global Popen mock intercepted Python's host
probe; that invalid run is retained in
[reviewer-harness-failure.txt](reviewer-harness-failure.txt) and is not a
candidate failure. A prior attempt during a concurrent edit also encountered a
renamed function; no acceptance claim uses that attempt.

The workflow diff adds only two `macos-15` steps. Existing Windows/Linux input,
Mac startup/source, Intel attribution and unsigned iOS steps are unchanged.
`READY_FOR_INPUT_ATTEMPT` is expressly bounded to later experimentation; neither
it nor these Linux controls qualifies native delivery, focus or OS capture.

The largest remaining evidence gap is the absence of an actual ARM Mac result.
After the two blocking guarantees are corrected and independently re-reviewed,
one clean-source run can establish native API availability, actual TCC booleans,
owned-window observation, source/export preservation and cleanup. Native input
acceptance remains open regardless of that run's readiness status.
