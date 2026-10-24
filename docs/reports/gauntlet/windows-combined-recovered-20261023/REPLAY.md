# Reopen the combined Windows evidence

The actual attempt fails; replay must preserve that outcome. Source approval in
SOURCE_REVIEW.md is distinct from REPORT.md. Official ZIPs are retained under
archives/, with original metadata and digests in supported-transfers.json.

From the repository root, use Python 3 plus Pillow and a fresh output directory:

```bash
REVIEW=docs/reports/gauntlet/windows-combined-recovered-20261023
OUT=builds/windows-combined-replay
python3 "$REVIEW/safe_extract.py" "$REVIEW/archives/windows-qa-receipts-12482332230.zip" "$OUT/outer" --sha256 d4408c6f02fc20759b064c30fa6fdfa9f77413fa67bafb27c5e825483570dae7
python3 "$REVIEW/safe_extract.py" "$OUT/outer/qa-receipts.zip" "$OUT/receipts" --sha256 bdef9bc942a7153f7a2c986fff56541127c1a8cd27777d1df12a6d27ee82067a
python3 "$REVIEW/safe_extract.py" "$REVIEW/archives/windows-qa-12481849407.zip" "$OUT/full" --sha256 a12faef0ea3c1590a07f931ade08accf6bb0244bfab28928a896808f8fe25e8e
python3 "$REVIEW/verify_receipts.py" "$OUT/receipts" --output "$OUT/raw-recomputed.json"
python3 "$REVIEW/audit_native_commands.py" "$OUT/receipts" --output "$OUT/native-commands-recomputed.json"
python3 "$REVIEW/audit_windows_source.py" "$PWD" "$OUT/receipts" --output "$OUT/source-Windows-recomputed.json"
python3 "$REVIEW/audit_gunplay.py" "$OUT/receipts/evidence/regressions/gunplay_rules.log" --output "$OUT/gunplay-recomputed.json"
python3 "$REVIEW/recompute_dry_observable.py" --mode candidate "$OUT/receipts/evidence/regressions/bot_dry_weapon.log" --output "$OUT/dry-observable-recomputed.json"
python3 "$REVIEW/audit_journey_ocr.py" "$OUT/receipts" --output "$OUT/journey-OCR-recomputed.json"
python3 "$REVIEW/audit_phase_captures.py" "$OUT/receipts" --full "$OUT/full" --output "$OUT/phase-captures-recomputed.json"
python3 "$REVIEW/audit_objective_stages.py" "$OUT/receipts" --output "$OUT/objective-stages-recomputed.json"
python3 "$REVIEW/audit_raw_sources_logs.py" "$OUT/receipts" --source-audit "$OUT/source-Windows-recomputed.json" --output "$OUT/raw-sources-logs-recomputed.json"
python3 "$REVIEW/audit_export_identity.py" "$OUT/receipts" "$OUT/source-Windows-recomputed.json" --output "$OUT/export-identity-recomputed.json"
python3 "$REVIEW/audit_full_qa.py" "$OUT/receipts" "$OUT/full" --output "$OUT/full-QA-crosscheck.json"
python3 "$REVIEW/audit_failed_stages.py" "$OUT/receipts" --output "$OUT/failed-stages-recomputed.json"
python3 "$REVIEW/audit_failure_diagnostics.py" "$OUT/receipts" --output "$OUT/failure-diagnostics.json"
python3 "$REVIEW/audit_runtime_complete.py" "$OUT/receipts" "$OUT/full" "$OUT" --output "$OUT/runtime-completeness.json"
```

The final completeness command must return exit 1 and false. Individual older
auditors serialize failed checks while returning exit 0; read their JSON verdicts.
Native suites, three input schedules, settings subtransaction, phase brackets,
defuse and full-match recovery pass their bounded checks. Whole living journey,
whole plant/device-resolution and unavailable success-only result comparisons
remain false. No command above launches the engine, OCR or a service.

`audit-run-r1.json` retains the reviewer's initial count-ordering bug and the OCR
KeyError caused by absent success-only result fields. `audit-run-r2.json` and
auditor-port-provenance.json retain the narrow reviewer-tool corrections. No
native archive is modified. The missing per-controller digest remains missing.

Direct original pixel findings and hashes are in visual-review.json. Six
convenience copies under original-images/ are byte-identical to the full ZIP.
The other originals remain in that supported ZIP. The EXE/PCK artifact was above
the transfer cap and is represented only by native attestation.

SHA256SUMS covers committed report files except itself. The decoded job log's
bytes equal UTF-8 encoding of the received response's structuredContent.content;
its native CRLF is preserved with a local Git attribute. No signed download URL
is needed or retained.
