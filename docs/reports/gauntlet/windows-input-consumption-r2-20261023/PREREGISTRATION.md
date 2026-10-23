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
