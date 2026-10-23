# Independent source review preregistration

Registered 2026-10-23 before detailed candidate code or output inspection.
Candidate: `c91d9b98a293ef8605d99ae6e83402d3af983519`.
Builder preregistration identity supplied by coordinator: `09a3ea84`.
Own branch: `codex/m5-objective-observability-independent-source-20261023`.
Own worktree: `/workspace/reviews/m5-objective-observability-independent-source`.
Scope: this exact report directory only. No canonical changes, nested agents,
Godot, native execution, import, export, CI or dispatch. Pure/source commands use CPU 4.

The source regression bar is the pre-instrumentation bot/authority logic at the
candidate parent, independently recovered and compared byte for byte after
removing only the added observer hooks. Historical archive 179 at original
`0527715` is a factual observation bar, not a replay or gameplay-quality bar:
100-second timeout, live carrier 6 near (-0.0768233, 0.0009438, -17.3271542),
100 HP and SMG 30/0, with no planning, LOS or target decisions. Other b2/e28
matches contain bot plants. Any claim that bots never plant is rejected.

Acceptance requires independent inspection and meaningful controls for all of:

1. Default trace collection is disabled; debug/offline opt-in is explicit;
   release and online paths deny private trace collection even if requested.
   No serialization, RPC, UI or public-state exposure is introduced.
2. Hooks add no RNG calls, extra target/path selection, ray/physics queries,
   protected-state mutations, command changes or authoritative outcome changes.
   Source erasure must recover the original policy exactly.
3. Trace dictionaries are caller-owned and detached, values have stable types,
   stale keys cannot survive calls, disabled/early-return and repeated invocations
   have explicit behavior, and nested aliases cannot mutate authority state.
4. Authority observations preserve stock 3-second plant and 5-second defuse,
   deny invalid interactions, describe early-return paths truthfully and capture
   before/after objective state with source/scene identity.
5. Historical reconstruction binds exact input/source/scene identities and
   states missing observations; geometric inference cannot become bot intent,
   live replay, root cause, policy quality or outcome-fix evidence.
6. Maintained pure tests pass in an initialized no-remote depth-one fixture.
   Independent boundary/mutation controls must fail under plausible unsafe or
   incomplete implementations. Preserve all failed tests and setup mistakes.
7. Evidence retains exact commands, exit statuses, source identities, limits
   and largest unresolved deficiency. No builder selfapproval, quality scores
   or whole G1/G2/G17 acceptance.

Largest uncertainty is fixed in advance: source controls and grammar parsing
cannot establish pinned Godot 4.7.2 compilation, real debug/release isolation,
trace correctness in an engine-driven match, performance overhead or tactical
quality. Those remain unverified without separately authorized native evidence.

No AI Slop is applied to report prose. A blind aesthetic comparison is
inapplicable to instrumentation source correctness.
