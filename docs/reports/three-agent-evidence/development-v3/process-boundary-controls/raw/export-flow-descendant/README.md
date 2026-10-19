# Export-flow descendant follow-up

Only `scripts/export_flow.py` and `scripts/test_export_flow.py` were edited in
the checkout. Shared matrix/process code and `godot_process.py` were not edited.
No Godot, native bulk work, campaigns, exports, commits, or GitHub operations.

All Python commands used the approved isolated CPython 3.13.15 executable:

`C:\Users\blith\AppData\Local\Temp\opencode\sightbreak-tools\python\cpython-3.13.15-windows-x86_64-none\python.exe`

## Controls

`before/` and `after/` contain identical copies of the supplied
`synthetic_descendant_entry.py` / `run_descendant_entry.py`. Each imports its
adjacent retained source snapshot first. Actual commands and exit codes are
recorded in `before/command.json`, `after/command.json`, and their nested
watchdog receipts. The original critic packet was never executed in place or
edited; full before/after hash manifests verify it remained unchanged.

Before: entry exit `0`, passing persisted JSON, then the descendant appended an
`ERROR:` after return. After: entry exit `1`, worker actual exit `0`, failed
persisted JSON, retained `HARNESS_ERROR`, no completed child marker, and stable
raw output after return. `watchdog.process.json` retains the containment receipt.

## Tests

Final tests execute the retained reviewed-source copies, not a later moving
checkout. Command JSON files record executable, argv, working directory, and
actual exit code.

- `test_export_flow.retry.log`: **27 tests, OK, exit 0**.
- `test_matrix_process.final.log`: **15 tests, OK, exit 0**.

The first export-flow run passed 26 tests before one final-audit deadline test
was added. The first 27-test batch (`test_export_flow.final.log`) failed with
an explicit Windows `WinError 1455` (paging file too small) plus missing entry
receipts. Its failed logs and exit code are retained, not presented as a pass.
The serial retry used unchanged reviewed source and passed all 27 tests.

Real CPython controls exercise entry, owner-token validation, initial failed /
incomplete receipts, descendant exit-zero + passing-JSON escape, separate
process groups, timeout cleanup, stable post-return logs, and normally awaited
children. Mocked controls exercise cleanup failures, stale evidence refusal,
receipt/source-hash preconditions, and startup/final-audit deadline expiry.

## Deadline and platform limits

The requested wall-clock **pass deadline** includes startup, command execution,
cleanup, and final audit. An expired deadline can never become a passing flow.
On failure the shared runner has bounded additional cleanup waits; the code
does not abandon descendants merely to return exactly at the pass deadline.
Real short-deadline controls assert return within four seconds.

Windows containment is exercised for real. Linux subreaper / POSIX cleanup
paths have shared mocked-unit coverage only here. Non-Linux POSIX hosts fail
closed through the shared runner before launching commands.
