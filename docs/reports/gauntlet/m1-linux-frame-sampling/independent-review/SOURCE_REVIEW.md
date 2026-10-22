# Independent source verdict

Accepted for the bounded diagnostic attempt, at exact builder source
`8afe0cc6b4c9051d3649a82bbcb4c8de8f947f9c`, base
`9616f52723666e651ca8ae839420cf2b308e5c5a`. This accepts source and pure controls;
native parsing, monitor output, overhead, the plant result and actual cleanup
remain unverified. Root must separately release the native lane.

The frozen source changes only the existing offline snapshot, the controller's
explicit Linux plant opt-in, one new sampler and its tests. Removing the 22-line
readback block reproduces the original GDScript bytes. Removing the new opt-in
statements reproduces the complete original controller AST, including all input,
capture, role, next-buy and whole-flow deadlines. There are no engine callback,
write-cadence, scheduling, quality, physics/FPS/time, authority or admission edits.
[source-audit.json](source-audit.json) retains twelve passing predicates and the
four source-file hashes; [source_audit.py](source_audit.py) reproduces them.

The sampler binds the already-owned Popen PID and kernel start counter, checks
both before and after collection, and discards uncertain rows. It neither
discovers nor signals processes. Reads, thread count and lifetime are bounded;
the one-second wait follows each collected sample, so delayed reads cannot cause
catch-up bursts. Missing counters carry availability/reasons. Cgroup paths stay
within the selected v2 root, with ancestor scope labeled as potentially shared.
Only the three graphics environment keys, categorized thread roles and the
typed offline phase/clock/frame whitelist are serialized. Actor, profile and
account payloads are excluded. `sampling_completed` describes the worker;
individual availability and the original product `passed` remain separate.

I requested the initially missing Time.get_ticks_usec documentation before the
freeze. The candidate includes it. Independent public fetches match all eight
retained document/source hashes and all 23 excerpts, both at the 4.7.2-stable tag
and pinned `ed1daf0bf` engine commit. See [api-verification.json](api-verification.json)
and [verify_api.py](verify_api.py). The engine source confirms that timing
monitors publish maxima at roughly one-second refreshes. Process time includes
renderer synchronization/draw; physics timing is one largest step. The viewport
texture size is output size, with internal 3D target size explicitly unavailable.

Independent execution passes 18 builder sampler/option controls, eight additional
adversarial controls, four existing role controls and 15 capture-fence controls.
All use synthetic files and inert process objects; the affinity getter is mocked.
The extra controls replace identity during environment and thread reads, discard
uncertain rows, retain unavailable/partial counters without zero-filling, exclude
private markers, reject nonfinite observations, enforce exact byte bounds,
retain sample-write errors and verify real one-second cadence plus prompt stop.
The first independent run had seven passes and one review-fixture KeyError: I
indexed the environment wrapper without its `value` layer. The corrected fixture
passes all eight; its original failed output is retained and is not a product
failure. The controls also adopt the frozen `sampling_completed` field name.

```sh
python3 scripts/test_linux_frame_sampler.py -v
python3 docs/reports/gauntlet/m1-linux-frame-sampling/independent-review/controls.py
python3 scripts/test_offline_role_guidance.py -v
python3 scripts/test_offline_capture_fences.py -v
python3 docs/reports/gauntlet/m1-linux-frame-sampling/independent-review/verify_api.py
python3 docs/reports/gauntlet/m1-linux-frame-sampling/independent-review/source_audit.py
git diff --check
```

No engine, native client, OCR, service, export or CI was run by this critic.
Pure controls prove error handling for the modeled cases, not native proc access
or every possible blocking filesystem read. The two-second join reports a
surviving worker as a cleanup failure; actual termination must be audited.

The largest remaining gap is the same-attempt native timing/scheduling receipt
under the failing workload. Run one source-bound Linux plant with seed 42,
1280x720 Standard/full scale, llvmpipe/two workers and original 180/15/12-second
budgets. Preserve any failed next-buy result and the original failed attempts.
An actual limit of eight plus near-eight tick/process deltas and process/draw
agreement would support catch-up saturation across the measured interval, not
prove each frame saturated or identify the expensive function. CPU totals and
coarse engine maxima cannot establish a complete frame breakdown. Windows
976x549 ANGLE software remains an unmatched diagnostic reference. Physical-device
performance and the broader release gate remain open.
