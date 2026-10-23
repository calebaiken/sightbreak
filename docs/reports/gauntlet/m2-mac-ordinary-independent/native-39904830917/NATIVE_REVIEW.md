# Independent first ARM iteration review

Verdict: **FAIL for the new ordinary gameplay component** in run
[`39904830917`](https://github.com/calebaiken/sightbreak/actions/runs/39904830917),
job `120254254021`, at exact source
`34dbd97a99068642cf07fa62288fe7437751c37e`. Its source controls failed before
the actual ordinary controller or stock Deploy step ran. Completed native
regression, menu and unsigned iOS compile evidence has the narrower passing
scope below. This does not make the failed job or ordinary component pass.

Step 24 ran 14 helper tests and emitted four errors. The original tracebacks
reject `/var`, an ancestor symlink in test-owned TemporaryDirectory paths, in:

- `test_default_userdata_rejects_symlinked_ancestors_and_tracks_file_modes`
- `test_non_native_host_never_compiles_or_launches`
- `test_private_userdir_requires_native_log_and_unchanged_default_directory`
- `test_staged_native_bytes_modes_and_only_two_setting_overrides`

The second source-control command did not run after the first command's nonzero
exit. The workflow skipped actual stock Deploy/living fire/reload/leave. No
`macos-ordinary-input` directory or native ordinary receipt exists in either
bounded artifact. The production path guard rejected the test fixture; this run
does not establish a production isolation failure. The independently reviewed
test-only correction has a separate verdict at `3730273` and does not rewrite
this failed iteration.

Both bounded artifacts were independently retrieved through the GitHub
connector. Their outer ZIP SHA-256 values match GitHub's published digests:

| Artifact | ID | SHA-256 |
| --- | --- | --- |
| Raw QA receipts | `12480985853` | `25cc999505a6a34bef8ae524fada94e9cfc047483a831c69eaab445046212051` |
| QA logs/receipts/original PNGs | `12480557724` | `6b269301285cac52b2bb0caf86a4340a8ed14fec1eddfb02fba7d7fb1d7f793b` |

The complete decoded original job log and both original ZIPs are retained here.
The inner receipt index verifies all 198 files; 196 files also present in the QA
artifact match byte-for-byte. The read-only audit passes 618 predicates covering
source/artifact receipts, inventories, native outcomes, original pixel hashes,
profile/release/cleanup receipts and stage bounds. It does not run Godot, a
compiler, native input or OCR. `audit_native.py` and `audit.json` retain the checks.

All completed native evidence binds the combined game tree
`55691684d31d44f1680141954bbe530443de9d1f`, content hash
`bcb872f6998ed8504c852dee354ab0acf5b6f19e58e40717267a1927e6d68a50` and
validation hash
`408ff238275cea29a466ed5b99c03f82ee8d1d18205100fe158d07bda0251671`.
The recorded Mac executable/PCK hashes are respectively
`9752120d0ab1b861730307427bcabbd0fbabae515b859cd2f290cfed793eae50` and
`db0aad30417a69d9e9bc5a7bbc171efe1f9f03090eaf960fcd82b4cfd4349894`.
The large development bundle was not transferred or independently reparsed.

| Completed native output | Independent scoped finding |
| --- | --- |
| Default exported startup | Clean headless/menu/demo exits; native package inspection reports 134 resources. Original graphical menu PNG inspected. |
| Maintained source suites | 15 suites, 9,434 reported checks, zero failures, all exits zero within 120 seconds. Exact 323-file game inventory matches the frozen source; 30 before/after producer receipts preserve fresh per-suite userdata. Temporary project and owned user namespace removal are recorded. |
| Dry-primary fixture | Actual 84 cases / 48 steps / 590 checks. Accepted observable recomputer rerun against this ARM log passes 1,974 predicates; unlogged protected snapshots remain outside that recomputation. |
| Transaction journal / gunplay | Actual competing process reports OWNER_BLOCKED with unchanged journal; 52 gunplay records and 2,840 reported checks, zero failures. |
| Read-only input preflight | 6.864 seconds, PID 4355, all required permissions true, no posted events or requests, exit zero and owned group gone without signals. |
| Actual Settings/Escape menu | 39.591 seconds, PID 4737 / window 45, five CGEvent posts and acknowledged down/up states. Original foreground PNGs show home, FIELD SETTINGS and returned home; the background PNG shows the engine splash and authorizes no input. |
| Menu mapping/cleanup | Full-window 960x568 pixels at scale 1 with bounds [40,32,960,568]. Original SETTINGS target recomputes to [307.9310,478.1382] points. Neutral owned controls, AppKit termination, exit zero and all six owned groups gone without signals. Source/profile entries preserved; normal cache/log side effects remain retained. |
| Graphical diagnostics | Five clean bounded default-renderer startup trials; all five original PNGs inspected. Minimal 3D controls show a cube; current/frozen game captures show menus. These are startup comparisons on a hosted ANGLE/Apple Paravirtual renderer. |
| Unsigned iOS compile | 88.643 seconds total; actual Xcode device build succeeds in 50.141 seconds. All 15 command groups report no live survivors, timeout or cleanup error. Unsigned arm64 device-app/PCK/134-resource inspection is natively attested; codesign's expected exit 1 says the app is unsigned. No final binary reparse, installation, simulator or physical-device claim. |

All 11 original PNGs were visually inspected. A strict scan of all 135 retained
QA logs finds no native error/resource-leak signature. Source-suite resource and
namespace cleanup receipts do not independently establish escaped-descendant
coverage; menu/iOS group receipts establish their recorded narrower cleanup.
The iOS source-before and source-after records are clean and identical.

The largest actual gap remains the entirely unexecuted ordinary component:
the exact copied app's private userdata route, stock Deploy, living authoritative
fire/reload pixels, FIELD MENU/LEAVE and ordinary close have no actual result in
this iteration. No later source or aggregate can inherit this source's native
evidence. A fresh source-bound attempt and independent original-output review
are required to judge those gates.
