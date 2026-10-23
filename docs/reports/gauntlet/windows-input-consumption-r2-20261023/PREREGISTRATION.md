# Windows input observation reader correction

Root builder begins this isolated correction on 2026-10-23 after fresh critic
preregistration `2a25c7cb` identified false acceptance in exact source
`c0738163965804297a1881905d5bb4646da40a16`. Base handoff is
`161d72c5f4018e5a8fb24669e1d5054bb6b12edb`; preserve that source and its results.
Independent critic findings are still being sealed. Their original cases must
remain unchanged for rereview. One invalid identical-input critic control is
excluded from product requirements and must remain disclosed in that review.

Benchmark: a direct receive with missing or stale metadata, an accepted packet
whose first sequence exceeds its last, or a connected send whose transport,
actor or local-attempt identity differs from its welcome must be rejected as
incomplete observation evidence. The current reader accepts these cases. This
is an evidence correctness boundary; it does not identify the earlier native
disconnect cause or establish input delivery.

Change only the pure reader and meaningful controls. Preserve all game hooks,
wire/RPC behavior, authority acceptance, privacy, defaults, native schedules,
limits and separate invocation/receive/accept/consume semantics. Require typed
fresh direct metadata and valid sequence intervals. Connect each send to the
current observed welcome; a new attempt or disconnect retires that welcome.
Do not fabricate a successful chain when required observations are absent.

Retain the original false-pass output before correction. Rerun the maintained
pure suite, unchanged independent falsifiers and a properly initialized exact
depth-one checkout. Original failed native logs must remain insufficient.
Source erasure/protected-byte comparisons must show runtime source unchanged.
All commands use CPU 4. No Godot, import/export, graphical/native invocation,
CI dispatch, combined integration or actual release is authorized here.

A separate critic decides source readiness. Builder tests cannot approve this
candidate. Any additional supported findings require explicit documentation and
retests. Largest remaining product gap is still actual Windows input consumption
through reconnect, followed by the living route/settings/focus journey.

Before implementation, the sealed rejection packet `bed06bc9` adds supported
cases for an unbound receive, a send outside its pending interval, and first
consumption before any receive/accept observation. The final unchanged r3 rig
contains 25 cases: 16 expectations met and nine false passes at the original.
Four malformed-receive/sparse relationship cases are explicitly permitted;
receive precedes packet validation, and coalescing prevents full batch pairing.
Do not impose matching sequence/epoch relationships across coalesced batches.

Root's initial no-checkout setup left selected tracked files absent despite an
initialized index. The printed deleted-file status is a setup failure, not a
source change. An exact `git restore --source=HEAD --worktree -- .` materialized
the selected tracked bytes and returned a clean status before implementation.

After the first source freeze `e0acf040`, the critic supplied one further actual
false pass: an authority expiry stage injected into client-role evidence. Before
the next edit, extend the correction to enforce each role's emitted stage set
for direct reasons, counters and retained latest metadata. Duplicate JSON/index/
consumed-sequence controls already reject and must remain so. Retain the first
source freeze and its original results; native code remains unchanged.
