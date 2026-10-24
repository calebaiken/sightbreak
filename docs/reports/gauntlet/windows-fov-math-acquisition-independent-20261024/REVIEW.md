# Independent b16 source/plan verdict: REJECT

Exact source `b16b012d720c0981cfc28146a651b3ba5f8a9caa`; sealed builder/runtime
handoff `25603855ad7029b10c6c4109a4d47b949d72c1d2`; protected base
`64afaa4132c1f1e1c1376f5269b46ff9918aa9a6`. The runtime docs commit preserves all
526 non-doc source identities from b16; code and runtime pins are distinguished,
without inferring ancestry. This reviewer did not implement this component. Root
explicitly reused the existing thread; no fresh/blind-context claim is made.
The separate receipt candidate has a DIFFERENT critic and is not approved here.

Two supported source failure groups reproduce in both runtime and initialized
one-commit-depth views: finalizer exceptions skip later owned closure and erase
the structured return, and supervision failure discards audit observations already
obtained. This rejects the source preparation under its unconditional ownership/
retained-evidence bar. Public collect correctly remains BLOCKED and none of these
models constitutes native acquisition, an actual Windows failure or SDK/API proof.

Initial prerege9b4f00e preceded inspection/tests; concrete4c95 controls preceded
execution. R1/R2 scripts/raw are retained;5e957 and4d219 additive registrations
correct model fidelity/overflow provenance and add healthy close pairs before
final replay. No candidate/source/test/route repair was made or inspected. Only
own review reports are changed. Existing helper thread supplied read-only source
contract support, with no execution or independent verdict; no new critic was made.

## Failure group 1: finalization can prevent later cleanup and its receipt

In `windows_fov_math.py:514–523`, streams.state() and streams.close() are outside
any guard. A stream finalizer error escapes execute_prepared's finally block,
skipping job.close_held(), finished/elapsed and the structured return. An earlier
failed status does not preserve a receipt once the function itself raises.

The source-derived model uses separate controller/root/job/stream objects, two
sink objects, two pipe objects and an unexpected-child held handle. A first sink
close error after the unexpected-child failure/owned cleanup yields:

- OSError escapes; no returned result/final timing exists.
- stdout sink close attempted1; stderr sink and both pipes attempted0.
- job.close_held called0; distinct unexpected handle502 attempted0 and remains open.
- The modeled root has already been waited. Its exit does not close those other
  resources or rescue the missing failure record.

The normal completion pair returns a coherent result and closes its resources.
A single final-state allocation interruption also escapes/skips closure; a body
flush error is correctly returned as failed with closure attempted. Late-close,
noEOF and literal-cap-overflow controls correctly fail overall. These distinguish
finalizer interruption from a generic failed acquisition status.

Two direct actual-source checks demonstrate the inner finalizer problem as well:
PipeRetention.close305–308 stops on the first sink exception, attempting none of
three remaining independent resources; WindowsJob.close_held265–267 stops on the
first fake CloseHandle failure, attempting501 but never502. Healthy direct pairs
close all resources. The outer job handle is intentionally retained until OS
teardown; this finding does not ask it to be closed and kill the controller.

Reproduce `close_error`, `unexpected_close_error`, `state_error` and both direct
first-error rows in own-controls/all-results.jsonl.gz and depth-controls/. Source
functions execute over owned temporary files/in-memory symbolic handle objects.
Fake Kernel calls are not Windows API calls. Harness force-close occurs only
AFTER recording candidate attempts/results and is never credited to the candidate.

## Failure group 2: pre-failure audit is discarded

supervise334–349 creates a local Audit and exports its receipt only on success.
At execute_prepared479, result.update(supervise(...)) never updates on exception.
The catch stores error text and later cleanup collects a DIFFERENT history.

The harness observes construction of the actual source Audit class, without
replacing observe()/receipt(). Coherent source-interface records establish that:

- A later pipe error loses the earlier sample/transition (total2, IDs100/200,
  page_faults101), even though that exact Audit object retains it.
- A later query failure loses2 samples and its last observation, again while
  cleanup/reaping and structured failed return otherwise complete.
- An observed extra child300 is held by a distinct birth/HANDLE before rejecting
  total3/IDs100,200,300. That offending Audit observation is absent from the failed
  returned result, which contains only subsequent cleanup observations.

