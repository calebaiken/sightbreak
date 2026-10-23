# Fixture acceptance correction r1

Source and pure controls only. The previous implementation freeze
`12901729f7be29d0f64d87a0d92219a84500f1a6` was rejected for runtime readiness by
independent review `51add37cd801731016a2f52049e66b17fa90b393`.
The [complete rejection](retained-rejection/REVIEW.md),
[unchanged audit](retained-rejection/audit.py),
[original recomputation](retained-rejection/recomputed.json) and
[original 14-method output](retained-rejection/pure-controls.txt) are retained
byte for byte. The earlier passing suite did not cover these acceptance gaps.
This correction requests fresh implementation review; it grants no runtime release.

## Controller changes and unchanged registration

An unused numbered display must have neither a socket nor an X lock, including
dangling symlinks. Readiness checks the owned Xvfb's `poll()` and original
`/proc` start identity before testing the socket and again after ownership proof.
The lock must name that PID. The published filesystem socket path must map to a
kernel Unix-socket inode actually held by that exact process through `/proc/PID/fd`.
The filesystem socket and lock identities must remain stable during observation.
The controller retains launch and readiness/failure receipts. This closes the
dead-child/new-socket acceptance race without trusting a path's existence alone.

Each condition has one absolute deadline, starting immediately before the client
launch path. It remains **180 seconds**, with acceptance strictly before that
endpoint. `SIGALRM`/`ITIMER_REAL` uses the remaining time to interrupt blocking
host observations and reads in the controller's main thread. An already active
real-time alarm is rejected, and the old signal handler is restored. Monotonic
checks also run after observations, at already-published ready/metrics paths,
before acknowledgements, after waiting for an already completed child, after
final cgroup/PNG/log reads, and through source recheck, condition validation,
publication, publication reread and final receipt hashing. There is no 1 ms
wait extension. A late or interrupted condition fails and stops later launches.

Owned cleanup retains its separate bounded TERM/KILL teardown. It cannot convert
a late condition into a pass. Successful conditions include cleanup in their
acceptance elapsed time; teardown after a failure grants no extra measurement
time. Start, absolute deadline, ordered stage clocks, end and elapsed observations
are retained in `block.json`. The atomic `condition.json` is an immutable earlier
receipt, reread and validated before acceptance; its exact SHA-256 and the later
acceptance clocks are retained in the block. Failed reads leave original logs and
metrics on disk. POSIX alarms and postchecks supply interruption and rejection;
they do not claim to make an uninterruptible kernel operation terminate on time.

The evaluator directly rejects nonfinite or negative pre-anchor clocks and
requires a finite positive cold duration. Zero is a valid pre-anchor clock.
The later readback endpoint also requires a finite positive clock/duration.
Every external JSON read and serialized fingerprint uses strict parsing, rejecting
NaN, both infinities and finite-syntax overflow such as `1e999`. The writer was
already strict. Symbolic nonfinite failure summaries remain evidence only.

The fixture GDScript/scene, source content, graphics settings, OFF/ON/ON/OFF order,
32 warm and 64 measured intervals, all ratio/drift screens and the
[registration](../PREREGISTRATION.md) remain unchanged. Shipping game bytes,
the original offline controller/flags/deadlines and canonical mission files are
unchanged. Median cadence, ordered samples, total, mean and largest interval
retain their reviewed limited meanings. No shipping optimization or gameplay
cost/improvement claim is made; the original Linux gameplay failures stay failed.

## Pure evidence

The maintained suite now passes **22 methods**, no skips:

```sh
python3 scripts/test_linux_profile_overhead.py -v
python3 docs/reports/gauntlet/m1-linux-opaque-cost-plan/implementation-correction-r1/replay.py
```

[Raw output](controller-evaluator.txt) and [replay evidence](replay.json) are retained.
The replay executes the critic's three unchanged function ASTs against both the
rejected controller bytes recovered by `git show` and the corrected controller.
The full historical audit is not rewritten to drop its original frozen-byte
assertions. The replay supplies current hand-authored positive records, which add
deadline evidence, and replaces only invented-PID cleanup with a fake teardown.
No actual `Popen` is permitted outside the critic's fake-process patches.

The original functions reproduce all three old failures against `1290172`:
dead Xvfb accepted; all four virtual clients at 181.047 seconds accepted; and an
infinite cold-anchor value returned as comparable. Against the correction, dead
Xvfb rejects, the first 181.047-second client rejects before finish acknowledgement
and prevents later launches, and the evaluator rejects the nonfinite cold clock.
The original falsifier assertions therefore fail on the corrected source, with
their observed rejection reasons retained separately.

Additional maintained controls cover late already-present ready paths, final
host observation, an already completed child returning from `wait`, condition
publication, final publication reread, an explicit delivered alarm during host
observation, and exactly-180-second rejection. A complete four-condition virtual
block accepted after publication/final read at **179.999 seconds per condition**
passes. A separate timer control verifies a 0.5-second remainder is armed rather
than restarting 180 seconds and that the previous handler returns. Virtual-time
cases mock timer arming to avoid mixing a 1 ms virtual remainder with real test
execution time; the explicit alarm control still invokes the production handler.

Positive socket-ownership data join the live PID, start identity, lock PID and held
kernel inode; mutations of each identity reject. An existing lock rejects before
process creation. Direct evaluator/API controls cover nonfinite/negative cold
endpoints, zero-clock acceptance, strict JSON constants/overflow, the 179.999/180
deadline boundary, and the prior estimator/treatment/source/host/cleanup controls.
[Case summaries](deadline-cases.json) and the compressed complete synthetic
positive boundary records are bound by the [correction ledger](source.json).

No Godot process, engine/import/compile/UID/export action, native fixture/Xvfb,
profiler, OCR, CI or service ran. GDScript syntax, resource traversal, actual
fingerprint/pixel stability and driver/runtime behavior remain unverified.
Fresh exact-source independent review must precede any separately authorized
staging/export/native lane release.
