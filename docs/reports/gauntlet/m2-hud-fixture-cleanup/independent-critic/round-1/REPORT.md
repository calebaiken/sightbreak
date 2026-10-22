# Independent HUD fixture cleanup review, round 1

Candidate `b899972940f865b57cea449ff5e3c73d5a0e27bb` improves on actual baseline
`60db9ff884ad6989c6bfd87cf2fe3405505a9997`, but is **NOT APPROVED** yet. Its normal
and explicit failure cleanup works; two supported edge cases need correction.
The critic used a separate worktree and made no builder-tree edits.

The largest deficiency is receipt truthfulness at
`game/tests/hud_objective_hint_test.gd:97`. After this control renames the owned
leaf aside and replaces it with a dangling symlink, cleanup refuses and exits 2,
but emits `removed:true`. Python's independent filesystem observation records
`path_is_symlink:true` and `path_lexists:true`; the link still exists. The
implementation tests whether a directory exists, which does not establish
absence of a filesystem entry. Track successful removal and check the entry
without following links. Raw proof is `edges/dangling-leaf-symlink.log` and
`edges/edge-results.json`.

The second deficiency is the report's broad statement that linked paths fail
explicitly. A preexisting `data/SIGHTBREAK_QA` symlink to an owned control target
is followed: initialization creates the leaf below that link, cleanup removes
its marker and leaf, and the run exits 0 with no reason. The target's unrelated
`protected.txt` stays byte-identical. This proves an unhandled ancestor link,
not protected-data deletion. Reject the linked shared parent before creating
fixture state, or explicitly narrow the declared protection. See
`edges/linked-shared-parent.log` and its saved native control script.

All controls ran actual pinned Linux Godot, not mocked filesystem behavior:

| Control | Observed result |
| --- | --- |
| Actual base HUD suite | All 33 checks pass; outer namespace cleanup passes; inner owner marker remains. Critic observes the orphan after the outer context exits, then removes its exact marker and empty leaf. |
| Candidate ordinary HUD suite | All 33 checks pass; inner marker and leaf absent; original native user directory restored. |
| Existing caller profile | All 33 checks pass; profile bytes unchanged. |
| Missing source resource | Native errors and original exit 2 retained; marker and leaf removed. |
| Protected profile / changed owner / hidden protected file | Explicit refusal and exit 2; injected files and marker bytes unchanged. |
| Forced assertion failure | Original exit 1 retained; marker and leaf removed. |
| Marker symlink | Refusal and exit 2; external target bytes and link preserved. |
| Leaf symlink to existing held directory | Refusal and exit 2; held marker and link preserved. |
| Dangling leaf symlink | Refusal and exit 2; held marker and link preserved; **false `removed:true` receipt**. |
| Unwritable leaf | Marker removal error retained, marker unchanged, original exit 1 preserved. |
| Linked shared parent | Exit 0, created leaf cleaned beneath the link, link and protected target sentinel unchanged; **ancestor link not refused**. |

Both candidate runners and the baseline runner report unchanged source and
copied resource inventories, removed temporary projects, and removed owned outer
namespaces. Refusal controls record observations before their later teardown,
which unlinks only the exact injected paths in the critic's isolated state.
The caller profile sentinel remains unchanged throughout the edge controls.

The six-control script's `standard-wrapper.log` exits 0. The independent edge
harness completes all native controls, writes `edges/edge-results.json`, and
finishes runner cleanup, then its final summary print raises a reviewer
`AttributeError` on the boolean summary field. `edges-wrapper.log` and the exact
executed `extra_controls.py` retain that failed harness iteration. No native
control is relabeled by that error; native results and filesystem observations
were written first. The defect is in the critic's terminal summary print.

The builder's 36 recorded candidate/evidence SHA-256 entries match their files;
the archived baseline fixture matches `git show 60db9ff:game/tests/hud_objective_hint_test.gd`.
Source review confirms all existing 33 HUD assertions, progression guards,
timeouts, and shipping resources remain intact. Cleanup only unlinks the marker
and removes an empty leaf. Removing a hardlinked marker name would leave other
names and bytes intact. Static check/use races remain possible for a concurrent
same-user writer because these path checks and unlinks are separate operations;
no concurrent-writer resistance or practical protected-data deletion is proven.

The comparison is labeled because cleanup behavior and source paths reveal the
implementations. It is a regression comparison against the actual base, not a
blind visual or shipped-game comparison. Windows/macOS execution of the fix is
unverified, including the original ARM platform. Controlled exits do not prove
cleanup after timeout, crash, or hard process kill. No product acceptance gate
is closed by this fixture review.

Commands were run in `/workspace/reviews/hud-fixture-cleanup-critic` with
`SIGHTBREAK_TOOLS_DIR=/workspace/tools` and distinct `SIGHTBREAK_STATE_DIR`
paths under that worktree's `.local/`:

```sh
python3 scripts/test_hud_fixture_cleanup.py --output builds/independent-hud-cleanup/standard
python3 builds/independent-hud-cleanup/extra_controls.py
```

The baseline control runs `baseline_control.py` with its import pointing to the
separate detached baseline worktree. `IDENTITIES.json` records exact source
identities and raw artifact digests. Root has been sent both counterexamples
for a separate builder correction and fresh independent re-review.
