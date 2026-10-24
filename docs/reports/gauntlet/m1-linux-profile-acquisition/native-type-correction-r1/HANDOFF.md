# Native fixture type correction source handoff

Unreviewed source/pure candidate only. Implementation
`2e9ed451b43280815324100171c51580c7f4ec98` follows the pushed preregistration
`86d5e62cb4f9f5127856cb06d78e937072e6c604`. The enclosing source/evidence freeze
is the commit containing this report and its `source.json`. Fresh independent
review of that exact full SHA and root's explicit lane release are required
before any second actual attempt. The builder grants neither.

The observed first attempt remains failed: outer exit 1, import child exit 0,
then strict rejection of the fixture parse/load errors at line 107. It produced
zero exports and zero native conditions or measurements. The original frozen
worktree, r1 output, claim and `.local` receipts stay unchanged. The independent
actual-output critic owns its separate complete archive/review at
`/workspace/reviews/linux-profile-acquisition-native/docs/reports/gauntlet/m1-linux-profile-acquisition/native-independent`.
This report's [read-only identities](source-preservation.json) bind the original
top-level receipts/logs and wrapper receipts; they do not replace that raw audit.

## Exact correction

The fixture uses `var keys: Array = value.keys()` in the runtime
`TYPE_DICTIONARY` branch of `_canonical(value)`. The untyped argument makes the
method expression unsuitable for the former `:=` inference. Dictionary keys
still supply the same Array to the exact original comparator and traversal.
The complete fixture differs by that one declaration. Every other `:=` site
was inspected: literal scalars/containers, known typed engine returns, typed
parameters/variables or explicit conversions supply their types. No other
direct inference from the untyped canonical value was found.

The supervisor changes only the corresponding fixture SHA-256 pin and its fixed
output from `builds/linux-profile-acquisition-r1` to
`builds/linux-profile-acquisition-r2`. The new fixture SHA-256 is
`bac96e5c3aa9e63dfe0aa41522076cb6352293a3d5d9e70657a19cdfa4d52b92`.
The source audit verifies the complete expected before/after bytes of both
modified files. Every other tracked path outside this new report directory is
unchanged from `f242a2f20adb3ba1d9c49feb1c6caca1bdbf52b9`.

The shipping game tree remains `55691684d31d44f1680141954bbe530443de9d1f`.
The diagnostic controller/evaluator, scene, tests, original offline controller,
pins, source references, prior reports and canonical mission files stay exact.
The original 1320-second whole bound, all per-phase caps, strict 180-second
conditions, five-second cleanup and ten-second failure publication stay exact.
CPUs 0,1, display :99127, LP2, pinned engine/templates, packaging amendment,
OFF/ON/ON/OFF, 32 warm/64 measured intervals, every formula/threshold and the
limited median-cadence claim are unchanged. Earlier Linux gameplay failures
remain failed.

## Source/pure evidence

The [acquisition suite](pure-controls/acquisition.txt) passes 31 methods, with
no errors or skips. The unchanged [fixture/controller/evaluator suite](pure-controls/fixture.txt)
passes 22 methods, with no errors or skips. These exercise the existing
synthetic positives and failures, original ten falsifiers, 64 publication
mutations, same-read/source-observation boundaries, payload checks, cadence
mathematics, deadlines and ownership controls. Tests use their existing fake
native-process routes. No test was added or changed to mirror the declaration.

The first acquisition run had one [sparse setup error](pure-controls/acquisition-missing-sparse-game.txt)
because the new checkout omitted tracked `game/export_presets.cfg`; restoring
the exact game tree preceded the fresh passing output. The first inline
source audit also had a retained [report-path allowlist setup error](pure-controls/SOURCE-AUDIT-SETUP-NOTE.md).
Neither failure is counted as a pass. No product code or test changed for
either setup repair.

The [saved source audit](audit_source.py) verifies the exact narrow delta,
unchanged original HEAD/clean tracked status, the absent fresh output/claim,
the source pins and original failure identities. The unchanged strict-log
function rejects both actual parse/load lines from the original import stderr.
Its [raw audit output](pure-controls/source-audit.txt) records the result.
This audit checks source preservation and retained bytes; it does not compile
GDScript or establish runtime type behavior.

```sh
python3 -B -m unittest discover -s scripts -p 'test_linux_profile_acquire*.py' -v
python3 -B -m unittest discover -s scripts -p test_linux_profile_overhead.py -v
python3 -B docs/reports/gauntlet/m1-linux-profile-acquisition/native-type-correction-r1/audit_source.py
```

## Held second-attempt recipe

Only after fresh independent exact-source approval and root's explicit lane
release, use the final reviewed full SHA in this own clean worktree:

```sh
cd /workspace/sightbreak-linux-profile-fixture-native-types
mkdir -p .local
python3 -B scripts/linux_profile_acquire.py --execute-frozen-source FINAL_REVIEWED_FULL_SHA > .local/linux-profile-acquisition-r2-wrapper.stdout 2> .local/linux-profile-acquisition-r2-wrapper.stderr
```

The fixed output/claim is new and absent at this checkpoint. Retain the initial
and terminal tool results in a new
`.local/linux-profile-acquisition-r2-outer-tool-receipt.json`, including actual
exit status. Do not reuse r1 or infer whole wall time from a terminal polling
duration. Root must confirm lane availability; the wrapper still refuses a
busy fixed CPU/display admission and never selects alternatives.

Only source inspection, pure Python checks and Git operations ran here. No
Godot, compilation/import, generated UID, export, Xvfb/native fixture, profiler,
OCR, CI, service, heavy process or nested agent ran. GDScript syntax, actual
text export/resources, fingerprints/pixels, runtime cleanup and cadence remain
unverified. The next action is fresh independent exact-source review.
