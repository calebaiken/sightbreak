# V3 frozen development validation

Status: **pre-freeze tooling; no V3 candidate has yet passed this procedure**.
The frozen reference remains `701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd`.
Its published 74-group matrix and separate twelve-condition, ten-client campaign
are historical V2 results, not results for this continuation.

## Source and evidence rules

- Commit the runtime **and all validation tooling** before native campaigns or
  exports. Use the same exact commit for exports, verifiers and packaging.
- Import with official Godot 4.7.2 **before** starting measurements. Record the
  actual platform/engine, Git commit/game tree and physical-byte hashes. A CRLF
  checkout need not share the historical Linux physical-content digest.
- A clean tree means no staged, unstaged or untracked edits. Ignored import,
  environment and evidence directories are generated data, not source.
- All attempt directories must be new or empty. Exports reject earlier target
  outputs/receipts; packaging rejects earlier ZIPs/manifest/checksums. Preserve a
  failed checkout/attempt and retry in a new frozen worktree rather than deleting
  earlier evidence. Do not re-attest old binaries with a new source receipt.
- Negative controls that mutate game source run only in separate disposable
  checkouts. Keep the original failure, corrected result, commands and source
  hashes. A printed `OK` followed by a nonzero process exit is a failure.

## Pure tooling controls

Use a supported interpreter with a normal process exit. On the current Windows
host, isolated CPython 3.13.15 is used explicitly: installed 3.14 crashes during
unittest shutdown even on the unchanged baseline; that failure remains retained.

```text
python scripts/test_build_manifest.py -v
python scripts/test_source_identity.py -v
python scripts/test_godot_process.py -v
python scripts/test_validate_matrix.py -v
python scripts/test_matrix_process.py -v
python scripts/test_offline_hud.py -v
python scripts/test_export_ui.py -v
python scripts/test_export_flow.py -v
python scripts/test_verify_builds.py -v
```

These are adversarial tooling/unit controls, not simulated substitutes for the
native matrix, process campaign, shipped binary, or human/device acceptance.

## Isolated Linux full validation and development packages

The branch-scoped `.github/workflows/v3-development.yml` checks out the exact
pushed commit, installs the pinned official engine and locked backend, and
performs the following as independent validation/build jobs. Keep the actual CI
run URL and downloaded artifact digest; do not reuse historical V2 artifact IDs.
The backend uses an actual ignored root `.venv` directory, not an untracked
symlink. Protocol fixtures require the published historical Git objects.

```sh
scripts/godot.sh --headless --editor --import --quit
xvfb-run -a .venv/bin/python scripts/validate_matrix.py --backend --protocol --render --out builds/v3-matrix
.venv/bin/python scripts/run_network_campaign.py --clients 10 --seconds 18 --port 39000 --out builds/v3-network
```

The maintained suite inventory remains `scripts/validate.sh`; the matrix adds
strict source/nested-log audits and new tooling groups without removing old
groups or weakening thresholds. Report the actual group count, failures and
unavailable groups, not an inherited `74/74`. Synthetic impairment is loopback
RTT/jitter/loss/reorder/blackout/reconnect evidence, not cellular/device evidence.

```sh
scripts/export.sh linux
scripts/export.sh android
scripts/export.sh ios
python3 scripts/verify_builds.py
python3 scripts/build_manifest.py package > builds/packaging.json
(cd builds && sha256sum --check checksums.txt)
python3 scripts/verify_packaged_builds.py --output builds/v3-package-verification
.venv/bin/python scripts/verify_integration_export.py --display :106 --visit-armory --reload-mode keyboard --timeout 240 --output builds/v3-export-network
.venv/bin/python scripts/verify_offline_export.py --display :107 --timeout 300 --output builds/v3-export-offline
```

The packaged verifier inspects extracted bytes, permissions and the actual Linux
entry points, not just archive existence. Its pure controls and independent mock
review do not establish a native pass: actual frozen Linux execution remains required.
Both UI controllers require a real X11 display (an isolated Xvfb is allowed),
XTest, Pillow and, for offline HUD OCR, Tesseract. They close the completed client
through the standard desktop close event and require clean normal exit.
`--quit-after` is only a deliberately premature-exit control, not the normal flow
or a wall-clock timeout. Screenshots and positive-health OCR must establish that
offline firing/reload happened while alive, with ammunition conservation.
The separate-process watchdog owns descendants before launch, bounds the complete
flow, retains partial OCR output, and rejects surviving descendants even when the
controller's own exit is zero. Its bounded failure-cleanup allowance cannot turn a
deadline overrun into a pass.

Upload failures as well as successes, including nested logs and hidden
`.local/validation/` native render captures. CI artifacts are **development-only**:
Android is debug-signed; iOS is an unsigned Xcode project, not a signed IPA.

## Native Windows subset

Set `GODOT_BIN` to the actual official Windows executable and use the explicit
Python executable selected above. The portable process helper preserves argv,
isolates Godot user data, cleans owned process trees and records unsupported RSS/
CPU sampling as unavailable/null. Import first, then run a frozen matrix in a new
external output directory. The Bash/X11 groups are explicitly **UNAVAILABLE** on
Windows and make that partial matrix non-passing; they are not removed or waived.
The complete Linux CI procedure is still required. Coordinate local native work
with other agents when the shared host is memory constrained.

## Unchanged acceptance gates

Keep source-owner branches and main unchanged. Independently judge neutral
outputs before opening source mappings or new owner quality/performance claims.
Use actual Valve-published CS2 image references and the repository-backed rubric;
8.5 is required in **each** applicable category, never just the mean. Uncaptured
whole-game areas remain unverified. Physical Android/iOS install, sustained GPU/
thermal/battery behavior, touch/gyro, complete human-played matches/gunplay,
production deployment and security remain open until actually tested.
