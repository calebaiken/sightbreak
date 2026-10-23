# Reproduce stabilization V2

Use exact source `701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd` with official Godot 4.7.2. Keep this checkout detached and clean throughout each campaign. Write evidence outside it. Do not commit tooling or reports inside a source-bound run.

Existing cloud toolchains were reused. Backend commands require the locked backend dependencies and a dedicated loopback development PostgreSQL on 127.0.0.1:55432. Each maintained backend harness creates/removes an isolated `_test` database. Native rendering requires a free 1280×720 Xvfb display; measured graphics here use llvmpipe, not a physical GPU. Package exports require the established templates, Android SDK/Java and editor settings. Never use the unrelated system Godot 4.6.3.

## Complete native campaign

Import is a dependency of native script execution on a fresh checkout: global script-class metadata does not exist until import completes. Running a network campaign concurrently with the first editor import is invalid. The retained premature attempt illustrates this failure; its first probe could not resolve TacticalMatch.

```sh
scripts/godot.sh --headless --editor --import --quit
DISPLAY=:105 .venv/bin/python scripts/validate_matrix.py --backend --protocol --render --out /tmp/sightbreak-v2-matrix
python3 scripts/run_network_campaign.py --clients 10 --seconds 18 --port 39000 --out /tmp/sightbreak-v2-network
```

The display must already be running. Use a new output directory for every attempt. The complete maintained matrix includes the original groups plus simultaneous reload/shot capture, rig contact, recursive child ObjectDB scanning and final source-identity comparison. Its summary records each group's source, exact command, exit, diagnostics and duration. Retain every failed and aborted attempt; never change an original result after a follow-up succeeds.

The source manifest includes Git commit, game tree and shipping-content SHA256. The final identity check rejects initial/final dirty state or changed runtime source. The network harness separately binds every condition to exact source. The full campaign and ten-client impairment campaign may use separate identical clean worktrees; finish imports before starting their child engines.

## Audio ownership and clocks

AudioStreamPlayer3D deletion requests stop, but AudioServer still owns playback until an audio mixer pass and a later main-thread cleanup. Harnesses must free owned scenes while the engine remains running, then allow the tested 0.5 s post-deletion drain before quitting. This is a test lifecycle correction, not a runtime audio event or authoritative reload-timer change. Strict top-level and child leak scans remain mandatory.

The Dummy driver uses 4096-frame buffers at 44.1 kHz, about 92.88 ms. It processes then sleeps, so buffer-frame time and elapsed wall time drift under process/scheduler delays. A wall-based sample-index assumption can misclassify genuine first-event samples as early. The capture records independently marked frame counters, uses physics stepping for 3D audio scheduling, and makes bus clears/cue/cancel marks atomic against mixing. Locks contain no await. It retains the original thresholds and rejects discarded capture frames.

The existing median onset offset remains part of the original assertion design; it must not replace independent cue marks or silence controls. CSV distinguishes diagnostic wall timestamps from cue/onset capture frames. These are mixer correctness checks, not phone output latency, audio listening or gameplay-quality acceptance.

Negative controls belong in a **separate disposable checkout** because they intentionally mutate files and restore them. They must never run in the full campaign's checkout:

```sh
python3 scripts/reload_negative_controls.py --only A5,A6,A7 --log /tmp/sightbreak-v2-controls.txt
```

A5 mutes voices, A6 fails cancellation and A7 plays unlogged audio before the first scheduled cue. The broad wrapper's baseline executes all of its native tests and requires a display. If a baseline fails, the wrapper does not execute mutations; retain that failure and its evidence limitations. `--no-baseline` is only a separately labeled targeted-control run after independently recorded baseline tests, never a way to relabel a failed baseline. The V2 report retains one unexplained wrapper failure alongside the subsequent exact maintained serial and negative-control results.

## Packages and actual Linux input

```sh
scripts/export.sh linux
scripts/export.sh android
scripts/export.sh ios
python3 scripts/verify_builds.py
python3 scripts/build_manifest.py package
python3 scripts/verify_integration_export.py --display :106 --xvfb /workspace/tools/xvfb/usr/bin/Xvfb --visit-armory --reload-mode keyboard --quit-after 200 --output /tmp/sightbreak-v2-native-network
git show a9d873eea9373fe7425b6e84da5e5971468af0a4:scripts/verify_offline_export.py > /tmp/sightbreak-v2-offline-controller.py
PYTHONPATH="$PWD/scripts" python3 /tmp/sightbreak-v2-offline-controller.py --display :107 --xvfb /workspace/tools/xvfb/usr/bin/Xvfb --quit-after 300 --timeout 300 --output /tmp/sightbreak-v2-native-offline
```

The final offline driver is separately versioned at a9d873e, SHA256 `30d408a9a92ab10472036a9e589e2e831b5e30bd5edc9cc10fe2dafd74c134c3`. Run that external controller against the frozen 701 helpers via PYTHONPATH as shown; do not edit the frozen checkout. It requires Tesseract and Pillow and checks rendered living-player ammunition; the older 701 offline script alone has weaker acceptance.

Use a free display for each driver and adapt the Xvfb path to the existing installation. Both drivers verify export/source content and executable hashes, retain native logs/screenshots, and reject failed normal exit. Network input is accepted only after the source authority observes real exported-client input/ACKs, shots and a desktop R-key reload. Offline screenshots require independent inspection; the driver does not introspect private exported authority state. Full bot lifecycle/objectives run in maintained native source tests. No phone/Xcode claim follows from these desktop paths.

Android is debug signed, API 24–36, arm64-v8a/x86_64. iOS is an unsigned Xcode project, with no signing team or IPA. Version 0.3.1-dev/build 4 distinguishes V2. The established delivery workflow runs on `integration/sightbreak-three-agent-artifacts`, exports all three targets, verifies actual resources/signatures and uploads a source-named 14-day Actions artifact. Its packaging success is separate from the native regression result. Each CI debug key can differ, so use the CI bundle's own inner checksums rather than local APK hashes.

Source manifests, complete results, actual delivery receipts, unchanged historical evidence and independent reviews are linked from [the V2 report](../reports/STABILIZATION_V2_REPORT.md).
