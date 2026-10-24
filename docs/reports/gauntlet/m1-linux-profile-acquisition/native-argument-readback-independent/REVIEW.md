# Independent effective-thread source verdict

REJECTED for full source acceptance at exact candidate
`93f32edf563c74e250a95505630d4b7870722c78`, implementation
`525b17f17fa8e1d500320198107553b42c9464ea`. The public-API correction is supported
by independently retrieved pinned Godot source. A new independent control finds
that both hashed fingerprint snapshots can substitute numeric `1` or `1.0` for
either thread boolean while the outer settings retain `true`; all four cases
pass `validate_condition`. This violates the preregistered rejection of wrong-type
and inconsistent thread readbacks.

Winner: neither source meets the complete registered bar. The candidate improves
the broken filtered-argument guard, but its new fingerprint observations need
strict boolean validation. The largest source gap is this numeric substitution;
the largest execution gap remains strict software-driver qualification followed
by actual evidence of the new effective-thread readings. No score, native
acceptance, H1 result or release follows.

The reviewer committed criteria `b928d9b0` before candidate code, handoff or test
output inspection and pushed that checkpoint. Work is isolated in
`/workspace/reviews/linux-effective-thread-fresh-source`, branch
`codex/critic-linux-effective-thread-source-20261023`. This is an asymmetric source
comparison against actual R3 failure and pinned implementation semantics; blind
labels would hide the evidence needed to judge it.

## Reproducible rejection

The independent method
`test_fingerprint_thread_observations_reject_numeric_substitution` starts from a
valid synthetic condition. It changes one new field inside both serialized
fingerprint settings, recomputes both SHA-256 values, and leaves outer
`fixture.settings` as strict boolean `true`. The otherwise identical rebuilt
boolean-true control passes. Each numeric variant should reject and instead
passes because Python dictionary equality treats `1 == True` and `1.0 == True`.

The vulnerable comparison is `content['settings'] == report['settings']` in
`scripts/linux_profile_overhead.py`. The new outer `is True` checks cover only
`report['settings']`. Identical forged initial/terminal fingerprints also pass
the later snapshot-equality check. This is a pure evidence-validation falsifier;
it does not claim an observed engine emits numeric booleans.

[The independent controls](test_independent_controls.py), the initial
[four-case probe](fingerprint-type-probe.stdout), and final
[owned](own-independent-final.stderr) /
[depth-one](depth-one-independent-final.stderr) results retain the exact failure.
Each final invocation runs ten methods: nine pass and one method records four
failed subcase assertions, exit 1. A narrow correction can require `is True` for
both fields inside each decoded fingerprint before accepting its settings.
The builder must retain these original failures and seek fresh independent review.

## Independently verified pinned semantics

[Independent retrieval identities](independent-upstream-identities.json) bind
14 full source files to exact upstream
`ed1daf0bf001b61586d9930840f2f1394092c079`. All twelve builder full-file identities
and all 23 builder excerpts match the independently fetched bytes. Additional
`core/os/thread.h` and `.cpp` close the main-ID semantics. Relevant independently
selected [excerpts](independent-upstream-excerpts.json) retain the chain:

- `main.cpp` consumes `--render-thread safe` into `separate_thread_render=0`
  without adding it to the stored main arguments. With deprecated options
  enabled, `unsafe` maps to the same state. `OS.get_cmdline_args()` cannot establish the exact
  full launch intent.
- Startup stores that state in OS, constructs `RenderingServerDefault` with it,
  and completes renderer initialization before game callbacks. Synchronous init
  sets `server_thread=Thread::MAIN_ID`; separate initialization assigns the
  worker caller ID before its synchronized initialization returns.
- Public OS methods return caller/main IDs; `get_main_id()` returns `MAIN_ID`.
  Public, boolean `RenderingServer.is_on_render_thread()` compares caller and
  server IDs. Requiring both main-caller identity and render-caller identity
  identifies synchronous execution at that observation. Render identity alone
  would also be true inside a separate render worker.

The fixture checks both identities before workload construction and records
fresh booleans in the existing settings/fingerprint observations. The controller's
unchanged exact engine, taskset-launch and live full-argv checks independently
require the explicit pre-separator `--render-thread safe` token. Missing,
duplicated, reordered, post-separator, `unsafe` and `separate` variants reject.
Filtered arguments remain a typed observation, without authority over launch
intent. No Godot compile or actual runtime call was made in this review.

## Source, pins and original preservation

[The independent auditor](verify_source_and_originals.py) passes
[11,389 predicates](independent-source-and-originals.json). Across the complete
non-document path/mode/blob union, 493 baseline paths become 494: exactly five
existing paths change and one pure test is added. All 488 other existing paths
match Git metadata and physical bytes. All 8,649 earlier document/report/pin
paths remain identical. Game, backend, server, workflows, installed skill and
art-tool subtrees are unchanged.

The complete supervisor function/class ASTs are unchanged; only its r3-to-r4
output constant and two accepted source hashes change. The controller changes
only `validate_condition` among function/class ASTs and replaces the fabricated
thread-argument setting with the two effective-state fields. The fixture changes
only the guard, settings observations and retained filtered arguments. Hash pins
match actual fixture/controller/scene bytes. Existing strict warning checks,
source/cache/payload seals, selectors, full graphics, CPUs0,1, LP2, display99127,
OFF/ON/ON/OFF, 32 warm plus 64 measured samples, 180-second conditions, phase
caps, 1,320-second whole cap, cleanup/publication bounds and every cadence/drift
formula remain unchanged. Candidate and builder r4 output paths remain absent.

All 370 original R3 files, 276,747,038 bytes, and all three external wrapper/outer
records rehash against actual critic
`c9c5c64d96d2010e0905953423b01b83e04384c1`. Its registry's file identities exactly
match the builder's earlier registry. The full original file set, exact ec6b
HEAD and clean tracked source are preserved at the finite audit observation.
This does not restore overwritten historical cache bytes or missed live process
details. R1 strict-import failure, R2 terminal-NUL failure, R3 startup failure,
and the original Linux gameplay failure retain their FAILED status.

## Pure checks and unverified runtime boundary

Both owned and freshly initialized exact depth-one checkouts pass all 38
acquisition, 22 fixture/controller and nine builder readback methods, no skips.
The final independent method then fails identically in both checkouts as described
above. [Depth-one identity](depth-one-identity.json) records exactly one reachable
commit, shallow=true, no baseline object, no alternate store and no tracked diff.
The sole copied extra file is the independent report-local control script.
The builder's history-free source auditor also passes in both checkouts.
All executed review/test work uses CPU4. [Setup failures](AUDITOR-SETUP-NOTE.md)
and their fresh outcomes remain separate.

The exact original VSync warning independently remains a strict acquisition
blocker. The standalone error/leak matcher ignores warnings; the unchanged real
outer `Acquisition.run_block()` strict gate rejects the exact warning in otherwise
bound synthetic data. That distinction is exercised rather than assumed.
Pinned GLX code warns and returns before updating `use_vsync` when all three
swap-control extensions are absent; X11 creation invokes this path for either
VSync mode. A disable flag supplies no source-supported correction here.

R3 still failed before first OFF readiness. Its actual filtered arguments,
effective thread state and VSync getter were never retained. Source semantics
explain the old guard mismatch without inventing those observations. No condition,
performance measurement or H1 completed. This review ran no engine/version,
native/import/export/render, CI, display or observer process, creates no new
native recipe, suppresses no warning and grants no retry or release.
