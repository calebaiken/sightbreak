# Recovery replay registration, 2026-10-24

This append-only recovery continues the independent review at own HEAD
`4e9ef3c34bbca1edb40c14e0e318cb254481825d`. Existing preregistrations
`15e82486` and `2e46306b`, controls `4e9ef3c3`, and all existing own/depth-one
stdout, stderr, identities and failures remain unchanged. Frozen candidate
`dce89495d04c9d3fefece0f8c7929e2e01b8e7df`; builder handoff
`f363e31077ad5aec79e901bff8d12bbaf9c27ddf`.

Before any new execution, register these bounded checks:

1. Verify every retained command receipt's stdout/stderr SHA-256 and record the
   original rig's corrected distinct counts. Verify both current source views,
   inventories, paths/modes/blobs against the exact candidate, original script
   identity, source erasure against Git `022d60f` and historical bytes against
   Git `0527715`. Record current shallow boundary, absent parent object,
   remote/alternate configuration and tracked/untracked source changes. A local
   shallow source repository proves this specific history-free checkout, not a
   new network clone or a different remote acquisition path.
2. Replay unchanged preregistered `fresh_controls.py` once per existing view on
   CPU 4, retaining each exact input as deterministic gzip plus stdout/stderr,
   exit and SHA-256 metadata in new `recovery-20261024/` paths. Expectations and
   mutations remain unchanged: complete positive accepts; each of twelve actual
   changed negative inputs rejects. Any accepted negative remains a finding.
   Save all 13 inputs even when the script exits 1. No fixture or reader edits.
3. Run grammar parsing of the exact two candidate GDScript files with the
   installed gdtoolkit parser, if present. Retain an unavailable parser or parse
   error as a failure; this cannot prove engine APIs/types or compilation.
4. Independently inspect emitter/reader/production source to decide which
   counterexamples are entailed by source. Report any unsupported expectation
   separately. Preserve the original rig's duplicate contradictory no-op:
   nineteen distinct inputs, one baseline plus eighteen real mutations; do not
   require its exit 1 to become 0 or count twenty distinct controls.

No new full clone. No Godot, native compilation/import/export, CI, rendering,
process inspection or Mac file-handling review. All production source is read
only. Existing retained maintained/source/original runs need no costly repeat
if their identities and raw hashes verify. Report source-only winner and largest
remaining gap; reject readiness if supported impossible receipts still accept.
No release-gate, native, API, quality or historical-cause acceptance follows.

Recovery setup observation: the sparse reviewer checkout lacks the working-tree
`correction-r2/HANDOFF.md`, so reading that path failed with `No such file or
directory`. The exact handoff was read successfully with
`git show f363e310:docs/reports/gauntlet/m5-objective-observability/correction-r2/HANDOFF.md`.
This was a source-document lookup failure, not a test pass or a changed fixture.
