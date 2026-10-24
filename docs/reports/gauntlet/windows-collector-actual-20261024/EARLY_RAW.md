# Early partial job-log findings

Supported GitHub job-log read at2026-10-24 09:11:54UTC returns a partial stream,
retained verbatim in `job-log-early.log` and its connector response. The decoded
UTF8 stream is2,172,019 bytes, SHA256
`5a242a8ccb3e507e83d91042354b2504b8d80d19609593f90d3e06cca8fc0abc`,
37,415 lines. It ends inside JSON at09:08:23; it is not the terminal complete
job log and cannot replace final raw logs or artifacts. No reason for this
snapshot boundary is asserted.

First staging returned1 because the repository ignores `.log` files. No commit
ran in that chain. The unchanged original log is explicitly force-added;
authored-file whitespace checks exclude that verbatim CRLF stream. Its Git
attributes are unspecified, so byte identity is checked against the staged blob.

The evaluated ordinary command at line486 is the preregistered Windows
`--visit-armory --timeout240 --observe-input-consumption` invocation, without
synthetic delay. Its printed result reports four shots, native client reload,
and38.171 seconds. The two delayed printed results report three shots/36.203
seconds and29 shots/36.328 seconds; the legacy inner exit receipt is0. These
are preliminary producer facts, pending independent original log/telemetry/
collector/action/capture reconstruction.

The living step starts09:06:31. Its visible traceback at line10954 is
`RuntimeError: Reopened export failed clean shutdown`. Exact candidate
`verify_offline_export.py:1021` raises this after reopened wait if either its
exit is nonzero or the complete reopened log fails the strict matcher. That
distinction is not resolved by the partial stream.

The same partial output reports `FIXED_ROUTE_REACHED`, six
`API_RETURNED_WITH_OS_RELEASE` pulse statuses,
`LIVING_CONTEXT_PRESERVED_THROUGH_CAPTURE`, and `LIVING_MOVEMENT_OBSERVED`.
It therefore reaches later controller code than the prior coarse-corridor
failure. The original states, native guards, stopped endpoint, settings,
LEAVE/reopen/focus and pixels still need independent verification. No success
flag overrules the later failed shutdown gate.

At09:14:26UTC the connector reports full-stock-match step33 still active;
living step30 remains the only reported failed step. Both objective steps report
success. The selected Windows qualification has a blocking producer failure;
separate passing scopes remain provisional until their raw evidence is checked.
No retry, source fix, causal diagnosis or overhead conclusion follows.