The normal pair does include its Audit receipt. Every source sample is a fresh
snapshot, so cleanup cannot mutate an earlier object into apparent history and
shared test-object identity cannot accidentally satisfy the assertion. Cleanup
state is not a reconstruction of the previously observed transition. Source
interfaces are modeled with coherent projected counters/lifetimes and symbolic
opaque identities; no literal Win32 value/clock feasibility or native capability
is inferred. The code loses the audit for any full source record extending those
source-relevant fields, independent of omitted unobserved native details.

Reproduce `pipe_error`, `query_error`, `unexpected`; full returned results and
captured source Audit receipts are retained losslessly. Those acquisitions remain
failed; the defect is loss of existing diagnostic/ownership evidence, not an
observed native math acceptance.

## Final-total lead: excluded from source verdict

cleanup_unreturned408 sets identity_coverage_complete from an earlier loop sample.
Its final417–418 check uses live IDs/active count without recomputing that field.
A1→final2 API-observation model leaves coverageTrue; unchanged1→1 and prior2→2
controls behave as expected. However, a permissible single-controller creation/
exit history after the first coherent controller-only total1 was NOT established.
Root agreed this must stay MODEL ONLY. It does not count toward REJECT, native
behavior, or a feasible source counterexample. Cleanup live absence and complete
historical identity coverage are distinct, as the retained hidden-child test shows.

## Actual checks and protection

Both views have the same final15 source controls:7 match,8 fail in the two groups
above. The3 final-total observation controls are separate/model-only. Full inputs,
results, resource attempts and source Audit receipts are in compressed JSONL,
with deterministic raw-input specs/hashes; no unique native output is omitted.
Original R1/R2 control sources and outputs remain separately retained. Final
models call actual PipeRetention attach/poll/state/close with injected read/
nonblocking functions; overflow literally exceeds8MiB rather than inventing a
flag below its source limit. Unexpected creation occurs after modeled Popen.

Selected80 maintained pure methods pass in each view,0failures/errors/skips, CPU4.
Exact method lists and omissions are in own-selected/RESULTS.json and depth-selected/.
We omit the one synthetic sdk_member extraction method and4 ProcInterfaceControls
under the strict noSDK/proc scope. This is NOT a full85 replay. The builder's
full85 results, original failures, and explicitly reconstructed R1 source remain
byte-exact in builder-evidence-exact/ with their original labels.

All47 actual builder evidence members match inventory byte counts/SHA256 and
sealed Git bytes. All526 physical non-doc paths/modes match b16 and runtime256;
all523 base paths plus every other original path identity are protected. Exactly
Windows controller/test/workflow are added. Game, Linux wrapper, old workflows,
588 canonical/schema2 inputs, kernel/parser and all original tests remain exact.
BINDINGS.json / BINDINGS-depth.json provide full direct physical proof. The depth
view is detached runtime256, shallow=true/count1 with disclosed shared objects;
its complete non-doc source equals b16. No full clone/object-isolation claim.

The actual detached runtime/component-manifest public collect path authenticates
its8 materialized components and reaches artifact feasibility BLOCKED. Assertions
show0 SDK extraction, WindowsJob, Popen and execute_prepared calls. Its generated
preflight failure and manifest copy are complete; no native originals exist.
Runtime manifest hash is9eede33699b5851ea8ed8c9a0e451d10e6d667993408d8b884dccba5f67b1d71.
No SDK/archive/executable was downloaded, opened as a process or extracted here;
no actual Windows API/proc/pidfd/helper/native/CI/route/reader replay occurred.

## Comparison and remaining gap

The finite prefix model and pinned uploader-client STORE calculation are scoped
preparation results. Arbitrary full Godot failure-user-log size and service/
connector rewrapping remain unproved. Detecting an oversized original is not a
proof it can fit the unchanged two32MiB deliverables. Public BLOCKED is correct
and must survive any source repair.

No candidate wins this source bar yet. b16 preserves the immutable route and
passes the selected old controls, but loses against the registered finalization/
audit obligations on concrete models. The largest source gap is an exception-safe
lifecycle that retains the audit and attempts every later owned close before a
failed structured result. The largest admission gap remains complete-original
retention plus unmeasured Windows/SDK/runtime behavior. Preserve b16/256 and all
raw. Any separately frozen repair needs its own preregistration/review; no target
substitution, source/native/acquisition approval or duplicate critic follows.
