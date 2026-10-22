# Independent bounded QA receipt review

No correctness finding in the inspected packaging path at
`32c37fe033842d924c2142e2d0e303d842f6c079`. Local evidence supports dispatching the
next CI run. The real compact artifact upload/download, particularly Linux, remains
pending. This review does not accept the tests contained in the archive as passing.

The exact committed packer and six tests were copied into `source/`; all six tests
passed. The workflow preserves both existing full artifact uploads with
`if: always()`. The compact ZIP is outside its source directory, uploaded with
compression level zero, and checked against 30 MiB including its own index and ZIP
metadata. Raw evidence is stored without normalization or truncation.

The reviewer extracted the actual original Windows QA archive from CI run
`39712752860`: 21,973,542 bytes, SHA-256
`8144fa7380fd5a649d8077570d982fe2994888a7a97601f1d67f2227077f1897`.
The independent reader derived the expected selection from the original ZIP,
then compared every selected compact member to those original bytes, the extracted
source, indexed size and SHA-256. All 91 selected files reconstructed exactly.
These include the actual manifest bound to `6a0d8d5`, three progression files, and
five observer event traces. All progression JSON and trace JSONL parsed.
No PNG, archive, native payload or excluded cache container was present.

The compact ZIP is 1,985,196 bytes, SHA-256
`f75a2149f545283b9e25d1ea1ca12fb95fcaebaa0db50481304a9b62176c8e04`.
Packing the same source a second time produced identical bytes. The builder's
106-file/6.68-MB result used the broader retained parent directory; this review's
91-file result uses the original Windows QA ZIP alone.

An additional real-size control supplied a 31,457,297-byte deterministic random
log, 17 bytes over the actual limit. Packaging failed with the download-bound
error, left the source byte-identical, published no output, and removed its
temporary archive. The smaller tests also covered index-overhead overflow,
symlink rejection, overwrite refusal, empty evidence, macOS text inclusion and
native/cache exclusion. The new artifact needs actual CI transfer evidence before
the connector-limit problem can be called resolved.

Exact controls, raw outputs, source script hashes, reconstructed index and native
paths are retained in this directory. `verify_archive.py` is the independent
reader/control; `INDEPENDENT_RECONSTRUCTION.json` records its results.
