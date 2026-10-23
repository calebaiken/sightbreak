# Independent source verdict

REJECT frozen source `04bc153e52341228b2f0d6f4ce72f784528ef1d4` for acquisition
release. Two source gates accept counterexamples. The largest gap is final
retained-byte sealing: the wrapper can publish exit 0 and `passed: true` after
previously validated evidence changes. No runtime attempt is released by this
review.

The review preregistration was pushed at `0784081` before detailed implementation
inspection and controls. This reviewer is independent of the builder. The scope
is source and pure Python only, with fake/forbidden Popen. No Godot, compiler,
import/export, Xvfb, native fixture, profiler, OCR, CI, services, or nested agents
ran. The original Gauntlet Loop, No AI Slop and eval, project Gauntlet, AGENTS and
mission instructions were inspected. This is a measurable source-contract
comparison, without a visual blind pair or native-performance claim.

## 1. Final success accepts changed retained evidence

High priority. `scripts/linux_profile_acquire.py:539` rechecks source, stage source
inventory, tools, payload, seal, independent payload receipt and host. It never
rechecks the earlier command logs against their recorded hashes, phase receipts
against their publication hashes, the diagnostic-stage record against the seal,
or the block/raw evidence against the earlier accepted values. The final manifest
at line 643 hashes the bytes present at that later time. It does not compare them
with the identities that passed the earlier gates.

[Independent controls](test_independent_controls.py) run a positive path through
the real command/ownership/log gate, hand-built ELF/PCK inspection, raw condition
and block gates, finalizer, phase deadlines, and main publication. Source/tool/
host admission and staging are synthetic, engine child creation is fake, and the
measurements and proof bytes are invented. The unmodified path passes. Each of
these mutations occurs after `run_block()` accepts and before the unchanged real
`finalize()`:

| Changed retained file | Mutation | Final result |
| --- | --- | --- |
| version command stdout | Replace with a `WARNING:` line | Exit 0, passed true |
| first condition `client.log` | Append a `WARNING:` line | Exit 0, passed true |
| first condition `proof.png` | Replace proof bytes | Exit 0, passed true |
| `native-block/block.json` | Set `passed` to false | Exit 0, passed true |
| first condition `condition.json` | Replace with `{}` | Exit 0, passed true |
| `version.phase.json` | Replace with `{}` | Exit 0, passed true |
| `diagnostic-stage.json` | Replace the seal-bound record with `{}` | Exit 0, passed true |

All seven changed files are included under their new hashes in the final
`outputs.json`. The version-log hash in the command receipt and the block hash
in the overall receipt still refer to the old bytes. The strict warning and
failed-block counterexamples therefore produce internally inconsistent success
packages. See [raw assertions](independent-controls.txt) and
[machine-readable results](independent-results.json).

Required correction: bind every retained acceptance input to the bytes that
passed its earlier gate, then reread the retained logs, stage and phase records,
block/condition publications, metrics and proofs before final success. Reject
identity or strict-log drift. The final manifest must describe those validated
bytes within the existing final/whole budget. Add controls for changes during
final publication as well as before finalization; hashing changed bytes anew
cannot establish the earlier validation.

## 2. ECFG critical-setting checks ignore feature overrides

High priority for the independent payload gate. In
`scripts/linux_profile_payload.py:87`, `project_properties()` reads every packed
key but checks only exact keys in `CRITICAL`. Additional feature-specific forms
of those keys are accepted without qualification. Fresh valid-MD5 packs containing
each of the following still pass the complete real `payload.inspect()`:

| Additional packed key | Value |
| --- | --- |
| `application/run/main_scene.linux` | `res://main.tscn` |
| `debug/settings/stdout/print_gpu_profile.linux` | `true` |
| `rendering/driver/threads/thread_model.linux` | `2` |

These controls rebuild the directory and MD5s after changing `project.binary`;
their acceptance is independent of checksum validation. They establish an
incorrect pre-seal project-setting assertion, not a complete native acquisition
success. The unchanged runtime controller may reject some resulting behavior,
and `--render-thread safe` remains present.

The candidate's own SHA-pinned `core/config/project_settings.cpp` registers dotted
setting names as feature overrides at lines 324–338 and resolves active overrides
at lines 415–433. Its retained bytes match the preregistered upstream hash.
Required correction: reject unexpected feature variants of critical keys, or
validate their effective values against the frozen stage and fixed export
features, preserving the legitimate existing mobile renderer setting. Do not
report the critical base value as sufficient evidence of the effective value.

## Confirmed source properties and controls

[Frozen-source verification](frozen-source-check.json) checks all 25 entries in
the submitted source manifest and all nine retained upstream source hashes.
Accepted fixture/controller, scene, 22-method suite, original fixed-view report
directory and shipping game remain byte unchanged versus `3fd9718`. The game tree
is exact `55691684d31d44f1680141954bbe530443de9d1f`. The candidate adds only its
acquisition scripts and component reports; no canonical mission file changes.

Source inspection confirms the external Linux text-mode amendment, private XDG
and template state, official archive SHA-512 plus installed-member comparison,
Git-blob source inventory, closed PCK resource set and MD5/data-range checks,
unchanged four-condition OFF/ON/ON/OFF child, separate original 180-second child
deadlines, 1320-second outer budget, phase limits and observed-identity cleanup.
These properties do not cure the two acceptance failures above. Cleanup still
has the expressly declared unobserved escaping-descendant limitation.

- [Maintained acquisition suite](acquisition.txt): 20 methods pass, no skips.
- [Unchanged fixture/controller suite](accepted-fixture.txt): 22 methods pass,
  no skips.
- [Alarm replay](alarm-replay.txt): old `22bb1f8` has the expected two failures;
  corrected source passes both. [Old raw](alarm-before.txt) and
  [corrected raw](alarm-corrected.txt) are retained separately. The replay's
  generated copies of existing builder reports were restored byte-exact from
  the frozen candidate in this own worktree.
- Independent suite: three methods, one positive method passes, ten rejecting
  subtests fail their required assertions, zero errors. Seven failures concern
  final sealing and three concern ECFG overrides. These are retained falsifiers,
  not passing implementation tests.

The first independent control version omitted initial creation of the synthetic
diagnostic-stage record. Its [raw output](initial-controls-stage-setup-omission.txt)
and [results](initial-results-stage-setup-omission.json) are retained as superseded
harness evidence. The current test creates the stage record before mutation and
binds its original path/hash into the seal; it reproduces all ten failures.

The new export, generated UID/cache stability, GDScript compilation, engine and
graphics behavior, actual cleanup, and measured cadence remain unjudged. Existing
Linux gameplay failures retain their original failed status. Fix both source
findings and obtain fresh exact-source review before root considers one attempt.
