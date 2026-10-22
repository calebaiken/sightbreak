# Re-open the retained Windows evidence

These commands only extract and read retained evidence. They do not launch native clients. Run them in a fresh directory after extracting `evidence.tar.gz`.

```sh
python3 safe_extract.py windows-qa-receipts.zip windows-outer --sha256 e6829d015b6763a110b87d8f6623f5a0a21ab466b668b116bdcd6794d433158e
python3 safe_extract.py windows-outer/qa-receipts.zip windows-receipts --sha256 4e64573bbd12a53b7ef8441d1cd09bde9b5400242f915790b794b01bea88a381
python3 safe_extract.py windows-qa.zip windows-full --sha256 884b6397eb57dbaf75ea3ee481abbc546f581094dd024f2cd0b0993836f2c541
python3 verify_receipts.py windows-receipts --output windows-recomputed-rerun.json
```

The expected functional summary is raw index=true, regressions=true, full match=true, both objective scenarios=true, ordinary journey=false, three native input/reload scenarios=true. Layouts are not applicable to this Windows job. The ordinary journey must remain failed with the exact retained dead-player context; no restart/focus pass may be inferred from a partial run.

Original PNGs remain inside the official full QA ZIP. `windows-image-review.json` identifies the seven original images viewed by the critic. `windows-failure-reconstruction.json` is an independent reconstruction of the failure, with verbatim action excerpts and raw native samples; it is not a replacement raw receipt or an implementation proposal.

The Windows engine-producer inventory uses the native checkout's bytes. `windows-source-resource-comparison.json` explains the sole LF/CRLF difference from the frozen Linux review checkout. Do not normalize the original ZIPs or decoded Windows log: the latter retains 17,623 CRLF endings and has a separate byte-identity receipt.

Linux outcomes and four-size captures remain pending at this documentation increment. No Linux raw artifacts, results or images are supplied by this Windows archive.
