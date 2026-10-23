# R3 analyzer freeze for fresh review

Policy amendment `e0e0f75` corrects the two baseline incompatibilities retained
from independent R2 rejection `40b640d6`. The analyzer now retains/reports Dummy
as the actual default headless driver, with explicit ownership/strict-exit-only
scope and no audible/physical qualification. No argv or driver is changed.

It accepts exactly one complete pinned banner line, at the start or after one
source-format WorkerThreadPool verbose line. Missing, wrong, partial, quoted,
buried, duplicate and conflicting banner cases are rejected. The accepted
preamble and banner line number are reported. Actual wrapper provenance must
still bind the exact executable, command and observed driver separately.

Pure results: 23 maintained tests pass, seven unchanged R2 critic controls pass
(including both baseline controls and five chronology groups), and the three
unchanged R1 falsifiers pass. Both originally saved R2 compatibility inputs are
accepted with strict failure preserved. `r3-pure/receipts.json` retains those raw
input hashes, outputs and a byte audit: all 422 original game/scripts paths equal
the reviewed `809dbc0` source. Observer/hooks remain untouched. Original R1/R2
rejections and incompatible old policy are preserved as history.

No engine/import/UID/GDScript compile/native/CI/OCR/service ran. The actual leak
remains unresolved; no source acceptance is self-issued. A separate acquisition
wrapper will follow as its own source freeze and needs independent review before
any runtime acquisition. The original exact-argv repeat controller is unchanged.
