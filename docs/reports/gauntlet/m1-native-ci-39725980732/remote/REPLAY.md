Preserve the original outer ZIPs and use `safe_extract.py` with each official SHA256 from raw artifact metadata. Extract the bounded inner `qa-receipts.zip` into `receipts/`, with SHA256 `81420daef300ec961d544d812889053c8b90dae3b5f5fba68413f0adb7e62017`. Each per-size outer artifact contains a named size ZIP; use its recorded inner digest in `PNG-artifact-audit.json` and extract into `images-960x540/`, `images-1280x720/`, `images-1920x1080/` and `images-1280x800/`.

The independent checks read source/artifact bytes only and launch no Godot, OCR or native timing workload:

```sh
python recompute_source.py /path/to/repository --output source-recomputed.json
python verify_receipts.py /path/to/review-root/receipts --output remote-recomputed.json
python audit_remote_images.py /path/to/review-root --output remote-layout-image-bindings-replayed.json
```

Source is read from frozen Git objects; later documentation HEADs do not relabel it. `verify_receipts.py` keeps the failed plant scenario false while separately validating defuse and other slices. The original failure reconstruction additionally retains the raw consumed plant edges, capture/death context and final status. Direct independent image review and native attestation limits are explicit in the report; unavailable gameplay PNGs and remote TSV bytes cannot be recreated by these checks.
