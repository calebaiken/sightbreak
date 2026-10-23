# Native/PostgreSQL receipt evidence

See [results and reproduction](../NATIVE_TRANSACTION_RESTART_RESULTS.md).
Files here are byte-preserved evidence (`.gitattributes` disables text conversion).

## Completed measurements

- `r9/baseline/`: exact `701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd`, three cases,
  **0/3 recovered**, all three authority/no-second-mutation checks pass.
- `r10/candidate-7b6f379/`: exact `7b6f379a3f8c809d0985a64e883cbadfdd78d135`,
  three cases, **3/3 recovered**, all authority/no-second-mutation checks pass.
- Both measured with identical harness/probe bytes frozen at `31438cbc`.
- `verification.json`: values independently extracted from retained rows/events;
  manifest integrity, barrier ordering, full economic-state equality, and exact
  original/retry request bytes were checked after the runs.
- `git-source-verification.json`: measured archive/source-file hashes re-derived
  from the exact Git commits. `publication-manifest.json` covers this bundle.

Within each arm, `summary.json` binds source, runtime, harness and probe hashes.
Each `run-N` contains safe fixture configuration, a timestamped/PID event stream,
five PostgreSQL snapshots, native stdout/stderr, journal snapshots and checks.
`*.raw.json` journals contain the original receipt bytes. Authentication secrets
are redacted; token digests and real PostgreSQL session rows establish fresh
authentication without publishing reusable credentials.

The optional native economy regression has separate original and calibrated
folders. The original **36/37 failure is retained**. The external one-line DNS
calibration passed **37/37**, and both executed GDScript sources are included.

## Earlier attempts and setup

| Folder | Retained outcome |
| --- | --- |
| `r1` | Python internal compiler failure while importing SQLAlchemy; no native purchase; generated database dropped. |
| `r2` | Occupied-native-slot preflight rejection, transcribed from tool output; no database created. |
| `r3` | Waiting wrapper's Windows `tasklist` out-of-memory failure before the harness ran. |
| `r4` | Resource gate timed out after 20 minutes; no measurement. |
| `r5`, `r6` | Real API/seed succeeded, native never reached HTTP barrier; databases dropped. |
| `r7` | Same startup failure with verbose capture and early probe events; database dropped. |
| `r8` | Same startup failure after setup-memory reduction; database dropped. |
| `r9/candidate-preflight.txt` | `cda6372` attempt refused the now-different shared cache checkout; no measurement. |
| `startup-diagnostic` | UI-only startup and parse checks; unread-pipe control reproduced the capture blocker. |
| `candidate-cache-preparation` | The pre-interruption isolated `cda6372` import completed; only line-ending metadata was restored. |
| `resume-finalsource` | PostgreSQL restart failure, successful recorded-cluster restoration, and exact `7b6f379` cache preparation. |

The successful capture correction uses private temporary files while the first
native process awaits the response barrier. Output is read/redacted after exit.
The first harness freeze `1fa754b` and later corrections are preserved in Git and
in the attempt-specific harness/probe copies. No successful `cda6372` PostgreSQL
recovery is claimed. No independent critic was dispatched by this harness task.
