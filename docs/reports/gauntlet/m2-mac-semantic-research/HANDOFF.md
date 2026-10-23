# Research handoff

Read [DECISION.md](DECISION.md) for the pinned Godot/AccessKit source chain and [READ_ONLY_AX_PREREGISTRATION.md](READ_ONLY_AX_PREREGISTRATION.md) for the next source component's proposed scope. The exact exported AX tree, observer permissions and AX/native frame agreement remain **unobserved**. This report contains no new helper or runtime implementation and grants no source approval or execution release.

The original focused native PNG, its fixed 2× image and original Vision JSON are copied byte-for-byte under `native-witnesses/`; [native-witness-index.json](native-witness-index.json) binds their hashes to independently retained commit `460fe42`, run `39920948579`, exact game source `c838907`. The raw and derived unique Deploy captions still have confidence 0.5. The original 0.8 gate still rejects, with no CGEvent or gameplay acceptance. All earlier failed iterations remain authoritative in their original reports.

[upstream-source-excerpts.json](upstream-source-excerpts.json) records 25 immutable source files, resolved commit metadata, SDK gitlink, full fetched-content hashes and bounded excerpts. The connector returned 404 for an attempted `platforms/macos/src/node_wrapper.rs` lookup: the actual `NodeWrapper::title` implementation was then found and retained from the already fetched `node.rs` lines 299–314. Two initial shell searches named nonexistent `scripts/smoke_macos_ordinary.py` / `scripts/macos_ordinary.py`; `rg --files` identified the actual `verify_macos_ordinary.py` and `macos_ordinary_input.py`. These were research lookup failures, not native results or passing tests.

The 293,059-byte `upstream-fetched-text.json.gz` retains full fetched public source text, including original source headers, so the source-hash/excerpt audit is reproducible without another fetch. It contains source text, not executable code. The report-only checks in [checks.txt](checks.txt) verify source excerpt/hash consistency against that fetched UTF-8 text, exact local native witness bytes against the retained Git objects, and unchanged runtime/product/workflow source against the base. No maintained runtime suite needs rerunning for this report-only delta. No engine, import, UID generation, Swift compiler, AX/native API, OCR executable, service or CI was run.

Exact completed command, from the own worktree:

```sh
python3 docs/reports/gauntlet/m2-mac-semantic-research/audit_research.py --historical-audit
```

The explicit historical review mode requires the existing review Git objects. Plain `audit_research.py` audits the checked-in source text/excerpts and native witness hashes without historical objects; neither mode is a maintained workflow check or a native probe.

Next, root may assign a source implementation of the preregistered opt-in diagnostic and a fresh independent critic. Freeze that separate component, replay pure controls from a depth-one checkout, review the combined workflow source and bind the exact ref before root considers a read-only ARM preflight. The full ordinary gameplay lane remains blocked by its original OCR failure until a later explicitly reviewed targeting method is supported by actual native data.
