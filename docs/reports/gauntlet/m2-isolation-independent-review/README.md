# Independent isolation and packaging evidence

The original critic rejected `1195b234` for a reproduced cleanup false-success
receipt. The follow-up critic accepts `daafe167` only for Linux source-suite
isolation and cleanup-receipt truthfulness after re-running the original
counterexample, five cleanup controls, all nine source suites and save-safety
controls. [Original review](ORIGINAL_REVIEW.md) and [follow-up review](FOLLOWUP_REVIEW.md)
remain separate; the original rejection was not rewritten.

The [packaging review](PACKAGING_REVIEW.md) found no local correctness issue at
`32c37fe`: all 91 selected files from the actual Windows QA ZIP reconstructed
exactly, repeated packaging was identical, and an actual over-30-MiB input failed
without source mutation or a partial output.

Actual Windows/macOS isolation CI and the compact artifact's real upload/download
remain pending. None of these source or packaging controls qualify exported
gameplay, physical input, performance, visual quality or a release.

`evidence.tar.gz` retains 400 regular files: exact original/follow-up briefs,
commands, raw native logs, engine path and exit receipts, inventories, independent
readbacks, counterexample scripts, packaging checks and reports. `MANIFEST.json`
records every archived file's length and SHA-256. The original critic's 340-file
local inventory is preserved verbatim; 171 raw Windows derivatives, duplicate
compact ZIPs and generated cache files are explicitly omitted in the manifest.
The follow-up's 229-file inventory is retained. No engine, native binary or cache
is added to this evidence archive.

The original 21,973,542-byte Windows QA ZIP is already retained as
`windows-qa.zip` inside
`../m1-native-ci-39712752860/evidence.tar.gz` at the docs base `32c37fe`.
Its SHA-256 is
`8144fa7380fd5a649d8077570d982fe2994888a7a97601f1d67f2227077f1897`.
The new archive references those exact bytes and does not duplicate the ZIP or its
screenshots. Its compact derivatives remain reproducible from the committed
packer, original source archive, retained index and exact commands.

From this directory:

```sh
sha256sum -c sha256.txt
python3 verify_archive.py
```

The verifier checks archive safety, every file hash, immutable original/follow-up
inventories, verbatim report copies, the referenced original Windows ZIP, all 91
selected Windows receipt hashes, and the before/after cleanup verdicts. It can
extract the verified archive with `--extract <fresh-directory>`. Original scripts
retain their exact historical workspace paths; use the portable verifier for
archive readback. This is integrity/recomputation of retained evidence, not a new
native execution or new CI result. The docs-only commit is based on `32c37fe` and
does not integrate the implementation follow-up itself.
