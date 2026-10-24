# R2 focus fence correction, source only

Registered before correction on 2026-10-23. Preserve rejected freeze `19304d5`
and handoff `0823cee` as ancestors. Independent rejection `0d4f7e0` names three
blocking classes: malformed timestamps can bypass the fence before freshness,
malformed nested objects can raise without the promised loss receipt, and
normalization loses non-object raw values while boolean zero movement passes.

The bar is the unchanged independent `probe_fence.py` case inputs and actual
controller AST, its 77 cases / 49 original rejection assertions, plus retained
original Windows raw states. Copy those review bytes unchanged into this report
before replay. The original assertions intentionally confirm defects, so a
corrected candidate must stop reproducing those assertions; a separate replay
receipt will check corrected outcomes for all unchanged cases. No original
review output will be overwritten or relabeled.

Validate the structure/schema/counter types of an available raw observation
before freshness can discard it. Retain ordinary missing-publication and valid
stale-state behavior. For fresh accepted states enforce the original living
actor/life/round/phase fence. Classify malformed nested/non-object values and
reader scope errors as `FOCUS_PRECONDITION_LOST`, with the exact rejected JSON
value, previous valid state and stage. Validate movement vector types strictly,
including boolean elements. Add meaningful living-positive, stale-publication,
and strict movement controls through the actual extracted controller waits.

Preserve captures, original ten-second and whole/stage deadlines, generic tap,
held neutrality, physical release, stock gameplay and CI. Run only pure Python,
AST/source checks and unchanged independent probes. No engine, import, UID,
native, OCR executable, export, CI, service, canonical document or runtime retry.
Freeze/push this correction separately. Any later Escape timing hypothesis needs
its own preregistration, commits, pure controls and independent approval.
