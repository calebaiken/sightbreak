# ARM Mac input readiness candidate

Candidate worktree: `/workspace/sightbreak-macos-input`, branch
`codex/m2-macos-native-input`, based on `e38ec3c`. [Criteria](CRITERIA.md) were
declared before source changes. No CI has been dispatched from this branch.

`scripts/probe_macos_input.py` queries supported read-only permission/display/
window/control APIs, then launches the unchanged exported smoke path. Existing
canonical player-profile or `.tmp` entries block that launch, so the screenshot
cannot retain existing callsign/training data. It retains
only windows owned by the exact child PID, the export's internal PNG, source and
artifact identities, profile-entry observations and process-group cleanup. It never posts
events, requests permission or takes an OS screenshot. Denied posting/capture
preflight returns exit 2 and `BLOCKED_EXTERNALLY`; missing native APIs and failed
startup remain failures. A ready result permits a later attempt and cannot pass
native input.

The engine log is redirected through supported `--log-file`. Native user-directory
cache/log files are inventoried before and after; ordinary launch may still
create/change native caches, and those files are preserved. Read-only describes
the permission queries, not all ordinary engine startup behavior. The first
candidate `ecb3070` was independently rejected for failing to distinguish these
side effects and allowing existing profile data into its smoke PNG. Revision 2
fixes both issues; the original criteria and first controls remain in Git.

The existing registered desktop workflow gains two separate ARM-only steps.
Every existing Windows/Linux and Mac gate remains in place. Parent review must
approve the source before a native dispatch; native output then needs a fresh
critic. Run on the same exact clean source as its Mac export:

```sh
python scripts/test_probe_macos_input.py -v
python scripts/probe_macos_input.py --output builds/desktop-playability/macos-input-preflight
```

Nine observer controls pass on Linux; the [revision 2 raw output](readiness/controls-r2.txt)
includes absent/existing/dangling player-profile entries and native cache
inventory without deletion. The [first seven controls](readiness/controls.txt)
retain an intentional native-host rejection and an actual owned-process cleanup
control. An initial control failed because a global `Popen` patch intercepted
Python's platform probe; the control now supplies its platform string explicitly.
There is no Mac API or native input pass in these controls. No engine workload
was run, beyond reading pinned Godot 4.7.2 `--help` to verify window flags.
The [earlier-step source inspection](PRIOR_STEPS.md) predicts fresh QA leaves no
canonical player profile; runtime entry checks still govern launch.

The largest open gap is actual ARM permissions. If both required preflights are
true, the next useful slice is pointer Settings navigation followed by Escape
back to the menu, with supported ScreenCaptureKit OS screenshots and frontmost
PID/control-state receipts. Persistent controls need verified Mac profile
isolation first. Pinned Godot has neither `--borderless` nor `--user-data-dir`.
Current Mac APIs obsolete `CGWindowListCreateImage`; do not runtime-call it as a
shortcut around ScreenCaptureKit. Prior unsigned iOS compile and startup reviews
remain separate from this unverified input work.
