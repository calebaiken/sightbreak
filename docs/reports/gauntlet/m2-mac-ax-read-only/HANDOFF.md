# Read-only AX implementation checkpoint

Status: **SOURCE CANDIDATE; final exact-source/depth-one replay pending the reserved Linux CPU lane**. No source approval, Apple compile, native API/OCR/engine execution or CI release is claimed. Root explicitly reserved the local CPU lane for its fixed Linux OFF/ON/ON/OFF acquisition after the completed pure replay below. Do not run the pending clone/tests until root releases that lane.

## Implemented component

- `scripts/probe_macos_ax.py`: public ApplicationServices ctypes observer, own PID and unique pinned visible layer-zero CG window, actual observer trust query without a prompt, three snapshots maximum within 5s, cumulative 256 nodes/depth 16, 0.25s AX messaging timeout, bounded child-array reads, 512-byte title cap, and 512 KiB receipt ceiling. Per-call guards reject late returns/current-window changes. It prunes text-entry/secure/search-field subtrees, reads titles only for semantic buttons/owned windows, and never reads AXValue/text/help/account fields or invokes an action/attribute setter/event API. AXValueGetType/GetValue are only the public CGPoint/CGSize geometry decoder, not AXValue attribute reads.
- `scripts/macos_ax_contract.py`: separately validates request/trust/time, full bounded tree/privacy provenance, unique semantic Deploy title/role/enabled frame and original native menu/text-box agreement. Only whitespace and observed middle-dot/bullet equivalence normalize the exact word sequence. It returns exposure metadata, never a click point or gameplay target. Original low-confidence native rows remain unchanged and still reject the ordinary 0.8 selector.
- `scripts/macos_ax_appkit.py`: a separate adapter exposing the declared single public AppKit focus request and ordinary termination, with static class/selector allowlists and no event allocation/posting. Window geometry pins once after fresh focused pixels; current rows are retained on every controller guard.
- `scripts/verify_macos_ax_read_only.py`: source/export/PCK/staged payload/helper/interpreter attestation, actual HOME and original no-symlink/default/private isolation, unchanged original budgets, capture helper defaults/raw Vision JSON, one permanent window pin, nested AX deadline, byte/hash/freshness binding, ordinary close and strict owned-group/log/source/payload/default-userdata finalization. Its sole engine amendment is `--accessibility always` before the original `--` separator. Private menu-created files are preserved and inventoried by byte hash; profile/account fields are not parsed or retained. Any match trace is a failure; no Deploy/reward input is sent.
- `.github/workflows/desktop-alpha.yml`: adds only the explicit `arm-macos-ax-read-only` choice, excludes that choice from the original normal native job, and appends a separate `macos-15` diagnostic-only job. A checked-in exact original workflow fixture verifies the normal job/matrix/steps remain unchanged apart from that exclusion. The new job runs pure controls, pinned setup, exact export, the read-only probe and evidence retention. It cannot fall through to input, ordinary gameplay, strict suites, unrelated diagnostics or iOS. This diagnostic does not qualify any omitted full-lane gate.

All original game, audio, gameplay, economy, authority, existing capture/selector/HUD/controller and strict-suite source remains unchanged. Eight source-bound original helper/runtime hashes and the original workflow are checked-in fixtures available in a shallow checkout. The original b294ef9 research report and all earlier native/source failures remain intact.

## Completed pure results and retained failures

The completed pre-freeze replay, [pre-freeze-pure.log](receipts/pre-freeze-pure.log), passes **12 commands / 110 top-level methods**: 27 new methods and 83 original Mac methods. Aliased-temp tests also replay their respective child suites. All processes in these tests are synthetic mocks or Python pure controls; none is a native engine/capture/AX observer execution. [structural-expanded.log](receipts/structural-expanded.log) and [controller-second.log](receipts/controller-second.log) retain prior completed new-control runs.

The first structural run had two positive-fixture errors: reused owner 123/bounds y32 did not match the new synthetic owner 12/bounds y60; the fixture was corrected, retaining [first-pure.log](receipts/first-pure.log). Negative controls were then rerun with the valid positive fixture. The first original replay also retained seven missing sparse screen-identity fixture errors in [original-mac-pure.log](receipts/original-mac-pure.log). Exact tracked `docs/reports/gauntlet/m2-macos-screen-identity/fixtures` were restored without source changes; [original-screen-restored.log](receipts/original-screen-restored.log) passes all seven and the complete later replay passes all 83 original methods. These setup/fixture failures are not relabeled native observations.

After that completed 110-method run, the explicit pruned-role list was conservatively expanded to include secure/search field role spellings and its matching pure loop. That final source delta has **not** yet been replayed. Root's CPU reservation then blocked further expensive testing and the required exact depth-one clone. This checkpoint must not be treated as fully validated on its final bytes.

## Pending exact-source checks after root releases CPU

Run these source/pure commands from a fresh exact depth-one sparse clone of this branch/ref, retaining new raw outputs and `git rev-list --count HEAD` (must be 1), exact HEAD and clean status. Do not increase workflow fetch depth. Include the two existing fixture directories named above and `docs/reports/gauntlet/m2-mac-derived-ocr/original-native-39912086121/macos-ordinary-input` in the sparse clone. No historical Git comparison is part of the maintained checks.

```sh
python scripts/test_macos_ax_read_only.py -v
python scripts/test_macos_ax_controller.py -v
python scripts/test_macos_ax_paths.py -v
python scripts/test_probe_macos_input.py -v
python scripts/test_macos_menu.py -v
python scripts/test_macos_focus.py -v
python scripts/test_macos_screen_identity.py -v
python scripts/test_macos_ordinary.py -v
python scripts/test_macos_ordinary_controller.py -v
python scripts/test_macos_ordinary_paths.py -v
python scripts/test_macos_ordinary_startup.py -v
python scripts/test_macos_deploy_ocr.py -v
```

Retain a source audit of unchanged original runtime/game files and exact normal workflow preservation; then freeze/push the tested source identity and send the raw outputs to a fresh independent critic. Root must review/bind any combined workflow ref before separately releasing the diagnostic-only ARM lane. No dispatch is authorized by this handoff.

The largest remaining uncertainty is the actual exported AX tree, TCC trust of this new observer, public AX/native frame agreement and completion within the fixed 5s collection budget. Source/pure observations prove none of these. An unexpected serialized-size invariant failure refuses to write a truncated substitute; the controller retains failure logs/native captures/CG guards and cannot qualify an absent AX receipt. A real unavailable/busy/ambiguous/late tree must remain failed evidence. No OCR confidence improvement, semantic gameplay targeting, ordinary Deploy/fire/reload/leave, Intel/physical/human or release acceptance is claimed.
