# Independent correction R1 verdict

REJECT exact correction `d0d94bec27f539b63e324c5468516ff2f0dd96d7` for runtime
release. It fixes all ten original counterexamples. A new control still observes
changed log bytes during final validation and returns exit 0 / overall passed
true. This mismatch between the bytes read and the bytes qualified is the largest
remaining gap. A second control identifies the absent final-publication source
observation described below.

Review preregistration was pushed at `0c65b35`, before detailed inspection and
controls. The original REJECT at `ff4cc71` remains intact. This review uses source
inspection and pure Python, fake Popen, invented ELF/cache/measurement/proof data,
and temporary source files. No engine, compiler/import/export, native fixture,
UID generation, Xvfb, profiler, OCR, CI, services, heavy work or nested agents ran.
The native/touch lane remains outside this review.

## Final log reread observes bytes that were never qualified

High priority, `scripts/linux_profile_acquire.py:90`. `Evidence.validate()` first
compares `identity(path)` with the first accepted identity at line 94. For logs it
then separately calls `path.read_text()` at line 96. It checks only the strict-log
matcher against this second read, without checking that read's length/hash against
the accepted identity. `Evidence.bind(log=True)` has the same two-read structure.

The [boundary control](test_boundary_controls.py) waits until overall publication
has completed and its alarm is restored, when main executes its last
`evidence.validate(closed=True)` at line 777. After the target log's identity read
has completed, the control changes the version stdout immediately before its real
semantic reread. That reread observes the new clean bytes. The wrapper accepts
them because they contain no warning. It returns exit 0 with overall passed true,
while the manifest and validated identity still refer to the old bytes.

[Results](boundary-results.json) record the distinct SHA-256s and
`semantic_reread_observed_changed_bytes: true`. [Raw assertions](boundary-controls.txt)
show the expected rejection failing. The unmodified positive path passes. This
control uses a write before a real validator read, so it demonstrates observable
drift inside the verifier. It does not depend on a write after the last read or
after return.

Smallest correction: use the same raw read for identity comparison and strict-log
analysis, including the final reread. Compare that raw read against the first
accepted identity before accepting its semantics. Preserve the original deadline,
append-only identities and rejected-byte evidence.

## Source checks end before final publication

The original registration requires, "Source/tool/stage/payload/UID/host checks run
again at final acceptance." R1 further describes checking previously accepted
identities "throughout final publication." The new evidence registry admits only
paths under OUTPUT. Repository source files remain outside it. The real source
checks finish inside `finalize()` at lines 649–650; subsequent publication and
readback checks at lines 755–778 inspect output evidence only.

The second control installs a temporary original source file and runs the real
`Acquisition.sources()` implementation with synthetic Git status/index/blob
responses. It verifies the blob before finalization, and the real finalizer's
source checks pass. During the `outputs.json` write, the control changes that
source. This precedes the later overall write/read, stdout and post-alarm
validation boundaries. The critic explicitly reruns the real source checker,
which rejects with `Source is not exact and clean`. The wrapper performs no later
source check and returns exit 0 / overall passed true. Its source-check count
remains three, excluding the critic's extra observation.

This establishes the missing publication-boundary source observation. The final
`source_unchanged` claim currently describes the earlier finalizer observation;
it cannot establish source cleanliness at the later publication boundaries.
Choose a named final-publication source observation, check it within the original
budget, and retain its boundary in the receipt. A source mutation in the manifest
write hook must precede and fail that promised observation. The scope is ordinary
concurrent writers to the checkout during acquisition. No claim of perpetual
immutability after the last guaranteed observation or after return is required.

## What the correction establishes

[Independent replay](replay_original.py) extracts the exact original critic test
bytes from `ff4cc71` and exact target Python files from Git into isolated temporary
copies. The control bytes are unchanged. [Rejected source](rejected-original-controls.txt)
reproduces ten failing subtests / zero errors. [Corrected source](corrected-original-controls.txt)
passes all three methods and all original rejection assertions; the positive
passes on both. [Replay identities](replay-summary.json) bind both source sets.

- [Maintained acquisition suite](acquisition.txt): 27 methods pass, no skips,
  including the 64 publication mutants, first-identity checks and stage-input
  drift controls.
- [Accepted fixture suite](accepted-fixture.txt): 22 methods pass, no skips.
- New boundary suite: three methods, positive passes, two required rejection
  assertions fail, zero errors. These failures are retained counterexamples.
- The first boundary-results JSON omitted descriptive control labels because
  the helper's `mode` field replaced them. [That initial metadata](initial-results-label-omission.json)
  remains retained; the current results use separate `control` labels. Assertion
  outcomes are unchanged.

Source inspection and maintained controls support the narrowed ECFG policy:
critical selectors must be declared by the frozen staged project and have safe
values/types; unexpected Linux/compound/custom selectors reject; legitimate
`.mobile`, declared safe variants and the two pinned base-default omissions pass.
The original three valid-MD5 Linux override falsifiers now reject.

[Frozen-source verification](frozen-source-check.json) checks all 43 ledger files
and all 13 original independent-review files byte-exact. Accepted controller,
fixture, scene, fixture tests, original registration/report directory and shipping
game remain unchanged from `3fd9718`. Game tree is
`55691684d31d44f1680141954bbe530443de9d1f`. Fixed text packaging, one payload,
OFF/ON/ON/OFF, 180-second child caps and 1320-second outer cap remain intact.

Actual export/cache stability, compilation, graphics, native cleanup and cadence
remain unjudged. Original Linux gameplay failures retain their failed status.
Correct the two publication-observation gaps and obtain fresh exact-source review
before root considers the one runtime acquisition.
