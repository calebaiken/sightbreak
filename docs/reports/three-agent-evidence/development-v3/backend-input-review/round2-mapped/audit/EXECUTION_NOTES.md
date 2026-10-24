# Execution boundary and reproducibility

All new writes are confined to this **new external audit directory**. No primary-repository source, tests, docs, published round1 files, index, or Git objects were written. Original input scripts are data for source inspection; none were imported/run.

## Actual audit interpreter

`C:\Users\blith\AppData\Local\Temp\opencode\sightbreak-tools\python\cpython-3.13.15-windows-x86_64-none\python.exe`

Every own Python invocation used `-I`. Standard-library imports are used; the own `auditlib.py` directory is explicitly inserted for those scripts only. There are no target/third-party imports, application/pytest/DB/native/service/network executions, or delegated agents. Earlier retained target receipts record **Python 3.12.14**, not this audit interpreter.

## Execution order

1. `verify_freeze_before_key.py`: direct tool exit 0, 28 checks passed. **No mapping bytes opened by this program.** Full anchors and the blind freeze statement verified before subsequent key inspection.
2. `discover_bound_inputs.py`: direct tool exit 0, 4 checks passed; external/repository key bytes match the supplied SHA-256.
3. `collect_selected_objects.py`: direct tool exit 0, 108 checks passed; exact Git snapshots saved externally, including all assurance raw payloads but excluding `critic-r2-parent` claims.
4. `audit_assurance.py`: direct tool exit 0; **167 passed / 2 negative checks retained**, both from the earlier failed/materialization-confounded attempt. A process exit 0 does not turn those checks into passes.
5. `run_offline_audit.py audit_retention_bindings.py`: child exit 0, 2,312 checks passed; stdout/stderr and program hash retained in `offline-executions.jsonl`.
6. `run_offline_audit.py audit_followup.py`: child exit 0, 24 checks passed; appended context explains the first-attempt byte conversions and preserves both negative checks and original artifacts.
7. `seal_audit.py`: final byte/source/exit consistency checks; writes the final source-hash index, execution ledger, decision ledger reference and checksum manifest. Its actual completion/exit and manifest anchor are returned by the tool invocation, not presumed from an empty stream.

The launcher allowlist contains only this audit's own named programs. It is not a way to run any retained verifier, test, service, import probe, benchmark or control runner. **Original Sol synthetic controls remain UNEXECUTED.** The four-constant reversal is byte/AST arithmetic, not execution of its reconstructed app.

## Recorded command evidence

`commands.jsonl` gives exact Git argv, UTC, explicit exit, stdout/stderr lengths, hashes and raw filenames for programmatic collection/audit. Object IDs and nonempty blob contents are checked explicitly. An expected empty `git diff --name-only` is accepted only with exit 0 and matching pinned source bytes/tree IDs; it is not a generic empty-output success rule.

Three initial read-only Git discovery invocations were observed directly through the tool, all with exit 0, before the corresponding structured captures:

```text
git ls-tree -r --name-only 866e2e1f38461fa245557c9015b6c1a1a97ad745 -- docs/reports/backend-trade-read-v3/identity-release-r2
git show 866e2e1f38461fa245557c9015b6c1a1a97ad745:docs/reports/backend-trade-read-v3/identity-release-r2/sol/FROZEN.json
git ls-tree --name-only 8070436f53dd98e9529e8c21ea7b0f7e3ecb6daf:scripts
```

These initial tool-rendered outputs have no separate raw transcript here; the relevant freeze/source objects were subsequently read and hashed by the captured collectors. File read/glob/grep tool operations were discovery/inspection only. Listing a parent critic path did not open or use that critic's claims.

## Final checksum rule

`SHA256SUMS.txt` covers all regular payload files recursively, including all **inner input manifests**, except itself and regenerable `__pycache__` files. There is no self-hash assertion. The final returned digest is the outer anchor. The directory and local timestamps are not trusted time attestation or immutable storage.

The completed first-round 165/1 binding history, the earlier R3 replay failure, and both verdict freezes remain unchanged. New receipts and post-hoc preimage evidence add information without superseding those originals. No broad backend/performance, memory/concurrency or production acceptance follows from this audit.
