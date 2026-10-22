# Reopen the independent Windows evidence

CRITERIA.md was committed as `2e580a6` before current output transfer. REPORT.md
states the bounded result and open gaps. Official ZIPs are under archives/;
supported-transfers.json binds IDs, sizes, digests and the exact source/run.
Temporary signed URLs were not used directly or retained. No EXE was downloaded.

Use Python 3 plus Pillow. In this directory, `sha256sum -c SHA256SUMS` checks all
retained files except SHA256SUMS itself. From a checkout containing frozen source
0527715, choose a fresh temporary output directory and extract:

```bash
python3 "$REVIEW/safe_extract.py" "$REVIEW/archives/windows-qa-receipts-12410890049.zip" "$OUT/outer" --sha256 05a22ea20540f93d9238736ad1c3515ad143424833ca7ac4d6e1632c30b9c400
python3 "$REVIEW/safe_extract.py" "$OUT/outer/qa-receipts.zip" "$OUT/receipts" --sha256 3c8d0af6ebbb49ce02ecdd884f94af5e398508b2d8e9fb54c78839944015c590
python3 "$REVIEW/safe_extract.py" "$REVIEW/archives/windows-qa-12409593990.zip" "$OUT/full" --sha256 8ef76aa1ea3809a4ee35da1adf407decd1cf417fd24def79097dd723dfe231af
python3 "$REVIEW/recompute_source.py" "$REPO" --output "$OUT/source-LF.json"
python3 "$REVIEW/audit_source_scope.py" "$REPO" "$OUT/source-LF.json" --output "$OUT/source-scope.json"
python3 "$REVIEW/audit_windows_source.py" "$REPO" "$OUT/receipts" --output "$OUT/source-Windows.json"
python3 "$REVIEW/verify_receipts.py" "$OUT/receipts" --output "$OUT/recomputed.json"
python3 "$REVIEW/audit_native_commands.py" "$OUT/receipts" --output "$OUT/native-commands.json"
python3 "$REVIEW/audit_gunplay.py" "$OUT/receipts/evidence/regressions/gunplay_rules.log" --output "$OUT/gunplay.json"
python3 "$REVIEW/audit_journey_ocr.py" "$OUT/receipts" --output "$OUT/OCR.json"
python3 "$REVIEW/audit_phase_captures.py" "$OUT/receipts" --full "$OUT/full" --output "$OUT/phases.json"
python3 "$REVIEW/audit_objective_stages.py" "$OUT/receipts" --output "$OUT/objectives.json"
python3 "$REVIEW/audit_raw_sources_logs.py" "$OUT/receipts" --source-audit "$OUT/source-Windows.json" --output "$OUT/source-logs.json"
python3 "$REVIEW/audit_export_identity.py" "$OUT/receipts" "$OUT/source-Windows.json" --output "$OUT/export.json"
python3 "$REVIEW/audit_full_qa.py" "$OUT/receipts" "$OUT/full" --output "$OUT/full-QA.json"
```

No command launches a game, native renderer, OCR or service. Gunplay recomputes
4,399 predicates / 52 actual records. Fourteen suites total 8,844 assertions.
All applicable receipt audits should pass; layouts are not applicable to this
Windows job. Both objective next-buy bounds remain below the original 12 s.
Default-profile objective restart remains distinct from earned disk/runtime
equality in the separate stock full match.

Pixel correctness needs direct original inspection. visual-review.json lists
all 45 images inspected, their hashes and findings; all 83 remain in the original
full QA ZIP. Six original-image convenience copies are byte-identical. Both
named phase PNGs are byte-identical to earlier accepted output, so this review
claims current regression correctness without a subjective blind winner.

The exact decoded-log bytes equal the UTF-8 encoding of
job-119699561669-log-response.json structuredContent.content. Retain native CRLF;
exclude received text from authored-document whitespace normalization.
audit-iteration-notes.json distinguishes historical audit controls and corrected
review-tool filename assumptions from actual current native results.
