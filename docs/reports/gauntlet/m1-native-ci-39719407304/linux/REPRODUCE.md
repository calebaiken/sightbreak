# Re-open the retained Linux evidence

After extracting `evidence.tar.gz` into a fresh directory, these read-only evidence-processing commands do not launch native clients:

```sh
python3 safe_extract.py linux-qa-receipts.zip linux-outer --sha256 507ecbb602a12d82a3f65b8944da1d4340ea5f2697d3376910f48b32b1029d9a
python3 safe_extract.py linux-outer/qa-receipts.zip linux-receipts --sha256 e9afac5bd1e6a841c25ae09c73e6139ff1d49ffc6e26ffd12c87414cc0db942d
python3 verify_receipts.py linux-receipts --output linux-recomputed-rerun.json
```

Expected summary: raw index=true, regressions=true, full match=true, both objective scenarios=true, ordinary journey=true, native input=true, layouts=false. Layout failures and forced cleanup remain failed. Raw Linux PNGs cannot be supplied by this archive: official full QA is 36,909,293 bytes, above the supported transfer limit. The actual failed generation receipts are retained, rather than substituted by older local captures.

For the exact platform validation-digest reconciliation, supply a clean frozen Linux source checkout whose `scripts`, `.github` and `game/tests` match 0ca125d:

```sh
python3 verify_validation_identity.py /path/to/frozen-source --output validation-recomputed.json
```

Both platform hashes should match. This analyzes the Windows checkout conversions in memory and never edits source bytes. The earlier one-file-only incomplete explanation is preserved in `cross-platform-validation-reconciliation.json`; final recomputation uses all four actual text paths outside the enforced LF rules.

The Windows review remains a distinct prior increment, with its original script and raw ZIPs unchanged. This Linux verifier adds explicit checks for physical W/LMB state during guarded focus recovery and the stock twelve-round score bound. Those strengthen independent receipt review without changing the native implementation or any native outcome.
