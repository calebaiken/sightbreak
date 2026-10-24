# Root deadline rejection and correction

Root inspected preparation `4ca7dc5d3e5f891650a60bec7a5a65dc28397bb9` and held
release. It found a concrete defect: the monitor accepted `child.poll()`
completion before comparing observation time to the420s deadline. A zero exit
first observed at or after420s could therefore produce a pass. There was no native
run, observer activation or output directory, so this is a rejected preparation,
not a failed or retried acquisition.

The original wrapper remains byte-identical in
`run_once-first-deadline-rejected.py`, SHA-256
`6f3ac3faeb2ec2558099257b654494e988e15a3ac60e18aa8c1df6e0148ab994`.
The original admission, controls and outputs also remain in commit4ca7dc5d.

The corrected wrapper reads the monotonic time after polling. Its shared
`deadline_state()` decision treats every observation at or after the deadline
as timed out, including a zero return code. The actual pass predicate also
requires `native_completion_within_whole_deadline`. It records
`runner_exit_observed_seconds`/UTC separately from cleanup and total wall time.
Cleanup remains a separate maximum5s and original phase limits are unchanged.

Pure controls call the same decision with successful completion at420.0,
420.001 and421.0; all time out. Completion at419.999 is admitted to the other
acceptance gates. A child still running at420 stops; at419.999 it continues.
The previous source, fresh-output and mocked cleanup controls still pass.
All ten controls use CPU4; no real observer, engine or native signal runs.

The corrected wrapper SHA-256 is
`1e3a8123a5c3adf4d3d379c3c6ff5703f514c9f7425a76e40cb2f5f52922b057`.
Root must inspect this revision and issue a new release binding this hash before
the sole invocation. The fixed output remains absent.
