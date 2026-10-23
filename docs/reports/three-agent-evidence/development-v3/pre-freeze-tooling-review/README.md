# Final pre-freeze tooling review receipts

These are **pre-freeze pure/synthetic controls and source reviews**, not native
matrix/campaign, audio acceptance, export or device results. Original attempts
remain unchanged at the origins recorded in `COLLECTION.json`.

- The first serial attempt (`201117`) failed two OCR checks after Windows
  standalone dead-root cleanup became truthfully unverified. It is retained.
- The OCR path was moved into the shared prelaunch containment boundary, using
  a streaming I/O worker. Its new actual-CPython late-descendant control rejects
  a root exit of zero while stopping the descendant; it is not a game run.
- The fresh `201340` serial attempt has **272 normal tests plus 74 optimized
  artifact-verifier executions**, all actual exits zero, with unchanged source
  hashes before/after. Both raw logs and the previous failed batch are included.
- Final cleanup controls contain **17 process plus 60 harness/source/campaign
  tests**. Exceptional Linux supervisor death may still leave detached children
  reparented elsewhere. Missing cleanup attestation is a failure, not proof of
  durable recovery; no broad unrelated-process scan/kill was introduced.
- The audio source critic ran **32 maintained tests plus nine guarded probes**
  and found no verified scoped false-pass blocker. It did **not** execute Godot.
  The native broad baseline and A5/A6/A7 captures must still run on frozen source.

Only regular root files from audio/CI critique directories are selected to avoid
republishing hundreds of synthetic fixture artifacts. Their original manifests,
failures and source hashes are retained; omissions are explicit in the collection.
The collection-time source comparison is a later read-only witness, not a new
test execution or a retroactive change to the October 19 receipts.

`SHA256SUMS.txt` covers every published file except itself. Raw bytes are protected
from Git newline conversion. No human, physical-device, production or 8.5 gate is
waived by a tooling assertion count.
