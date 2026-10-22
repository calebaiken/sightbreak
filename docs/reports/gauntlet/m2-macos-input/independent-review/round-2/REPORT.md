# Independent source review: accepted for one actual ARM preflight

Subject: `946446f11c3bf4bf46439b7a8ec97dea76d032a1`, including the revision-2
criteria and the six-line workflow delta from `e38ec3c`. Reviewed 2026-10-22.
Later `69df937` changes documentation only; the inspected implementation and
criteria are identical. No Mac host, native export, engine workload or CI was
run by this reviewer.

**ACCEPT for one actual ARM permission-query and ordinary owned-export-window
preflight under the revised criteria.** No remaining source blocker was found
for this bounded diagnostic. Native keyboard/pointer input, focus, OS capture,
gameplay and device/human-play acceptance remain open. This is source approval
for a run, not approval of an unseen run or a later event-posting driver.

Both [first-review blockers](../round-1/REPORT.md) are resolved:

- `require_absent_profile()` rejects canonical profile and temporary entries
  using entry-aware `lexists`, including directories and dangling links. The
  guard runs before native-directory inventory and again immediately before
  `Popen`. The ordinary menu therefore starts from absent player-profile entries
  under the declared prerequisite, without hashing or reading an existing
  profile. After owned-process cleanup, newly appearing profile entries force
  `FAILED`. This is a pre/post entry observation, not filesystem isolation or a
  lock against another concurrently running application.
- Supported `--log-file` directs the engine log into evidence, and both captured
  stdout/stderr and the engine log are checked for native errors. The criteria
  now state that ordinary startup may write native caches. Before/after native
  filenames, sizes, hashes and directory effects are retained; native files are
  preserved. The claim is player-profile-entry preservation, not complete
  native-user-directory immutability.

The ctypes/API assessment from round 1 still applies. Darwin-arm64 primitive,
pointer and CGRect declarations are consistent on source inspection; missing
symbols fail closed. No requesting permission API, event creation/posting,
AppleScript, TCC mutation or obsolete screenshot API was added. Window report
entries are limited to the exact exported child PID at layer zero; unrelated
titles and metadata are discarded. Combined-session key/button snapshots do
not prove focus or delivery. Actual symbol availability, native ABI behavior and
TCC booleans remain unmeasured.

Clean source identity, the export receipt/full payload and executable hash are
checked before launch; source and export validation repeat after a successful
cleanup/finalization path. A new session scopes TERM/KILL cleanup to the owned
process group. A remaining group forces failure. The prior exited-leader/live-
descendant observation remains a conservative false-failure limitation: cleanup
does not poll group disappearance after a leader has exited. The native-child
deadline is a Python polling budget; synchronous OS calls and native-directory
hashing do not have separate watchdogs. Neither limitation permits false
readiness in the controls inspected here.

All nine packaged Linux controls pass. The independent
[frozen-source harness](review_controls.py) additionally passes ten integrated
mocked-flow checks: existing file/directory/dangling profile refusal without
spawn; a profile appearing before the second guard; engine-log redirection and
preserved cache creation; profile creation after launch; engine-log error;
remaining owned group; source drift; and expired child-run budget. The
[raw output](controls.txt) records the source commit and script SHA256. Only the
packaged process-group control launches a real disposable Python child; native
APIs, exports and engine execution are absent from these tests.

The workflow still adds only the ARM `macos-15` observer-control and preflight
steps. Existing Windows/Linux input, Mac startup/source, Intel attribution and
unsigned iOS steps are unchanged. `git diff --check e38ec3c..946446f` passes.
Denied posting/capture permission remains an exact external blocker;
prerequisite blockage and execution/finalization failures retain distinct
receipts. No result sets `native_input_verified` true.

The greatest remaining gap is actual ARM Mac evidence. Review the next run's
exact source/export identity, individual permission API booleans, exact-PID
window observations, original internal PNG and logs, profile-entry/cache effects
and owned-group cleanup before accepting its preflight result. A ready result
can justify designing a separate reviewed input attempt; it cannot establish
native input acceptance.
