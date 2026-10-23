# Explicit Windows diagnostic execution adapter

Before workflow edits, register a manual opt-in for the separately reviewed
Windows input-observation source. Original `desktop-alpha.yml` uses the normal
undelayed exported-input command, and none of its invocations request the new
diagnostic flag. Dispatching it unchanged cannot measure the missing stages.

Add one boolean workflow-dispatch input, default false, and append the fixed
`--observe-input-consumption` flag only for Windows when explicitly selected.
Keep original matrix, permissions, actions, exports, native suites, controller
schedules, all timeouts, outputs, delayed comparisons and other platforms exact.
No shell text may come from a free-form dispatch input. Enabling the adapter
must still use the runtime guest/debug/loopback admission gates; it grants no
new gameplay or authority behavior.

Benchmark the workflow structure against the original with the new input and
one fixed expression reversed; every other byte must match. Parse the YAML and
independently review the combined source before release. Preserve source-only
limits: the reader correction, runtime hooks and initial route pulse all need
their own independent acceptance and exact combined verification. New Godot
runtime checks and actual native behavior remain unexecuted.

No workflow dispatch, native run, release reference or qualification is granted
by this adapter. Actual criteria, immutable source/ref binding and one explicit
root release must precede any later run.
