# Combined Windows e28c8e9 source gate

Critic-owned review, 2026-10-23. Exact freeze
`e28c8e90b9ef2d0c766bd9152c194e3197ceba9a`, previous combined source
`c838907cf4978e53c57423e08c23277c34f4496d`, accepted cover route
`af13a9979988d8b19de670fe27b78672ad2369ed` based on `a089473`.
The previous combined Mac/Linux source review is `2a3bcdf`; cover review is
`5820ca7`. Their original source scopes and actual failures remain intact.

Before tests, declare binary source readiness: accept only if the entire tracked
scripts/workflow/game inventory and modes are exactly c838907 plus the four
accepted af13a99 script paths, with the validate.sh registration explicitly
bound. Game tree must stay `55691684d31d44f1680141954bbe530443de9d1f` and shipping
content SHA-256 `bcb872f6998ed8504c852dee354ab0acf5b6f19e58e40717267a1927e6d68a50`.
Workflows and all unrelated Mac/Linux/source helpers must remain byte-identical.
Retain previous independent review/evidence trees and original failures.

Create a separate sparse depth-one checkout at exact freeze, with only one
reachable commit and original historical objects absent. Check tracked byte/mode
bindings, clean status, read-only build source identity, all relevant pure
Windows route/approach/focus/capture/reader/OCR and packaging controls, plus
relevant unchanged Mac/Linux shallow-readiness controls. Bind workflow lane,
ordered full Windows stages, timeouts, guards and raw artifact retention to the
accepted workflow. Retain all command exits/raw outputs/counts/skips/failures.
No engine, import, UID, native input, OCR executable, export, CI, service or nested
agent may run. This gates one existing full Windows workflow only after root's
separate release and fresh actual critic; it performs no dispatch, grants no
runtime acceptance and approves no retry.
