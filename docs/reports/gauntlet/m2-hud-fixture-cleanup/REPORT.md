# HUD fixture cleanup candidate

The baseline passes its HUD assertions but leaves a private native directory
outside the source-suite runner's cleanup scope. The ARM Mac log from
[run 39719407304](https://github.com/calebaiken/sightbreak/actions/runs/39719407304)
identifies `SIGHTBREAK_QA/hud-objective-hint-2472-215773`. Its fixture source matches
the task base `60db9ff884ad6989c6bfd87cf2fe3405505a9997` byte-for-byte. The actual
ARM source receipt and HUD log are retained in `evidence/arm-ci/`.

A local native baseline reproduces the orphan directly: the suite exits 0 with
33 checks passing, the runner removes its outer namespace and reports clean
cleanup, but the inner directory still contains `hud-fixture-owner.txt` with the
fixture's exact owner name. `evidence/baseline/orphan-observed.json` records this
filesystem observation before the control removes its own marker and empty leaf.

The candidate routes every explicit fixture exit through one finalizer. It verifies
the native path and ownership marker, lists hidden files too, removes only the
matching marker and its now-empty leaf directory, and restores the original native
user-directory settings. It never recursively removes fixture contents or the
shared `SIGHTBREAK_QA` parent. Unexpected files, changed ownership, linked paths or
removal errors fail explicitly. An existing nonzero test result remains nonzero;
a cleanup error changes an otherwise successful result to exit 2. The receipt
records the native path, removal outcome, restored identity and final exit.

All six native controls pass on Linux with pinned
`4.7.2.stable.official.ed1daf0bf`:

| Actual native control | Result |
| --- | --- |
| Ordinary HUD suite | All 33 checks pass; marker and inner leaf removed; original identity restored. |
| HUD suite with an existing caller-profile sentinel | All 33 checks pass; sentinel unchanged; marker and inner leaf removed. |
| Missing main-source resource | Actual native errors and exit 2 retained; marker and inner leaf removed. |
| Protected save in the inner fixture | Fresh-save guard exits 2; cleanup refuses deletion; profile and ownership marker unchanged. |
| Changed ownership marker | Cleanup exits 2 and leaves its changed bytes untouched. |
| Hidden protected file | Cleanup exits 2 and preserves both the hidden file and ownership marker. |

The caller-profile sentinel is in the unique runner-owned startup directory, so
the control never edits an ordinary application profile. Its SHA-256 remains
`7f398b4b44e648267160e5acdc56a02bab2f3a3868780b8c549f328d855d1293`
through the successful HUD run and every negative control. After retaining the
three refused-cleanup observations, the controls remove only their known injected
files from their verified unique leaves. This later teardown does not relabel the
fixture's refusal as successful cleanup. Outer namespace and temporary-project
cleanup also pass; source and copied resource inventories remain unchanged.

```sh
SIGHTBREAK_TOOLS_DIR=/workspace/tools SIGHTBREAK_STATE_DIR=/workspace/sightbreak-hud-fixture-cleanup/.local/candidate-final python3 scripts/test_hud_fixture_cleanup.py --output builds/hud-fixture-cleanup/candidate-final
python3 -m py_compile scripts/test_hud_fixture_cleanup.py
git diff --check
```

`evidence/candidate/` retains native logs, control scripts, producer receipts and
filesystem assertions; `IDENTITIES.json` records source and evidence digests.
Raw logs preserve their trailing blank lines. No HUD expectations, progression
guard, shipping setting, gameplay behavior or watchdog changed.

This is a builder candidate for a fresh critic. Windows/macOS execution of the
correction remains unverified. The tests cover controlled native exits; they do
not establish cleanup after a hard process kill. No visual or gameplay acceptance
gate is closed by this fixture correction.
