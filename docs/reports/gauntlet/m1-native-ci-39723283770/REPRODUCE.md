# Re-open the actual Windows retry evidence

Extract `evidence.tar.gz` into a fresh directory, then run these evidence-only commands. They do not launch native clients.

```sh
python3 safe_extract.py windows-qa-receipts.zip windows-outer --sha256 1f92eafec11e95c69275517b5abf1c6d8cb2f82e82aecd7996c55ae5da2a4212
python3 safe_extract.py windows-outer/qa-receipts.zip windows-receipts --sha256 0708009eafec0e7fa900f84ce639aa7202d51d702b66dadf40f1b5cad558feff
python3 safe_extract.py windows-qa.zip windows-full --sha256 109b050253ad8bd8cc8e9262ba33d88b54de83a5156ef44647dd473445691b93
python3 verify_receipts.py windows-receipts --output windows-recomputed-rerun.json
```

Expected summary: raw index=true; native suites including the separate HUD fixture cleanup=true; settings transaction=true; normal/controlled/legacy input=true; plant/defuse=true; stock match/restart=true; ordinary journey=false. Layouts are not applicable to this Windows-only run.

The final visible-control failure is in original `windows-full/offline-input/ocr-current.png`. `failure-reconstruction.json` keeps raw samples/actions, exact input-image identity and the native TSV limitation. `image-review.json` lists eight original PNGs directly viewed. `windows-recomputed-initial-incomplete.json` retains the verifier's first missing-field mistake; the corrected method does not invent a numeric HUD result absent from the failed native receipt.

Source/run identity is dc2a198 / 39723283770. Neither this archive nor its pass slices relabel the separate 0ca125d combined run, satisfy the unexecuted journey restart/focus steps, or close a complete release gate.
