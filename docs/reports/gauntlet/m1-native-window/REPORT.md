# Native X11 lifetime correction

Candidate implementation is ready for independent review. The builder has not
accepted the component or the larger desktop milestone.

The baseline controller terminates its Python process when a native window
disappears between discovery and inspection. A real-Xvfb regression reproduced
the reported `BadWindow / X_GetProperty` failure and a second fatal
`BadWindow / X_SetInputFocus` race. Both child processes exited 1. Their unchanged
raw output is in [baseline-races.txt](baseline-races.txt).

## Change and evidence

`NativeUI` now checks native requests inside a scoped Xlib error handler. It drains
earlier errors separately, synchronizes each request while the callback is alive,
then restores the previous handler. Only the expected missing-resource code,
request and target on the controller's display qualify as a vanished window.
Unrelated errors raise a Python exception with their protocol details. Handler
installation is serialized across this module's controller instances because
Xlib's handler is process-wide.

Discovery skips vanished candidates. Focus returns false for a vanished target
and confirms successful focus from the server. Diagnostics clear destroyed cached
targets. Layout geometry and close requests fail through Python so the existing
caller's cleanup can execute; a missing window never becomes a passed capture.
The existing geometry bounds and advertised `WM_DELETE_WINDOW` checks remain.

| Matched check | Baseline | Candidate |
| --- | --- | --- |
| Destroy after enumeration, before real `XFetchName` | Fatal Xlib exit 1 | Survives; discovers/focuses the surviving named window |
| Destroy immediately before real focus request | Fatal Xlib exit 1 | Returns false; stale target cleared |
| Legitimate largest named window and advertised close | Pass | Pass |
| Fifty focus/diagnostic iterations | 0.015908 s | 0.060310 s |

The extra checked round trips increase this tiny query workload's elapsed time.
The candidate stays within the predeclared five-second watchdog. These timings
come from one shared Linux host and are not a game-performance improvement or a
physical-device measurement.

[Final native output](candidate-native-tests-r2.txt) records nine child cases,
all exit 0, and a cleanly reaped Xvfb process. The additional cases cover stale
diagnostics, actual layout geometry on a destroyed target, close failure,
unrelated `BadValue`, a pending unrelated error, an error for another resource,
and prior-handler restoration after success and failure. All created fixture
windows and connections close. Injection wraps an operation boundary but issues
real destruction and real failing requests to Xvfb; these are not mocked replies.

The earlier [seven-case exploration](candidate-native-tests.txt) also passed.
It was an intermediate working copy, before the extra error-boundary and close
controls, and is not the final source receipt.

The adjacent [observation regression](native-observation-regression.txt) ran
seven tests: four passed and three Windows-only cases were skipped on Linux.
Python compilation and `git diff --check` passed. No Windows execution is claimed.

## Reproduction and source identity

Base: `561d0cbba651514bfac96c50437a849d65843545`.
Branch: `codex/native-window-lifetime`.
[SOURCE.json](SOURCE.json) records final code hashes and the tested baseline file.

```sh
python3 scripts/test_native_window_lifetime.py \
  --xvfb /workspace/tools/xvfb/usr/bin/Xvfb
python3 -m unittest discover -s scripts -p test_native_observation.py
python3 -m py_compile scripts/verify_integration_export.py \
  scripts/capture_desktop_layouts.py scripts/test_native_window_lifetime.py
git diff --check
```

For the comparison, write `git show 561d0cb:scripts/verify_integration_export.py`
to a temporary file and pass its path with `--module`. Run `--case discovery-race
--case focus-race` to reproduce the two fatal baseline controls; run
`--case positive-and-repeat` for the matched positive/timing workload. The default
isolated display is `:231`; choose another unused number at least 200 if needed.

## Limits and next review

Actual exported layout generation must be repeated on the integrated candidate.
This component test does not certify all layout sizes, game captures, gameplay,
physical-platform behavior, input responsiveness or visual quality. X server
disconnects and arbitrary concurrent third-party Xlib handler replacement are
outside this change. Unexpected protocol errors remain failures.

The critic should inspect the actual raw outputs, repeat native cases and compare
the scoped correctness result with the baseline. The largest unverified issue is
whether the complete exported-layout workflow now finishes under its original
conditions; the builder does not infer that from tiny-window tests.
