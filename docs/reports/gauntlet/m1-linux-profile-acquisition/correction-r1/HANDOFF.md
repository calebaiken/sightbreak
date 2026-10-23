# Retained-evidence and critical-setting correction R1

Source-only correction is ready for independent exact-source review. No runtime
acquisition is released. Implementation savepoint: `af8d299`; the enclosing
report freeze also binds these bytes in `source.json`. Original rejected freeze
`04bc153e52341228b2f0d6f4ce72f784528ef1d4` and its original component reports are
unchanged. [Independent REJECT](retained-rejection/REVIEW.md) and all thirteen
original review files are retained byte-exact from critic
`ff4cc71b1a81c073a92acea1b56007e4508282e7` with an identity ledger.
[Correction preregistration](PREREGISTRATION.md) was committed and pushed at
`b75017d` before implementation (`8f050d2`, then `af8d299`).

## What changed

The outer acquisition now keeps an append-only in-memory registry of the first
bytes qualified at its gates. A later bind must match that original identity.
Semantic JSON/log reads are bound to the bytes read; JSON publications are bound
to their expected serialized bytes. Strict logs are reread under the existing
strict matcher. Initial stage files are bound before packaging amendment, with
the two deliberately amended config files checked against the original stage
record and then bound after the amendment.

The registry binds command stdout/stderr, phase publications, original/stage/
amendment/inventory and generated-UID publications, staged source and relevant
import/UID/class cache inputs, ELF/PCK/independent payload/seal, and raw block,
condition, client/Xvfb logs, metrics and proof bytes. Finalization also verifies
the seal's exact stage-record path, original digest and in-memory stage value.
Previously accepted identities are checked before and after finalization and
throughout final publication. They are never replaced with newly changed bytes.

`outputs.json` describes the validated closed output set preceding that manifest
and `overall.json`. The manifest is then bound and the overall receipt snapshots
the preceding registry, including the manifest. A private registry entry binds
the overall bytes too; that entry cannot be included in its own serialized
receipt. Closed-set and original-identity checks run after manifest publication,
overall publication/readback, stdout and alarm restoration. Unexpected extra
files reject as well. Rejected command receipts retain the original gate hashes;
current rejected bytes are recorded under separate `failure_observation` fields.

The pure payload inspector now qualifies every critical setting and any dotted
variant against the exact inventoried staged `project.godot`. Unexpected variants
reject even when their value is safe. Declared variants must have the registered
safe type/value. The existing `.mobile` renderer is retained. The two already
registered pinned-default omissions remain allowed only for their base keys.
This is a narrow source-aware acceptance policy, not full Godot feature emulation.

The pinned engine bytes explain why this is required:
[`ProjectSettings::_set`, lines 324–338](https://github.com/godotengine/godot/blob/ed1daf0bf001b61586d9930840f2f1394092c079/core/config/project_settings.cpp#L324)
splits names after the first dot and registers suffix features;
[`get_setting_with_override`, lines 415–433](https://github.com/godotengine/godot/blob/ed1daf0bf001b61586d9930840f2f1394092c079/core/config/project_settings.cpp#L415)
selects a matching active OS feature. The retained source SHA-256 remains
`7de9335773ee4498d7559300d06f14717e715909db92b62b52dd44887e19cc94`.
Testing only a packed base key could therefore assert the wrong effective value.

## Pure evidence

- [Maintained acquisition controls](pure-controls/acquisition.txt): 27 methods
  pass, including the original independent positive/ten falsifiers, 64 late
  publication mutations across five hooks, first-identity/closed-set controls,
  stage-input drift, qualified settings, allowed default omissions and original
  positive deadline boundaries. No skips.
- [Unchanged accepted fixture suite](pure-controls/accepted-fixture.txt): all
  22 methods pass, no skips. Controller, fixture, scene, fixture suite and game
  are byte unchanged from accepted `3fd9718`.
- [Replay script](replay_rejection.py) runs the critic's unchanged test bytes in
  isolated Python source copies. [Rejected-source replay](pure-controls/rejected-replay.txt)
  reproduces ten failing subtests / zero errors. The valid positive passes.
  [Corrected replay](pure-controls/corrected-replay.txt) passes all three methods,
  all ten rejection assertions and the valid positive, with zero errors/skips.
  [Machine summary](pure-controls/replay-summary.json) binds both sets of source
  hashes; per-case JSON is retained alongside both raw outputs.
- [Source and preservation check](pure-controls/source-preservation.json)
  verifies original reports/review bytes, all nine retained upstream files,
  accepted files and game tree `55691684d31d44f1680141954bbe530443de9d1f`.
- The [initial publication harness errors](pure-controls/initial-publication-harness-errors.txt)
  are retained with their [explanation](pure-controls/INITIAL-HARNESS-NOTE.md).
  Five malformed-manifest summary reads were harness errors; that run is not
  counted as passing evidence. Valid JSON mutations fixed the summary reads.

Reproduce with pure Python only:

```sh
python3 -B -m unittest discover -s scripts -p 'test_linux_profile_acquire*.py' -v
python3 -B -m unittest discover -s scripts -p test_linux_profile_overhead.py -v
python3 -B docs/reports/gauntlet/m1-linux-profile-acquisition/correction-r1/replay_rejection.py
```

The preserved text-mode diagnostic packaging, pinned editor/templates, fixed
OFF/ON/ON/OFF order and single payload remain unchanged. Each condition still has
its original 180-second deadline; phase caps and the 1320-second whole cap are
unchanged. No engine/import/compile/UID/export/Xvfb/native/profiler/OCR/CI/service
process ran for this correction. The original Linux gameplay failures remain
failed. These controls establish a source contract with invented data, not an
actual export, GDScript compilation, cleanup/performance result, complete profiler
cost or shipping/gameplay improvement. Root must obtain fresh exact-source
review before considering the one runtime acquisition.
