# Native ARM Mac input preflight

Revision 2 narrows the original launch-side-effect wording after independent
rejection. Read-only describes the permission queries. An ordinary exported
smoke launch can create Godot user-directory caches; those effects must be
inventoried and retained. No native player profile may exist before launch.

Declared 2026-10-22 before implementation. The inspected baseline is the actual
ARM run [39721286005](https://github.com/calebaiken/sightbreak/actions/runs/39721286005)
at `2a2b732`: native startup, source suites and unsigned iOS compile passed their
bounded independent reviews. Its workflow deliberately excludes Mac input.
`verify_integration_export.py` uses X11 or Win32, with no Darwin implementation.
This increment measures native readiness; it cannot pass keyboard, pointer,
offline gameplay, physical-device or human-play acceptance.

1. Run only on native ARM macOS. Retain exact host, native engine identity,
   clean source/build-manifest identity and executable SHA256. Revalidate source
   and the export after execution. Linux controls establish observer readiness.
2. Query only non-requesting permission APIs: `CGPreflightPostEventAccess`,
   `CGPreflightScreenCaptureAccess`, `CGPreflightListenEventAccess` and
   `AXIsProcessTrusted`. Preserve each boolean and API name. A false posting or
   capture preflight is `BLOCKED_EXTERNALLY`; do not request permission, post
   input, use AppleScript/System Events, alter TCC, or retry through another
   identity. Listen/AX results are diagnostic; their failure does not establish
   posting/capture denial.
3. Inspect active-display bounds and `CGWindowListCopyWindowInfo` for the exact
   exported child PID. Record only that child's windows. Window metadata does
   not establish keyboard focus or event delivery. No unrelated window titles,
   screenshots or player profile contents are retained. To keep the internal
   smoke PNG free of existing callsign/training data, require canonical native
   `offline_training.json` and `.tmp` entries absent before any export launch.
   Existing entries, including dangling links, block launch and remain untouched.
4. Launch the unchanged real export using existing `--smoke --capture` behavior
   and supported `--windowed --resolution --position` flags. Observe a visible
   PID-owned layer-zero window before normal exit and retain its original
   internal PNG. Require normal exit zero, clean native log and
   `SIGHTBREAK_MAIN_READY screen=menu`. The PNG proves exported rendering only;
   it is not an OS screenshot. Never call obsolete screen-capture APIs.
5. Bound the native run to 60 seconds; on cancellation/failure reap only the
   owned process group, verify it is gone, and retain truthful cleanup receipts.
   Preserve prior attempts by rejecting nonempty output. Use supported
   `--log-file` to put the engine log in evidence. Observe pre/post native
   user-directory filenames, sizes and hashes, including cache creation/change;
   never remove those files. Verify the two player-profile entries remain
   absent. Ordinary launch side effects are distinct from read-only API queries.
6. Existing Windows/Linux source/input gates, Mac default startup, source suites,
   Intel attribution and unsigned iOS gates remain unchanged. Register this as
   a separate ARM-only diagnostic. No CI dispatch until independent source
   review; no readiness result becomes native-input acceptance.

If permission allows the next step, implement one ordinary menu/settings
navigation with real CoreGraphics keyboard and pointer input, native focus and
control-state observations, supported OS screenshots and independent pixel
review. Persistence changes require a verified native profile-isolation method
first. Mac permission denial remains the exact external blocker; startup and
iOS compile results stay distinct.
