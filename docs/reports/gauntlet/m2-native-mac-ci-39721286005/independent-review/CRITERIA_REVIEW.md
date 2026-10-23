# Separate SDK follow-up review

Run `39721286005`, job `119635074896`, frozen source `2a2b732c9f4637e9c2c68890cdd0f13d8fa89906`.
The original run `39719407304` at `0ca125d` remains a failed iOS link and a separate Intel startup investigation.

The reviewed SDK correction requires a real unsigned arm64 device link strongly referencing all five globals missing from the old iPhoneOS18.5 SDK. Installed Xcodes are bounded and selected through process-local `DEVELOPER_DIR`. The original 900-second total budget, pinned Godot/template checksum, clean source/PCK identity, generic-device Debug build, strict unsigned Mach-O/platform check and final codesign assertion remain required. A successful probe does not prove the full game link. The actual native compile, app inspection and post-build source check need outcome evidence.

The separate workflow edit selects exactly one ARM host only for the explicit manual ARM lane; no omitted platform inherits acceptance from it. The connector job list confirms exactly one macos-15 job for this run. Source snapshots and later independent SDK/workflow implementation reports are retained with distinct commit identities.

Signing, installation, runtime, touch, suspend/resume, simulator architecture support, physical devices, human play and release acceptance remain separate. This review can verify the device compilation slice from actual logs and source-bound native output receipts; it cannot reopen binaries that were not uploaded in a bounded artifact.
