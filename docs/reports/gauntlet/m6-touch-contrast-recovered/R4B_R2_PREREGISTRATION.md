# R4B R2 ownership receipt reconciliation

SOURCE/PURE ONLY. R4B source readiness remains REJECTED at independent verdict
`ce3510e3776c8fec42ef1de648b14a453c221724`. No engine, import, native render,
OCR, UID generation or lane release is authorized. R3 FAIL, R4 NO GO and the
first R4B rejection remain retained. Geometry and product are frozen unchanged
at `2ea23f947aec6085449bced53c9b061618a67029`.

This is a narrow method-only correction. A false-zero native wrong-owner count
or a forged winning action can currently disagree with independent replay
without invalidating baseline provenance. The candidate quality gate fails,
but the baseline comparison accepts that invalid receipt. Do not require a
genuinely bad baseline product to pass candidate quality gates as the fix.

For BOTH sources, define the full native ownership sample map from every saved
isolated footprint pixel. Every supported coordinate implicitly claims its own
action unless the native wrong-owner witness list assigns another action or
the unclaimed empty string. Reconcile that complete map exactly with replay:
support count, wrong/unclaimed counts and all wrong sample coordinates/winners.
Reject missing, extra, duplicate, unsupported/out-of-bounds, malformed or
wrong-winner witnesses, including an incorrect unclaimed classification. Do
not reconcile only totals or set membership without the winning identities.
Witness list ordering has no semantic meaning; its complete mapping does.

Any contradiction is a provenance error through audit_source and the final
baseline/candidate comparison, for either source. A correctly recorded wrong
owner remains a genuine product failure with valid provenance. Such a failing
baseline stays comparable to a candidate that passes its independent quality
gates. Keep explicit positive controls for that distinction.

Retain the fresh critic's report, original checks.py, checks.json and exact
falsifier expressions unchanged. Replay those original contradictory cases on
the rejected method and the corrected method, preserving both outputs. Add
separate negative controls for false zero/counts, omitted/extra/duplicate
coordinates, wrong valid-action winners, unclaimed misclassification and
unsupported samples. Exercise both source variants and the complete audit_source
provenance/comparison/CLI path using explicitly synthetic metadata controls.

Do not change product/source geometry, native fixture, ownership sampling,
contrast thresholds, complete glyph/AA/occlusion predicates, final-band
semantics, source/UID/background fences or earlier evidence. Reuse the exact
geometry certificate as historical source support, not a new native result.
Freeze/push the corrected method and exact source/UID receipts for a fresh
independent reviewer before any runtime. Builder controls are not acceptance.
