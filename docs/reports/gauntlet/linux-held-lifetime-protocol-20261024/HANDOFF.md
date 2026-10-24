# Read-only lifetime protocol proposal

PROTOCOL.md is concrete enough for a DIFFERENT pre-edit adjudicator. It recommends
retained lifetime records plus descriptor-bound reaping, with conservative
INCOMPLETE for ready/ECHILD/externally reaped/unknown-adoption cases. A known adopted
zombie remains tracked outside live() and can be reaped by fd. Root Popen wait
ownership is exclusive. Exact proposed scope is two new LinuxKernel methods,
`pidfd_alive(self,fd)` and `reap_pidfd(self,fd)`, and exact unaliased `import select`
plus `import errno`; all ten old kernel methods/protection JSON stay byte-exact.
The proposed reconstruction erases only those additions before existing approved
OwnedTree/FakeKernel class restoration. No broader source edit is requested.

Old source8cc remains REJECT85c; this is not code, implemented evidence or an
approval. The largest open decision is whether conservative failure for an
unprovable external reap/not-yet-adopted lifetime is an acceptable completeness
cost. Exact Python waitid mapping and future interface availability remain
prerequisites, not assumed host facts. Strict observed-success deadlines remain
60s whole/5s cleanup; no preemption/hard wall guarantee or new timeout extension.

SOURCE_IDENTITIES.json pins17 complete original source/report files by commit,
Git blob, byte count and SHA-256, without copying large reports/receipts/kernel
sources. PURE_MODEL_PLAN.md defines finite object/event bounds and necessary
counterfactuals before later implementation/execution. Root's R5 remains frozen;
root owns separate R6. This task changes only this docs directory. No tests or
actual proc/poll/wait/pidfd/API/native/capability/helper/engine/CI ran; no new agent
or duplicate reviewer was spawned. Git-only source reads were used.

The own no-checkout/read-tree sparse initialization emitted inherited non-cone
pattern warnings; it still initialized this docs view. Two insufficient short
commit prefixes and one guessed protection filename failed read-only Git lookup;
all cited identities were subsequently resolved to exact existing commits/paths.
No source file, original report or protection hash was altered or deleted.
