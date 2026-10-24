# Final cleanup-scope correction

Only these checkout files were edited:

- `scripts/matrix_process.py`
- `scripts/test_matrix_process.py`
- `scripts/godot_process.py`
- `scripts/test_godot_process.py`

No commits, staging, GitHub, databases, engines, native campaigns or exports.
All executed Python used the approved isolated CPython 3.13.15 with `-B`.
Controls and tests ran serially. Native launches/signals were mocked; real
process trees contained CPython only.

## Corrections and explicit limit

**F1, Linux exceptional-supervisor-death:** this is the permitted minimal
fail-closed scope correction, NOT durable crash recovery. A completed Linux
subreaper now retains `posix_cleanup_verified` only after reaping descendants.
The parent requires that attestation plus successful supervisor completion
before it can treat descendant cleanup as verified. Missing/failed attestation
retains the actual command exit when available, attempts only known owned
groups, and emits `HARNESS_ERROR ... detached-descendant cleanup unverified`.

An exceptional supervisor death can still leave an already detached child
reparented away. That unresolved limit is explicit in source, receipts and this
review; it is not claimed fixed. No caller-wide subreaper, cgroup, global process
scan, speculative PID kill or cross-work ownership was introduced. Ordinary
subreaper cleanup and exited-leader group signalling remain in place.

**F2, Windows standalone helper:** an already-exited root is reaped but raises
cleanup uncertainty instead of reporting verified descendant cleanup. Nonzero
taskkill is a failure even when the root exits during the call; the exited root
is not killed again. This intentionally also applies to direct helper callers
that lack prelaunch ownership, including an already-completed standalone leaf.
The separate parent-held Windows Job Object and prelaunch assignment in
`run_process` are unchanged. Linux harness/campaign behavior is unchanged.

## Evidence

`before/critic_controls.py` and `after/critic_controls.py` are byte-identical
copies of the original critic script. `run_review.py` preloads the appropriate
retained source snapshot, then runs the original control functions unchanged.
The after replay catches only their expected old-behavior assertions and adds
the corrected fail-closed gates. All original observations, raw logs, actual
commands and exits are retained. The real Windows grandchild is not killed by
these controls; a synchronize-only handle confirms its natural two-second exit.
Linux behavior is modeled with mocks, not claimed as real Linux execution.

`critic-packet-hashes-before.json` / `critic-packet-hashes-after.json` verify
that the original critic packet remained untouched. Reviewed source snapshots,
hashes, current-checkout equality, and an incremental four-file diff are saved.

## Verification

Approved interpreter:
`C:\Users\blith\AppData\Local\Temp\opencode\sightbreak-tools\python\cpython-3.13.15-windows-x86_64-none\python.exe`

From `after/source/scripts`:
`-B -m unittest -v test_matrix_process test_godot_process`

**77 tests passed, exit 0**: 17 matrix-process tests and 60 harness/source/
campaign tests. All prior 58 harness tests remain; the exited-Windows-root
expectation is deliberately stricter, and two race/uncertainty tests were added.
All campaign inventories, thresholds, source identity and evidence gates remain.

Both before reproduction and after scope-correction reviews exited 0 under
their respective gates. This is scoped synthetic verification, not a native,
CI, performance or acceptance pass.
