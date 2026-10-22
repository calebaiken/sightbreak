# Independent observer v2 readiness

Verdict: ready for a new controlled trial after the parent releases its execution
lane. This is a tooling review, not acceptance of an actual match. Trial 1 remains
BLOCKED and its original observer is unchanged.

Reviewed observer SHA-256:
`d1ec8562d95f614cb6e3e996febb66cf6e4dda1cce5ab8a3e94f7639fd949179`.
Reviewed recomputation SHA-256:
`09599411b2f3a2b8754dccc54f4d3fd4c6168e3587d7f2471e9f70205fc0ebb0`.
Original observer SHA-256:
`ca1c8fb7bf5edf8b537fe1e4b132aa0b6c4b559eea1773673ad04e6adcde8824`.

Sixteen standard-Python controls pass. `controls-d1ec8562-attempt-2.txt` contains
the complete result; `proof-receipt.json` binds the source and proof hashes and
retains the fake-process reports and outputs. Reproduce with:

```sh
python3 -B docs/reports/gauntlet/m3-account-activity-qualification/independent-review/v2-independent-review/independent_controls.py
```

The independent fake-process controls establish these specific behaviors:

- A stream stdin BrokenPipeError takes the child cleanup path, persists its PID
  and error, waits for the fake child, and closes its input and output streams.
- An explicit-query timeout kills the fake child, obtains and preserves its final
  stdout/stderr, and keeps the receipt at `not_observed`.
- A partially published replay checkpoint neither starts the final query nor
  aborts the observer; its invalid checkpoint tag is absent from the retained row.
- The actual recomputation's temporal fragment rejects a replay tag on an older
  stream row, a request made before replay despite a later SQL timestamp, a failed
  explicit query despite a later stream row, and changed final settlement tables.
  Its valid synthetic fixture passes both independent time boundaries.

The eight existing controls also pass, including rejection of the actual
first-trial in-flight row and partial/null/bad/naive checkpoint filtering. No
temporal false acceptance was found. The fixed SQL and Docker ownership checks
remain scoped to the run's fake container; no credential or environment read was
added. This review started no native game, API or container, queried no database,
and accessed no environment or credential values. All process interactions in
the proof are mocked. The temporal fragment is extracted with AST and does not
import or execute the recomputation's SQLite code.

The largest remaining gap is scheduling: unchanged builder teardown may remove
PostgreSQL before the separate final query completes. The oracle rejects missing
or failed final evidence. The stdout polling loop also cannot enforce its own
deadline while blocked waiting for a line. These are reliability limits, not
permission to infer acceptance. A new trial must use entirely new fake accounts,
resources and output; retain both actual post-replay stream evidence and the
separate successful query receipt.

Failed proof attempts are retained. The first 9cdbbed7 proof run omitted `json`
from the synthetic oracle scope; the corrected second run passed fourteen tests.
The first d1ec8562 proof run used an outdated prose marker to locate the AST
fragment after the parent strengthened its historical-payload rejection; the
corrected second run uses the `sha(raw)` statement boundary and passes sixteen
tests. These failures concern this independent proof fixture, not runtime results.
