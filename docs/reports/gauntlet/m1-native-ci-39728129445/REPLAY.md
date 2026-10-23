# Replaying the byte audits

`REPORT.md` is the independent result. `CRITERIA.md` precedes the output review and `BRIEF-EXACT.txt` retains the assigned brief verbatim. `jobs-0557.json` records exactly one completed Windows job and the failed plant step; the wrapper's observation timestamp is authoritative. The filenames of intermediate polls are labels, not exact observation times.

The two ZIPs in `archives/` are the original official connector artifacts. The bounded outer ZIP contains `qa-receipts.zip`; its extracted `evidence/` files are original native receipts, profiles, action traces, OCR stdout and logs. The full QA ZIP contains those same 205 files plus 79 original PNGs. No native executable was downloaded.

Use Python 3 and Pillow. Set `REVIEW` to this evidence directory, `REPO` to any checkout containing frozen source commit `a8eb7eb81c74f306a9600820cb6e78f98a5e1630`, and `OUT` to a fresh temporary directory. These commands only extract, decode, hash and read source. They run no game or OCR.

```bash
mkdir -p "$OUT"
python3 "$REVIEW/safe_extract.py" "$REVIEW/archives/windows-qa-receipts-12405321729.zip" "$OUT/outer" --sha256 bc99526702f3af8a42e03424e3fc6e0614d7cdc848759c4110264c88fa288f7f
python3 "$REVIEW/safe_extract.py" "$OUT/outer/qa-receipts.zip" "$OUT/receipts" --sha256 610052059b94206a4dd0087145fb5f5b3aa418b68beb13b528d3045d08a55678
python3 "$REVIEW/safe_extract.py" "$REVIEW/archives/windows-qa-12404459761.zip" "$OUT/full" --sha256 ea963c1a18bd9d5dd78bd344ff05ab4acc381942882b7b78ddcd512bb09e2dd1
python3 "$REVIEW/recompute_source.py" "$REPO" --output "$OUT/source-LF.json"
python3 "$REVIEW/audit_windows_source.py" "$REPO" "$OUT/receipts" --output "$OUT/source-Windows.json"
python3 "$REVIEW/verify_receipts.py" "$OUT/receipts" --output "$OUT/recomputed.json"
python3 "$REVIEW/audit_journey_ocr.py" "$OUT/receipts" --output "$OUT/journey-OCR.json"
python3 "$REVIEW/audit_full_qa.py" "$OUT/receipts" "$OUT/full" --output "$OUT/full-QA.json"
```

The expected overall plant result is **false**, while defuse is true. All other applicable verification slices pass. Missing Linux layouts are not applicable to this Windows-only job. The full QA audit should report 205 matching originals and 79 intact PNGs. The journey OCR audit should report 16 complete native stdout files, strict LEAVE call 16 and a passing whole journey. These results do not establish repeat reliability or platform release acceptance.

`job-119656711230-log-response.json` preserves the connector response. `job-119656711230-decoded.log` is exactly its `structuredContent.content` encoded as UTF-8 with no newline conversion. It is received decoded text, not an original GitHub log ZIP. Its 1,313,584 bytes contain 23,614 LF, including 23,608 CRLF; SHA256 is `3890c7ec9e23d8b6db588cc156fc1029b0c0ce6d1624ecd829afcc1f6455f824`.

`source-reconstruction-LF.json` retains all frozen source byte records. `source-reconciled.json` explains the four Windows CRLF paths and validates every native game-resource hash and the Python controller. `recomputed.json`, `journey-OCR-recomputed.json`, `plant-failure-reconstruction.json` and `full-QA-crosscheck.json` are independent audit outputs; they are distinct from the original native receipts in the ZIPs. `visual-review.json` identifies the 33 originals inspected directly. `capture-timing-reconstruction.json` projects the exact retained action/event context for the two stale transition captures, with explicit missing per-capture authority brackets and separate process clock domains. Selected copies under `original-images/` are byte-identical conveniences; all originals remain in the full QA ZIP.

`SHA256SUMS` covers every retained evidence file except itself. Verify it from this directory with `sha256sum -c SHA256SUMS`.
