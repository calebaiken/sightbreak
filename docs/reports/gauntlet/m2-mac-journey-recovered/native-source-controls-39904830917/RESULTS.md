# Test-only correction frozen; repeat native run pending

Corrected test/workflow source is
`3730273b65717c91565771beda700f66366c0346` on
`codex/m2-mac-journey-recovered`. It changes only the two new test modules, adds
one test module and invokes that new control from the existing ARM source-control
step. Both production runtime files and the game remain byte-identical to
independently accepted `bd9ac47`. `corrected-pure/results.json` retains their
matching Git blob IDs and every tested source-file SHA-256.

The completed original ARM job ran the helper command and failed with four
`/var` symlink errors. Its ordinary gameplay step was skipped, and bash stopped
before the mocked-controller command. The full decoded original job log and final
step metadata remain beside this report. The first unavailable-log response is
retained too. This correction does not change that failure into a pass.

The Linux pure reproduction sets TMPDIR to a freshly owned directory alias.
Both original test commands fail the unchanged runtime symlink guard, reproducing
the same fixture error without an engine, native input or OCR. The original helper
command has the same four error sites as ARM. The controller command also fails
against the alias; that was a latent fixture error because the original ARM job
stopped before reaching it. `baseline-alias/` preserves both complete outputs.

The correction resolves each freshly owned TemporaryDirectory root with
`Path(...).resolve(strict=True)` before creating test fixtures. Descendant aliases
remain unresolved so the production negative controls still reject them. Neither
runtime path handling nor the no-symlink policy changes.

All 59 top-level normal pure tests pass: the previous 57 plus two path controls.
The helper, mocked-controller and new path-control commands also pass with an
aliased TMPDIR. The new control reruns all 21 helper/controller cases under the
alias, rejects the raw alias and its descendants through the unchanged runtime,
and accepts the owned canonical target. A mutation restoring the original
unresolved test roots makes the new control fail. The expected mutation failure,
normal/alias outputs, command results, durations and hashes are retained in
`corrected-pure/`. Compilation and `git diff --check` pass.

The builder made no native, engine, OCR or CI repeat attempt. Fresh independent
source review and combined-source integration review remain required before root
releases a repeat. Actual private-override support, stock Deploy, living gameplay,
native Vision HUD checks and teardown remain unverified.
