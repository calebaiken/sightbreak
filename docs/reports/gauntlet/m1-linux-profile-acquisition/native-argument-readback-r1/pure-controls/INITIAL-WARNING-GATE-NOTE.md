The first eight-method control run had seven passes and one failed assertion.
The new test incorrectly expected the existing standalone `native_log.failed`
error/leak matcher to reject a warning. It does not; the outer acquisition's
unchanged `strict_log` and raw-condition readback supply the strict warning gate.
The failed run is retained as `initial-warning-gate-assumption-failed.txt`.

The correction changes only the test: it records that standalone behavior and
adds the exact original VSync warning to otherwise valid synthetic bound data,
then exercises real `Acquisition.run_block()` and requires rejection there. The
strict implementation remains unchanged; no warning is suppressed or forgiven.
