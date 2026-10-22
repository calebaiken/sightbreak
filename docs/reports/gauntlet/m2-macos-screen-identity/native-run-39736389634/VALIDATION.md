# Read-only replay and check limits

Run from the repository root. All scripts read retained originals and immutable
Git objects; they invoke no implementation, engine, compiler, native API or OCR.

```sh
python docs/reports/gauntlet/m2-macos-screen-identity/native-run-39736389634/recompute_source.py /workspace/sightbreak-mac-menu-native-review --output /tmp/mac-identity-source.json
python docs/reports/gauntlet/m2-macos-screen-identity/native-run-39736389634/audit_receipts.py docs/reports/gauntlet/m2-macos-screen-identity/native-run-39736389634/receipts --checkout /workspace/sightbreak-mac-menu-native-review --source /tmp/mac-identity-source.json --output /tmp/mac-identity-suites.json
python docs/reports/gauntlet/m2-macos-screen-identity/native-run-39736389634/audit_focus_sequence.py docs/reports/gauntlet/m2-macos-screen-identity/native-run-39736389634/full-qa --output /tmp/mac-identity-focus.json
python docs/reports/gauntlet/m2-macos-screen-identity/native-run-39736389634/audit_screen_roles.py docs/reports/gauntlet/m2-macos-screen-identity/native-run-39736389634/full-qa --output /tmp/mac-identity-screens.json
python docs/reports/gauntlet/m2-macos-screen-identity/native-run-39736389634/audit_diagnostic_selection.py docs/reports/gauntlet/m2-macos-screen-identity/native-run-39736389634/full-qa --source /tmp/mac-identity-source.json --output /tmp/mac-identity-diagnostic.json
python docs/reports/gauntlet/m2-macos-screen-identity/native-run-39736389634/audit_native_outputs.py docs/reports/gauntlet/m2-macos-screen-identity/native-run-39736389634 --source /tmp/mac-identity-source.json --output /tmp/mac-identity-native.json
```

Observed audit results: 80 indexed original receipts match, all 307 resource
hashes match Git, both actor producer receipts and three produced-file hashes
match. Menu status is PASS_MENU_NAVIGATION_ONLY with four bound capture receipts,
home/settings/home roles, one activation request, five event-post attempts,
four native down/up observations, normal exit and owned cleanup.

Strict regressions remain FAILED at actor: 73 assertions, zero assertion
failures, exit 0, six ObjectDB instances leaked; later 11 suites are unreached.
The actual input-mode diagnostic is SKIPPED with no native verbose repeat.
Mocked control stdout with source_commit invented does not qualify that repeat.
The original warning and full receipts remain byte-for-byte preserved.

The source reviewer independently confirms exact source identity, 307 hashes,
actor receipts, diagnostic skip and the separately bounded iOS compile/link.
Original raw logs can contain trailing whitespace and final blank lines;
whitespace checks apply to authored review documents/scripts without rewriting
native originals or invalidating artifact hashes.
