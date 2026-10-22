# Independent HUD fixture cleanup review, round 2

**APPROVED for the bounded controlled-exit Linux fixture correction** at
`2b06960d3ce05e137cea83b18edf686cc337730b`. This candidate wins against the actual
`60db9ff` baseline: it removes the orphan on normal and failed controlled exits,
keeps the original 33 HUD assertions and progression guards, restores the
caller's native directory identity, and preserves unexpected state on refusal.
The original `b899972` rejection and counterexamples remain in `../round-1/`.
Root built the revision; this independent critic used a separate clean detached
worktree and did not edit either builder tree.

Both supported first-round deficiencies are fixed in actual native output:

| Edge | Rejected candidate | Corrected candidate |
| --- | --- | --- |
| Dangling leaf symlink | Refuses exit 2 while falsely reporting `removed:true`; symlink remains. | Refuses exit 2 and reports `removed:false`; symlink and held marker remain unchanged. |
| Linked shared `SIGHTBREAK_QA` parent before initialization | Follows the link, creates and removes the leaf below it, exits 0. | Explicitly refuses creation, exits 2 with `owned:false` and `removed:false`; target sentinel and parent link remain unchanged. |

The implementation now records removal only after successful empty-leaf removal
and an entry-aware absence check. It checks the `SIGHTBREAK_QA` child for a link
before creation and again before cleanup. It continues accepting the operating
system's native data root, whose own path may legitimately contain links.

The critic independently reran all six standard controls and all six original
edge controls on pinned actual native Linux Godot. The ordinary suite and
caller-profile suite each report `checks=33 failures=0`. Missing-source exit 2
and forced-assertion exit 1 survive successful cleanup. Protected profile,
changed owner, hidden file, marker link, and leaf link all refuse while retaining
their bytes or links. An unwritable owned leaf preserves its marker and the
original exit 1. Every native cleanup receipt restores the original native
user directory. Caller-profile sentinels stay byte-identical.

Two additional actual native controls pass:

- Replacing the owned leaf with an unrelated regular file causes an inspection
  failure and exit 2, reports `removed:false`, and preserves that file's bytes
  and the held original ownership marker.
- Replacing the shared parent with a symlink after initialization causes cleanup
  to refuse with the linked-namespace reason. The target sentinel, link and held
  original marker remain unchanged; original exit 1 stays exit 1.

`standard/`, `edges/` and `additional/` retain native logs, scripts, producer
receipts, independent filesystem observations and runner finalization reports.
All three runners report unchanged source and copied resources, removed owned
outer namespaces and removed temporary projects. Every wrapper exits 0. The
second-round edge harness fixes only the first-round critic's final summary
print and tightens the two counterexample assertions to require the corrected
behavior. Refusal observations are saved before exact known-file teardown.

The frozen source checkout remains clean at the reviewed commit after the runs.
The actual fixture bytes match that commit, and `IDENTITIES.json` records its
game tree, fixture hash and retained raw artifact digests. Python compilation
and `git diff --check` also pass. Retained native probe logs intentionally keep
their original trailing blank lines.

The remaining largest qualification gap is actual corrected Windows/macOS
execution, especially the ARM platform where the orphan was first observed.
These Linux controls do not establish that acceptance. Cleanup still cannot run
after a hard process kill or crash. Separate path checks and removal calls do
not provide atomic protection against a concurrent same-user filesystem writer;
the revision criteria correctly limit this to cooperative local fixtures.
No supported regression or protected-data deletion was observed, and no product,
visual, gameplay, device or release gate is closed by this review.

The comparison remains labeled because the behavior reveals each implementation;
the actual native baseline is retained in round 1. All controls ran from
`/workspace/reviews/hud-fixture-cleanup-revision` with
`SIGHTBREAK_TOOLS_DIR=/workspace/tools` and distinct state directories under
that worktree's `.local/`:

```sh
python3 scripts/test_hud_fixture_cleanup.py --output builds/independent-hud-cleanup/standard
python3 builds/independent-hud-cleanup/extra_controls.py
python3 builds/independent-hud-cleanup/additional_controls.py
```

The two archived Python harnesses are the exact executed second-round versions.
No maintained assertion, timeout, shipping setting, presentation or gameplay
source changed during the independent tests.
