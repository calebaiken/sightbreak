# Independent review of 1195b234

Request changes for one reproduced P2 evidence defect. The candidate improves
normal Linux source-suite isolation over `6a0d8d5`; its cleanup failure receipt can
claim success after cleanup fails. Windows/macOS native execution remains pending.

The reviewed source was a clean detached worktree at
`1195b23423b4cb37c613e9e0304508d4c2637aff`. Later uncommitted builder work was excluded.
Baseline and candidate have the identical game tree
`13079ab8a3de9b18252a652ed57157e0776cf394`, so game assertions and persistence guards
were unchanged. This was an identified source/evidence comparison; no blind
preference or quality score is claimed.

## Reproduced finding

P2, `scripts/run_native_regressions.py:163–180`: a namespace deletion failure after
successful native suites can write `isolation.json` with `passed: true`,
`failure: null`, and `cleanup: []`. `__exit__` computes success from its incoming
exception rather than an exception raised by cleanup, and `all([])` succeeds.
The process still fails, so CI is not falsely green, but the retained acceptance
receipt is false and the owned namespace remains on disk.

`cleanup_failure_control.py` ran the real pinned native `peer_lifecycle` suite
successfully, then injected PermissionError only for that runner's namespace
deletion. `cleanup-failure-observed.json` records the error, false success receipt,
and namespace residue. The reviewer then removed only that owned residue.
The candidate code was never edited. Require explicit cleanup error evidence,
an outcome for every owned namespace, temporary-project removal, and preservation
of the original native failure if cleanup also fails. This is the largest internal
correctness deficiency in the reviewed candidate.

## Native evidence

Engine `4.7.2.stable.official.ed1daf0bf`; the installed binary matched its editor
archive, whose SHA-512 matched the pinned toolchain checksum. All native runs used
fresh review-owned state under `/workspace/reviews/m2-isolation-critic/state/`.

| Suite | Native checks | Exit |
| --- | ---: | ---: |
| actor | 73, zero failures | 0 |
| match | 75/75 | 0 |
| state_privacy | 55, zero failures | 0 |
| movement_prediction | 725, zero failures | 0 |
| peer_lifecycle | 16, zero failures | 0 |
| input_mode | 31, zero failures | 0 |
| menu_focus | 30, zero failures | 0 |
| offline_diagnostics | 60, zero failures | 0 |
| hud_objective_hint | 33, zero failures | 0 |

Every suite had a distinct engine-reported path beneath
`state/all-nine/data/SIGHTBREAK-native-tests-1825226d93d748709c6be34f9d022188/`.
Each before-probe reported no profile or diagnostics, and each after-probe reported
the same path. The reader checked native logs, exits, engine-selected settings,
copied produced-file hashes, and actual namespace removal. Normal import took
4.933 seconds; these are source-test execution costs only. The workflow keeps the
same nine-suite list/order and 120-second suite timeout; setup is bounded at 120
seconds and probes at 30 seconds. These bounds were inspected in source and
receipts; a deliberately hung 120-second process was not run.

The save-safety run reproduced the real shared-producer failure: input-mode passed
31 checks and wrote a canonical profile; menu-focus then exited 2 with
`Use a fresh isolated state directory; player saves are never overwritten`.
The produced bytes stayed unchanged. This matches the retained ARM Mac CI failure
from run `39712752860`, job `119607694324`, inspected in the candidate evidence.
The test then preserved a canonical sentinel while the three isolated suites
passed, verified native CRLF startup, and rejected an existing suite save before
that suite executed. Both normal runs removed their private project and owned
namespace. All 295 source game resource bytes matched the saved inventory and Git
objects. All 47 preexisting workspace/user profile files, including a separate
preexisting ordinary-path review sentinel, remained byte-identical.

The candidate wins the baseline comparison for normal Linux test correctness:
the shared save no longer blocks menu-focus or the following suites, while the
save guard remains strict. The cleanup receipt defect must be corrected before
acceptance. Actual Windows/macOS native paths and the next CI run remain pending;
these source runs establish no exported gameplay, physical input, visual quality,
performance or release qualification.

Raw logs, engine receipts, inventories, commands and fault controls are retained
beside this report. `INDEPENDENT_CHECKS.json` contains the independent readback.
