## Verdict: request changes before freeze

The exact-commit comparison closes the original **old receipt A → package at commit B** path. However, stale-artifact re-attestation and stale-success evidence remain possible. I found no basis to claim a green 74-group/12-condition campaign, native exported-client success, or device/human acceptance.

### Verified defects

#### 1. P1 — Existing artifacts can still be re-attested under another commit
**`scripts/build_manifest.py:63–85`**

`begin()` overwrites `source.json` but leaves existing outputs untouched. `finish()` accepts any existing nonempty output and binds its bytes to the new receipt.

**Reproduced in an isolated temporary fixture:**
1. Produce completed exports with clean source identity A.
2. Change the mocked clean source identity to B.
3. Call `begin(target); finish(target)` for all targets, **without exporting or changing any artifact**.
4. `package()` succeeds, labels everything B, and archives the original A bytes.

The normal `export.sh` wrapper correctly aborts on a nonzero exporter exit; this is a **receipt/API guarantee gap**, not evidence that its normal failure handling already bypasses the check. Nevertheless, the manifest API still cannot establish that the artifact was produced during the current attempt.

It also overwrites the previous attempt’s receipt. Prefer fresh attempt directories and reject pre-existing payloads rather than deleting evidence.

#### 2. P1 — Failed artifact re-verification leaves an earlier `passed: true` result
**`scripts/verify_builds.py:66–78, 133`**

Unlike the two interactive controllers, this verifier reuses its output directory and writes `results.json` only on success.

**Reproduced:** seed `builds/verification/results.json` with `{"passed": true}`, then mock the current Linux smoke process to return failure. Verification raises, but the old successful JSON survives alongside the new failed log.

Timeouts are worse: `subprocess.run()` raises before line 76 writes the log. A negative control confirmed that captured current-attempt output is discarded and an old log remains untouched.

Use an empty/new attempt directory, preserve timeout output, and record the current attempt’s failed/incomplete status. A failing process exit does not make stale successful evidence safe to retain at the canonical result path.

#### 3. P1 — The “living-player” OCR check fails open
**`scripts/verify_offline_export.py:91–96, 145–155`**

The living-state check only rejects two exact negative words. It does not require recognizable health text or positive health.

**Reproduced against the extracted, unchanged `read_hud()` function:** both of these status OCR results are accepted with ammunition text `12 / 60`:
- Empty text
- `000 HEALTH`

The ammunition assertions demonstrate fire/reload changes, but this parser does **not positively establish a living player at either capture**. Require a recognized health value greater than zero and fail closed on unreadable status. Keep independent screenshot review open.

#### 4. P2 — Version checks pass despite an actual project-version mismatch
**`scripts/build_manifest.py:13–15`; `game/export_presets.cfg:47–48, 75–76`; `scripts/test_build_manifest.py:149–155`**

The manifest and mobile presets say `0.3.2-dev`/build 5, but `game/project.godot:6` still says:

```ini
config/version="0.3.1-dev"
```

The existing version test checks only the mobile presets, so it passes. This is not merely unused metadata: the network build-information response reads `application/config/version`.

Add the project setting to the version-consistency test before freezing.

#### 5. P2 — Packaging strips executable permissions from Linux wrappers
**`scripts/build_manifest.py:109–112`; `game/export_presets.cfg:17`**

Every archived file except the exact filename `sightbreak.x86_64` is forced to mode `0644`. The Linux preset enables the debug console wrapper.

**Reproduced:** a fixture `linux/sightbreak.sh` with executable permissions is archived as `0644`. The direct ELF smoke test does not exercise this packaged entry point.

Preserve appropriate executable bits and inspect the extracted package, not just the pre-package executable.

#### 6. P2 — The workflow’s pre-campaign cleanliness gate is incomplete
**`.github/workflows/v3-development.yml:24–28`**

`git diff --exit-code` ignores untracked files and staged-only changes. Thus, newly generated untracked source/UID files can pass setup and allow the matrix to start before the checkout satisfies the whole-source freeze requirement.

The matrix’s final cleanliness check can report failure afterward, but cannot retroactively establish **clean source before the campaign**. Use the same explicit whole-source cleanliness gate immediately before starting validation.

#### 7. P2 — Artifact uploads omit some raw rendering evidence
**`.github/workflows/v3-development.yml:37–39`; `.github/workflows/engineering.yml:42–45`**

The invoked native-render wrapper stores subordinate logs and screenshots under `.local/validation/native-*`. Neither upload configuration includes those directories.

The uploaded outer matrix log can point to raw evidence that disappears with the runner. This falls short of retaining all failed-attempt evidence, particularly captures needed for independent visual inspection.

### Conditional risks — not observed native failures

- **Packaging has a check/read race — `scripts/build_manifest.py:88–120`.**  
  An isolated mutation injected after payload validation but before archive reads produced a successful package whose archived secondary payload disagreed with its receipt. Its archive checksum was valid because it hashed the changed archive. No final source/payload recheck exists. This requires a concurrent writer; I did not observe one during a real export.

- **The exported-client frame budgets depend on slow rendering — `.github/workflows/v3-development.yml:71, 74`.**  
  Network uses 200 frames; offline uses 300. At 60 FPS these provide approximately 3.3/5 seconds, shorter than the controllers’ mandatory sleeps and interactions. They may work under slow llvmpipe yet exit early on a faster runner. Linux behavior remains unverified; prefer completion-driven native quit with a separate watchdog.

- **Whole-source byte/symlink coverage is not exercised — `scripts/build_manifest.py:23–32`; `scripts/test_build_manifest.py:31–33`.**  
  All manifest tests mock `source()`. Only game runtime bytes are hashed; tooling identity relies on Git status. Symlink-target changes, Git status configuration, and generated-file behavior therefore remain untested. I found no current tracked symlink establishing an active bypass. The `.venv` directory change does address the earlier symlink-cleanliness issue.

### Test and scope limitations

- The **18 existing unit cases reported `OK`**.
- Seven isolated negative controls reproduced the behaviors above: artifact re-attestation, stale successful results, timeout-output loss, wrapper permissions, packaging mutation, version mismatch, and fail-open HUD parsing.
- **The local Python process crashed after reporting successful assertions**, with native exit `-1073741819` (`0xC0000005`). I do **not** count that as a clean test-process pass.
- No source edits, commits, native Godot runs, or GitHub writes were performed. Concurrent network-file changes were excluded.

The explicit **NOT TESTED** device/Xcode fields and screenshot-review limitations are appropriate. None should be waived to resolve these findings.
