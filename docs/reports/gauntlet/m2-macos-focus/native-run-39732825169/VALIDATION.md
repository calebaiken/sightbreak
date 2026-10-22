# Read-only replay

Run from the repository root. These scripts read immutable Git objects and
retained original files; they launch no Godot, native API, compiler or OCR:

```sh
python docs/reports/gauntlet/m2-macos-focus/native-run-39732825169/recompute_source.py /workspace/sightbreak-mac-menu-native-review --output /tmp/mac-focus-source.json
python docs/reports/gauntlet/m2-macos-focus/native-run-39732825169/audit_receipts.py docs/reports/gauntlet/m2-macos-focus/native-run-39732825169/receipts --checkout /workspace/sightbreak-mac-menu-native-review --source /tmp/mac-focus-source.json --output /tmp/mac-focus-audit.json
python docs/reports/gauntlet/m2-macos-focus/native-run-39732825169/audit_focus_sequence.py docs/reports/gauntlet/m2-macos-focus/native-run-39732825169/full-qa --output /tmp/mac-focus-sequence.json
python docs/reports/gauntlet/m2-macos-focus/native-run-39732825169/audit_native_outputs.py docs/reports/gauntlet/m2-macos-focus/native-run-39732825169 --source /tmp/mac-focus-source.json --output /tmp/mac-focus-native.json
```

Observed results: 127 indexed receipt hashes match; source resources 307,
producer receipts 14 and produced-file hashes 21 match. Seven suites contain
1,584 assertions with zero assertion failures. The input-mode clean-log failure,
five unreached suites and FAILED menu status remain visible. Four original OS
captures, one activation request, one focus sample, five event-post attempts
and four native down/up observations are retained. Separate iOS compile/link
passes with its stated binary/runtime limits.

The initial review reader assumed a HUD log existed after an earlier suite
failure; its FileNotFoundError, reader and exit 1 are preserved. The revised
reader accepts partial file presence as evidence and records the actual missing
suites. It does not convert the native failure into success.

Whitespace checks apply to authored documents and scripts. Original Xcode/Godot
logs retain their trailing whitespace/final blank lines so transferred hashes
remain unchanged. The complete evidence diff can report those native log lines.
