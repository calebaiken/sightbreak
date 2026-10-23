# Reopen the actual Windows evidence

The actual combined attempt fails. Replay must preserve the failed living
journey, unreached focus experiment and missing success-only fields. All commands
below read retained bytes; none launches Godot, a native client, OCR or a service.
Use Python 3 with Pillow and a fresh output directory from the repository root:

```bash
REVIEW=docs/reports/gauntlet/windows-native-a089-independent-20261023
OUT=builds/windows-a089-original-replay
python "$REVIEW/safe_extract.py" "$REVIEW/archives/windows-qa-receipts-12486386097.zip" "$OUT/outer" --sha256 92a5283f00e9a92a32e25914b5dfee32659ddbc8932693f2f0a19894d407c740
python "$REVIEW/safe_extract.py" "$OUT/outer/qa-receipts.zip" "$OUT/receipts" --sha256 6aa26318a715ad6c1da0a1e67c276b4939af5dab1d2acf5560f0774911d9668a
python "$REVIEW/safe_extract.py" "$REVIEW/archives/windows-qa-12485916617.zip" "$OUT/full" --sha256 67fc08feda5ffe214eca9cd31e149b9561870498ddbe67a2befd564df6eaf3d2
python "$REVIEW/verify_receipts.py" "$OUT/receipts" --output "$OUT/raw-recomputed.json"
python "$REVIEW/audit_native_commands.py" "$OUT/receipts" --output "$OUT/native-commands-recomputed.json"
python "$REVIEW/audit_windows_source.py" "$PWD" "$OUT/receipts" --output "$OUT/source-Windows-recomputed.json"
python "$REVIEW/audit_gunplay.py" "$OUT/receipts/evidence/regressions/gunplay_rules.log" --output "$OUT/gunplay-recomputed.json"
python "$REVIEW/recompute_dry_observable.py" --mode candidate "$OUT/receipts/evidence/regressions/bot_dry_weapon.log" --output "$OUT/dry-observable-recomputed.json"
python "$REVIEW/audit_journey_ocr.py" "$OUT/receipts" --output "$OUT/journey-OCR-recomputed.json"
python "$REVIEW/audit_phase_captures.py" "$OUT/receipts" --full "$OUT/full" --output "$OUT/phase-captures-recomputed.json"
python "$REVIEW/audit_objective_stages.py" "$OUT/receipts" --output "$OUT/objective-stages-recomputed.json"
python "$REVIEW/audit_raw_sources_logs.py" "$OUT/receipts" --source-audit "$OUT/source-Windows-recomputed.json" --output "$OUT/raw-sources-logs-recomputed.json"
python "$REVIEW/audit_export_identity.py" "$OUT/receipts" "$OUT/source-Windows-recomputed.json" --output "$OUT/export-identity-recomputed.json"
python "$REVIEW/audit_full_qa.py" "$OUT/receipts" "$OUT/full" --output "$OUT/full-QA-crosscheck.json"
python "$REVIEW/audit_failure_diagnostics.py" "$OUT/receipts" --output "$OUT/failure-diagnostics.json"
python "$REVIEW/audit_settings_failure.py" "$OUT/receipts" --output "$OUT/settings-failure-recomputed.json"
python "$REVIEW/audit_focus_actual.py" "$OUT/receipts" "$OUT/full" --output "$OUT/focus-actual-recomputed.json"
python "$REVIEW/audit_runtime_complete.py" "$OUT/receipts" "$OUT/full" "$OUT" --output "$OUT/runtime-completeness.json"
```

The final command must return exit 1 and false. Some inherited auditors serialize
failed checks while returning exit 0: inspect their JSON. Native suites, three
input schedules, both objectives and full-match earned reload pass their bounded
checks. Journey, completed settings transaction, resumed/LEAVE OCR, reopened
phase bracket, typed focus rejection and fresh movement remain unqualified.
The source audit retains a false success-only controller-digest comparison while
its exact complete validation/source-resource comparisons pass.

`audit-run-r1.json`, `audit-run-r2.json` and
`settings-initial-auditor-overcomparison.json` retain reviewer-tool failures and
their narrow corrections. `auditor-port-provenance.json` records inherited source
and adaptations. Original native archives are unchanged. `visual-review.json`
records direct findings for 35 originals and hashes of seven convenience copies;
all 77 originals remain in the official full QA ZIP.

Run/job/step metadata and the exact connector-decoded log response are retained.
To recover its exact UTF-8 bytes, parse `job-120291226421-log-response.json` and
write `structuredContent.content.encode('utf-8')`. Its digest and newline counts
are in `supported-transfers.json`; it is not an original GitHub log ZIP. The
development package exceeds the supported transfer cap and is represented only
by native source/export/runtime attestation. No signed download URL is retained.

The registration timing limitation remains in `REGISTRATION_TIMING.md`. The
original before-dispatch claim is not restored by replay. The previous b2
failure stays in its original evidence directory and keeps its source identity.
