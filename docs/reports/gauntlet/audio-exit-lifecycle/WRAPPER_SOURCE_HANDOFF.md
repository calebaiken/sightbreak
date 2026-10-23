# Acquisition wrapper source freeze

Separately reviewable wrapper, preregistered at `57e5921`, following analyzer
freeze `73cdfc2`. It is Linux-only and uses `/proc` start ticks with PID/PGID/SID
observations. Mac/Windows acquisition is unsupported. No product platform code
changed. Both analyzer and wrapper need fresh independent review before use.

The exact original root verbose controller is retained with SHA-256
`43dfdeae51aaa95dbb43aeb33125c772688f50e604cc471c8b4ba0309734c7fe` under
`wrapper-preregistration`. This adaptation adds exact source/Git-blob checks,
caller-pinned executable SHA-256 and version, native userdata probes, per-file
UID/cache inventories, strict import scanning, finalization on errors and time
reserved inside the whole bound. It uses individual validated PID/start signals;
group/session membership is recorded and required gone. It never kills by name.
Unlike the old error-line matcher, `native_log.failed` retains ObjectDB WARNING
failures, including exit-zero import failures that skip the suite.

One exclusive fresh directory reserves the attempt. Every copied game byte
matches the clean full source commit; only the two declared userdata settings
change in the owned private project. Import may add Godot cache files and valid
UID sidecars for copied scripts without a prior sidecar. UID bytes and source/
copy maps are retained. Before/after engine probes must report the exact private
project, private XDG/native userdata and default Dummy driver. The suite reports
its actual driver again, bound to unchanged headless argv. An incomplete actual
fixture owner census fails acquisition integrity; unknown playback owners remain
explicit in the analyzer output.

Process caps are 120 seconds for import and suite, 30 seconds for version and
identity probes, 240 seconds for the whole attempt. Each process launch reserves
five seconds for cleanup and eight for finalization inside that whole bound.
TERM/KILL cleanup rechecks exact PID/start identity before signaling. Reused PIDs
are skipped; escaped children already observed remain tracked by stable identity.
An unproven root group/session is not signaled. Observed survivors or remaining
original session/group rows fail cleanup and retain the private trees. Polling
can miss an unseen child that escapes/reparents between observations; complete
arbitrary-descendant cleanup remains unqualified.

All actual combined stdout/stderr logs retain hashes and attempted-phase
receipts. Overall errors/finalization failures remain failures. After inventory
and source checks, produced private state is archived and owned project/state
directories are removed only if process cleanup is proven within this scope.
A strict leak returns exit 1 even when acquisition integrity passes. A clean
sample never changes `original_leak_blocker_resolved=false`.

Pure checks: `python3 scripts/test_acquire_audio_lifecycle.py -v` passes 13 tests.
Full flows use mocked phases and explicitly synthetic logs/UIDs; process-loop
tests use mocked Popen, clocks, process tables and signals. They cover exact argv,
strict warnings, source/engine/fresh-output refusal, real blob checking, UID and
source drift, foreign/preexisting userdata, wrong driver, spawn failure, timeout
reservation, escaped observed child cleanup, PID reuse, stubborn TERM/KILL
survivors and receipt preservation. `wrapper-pure/expanded-process-controls.log`
retains a test setup error where one new clock control initially used a real
expired deadline; the corrected final result is separate. No engine process ran.

Future command shape, only after separate release of the exact source:

```
python3 scripts/acquire_audio_lifecycle.py --source-commit <full-reviewed-wrapper-commit> --engine <pinned-linux-executable> --engine-sha256 <reviewed-executable-sha256> --output <fresh-owned-ignored-or-external-directory>
```

The wrapper has no download/install, driver override, existing exact-argv replay
change, extra game actions/waits, or leak suppression. Observer/hooks and all
422 original source paths remain unchanged. Native preparation, GDScript/API
correctness, actual cleanup, actual ownership and strict cleanliness remain
UNVERIFIED. This builder ran no Godot/import/UID generation/GDScript compile,
native/CI/OCR/service and issues no source or runtime approval.
