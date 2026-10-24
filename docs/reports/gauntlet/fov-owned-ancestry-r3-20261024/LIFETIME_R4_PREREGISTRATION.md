# Held-lifetime correction, before implementation

2026-10-24. Source base `8cc38cdcd7dfff37056782149e513c08037e4e77`,
handoff `9807106cb79033cd00b69c1411c3808488c372bb`. Independent review
`85cba435886f3963f5db2bf694ada9ae7cbf5d89` rejects two same-start-tick
ancestry schedules and one stale `live()` result. Preserve that review, original
failed outputs and all earlier failures. This is a source/pure-test amendment;
the sole native attempt remains consumed and rejected. No API experiment,
native child, signal, helper, SDK, CI or retry is authorized.

## Required invariant and proposed mechanism

A numeric PID/start-tick pair is only a projection. Every queued descendant and
every reported live entry must remain bound to its retained pidfd lifetime.
Check held exit readiness before and after numeric identity reads, child-list
enumeration and new-child binding. An exited parent cannot establish an edge,
including a replacement with the same numeric PID and exposed birth tick.
Uncertain readiness must reject. Never infer ownership from process group alone.

Propose one narrow `LinuxKernel.pidfd_alive(fd)` method using a nonblocking
`select.poll` readiness check: no readiness means live; POLLIN means exited;
POLLERR/POLLHUP/POLLNVAL, unexpected masks or polling failures reject as unknown.
The exact exit-mask interpretation must be supported by pinned kernel source
before final freeze. `OwnedTree` uses that method at every retained-lifetime
boundary. Existing child PPID and parent checks stay. Genuine owned-orphan
adoption by the unchanged supervisor remains valid. Binding keeps pipe retention
first and never equates pidfd readiness with stream EOF or successful shutdown.

The pure kernel adapter must retain distinct lifetime objects behind descriptors;
an exited held handle never retargets to a reused numeric PID. Add explicit fake
readiness to that adapter rather than calling real poll/pidfd/signal APIs.

## Protection amendment proposed; independent adjudication required

No protection guard changes are authorized by this document alone. Request only
one additive method in `LinuxKernel`, plus the required `select` import. Preserve
all old methods, their order and bytes. A future protection adapter may erase
only the unique AST method `LinuxKernel.pidfd_alive` and exact single import before
the existing `OwnedTree`/`FakeKernel` baseline reconstruction. It must reject
duplicate, missing, decorated, malformed or out-of-class methods, preserve all
outside comments/decorators/helpers, and compare the remainder to the unchanged
original protected hashes. The original protection JSON stays byte-exact.

`OwnedTree` and the fake class remain the already adjudicated editable scopes.
Do not erase all of `LinuxKernel` or replace its old implementation with a donor.
Implement the proposed mechanism only after the existing independent critic
adjudicates this narrow extension. Review may require a different poll contract.

## Registered validation

Replay the exact independent three failing methods without editing assertions;
if a new kernel interface requires a model adapter, register its exact changes
before execution and preserve the original model. Add generated schedules for
parent exit/reuse before and during enumeration, between child identity/open/
recheck, stale live entries, unknown readiness, and root exit. Include same-tick
and changed-tick reuse, stable three-generation trees, genuine supervisor orphan
adoption, normal exit/zombie accounting and failed handle binding. Require zero
foreign adoption and zero successful fake signal to foreign lifetimes.

Rerun the maintained pure suites with real subprocess/pidfd/signal/native-library
operations forbidden inside test bodies. Test the real poll method only through
an explicitly mocked poll factory; no descriptor is opened. Preserve baseline
62-method results, protection failures and every failed iteration. Verify exact
physical source/modes in own and initialized one-commit views. A separate critic
must evaluate the frozen candidate and largest remaining gap.

Even source acceptance would not resolve inherited physical-source binding,
the absent child-list interface, native codec execution, or platform gameplay.
No whole mission gate closes from this component.
