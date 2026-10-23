# M2 source-test state isolation

Declared before implementation on `6a0d8d5d85b4fb37943903886982f51b4ed230b0`.
Builder: `/root/branch_recon`. Independent acceptance belongs to a separate critic.

The reference is the actual [native CI run 39712752860](https://github.com/calebaiken/sightbreak/actions/runs/39712752860),
ARM Mac job `119607694324`. Its retained artifact `12397669289` has SHA-256
`9ae670e01ef433fbedb585d12b23c327cfaba22d92e742dd56d28c35f7f1b64b`.
The inspected raw logs show input-mode 31/31 passing, followed by menu-focus exit 2:
`Use a fresh isolated state directory; player saves are never overwritten`.
This is a state-isolation failure, not a failed menu-focus assertion.

| Component | Required evidence |
| --- | --- |
| Reproduction | The same input-mode → menu-focus sequence fails when the actual Godot producer shares one user directory. Retain the positive first suite and exact second-suite failure. |
| Native identity | Each source suite uses a fresh custom-user-directory identity on a temporary project copy. The engine itself reports the actual producer path and selected identity before and after each run. |
| Resource preservation | Original game/config/script/asset bytes remain unchanged. Original resources in the copy remain unchanged; only its startup user-directory identity differs. |
| Save safety | An existing save is rejected rather than overwritten. A sentinel at the ordinary application save path remains byte-identical while the three isolated suites execute. |
| Genuine coverage | Input-mode, menu-focus and offline-diagnostics run with their existing assertions and unchanged 120-second suite watchdog. Check actual exits and native errors, not a wrapper's final status alone. |
| Cleanup | Remove only the unique runner-owned user-data namespace and temporary project. Retain raw logs, actual produced-file hashes and cleanup receipts. Never repurpose HOME or edit the shipping project config. |
| CI integration | Replace the current shared-state block with the same suite list and failure policy. Windows and macOS execution remain pending until actual native-host CI results exist. |

Setup has a bounded 120-second import watchdog. Each probe has a 30-second
watchdog. Record elapsed times as source-test execution cost, not game performance.
No gameplay, visual-quality or release gate can be closed by these source tests.
