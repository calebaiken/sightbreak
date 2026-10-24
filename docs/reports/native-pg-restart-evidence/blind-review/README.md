# Independent PostgreSQL outcome review

These are the independent critic's original frozen files, copied byte-for-byte.
The verdict was frozen before identity or source access and recorded in
[PR18 comment 6355013968](https://github.com/calebaiken/sightbreak/pull/18#issuecomment-6355013968).

- **Outcome:** Set-8F5F7604 wins, 3/3 exact recoveries versus 0/3.
- **Audit:** all 122 packet payloads, six cases, 30 SQL stages and 2,078 consistency
  checks pass. Both arms settle each original purchase once; the winner also
  recovers its exact receipt and full result.
- **Remaining question:** blind observations alone cannot establish the recorder's
  authenticity or exclude fixture-assisted recovery. Exact-source/API binding is
  being reviewed separately, followed by a narrow recovery-input absence control.

`_FROZEN_VERDICT.md` is the full independent verdict, not a parent-written summary.
Its SHA-256 is
`750bfb02e65f3f348567b8bf453b4387f931c70549d7c50469d377fc63bec2ee`.
`sha256.json` binds the verdict, audit script and audit output. Scoped `-text`
preserves their original bytes.

To reproduce the offline audit, extract the adjacent `blind/packet.zip` into a new
scratch directory, copy `_independent_audit.py` into that extracted root, and run
`python _independent_audit.py` there. It reads the supplied observations and writes
its audit output in that directory; it does not run Godot, HTTP or PostgreSQL.

The original frozen packet and verdict remain unchanged by subsequent provenance
inspection or additional experiments. This is evidence for the declared stable
postcommit/direct-method crash boundary, not manual UI, arbitrary instruction-window
or power-loss qualification.
