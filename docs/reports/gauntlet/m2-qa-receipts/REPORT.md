# Bounded raw QA receipts candidate

Builder result; fresh independent review and a real CI upload/download are pending.
The existing package and full QA artifact uploads remain intact. No game test,
assertion, watchdog or qualification condition changed.

The workflow adds `sightbreak-qa-receipts-<target>-<runner>-<source SHA>`, containing
one `qa-receipts.zip`. It includes raw JSON, JSONL and logs, plus macOS diagnostic
text; its index records every selected path, length and SHA-256. Source manifests,
progression files and authoritative traces retain their original bytes. Screenshots
remain in the existing full QA artifact. Native payload containers, archives and
caches are excluded.

The packer stores a deterministic ZIP, capped at 30 MiB including the internal
index and ZIP metadata. Upload compression is disabled so the remaining 2 MiB
under the connector limit accommodates the artifact wrapper. Oversize or changing
evidence, an existing output, symlinked evidence or an empty selection fails
without publishing a partial archive. The workflow still attempts both original
full artifact uploads if the compact packaging step fails.

Six file-based tests pass: exact selection/reconstruction and repeatability,
oversized raw evidence, index-overhead overflow, existing-output/source-directory
protection, empty selection and symlink rejection. Native source/progression/trace
fixtures include trailing blank lines so text is never normalized. See `TESTS.txt`.

The actual retained Windows QA output from run `39712752860` was also packed and
read with a separate standard-library reader. All 106 selected files reconstructed
byte-for-byte and matched their source files and SHA-256 index. The archive is
6,678,572 bytes; SHA-256:
`d876cfabd922eb9abdd98246aaeb70d3647f391e9d877d82e179712153cacc38`.
It contains the Windows source manifest, three actual offline training profiles
and five observer event traces. `ACTUAL_NATIVE_INDEX.json` and
`ACTUAL_NATIVE_RECONSTRUCTION.json` retain that comparison. This is packaging
proof only; the contained tests' failures remain failures.

Commands:

```sh
python3 scripts/test_package_qa_receipts.py -v
python3 scripts/package_qa_receipts.py --source /workspace/sightbreak-v1-execution/builds/mission-m1/critic-ci-39712752860 --output builds/m2-qa-receipts/actual-native.zip
python3 -m py_compile scripts/package_qa_receipts.py scripts/test_package_qa_receipts.py
git diff --check
```

The actual local ZIP remains at the output path above; the index records the exact
source directory and raw-file digests for reconstruction. The unavailable Linux
artifact was not bypassed or treated as passing. The largest remaining gap is the
new artifact's real upload/download on the next CI run, especially Linux. No
builder acceptance or platform gameplay claim is made.
