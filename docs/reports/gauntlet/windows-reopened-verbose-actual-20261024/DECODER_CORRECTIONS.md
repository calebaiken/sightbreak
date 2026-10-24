# Decoder preparation and corrections

The first report-helper draft was reviewed before any future offline raw or
partial logs were read. The read-only helper critic identified potential crashes
on missing command/log evidence; overconfident type classification despite
acquisition/count/UTF8/ID/flow gaps; unmatched leak-line handling; and missing
literal type/owned-path/observer-argument-position checks. These findings concern
the offline decoder, not a native product counterexample or a changed runtime gate.

The corrected helper preserves missing/malformed evidence, extracts all raw leak
and ResourceCache lines with their original anchors, validates decimal uint64 IDs,
and checks the preregistered command/source/type fields. It emits no automatic
actual admission or product verdict. Complete source/package provenance and
HUD/action/progression/cleanup context remain manual review items. Six pure
known-format/missing-evidence controls pass; original stdout/stderr are retained.
No engine/native controller is imported or run. No future raw was used to tune it.

A broad read-only search through old report JSON matched very long lines and its
tool response was truncated. That response is not used as complete raw evidence.
A filename search and bounded structured JSON read identified the original
supported-download record. No original file was changed or replaced.

An initial chronology helper incorrectly required original reviewer commit IDs
to be ancestors of root release and asserted before writing a result. Root had
retained the report snapshots with different commits. Corrected proof compares
six exact admission files against the release snapshot and records the original
preregistration09:50:00, admission09:52:44 and release09:55:23 UTC commit times.
The source/runtime and earlier admission were unchanged. Root subsequently
supplied exact original commit/push output files; these are copied byte-exactly
and hashed. Push stdout has no embedded UTC. Its prior execution sequence is
root-reported and compared with immutable commit times and the dispatch clock;
filesystem timestamps provide no chronology proof.
