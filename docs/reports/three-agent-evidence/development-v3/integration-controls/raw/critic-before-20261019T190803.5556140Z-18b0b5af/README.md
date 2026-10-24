# Retrospective preservation of the pre-fix critic review

## Status and provenance

- This is a **new external evidence directory**, created at `2026-10-19T19:08:03.5556140Z`. That is the preservation time, **not** an original test execution time or a source freeze time.
- The review and commands/tool outputs are transcribed from the conversation's retained tool calls and results. Original terminal transcript files were not created during those runs. Native stdout and stderr were not separately retained.
- **No controls have been rerun for this preservation request.** No actively changing source files have been read for replay, edited, or committed.
- The original temporary fixture directories were cleaned up by `TemporaryDirectory` and are **unavailable**. Their original fixture files, ZIP archives, result JSON files, timestamps, and hashes were not retained; none are recreated or represented as original receipts here.
- Original pre-fix working-tree byte hashes and a real `build_manifest.source()` receipt were **not collected**. The control snapshots named `A`, `B`, `TREE`, and `BYTES` were explicit mock values, not Git identities or measured hashes.
- The original review did retain a tracked-file diff, the new workflow's full text, and immutable Git index blob IDs. These are preserved under `sources/`. Any recovered baseline bytes come from those exact immutable object IDs, never from the current working tree.
- Any reconstructed reviewed source is explicitly **Git-normalized/derived**, not a byte-exact capture of the original working tree. Original reads/diffs warned about CRLF conversion, so original working-tree bytes cannot honestly be recovered from rendered text alone.
- Archived `.ps1` commands preserve their **original** dynamic working-directory behavior. They are provenance, not a safe replay launcher for the live checkout. **Do not run them against actively changing source.**

## Seven negative controls

| Control | Original command/output | Observed outcome | What is missing |
| --- | --- | --- | --- |
| Old outputs re-attested as another commit | `commands/02-seven-negative-controls.ps1`, `outputs/02-seven-negative-controls.tool-output.txt` | Isolated fixture reproduced successful packaging under B with unchanged A artifact bytes | Original temp fixture/ZIP and a contemporaneous receipt/hash |
| Executable wrapper permissions stripped | Same command/output | ZIP entry for fixture `sightbreak.sh` was `0644` after input was made executable | Original temp fixture/ZIP |
| Failed re-verification leaves old success JSON | Same command/output | Mocked current failure raised while earlier `passed: true` survived | Original temp JSON/log |
| Timeout loses current output and retains old log | Same command/output | Injected `TimeoutExpired` left prior log unchanged | Original temp log; separate native stdout/stderr |
| Payload mutation after validation is accepted | Same command/output | Injected secondary-payload change appeared in successful ZIP while receipt disagreed | Original temp payload/ZIP |
| Project/manifest version mismatch | Same command/output | Read `0.3.1-dev` in project versus `0.3.2-dev` in manifest | Original working-tree byte hashes |
| Living-HUD check accepts blank/zero-health OCR | Initial attempt above; corrected in `commands/03-hud-corrected-plus-baseline.ps1`, `outputs/03-hud-corrected-plus-baseline.tool-output.txt` | First harness attempt had a missing `args` test stub; corrected isolated function control accepted both blank and `000 HEALTH` status with `12 / 60` ammo | Original temp artifacts; no real OCR/native-game observation |

Six controls reported `ok` in command 02. The seventh initially errored because of the control harness itself, and then reported `ok` after its stub was corrected in command 03. These tests intentionally assert the observed undesirable behaviors; their `ok` output is **not** evidence that production behavior is correct.

The wrapper control called `chmod(0o755)` on Windows but did not assert the source file's resulting POSIX mode or execute the wrapper. It verifies the ZIP entry's forced `0644` metadata, **not an observed Linux launch failure**. The original fixture's actual mode is unavailable.

## Unit-process caveat

The maintained suite reported all 18 cases `OK`. The explicit exit capture in command 04 then reported `PYTHON_EXIT_CODE=-1073741819` (`0xC0000005`); the shell tool reported code 5. Earlier tool results reported nonzero tool exits without explicitly recording the Python-native exit. Consequently, **no clean native unit-test process pass is claimed**.

## Contents

- `REVIEW.md`: verbatim substantive review returned to the author, saved retrospectively.
- `commands/`: original executed PowerShell command strings, including both HUD harness versions.
- `outputs/`: retained tool-visible outputs, including harness errors and nonzero exits. These are transcriptions of tool results, not recovered terminal files.
- `sources/observed-working-tree.diff`: the pre-fix diff retained in the conversation (excluding warning preamble, saved separately).
- `sources/observed-new-v3-development.yml`: full new-workflow text retained in the conversation.
- `tools/capture-source-evidence.ps1`: preservation-only helper; accesses only the explicitly recorded immutable Git blobs, reconstructs source solely in this external directory, and records provenance/hashes. It does not execute controls.
- `sources/immutable-baseline/`: exact Git blob bytes, if recovery succeeded.
- `sources/reconstructed-reviewed/`: derived Git-normalized reviewed source, if reconstruction succeeded. **Not original working-tree byte captures.**
- `sources/source-evidence.json`: immutable IDs, recovery/reconstruction status, and appropriately labeled hashes.
- `capture-source-evidence.log`: output from the new preservation-only helper, not an original test log.
- `SHA256SUMS.txt`: integrity hashes of saved evidence; created now, not contemporaneous execution receipts.

The reconstructed tree is a scoped source subset with selected supporting scripts, not a full checkout, engine installation, or exported build.

No Godot, exported client, GitHub write, human/device acceptance, 74-group campaign, or 12-condition campaign was executed or certified by this critic.
