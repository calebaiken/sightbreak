The retained ZIPs are the unchanged original connector artifacts. Extract them in fresh directories with `safe_extract.py` and their official SHA256 values from the report. The outer receipts ZIP contains the inner `qa-receipts.zip`; extract that with SHA256 `860264ed21f120cbd523a33d04da59d4bb7fee4700fce6fca74a2bbeae611d9b`.

These commands only read source and transferred evidence; they launch no game, OCR, compiler or permission API:

```sh
python recompute_source.py /path/to/repository --output source-recomputed.json
python audit_mac_outputs.py /path/to/inner-receipts --identity source-recomputed.json --full /path/to/full-QA --output recomputed.json
python audit_native_suites.py /path/to/inner-receipts --output regressions-recomputed.json
```

The source helper reads exact frozen Git objects, so a later documentation HEAD does not change the expected source. Independent original-pixel review is separate from these byte/receipt checks. Native binaries, PCKs, cache files and remote filesystem aliases are not supplied by these bounded QA artifacts; their native attestation and practical limits are explicit in the report.
