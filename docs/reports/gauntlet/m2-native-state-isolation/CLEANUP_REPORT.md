# Cleanup receipt correction candidate

Independent critic `/root/native_isolation_critic` found a P2 false passing receipt
on `1195b23423b4cb37c613e9e0304508d4c2637aff`. After a real native success, an
injected namespace cleanup `PermissionError` failed the process but left
`isolation.json` saying `passed=true`, `failure=null`, `cleanup=[]`. The owned
namespace remained. The critic's original control and observation are retained
unchanged in `evidence/cleanup-critic-before/`.

The follow-up starts finalization with a failing state and records every registered
namespace before attempting removal. Inventory, namespace and temporary-project
errors are recorded separately; each remaining cleanup is still attempted. A
passing result requires a nonempty, complete namespace cleanup and verified
temporary-project removal. The original native exception remains the primary
propagated failure when finalization also fails. The JSON receipt is published
atomically after finalization. Suite execution, source identity, save guards and
watchdogs are unchanged.

`scripts/test_native_suite_cleanup.py` runs the actual native peer-lifecycle suite
(16 checks, no failures) before each scoped fault injection. All five controls
passed on Linux with Godot `4.7.2.stable.official.ed1daf0bf`:

| Control | Observed receipt and exception |
| --- | --- |
| Normal success | `passed=true`, one removed namespace, temporary project removed, no error. |
| Namespace cleanup denied | `passed=false`, attempted namespace removal records its PermissionError, namespace remains, temporary project removed; PermissionError propagates. |
| Temporary cleanup denied | `passed=false`, namespace removed, temporary removal false with PermissionError; PermissionError propagates. |
| Source inventory read denied | `passed=false`, inventory error recorded, both cleanup operations complete; PermissionError propagates. |
| Native and cleanup failures | A real external Godot control emits an ERROR and exits 9. The wrapper's original RuntimeError object propagates unchanged, `passed=false`, and the additional namespace PermissionError remains in the receipt. Temporary project removed. |

The controls retain these failed receipts before explicitly removing only their
own remaining resources. Every control's final teardown verified removal. A
cleanup failure is never relabeled successful by the control's later teardown.
All raw native outputs, commands, path receipts and failed/passing finalization
records are retained in `evidence/cleanup-candidate/`. `CLEANUP_IDENTITIES.json`
records the baseline, candidate file hashes and raw evidence hashes.

Commands:

```sh
SIGHTBREAK_TOOLS_DIR=/workspace/tools SIGHTBREAK_STATE_DIR=/workspace/sightbreak-ci-isolation/.local/cleanup-controls python3 scripts/test_native_suite_cleanup.py --output builds/m2-isolation/cleanup-controls
python3 -m py_compile scripts/run_native_regressions.py scripts/test_native_suite_cleanup.py
git diff --check
```

The whitespace check covers code and authored documentation; raw logs preserve
their original trailing blank lines. This is a builder candidate for the critic's
re-review. Actual Windows/macOS source-suite qualification and new compact-artifact
upload/download remain pending. These controls establish no gameplay release gate.
