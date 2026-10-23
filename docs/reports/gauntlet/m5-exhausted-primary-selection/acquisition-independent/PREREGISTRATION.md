# Independent acquisition source review

Review target: `c7145cd48eb6d91246b526e5dc1fb5aaa655246d` on
`codex/m5-exhausted-primary-selection-20261023`. This review owns
`codex/m5-acquisition-source-critic-20261023` in
`/workspace/reviews/m5-acquisition-source-critic`. The accepted game candidate
is `1b7ebc71290e6c4c23017f7a2d8539d7c5eec149`; the earlier candidate critic is
`66f31a6778930fb16de41594ec0bd11b7a70189a`. Neither is re-approved here.

I read the recovery AGENTS.md, existing mission/ownership/gate documents and
the original Gauntlet and No AI Slop skills plus eval. This is source review
with pure or mocked Python checks only. No Godot, import, GDScript compile,
native signal, child test process, OCR, services, CI or nested agents.

The concrete bar is the frozen wrapper's own preregistration and unchanged
accepted candidate source/manifest. Blind A/B is inapplicable to deterministic
acquisition rules. I will retain exact source identities and raw test streams.

Before any test execution I declare these checks:

1. Verify target/freeze hashes, accepted game/scripts tree equality and accepted
   manifest binding. Inspect actual argv, caps and ordering rather than inferring
   behavior from documentation. Candidate must have four native stages within
   240 seconds; regressions must have ten within a separate 480 seconds. Both
   blocks must consume exclusive per-HEAD/block claims, preserve failed output
   and stop all later native stages after any failure.
2. Run the retained builder pure tests unchanged. Independently exercise clean
   candidate and regression control paths while replacing only external/native
   operations, and verify exact argument vectors, state variables and audit
   ordering. The candidate authority audit must precede its after producer.
3. Challenge source and private-copy equality, allowed UID addition, original
   mutation/removal, native userdata identity/leftovers, complete stdout/stderr
   warning scans, and incomplete/duplicate/failing suite completion markers.
4. Challenge phase and whole deadlines, especially success at a boundary,
   cleanup/final receipt timing and preservation of the first failure. Inspect
   process registration, blocked-signal boundaries, stable identity checks,
   cleanup fallback and the documented escaped-descendant limit. All process
   behavior is mocked; no actual signal or cleanup guarantee follows.
5. Report explicit ACCEPT or REJECT for the wrapper source only, the strongest
   remaining deficiency, exact supported scope and unobserved native facts.
   Any false acceptance or broken mandatory acquisition guarantee blocks release
   under this source review. Keep the failing counterexample rather than fix
   the builder's files. Root owns runtime release and canonical mission updates.

The review can accept only source and pure/mock behavior. It cannot establish
native startup, parser readiness, runtime UID behavior, real private userdata,
actual cleanup, audio ownership, selection quality or a release gate.
