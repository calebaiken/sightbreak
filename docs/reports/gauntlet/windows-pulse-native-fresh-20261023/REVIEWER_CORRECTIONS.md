# Reviewer corrections retained

Audit R1 remains unchanged. Its source-byte model copied the prior eleven Windows CRLF paths and missed the newly tracked strict-log fixture `.gitattributes` and `provenance.json`. An independent exact-source Git checkout-filter reconstruction with `core.autocrlf=true` identifies thirteen changed paths and exactly matches the native validation hash. R2 adds only those two explicit paths; no native source or output changed. All 327 game resources already matched in R1.

The first raw input auditor expected `authority.json` for every reached schedule. The failed ordinary schedule has no success-only authority summary. R1 retains that FileNotFoundError and its incomplete aggregate input result. R2 records that missing summary and failed fire/reload predicates explicitly, reconstructs the retained zero-shot telemetry, and continues independently through both remaining schedules. The ordinary failure stays failed.

A one-off summary reader attempted `.items()` on the gunplay audit's integer `checks` count and stopped. The corrected reader distinguishes dictionaries from integer counts. This did not modify evidence or any auditor result.

No candidate source, native output, original archive, threshold, deadline or failure predicate changed.

The first staged whitespace check reports the original decoded Windows job log's CRLF line endings as trailing whitespace and exits 2; the tool truncates that large diagnostic. The complete original log remains unchanged. Its report-local attributes now preserve it as an immutable binary diff, while authored review code and prose keep normal whitespace checks. No native byte was normalized or discarded.
