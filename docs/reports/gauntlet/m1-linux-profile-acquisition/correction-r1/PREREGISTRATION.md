# Correction R1 preregistration

This is source and pure-Python work only. The rejected acquisition freeze is
`04bc153e52341228b2f0d6f4ce72f784528ef1d4`; independent REJECT and falsifiers are
retained byte-exact from critic commit
`ff4cc71b1a81c073a92acea1b56007e4508282e7` in `retained-rejection/`.
The earlier reports, controls, failed observations and source freeze remain
historical evidence. They are not passing controls for this correction.

Two hypotheses will be tested before a new exact-source review:

1. An append-only in-memory evidence registry, populated at the original
   successful gates, can reject retained-byte drift before finalization and
   throughout final publication. Rebinding a path must compare with its first
   accepted identity, never replace that identity. Command logs, phase receipts,
   stage publications, independent payload/seal and raw block/condition/log/
   metrics/proof evidence will be bound. Final rereads must compare these original
   identities and strict logs, and the output manifest must describe those same
   validated bytes. Publication/read/stdout/alarm-restoration mutation controls
   must fail within the existing final and whole deadlines. Unchanged valid
   evidence and existing just-before-deadline positives must pass.
2. Packed critical project settings must be qualified by exact staged source,
   including dotted feature selectors. The pinned engine registers selectors
   after the first dot (`project_settings.cpp:324–338`) and resolves active OS
   overrides (`415–433`). Unexpected selectors of any critical base will reject;
   declared critical variants must match the frozen staged value and registered
   expected critical value. The existing `.mobile` renderer remains supported.
   Fresh valid-MD5 packs with the critic's three `.linux` overrides must reject,
   together with compound/other-feature variants. The legitimate source settings
   and permitted default omissions must pass. This is a deliberately narrow
   source-aware policy, not a complete simulation of Godot feature resolution.

The unchanged independent controls will be replayed against the rejected source
and the correction. Additional maintained synthetic controls will exercise late
publication drift, positive boundaries and original-identity rebinding. No engine
or native process may be used: Popen is fake or forbidden. The accepted fixture,
controller, game, original Linux failures/flags/settings, OFF/ON/ON/OFF order,
180-second condition deadlines, phase caps and 1320-second whole cap stay frozen.
No shipping improvement, complete profiler overhead or gameplay-cost claim is
permitted. No engine/import/compile/UID/export/Xvfb/native/OCR/CI/services run is
released. A fresh critic must bind the exact combined source before root can
consider one runtime acquisition.
