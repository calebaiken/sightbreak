# Replaying the independent byte audits

`CRITERIA.md` was committed before output artifacts existed; `BRIEF-EXACT.txt` preserves the assignment verbatim. `REPORT.md` is the final independent result. Intermediate metadata filenames are labels; each wrapper's observed timestamp is authoritative. The final recorded job metadata confirms one successful Windows job and the artifact metadata binds the exact frozen source.

The original official ZIPs are under `archives/`. The bounded outer ZIP contains the original `qa-receipts.zip`; extract that ZIP for native `evidence/` and its indexed original bytes. The full QA ZIP contains those same 206 files plus 83 PNGs. No EXE bytes were transferred.

Use Python 3 and Pillow. Set `REVIEW` to this directory, `REPO` to any Git checkout containing frozen source `3b5cf7640e256dff404b401bf2b27ffaff157bdd`, and `OUT` to a fresh temporary directory. None of these commands launches a game, renderer or OCR.

```bash
mkdir -p "$OUT"
python3 "$REVIEW/safe_extract.py" "$REVIEW/archives/windows-qa-receipts-12407696223.zip" "$OUT/outer" --sha256 16d2eb10f599593394af0aa85c12ac9774f1c0c1ab5e693b6376e69913617a2c
python3 "$REVIEW/safe_extract.py" "$OUT/outer/qa-receipts.zip" "$OUT/receipts" --sha256 1ec46da3b37712fc547ccd7a5cb9046e49678d93eb8c641c5348e6e371aa87fc
python3 "$REVIEW/safe_extract.py" "$REVIEW/archives/windows-qa-12407158670.zip" "$OUT/full" --sha256 573a9eb59c44c38ee9d9b6846c65576db8cf2c3d916eff7bf5b043a03b3d4a6c
python3 "$REVIEW/recompute_source.py" "$REPO" --output "$OUT/source-LF.json"
python3 "$REVIEW/audit_windows_source.py" "$REPO" "$OUT/receipts" --output "$OUT/source-Windows.json"
python3 "$REVIEW/verify_receipts.py" "$OUT/receipts" --output "$OUT/recomputed.json"
python3 "$REVIEW/audit_journey_ocr.py" "$OUT/receipts" --output "$OUT/journey-OCR.json"
python3 "$REVIEW/audit_phase_captures.py" "$OUT/receipts" --full "$OUT/full" --output "$OUT/phase-captures.json"
python3 "$REVIEW/audit_objective_stages.py" "$OUT/receipts" --output "$OUT/objective-stages.json"
python3 "$REVIEW/audit_raw_sources_logs.py" "$OUT/receipts" --source-audit "$OUT/source-Windows.json" --output "$OUT/additional-raw.json"
python3 "$REVIEW/audit_full_qa.py" "$OUT/receipts" "$OUT/full" --output "$OUT/full-QA.json"
```

All applicable original receipt slices, both objective stage checks and both phase bracket checks should pass. Layouts are not applicable to this Windows job. OCR should report sixteen complete calls and strict LEAVE call 16. Full QA should report 206 byte-identical originals and 83 intact PNGs. Regression logs should report no engine errors or ObjectDB/instance leaks. Those byte/state audits cannot replace the separate direct original pixel review in `visual-review.json`.

`job-119678513156-log-response.json` preserves the connector response. Its `structuredContent.content` encoded as UTF-8 without newline conversion exactly equals `job-119678513156-decoded.log`: 1,623,994 bytes, SHA256 `169d8131debb28fa65fb97aa24135b8e8eacacbba92c971af4a4305aab9c4416`. The text contains 29,236 LF including 29,230 CRLF. Raw received CRLF and original whitespace remain untouched; authored documentation whitespace checks exclude that received log.

The source inventory, Windows reconciliation, raw receipt recomputation, OCR, phase brackets, objective stages, additional native log audit and full QA crosscheck are independent review outputs. The official ZIPs contain the original source-bound native results. Selected `original-images/` copies are byte-identical conveniences; all originals remain in the full QA archive. Objective fixtures create no training save and support only default-profile restart; ordinary journey and stock-match files provide changed-settings and earned disk/runtime profile evidence.

An initial ad hoc source scan encountered the expected list-shaped regression `results.json`; it was corrected to handle only dictionary result records and the manifest. Another exploratory profile read confirmed that incomplete objective fixtures have no save file; the final audit records the absence and limits the restart claim. These were review-tool assumptions, not native fixture failures. No native iteration or failed raw result was discarded.

`SHA256SUMS` covers all retained evidence files except itself. Run `sha256sum -c SHA256SUMS` from this directory to verify it.
