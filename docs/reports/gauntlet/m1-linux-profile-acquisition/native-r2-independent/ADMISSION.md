# Conditional source admission

ACCEPT the preregistered review subject and preparation for one eventual actual
attempt at exact `216d39ada8f9d11e2d8544d01fde42da49607b14`. This is source
admission only. ROOT ONE release is unobserved and the native lane remains held.
No actual R2 output was read and no engine/native process was started.

Preregistration `2082e964` was committed and pushed before these admission checks.
Fresh source acceptance remains the separate `f8659bba3a6d3e1405230fdf85c2e300a037c218`.
The read-only [source check](check_source_admission.py), run on CPU 4, completes
in 0.489 seconds with [1,798 passing predicates](source-admission.json) and
empty [stderr](source-admission.stderr). It verifies:

- Exact clean candidate and original failed-source HEADs.
- All 430 candidate and 430 original tracked game/script files against frozen
  Git blobs; all original source identities also match the retained 430-file ledger.
- All 20 correction source-manifest artifacts against both their recorded
  SHA-256/lengths and the exact candidate Git bytes.
- The entire narrow fixture/supervisor delta and unchanged shipping game tree.
- Absent fresh R2 output/claim/symlink and absent fresh R2 external outer records.
- Twenty-five original top-level raw/outer files against the original actual
  critic's registry, without changing any retained byte.

This light observation does not reopen the full 224-file original cache/template
tree or its archive. The original actual critic already preserves that complete
audit; this critic's independent complete rehash waits for root's CPU clearance.
It also does not verify installed engine/archive bytes, GDScript compilation,
export representation, native processes, fingerprints, cadence or runtime cleanup.
The prior schema-inspection error is retained in [its note](SOURCE-INSPECTION-NOTE.md)
and is never counted as a passing preservation result.

The [read-only observer](observe_processes.py) is prepared but has not been
activated. Its [pure controls](observer-controls.stdout) pass tricky `/proc/stat`
names, multigeneration descendant expansion and PID/start identity distinction;
[stderr](observer-controls.stderr) is empty. Both saved scripts parse. The
observer launches no child, sends no signal and reads only selected non-secret
environment variables from relevant processes. Its runtime is CPU 4, nominal
100 ms identity polling, 60-second exact-supervisor discovery, 1,440-second total
cap and ten-second terminal observation window. It records socket/listener and
fixed display publication state, actual affinity including threads, PGID/SID,
start ticks and retained descendants. It records observations and gaps; it does
not supply a native verdict or guarantee observation of between-poll escapes.

The largest current uncertainty is actual pinned-engine compilation/import of
the corrected fixture. The original Linux import failure and original gameplay
failures remain FAILED. No score, runtime approval or root release is granted.
