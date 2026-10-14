# Reproducible engineering validation

Use the existing pinned/checksummed `scripts/setup.sh` (Godot4.7.2) and `scripts/setup-android.sh`. Java17, Android SDK/build-tools36, debug keystore and native export templates are required for Android. `scripts/export.sh linux|android|ios` records exact commit, game-tree and content hashes. `scripts/verify_builds.py` checks APK signature/manifest/ABI/landscape, Linux startup, excluded test harnesses, iOS project structure and stale source. `scripts/build_manifest.py package` writes checksums and distributable archives.

`DISPLAY=:99 .venv/bin/python scripts/validate_matrix.py --backend --protocol --render --out /absolute/output` runs the maintained suite inventory, all networking groups, isolated PostgreSQL/economy/recovery groups and native lifecycle checks. Unlike a fail-fast shell invocation, it retains **every** group's exit/log failure and continues independent tests. Any failure makes the aggregate exit nonzero. Display-backed software rendering is explicitly a lifecycle/correctness check, never mobile GPU evidence.

The manual-only `engineering.yml` workflow defines standard Linux validation and optional debug Android export. It is restricted to public repositories to avoid implicitly enabling billed private runner use; no workflow has been remotely executed or verified in this session. No production secret or signing account is needed. Regression failures remain failures in CI. Android artifacts are development-signed; physical install, touch, thermal, battery and GPU acceptance need phones. iOS export creates an unsigned Xcode project; macOS/Xcode, Apple signing and a device are required to produce/validate an installable app. Linux-generated projects are not installable iOS builds. Debug symbols and native crash symbolication on actual phones remain unverified.

## Actual integrated artifacts

Final60cf125 exports include imported Relay AR/rig textures and compiled privacy/interpolation/prediction/lifecycle/outbox modules; tests are excluded. Godot export templates do not support external editor `--script` drivers. The maintained native verifier drives the actual executable through X11/XTest and uses a source Godot authority fixture on loopback:

```sh
python3 scripts/verify_builds.py
python3 scripts/verify_integration_export.py --reload-mode keyboard --output /absolute/evidence/native-ui
python3 scripts/build_manifest.py package
(cd builds && sha256sum -c checksums.txt)
```

Requires Pillow, X11/XTest and Xvfb. Keyboard mode requires the server to observe actual client reload input; authority mode explicitly leaves that input unverified. Capture timestamps can lag authority events under software rendering; inspect images before captioning them. The verifier requires supported timed engine exit and fails on errors/leaks. Source SHA, runtime content hash, ELF SHA and authority evidence are retained. APK format/signature verification is not Android startup, and an unsigned iOS project is not a compiled/signed app. The cloud session used Java21.0.12.1; Java17 is the documented minimum.
