# First failed native leak diagnostic handoff

Candidate implementation: `f3896c60d367466129ba5d2a906234b2dee8174f`, based on
root `a3b7070`. Preregistered criteria/raw-boundary commit: `dcf3885`.
Fresh independent source review accepts one bounded actual ARM diagnostic attempt.
No local engine, OCR, native APIs, events or
CI ran. The backend native CPU lane was reserved throughout this source work.

Native run 39736389634 at 20464da passes the bounded menu gate. Its separate strict
source result remains FAILED: actor reports 73 assertions, zero failures, exit 0
and six ObjectDB leaks; the other 11 suites are unreached. The input-mode-only
diagnostic correctly skipped. No verbose object types exist. The previous b09cfe1
run 39732825169 reaches input_mode after six clean suites, then reports two leaks;
its later five suites are unreached. Both boundaries remain retained separately;
cause and possible nondeterminism are UNKNOWN.

The existing CLI and default input_mode constructor remain compatible. Selection
now permits only actor or input_mode as the first failed, terminal suite, with
earlier receipts clean and known suite identifiers unique. It checks the selected
original maintained argv/current pinned binary, private project, original native
producer paths, namespace, cleanup, source and failed-suite leak log. Evidence
fingerprints include both whitelisted logs, with absent files explicitly null.
Source and original evidence are checked again before constructing a repeat.

Only the selected maintained script receives --verbose. The inherited fresh
private project/user-data namespace, 240 s shared deadline, 6 min workflow bound,
owned process groups, raw logs, hashes and cleanup remain. Unknown/unvalidated
bootstrap state is preserved without invented cleanup. The output directory is
now `builds/desktop-playability/source-leak-verbose`. No product fix, warning
suppression or repair of the original strict failure is included.

Readiness: eight legacy and six new unique pure control methods pass. New controls
check byte-exact actual fixtures (with macOS /var path resolution explicitly
simulated on Linux), both selected suites, foreign/unsupported/absent/unclean
evidence with no launch, earlier failures/duplicates/later results, exact actor
argv, other-suite refusal, and changes during selection. Workflow YAML parses,
IDs are unique, and strict native argv/failure semantics are unchanged. Stored
replay and mocked processes establish source readiness only. Root owns any next
registered ARM dispatch after fresh independent source approval; actual verbose
object types and cause require independent review of new native originals.

The fresh critic passes 17 independent pure methods and the same 14 maintained
methods, including real inherited lifecycles with every process/native producer
mocked, 36 adversarial selection cases, seven malformed receipt shapes, deadline
and mutation no-launch checks, namespace cleanup failure, and bootstrap namespace
preservation. Its report, controls, raw logs, fixture equality audit, exact-source
blob/hash manifests and representative `PURE-MOCKED-*` receipts are retained in
`independent-review/`. Full frozen source snapshots remain external and are bound
by the accepted commit and manifests. This approval is source readiness only;
the original strict failure and the unknown actual leaked types remain intact.
