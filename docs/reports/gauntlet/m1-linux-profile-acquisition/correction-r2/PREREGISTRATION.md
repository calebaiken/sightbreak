# Correction R2 preregistration

Source and pure Python only. Exact R1 freeze `d0d94bec27f539b63e324c5468516ff2f0dd96d7`
was independently rejected at `c339065c80e13a945b87c7f01a65655639be8281`
(critic preregistration `0c65b35`). Its original review, controls, raw output and
initial metadata are retained byte-exact in `retained-rejection/` before code.
All original/R1 registrations, reports and failed controls remain historical.

Only two corrections are registered:

1. For log binding and rereading, compute identity and strict semantics from the
   SAME raw byte read. Compare that observed identity against both the original
   accepted identity and any caller-provided expected bytes before accepting it.
   Eliminate the later unchecked `read_text` semantic read. Retain the exact old
   boundary control and its rejection; its old read_text injection route ceases
   to exist, so an explicit equivalent before-read_bytes control must actually
   change bytes observed by the corrected validator and require rejection.
   Include a clean unchanged positive and direct bind/validate controls.
2. Observe source once at the named boundary **after output-manifest readback and
   before overall publication**. Run the existing full source checker under the
   original final/whole deadline and retain start/end, result and scope in the
   overall receipt. Source drift injected during manifest write must precede and
   fail this observation. Any Git logs created by this observation occur after
   the initial output manifest; their original identities are retained in the
   complete `overall.validated_evidence` registry. No manifest rewrite/retry is
   introduced. The source claim covers this finite observation interval, not
   perpetual immutability after it or after return. Late completion still fails
   the existing cap; positive just-before-boundary controls must pass.

Replay the two exact old falsifiers against R1, retain their positive, and use
the explicitly adapted raw-read hook for the new implementation. Retain and run
all ten original falsifiers, all 64 maintained publication mutants, and the
unchanged accepted fixture suite. No new abstraction, gameplay change or budget
extension is intended. Accepted fixture/controller, game, packaging/graphics,
OFF/ON/ON/OFF, 180-second condition caps and 1320-second outer cap stay unchanged.
No engine/import/compile/UID/export/Xvfb/native/profiler/OCR/CI/service/heavy
process or nested agent is authorized. Push a clean exact source/report freeze
for fresh independent review before any runtime decision by root.
