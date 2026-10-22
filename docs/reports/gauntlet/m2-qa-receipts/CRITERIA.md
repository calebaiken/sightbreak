# Separately downloadable raw QA receipts

Declared before implementation, after isolation commit
`1195b23423b4cb37c613e9e0304508d4c2637aff`.

The reference failure is Linux QA artifact `12398970032` from native run
`39712752860`: the parent measured 47.9 MB, above the connector's 32 MiB download
limit. Its official CLI download redirect was denied; this work does not retry
that denied path. Existing full package and full QA artifacts must remain intact.

The component must:

1. Add one plainly scoped raw-receipts artifact. Preserve every selected JSON,
   JSONL and log file, including source identity, progression, observer and
   authoritative trace files. Preserve macOS diagnostic text. Screenshots remain
   in the existing full QA artifact.
2. Exclude native binaries, archives and cache/developer directories. Reject
   symlinked evidence. Never mutate source evidence or silently truncate it.
3. Include a sorted path, byte-count and SHA-256 index inside a deterministic ZIP.
   Exact reconstruction and digest checks must succeed.
4. Bound the single uploaded ZIP at 30 MiB, leaving 2 MiB for upload wrapper
   overhead. Exceeding the bound must fail without publishing a partial ZIP;
   existing full artifacts must still be uploaded.
5. Verify selection, native source/progression/trace bytes, reproducibility,
   oversized incompressible evidence and overwrite rejection with real files.
   Also pack and independently read an actual retained native QA directory.
6. Keep test commands, acceptance thresholds and existing artifact uploads intact.

A builder cannot accept this candidate. A fresh critic and the next native CI
upload/download must qualify the new artifact path.
