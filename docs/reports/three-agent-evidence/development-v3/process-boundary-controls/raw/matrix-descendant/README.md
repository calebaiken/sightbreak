# Matrix descendant control, 2026-10-19

Scope: only `scripts/validate_matrix.py`, `scripts/test_validate_matrix.py`,
new `scripts/matrix_process.py`, and new `scripts/test_matrix_process.py` were
edited in the checkout. No Godot, network campaign, export, commit, or GitHub
operation was run. The inventory tests mock all matrix commands.

## Before / after

`before/control_descendant.py` and `after/control_descendant.py` are identical
copies of the supplied critic control. Each imports its adjacent retained source
snapshot first. Both run with the isolated CPython 3.13.15 executable:

`C:\Users\blith\AppData\Local\Temp\opencode\sightbreak-tools\python\cpython-3.13.15-windows-x86_64-none\python.exe`

The before control reproduced `passed: true` followed by a child-written
`ERROR:`. The after control retained the actual root exit `0` but returned
`passed: false`, logged `HARNESS_ERROR`, killed the descendant, and its raw log
did not change during the eight-second post-return observation.

The supplied earlier critic descendant receipt is copied separately into
`original-critic-descendant-control/`. No previous evidence was modified.

## Final tests (all launched with that interpreter and `-B`)

| Command | Tests | Result | Raw output |
| --- | ---: | --- | --- |
| `scripts/test_validate_matrix.py -v` | 18 | OK | `test_validate_matrix.final.log` |
| `scripts/test_matrix_process.py -v` | 15 | OK | `test_matrix_process.final.log` |
| `scripts/test_source_identity.py -v` | 7 | OK | `test_source_identity.log` |
| `scripts/test_verify_builds.py -v` | 67 | OK | `test_verify_builds.final.log` |

The real Windows controls cover a surviving descendant, a separate process
group, timeout cleanup with retained partial output, blocked job breakaway,
non-inheritable job handles, and a normally awaited nested matrix check.

Initial attempts are retained too: `test_matrix_process.first.log` exposes a
Windows-host mock missing `SIGKILL`, fixed in the test; the initial verifier
invocation was stopped by the 30-second shell deadline and has incomplete
`test_verify_builds.log`. The final verifier invocation completed normally with
a 120-second shell deadline. Neither initial attempt is presented as passing.

## Source identity and limits

`after/reviewed-source-hashes.json` hashes all reviewed source copies, including
the dependencies used by these tests. `after/source-match-final.json` verifies
all eleven copies still matched the checkout after testing. The final process
inspection found no remaining isolated-interpreter process.

Windows containment was exercised for real. Linux subreaper, escaped-group,
leader-already-exited, and cleanup-error paths have mocked unit coverage only;
no real Linux runtime was available under the authorized interpreter constraint.
Non-Linux POSIX hosts fail closed before launching a command because a plain
process group cannot safely contain setsid/double-fork descendants. Unexpected
supervisor death or forced outside interference is a harness failure, not a
pass; Linux outer cleanup is best effort after such a failure. No claim of
kernel-level containment against hostile privileged processes is made.
