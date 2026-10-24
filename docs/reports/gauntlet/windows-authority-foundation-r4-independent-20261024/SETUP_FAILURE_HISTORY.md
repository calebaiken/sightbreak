Own no-checkout/read-tree initialization initially populated only the new report;
checkout-index -a then restored the selected exact tracked source files. The R4
handoff is docs-only after source52d2, so its exact d84 Git blobs were copied into
frozen-builder-d84 rather than treated as files already present at source52d2.
No source test ran before exact code was physically populated/hash pinned.

First literal-traced run135/45failure events/12errors had11 FileNotFoundError
subtests for omitted sparse expiry-builder-tests/CRITIC_COPY_MANIFEST.json and
its fixture files, plus the actual retained generation-construction error. Raw
stdout/stderr/CALLS/failure metadata are retained under literal-traced unchanged.
The exact tracked expiry-builder-tests directory was added to this own sparse
view and checkout-index populated it. Fresh literal-traced-r2 runs the same
unchanged135 methods:45failure events/1error. None of the sparse errors is a
candidate defect or a passing test; no assertion was skipped or reinterpreted.
