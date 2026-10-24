# Exact original-control adapter before execution

Original fifteen controls and three separately excluded API-only totals models
come from eac72c2e/fresh_controls.py, copied byte-exact as literal_original_controls.
Run that literal script first with a protected harness; it may abort at a changed
exception type. Preserve its exact raw output/status, without calling it a full
fifteen-case result.

The separately frozen adapted script changes only two direct failure catches from
OSError to (OSError,ValueError), because the repair explicitly returns aggregate
ResourceFinalizationError(ValueError). All matching/closure assertions remain.
The late-close delay moves from the stream wrapper.close extension into the actual
stderr sink.close after successful close, using the same model clock/two seconds.
Both default source versions actually close that sink. This preserves the intended
source-supported blocking-close deadline test when the repair finalizes known
resources directly instead of invoking wrapper.close. No production method changes.
Run this identical adapter on frozen b16 and ab864; report its differences from
original preserved eac outputs. No model count, expected predicate or input payload
change. The script's hardcoded b16 source/runtime summary fields are original labels;
actual target/code hashes are pinned separately by this review, never inferred.

Select80 old pure methods under the previous explicit SDK/proc omissions plus16
new repair methods. Register a protected wrapper before imports that blocks real
Popen/system/spawn, dynamic CDLL/WinDLL and pidfd/signal actions. Local Git source
proof runs outside that wrapper, not during tests. New temporary pure files may be
removed by their own test hygiene after resource observations are recorded; no old
archives/checkouts are removed. No native/SDK/helper/process probe is permitted.
