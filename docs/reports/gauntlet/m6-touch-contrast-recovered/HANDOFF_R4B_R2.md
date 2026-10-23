# R4B R2 method-only review handoff

SOURCE/PURE ONLY. No engine, native render/import, OCR, UID generation, live HUD,
export or runtime lane was used or released. Fresh independent source review is
required. R3 FAIL, R4 NO GO and R4B source REJECT remain retained.

Exact method freeze: `b001fc5087960729535f63c896b40d6dc25bd272` on
`codex/m6-touch-contrast-recovered`. [Preregistration](R4B_R2_PREREGISTRATION.md)
was committed/pushed first at `1cad5ca`.
[SOURCE_FREEZE-r4b-r2.json](SOURCE_FREEZE-r4b-r2.json) SHA-256:
`f9d292d7cb04fc129eee7df84fdc1c0591ae14600497bcf63aac0243cd7f2563`.
Analyzer SHA-256:
`c47bb2fd7a3b8eab83765fd75ee76885815fc5ae467ffac6b99859e72be05141`.

## Narrow correction

The prior method `2ea23f9` allowed a baseline native ownership receipt to
contradict replay without invalidating provenance. Fresh independent REJECT
`ce3510e3776c8fec42ef1de648b14a453c221724` is copied unchanged under
[retained-r4b-fresh-critic](retained-r4b-fresh-critic/REVIEW.md).

For both source variants, ownership validation now reconciles the complete
sample map against independent replay. Every isolated-footprint support pixel
implicitly claims its own action unless the native wrong-owner list names a
different action or the empty unclaimed winner. Support/wrong/unclaimed counts,
every coordinate and every winning identity must match. Missing, extra,
duplicate, malformed, unsupported/out-of-bounds and wrong-winner samples are
provenance errors. The complete missing/extra/wrong-winner differences remain
reported. Witness array ordering is irrelevant; the complete map is required.

Those errors propagate through audit_source to provenance_valid and the final
comparison for either source. A correctly recorded bad baseline retains valid
provenance, fails its product gate and remains comparable to a passing candidate.
The correction does not require the baseline to pass candidate quality gates.

Across game and scripts, only the ownership receipt validator and added pure
test code changed since the rejected R4B freeze. Product and native regression source,
geometry translator, fixture, sampling, source/UID/background fences, 4.5:1 and 3:1
thresholds, complete glyph/AA/occlusion checks, final-band predicate and all
earlier failures remain unchanged. No geometry or product correction is hidden
inside this method change.

## Retained verification

[54 pure controls](r4b-r2-pure-freeze.log), exit 0. The added controls cover 18
receipt mutations for both variants, full provenance and CLI rejection of each
contradictory baseline, and a genuine bad-baseline positive control. Marker
metadata explicitly stubs decoding/source geometry/contrast; it is not native.

The critic's original checks.py SHA-256 is
`82d9f52fca8e5af6c8296b3bc32ac6532df09cd69a2b912e9b7691c75b778266`,
matching the review original byte-for-byte. The
[replay driver](replay_r4b_critic_falsifier.py) executes its unchanged blocker
expressions against the rejected exact method and corrected method. The
[retained replay](r4b-r2-unchanged-falsifier-replay.json) shows the old false
accept, then provenance rejection for the false-zero receipt and forged `pause`
winner where replay selects JUMP. The entire old checks.py is historical and
still binds its rejected freeze; it is not falsely claimed to pass a new freeze.

[Positive full comparison control](r4b-r2-genuine-bad-baseline-control.json):
three accurately recorded FIRE failures (including an unclaimed pixel), zero
receipt errors, baseline provenance true/product pass false, and comparison CLI
exit 0 against the explicitly synthetic passing candidate. This distinguishes
invalid evidence from a valid product failure.

The prior 32-case / 2,482-interval geometry certificate is unchanged source support,
not a new native result. The fresh critic found no geometry blocker within its
declared cases. Its native raster/Vector2, dynamic joystick, custom-layout,
editing/reach, accessibility and reference-quality limits still apply. The
three retained final-band falsifiers remain: opaque U is not identifiable from
P/B/W alone, an inward band can pass an invisible outer contour, and component
minimum alpha does not prove every interior primitive's survival. Exact source
suppression, complete glyph gates and independent actual-image review remain
necessary. Builder controls do not grant acceptance.

## Exact prepared sources

New source-only projects:
`/workspace/sightbreak-touch-contrast-fixture-recovered-r4b-r2/{baseline,candidate}`.
Each has 323 original game paths and 327 verified source/fixture/UID paths, unique
UIDs and no `.godot`. The twenty-two frozen files match the exact method freeze.
The game tree is byte-identical to R4B product `2ea23f9`; only its source commit
identity changes in the fresh receipt. Original projects remain untouched.

| Source | Exact source commit | SOURCE.json SHA-256 |
| --- | --- | --- |
| baseline | a52022169241df9ff662039547a375e1c46ac1c5 | 8769df11adb16daefd652d6694b2917cf4ecd95db59e77bccfb99cc5a651788f |
| candidate | b001fc5087960729535f63c896b40d6dc25bd272 | a423eb35530201a0b6090a146a8211c802ea80c99c328d5879d391e28ea03780 |

Pure replay before runtime release:

```sh
PYTHONPATH=scripts python3 -m unittest -v test_touch_geometry_r4b test_touch_method_r4b test_touch_receipts_r4b_r2
python3 docs/reports/gauntlet/m6-touch-contrast-recovered/replay_r4b_critic_falsifier.py
python3 docs/reports/gauntlet/m6-touch-contrast-recovered/capture_r4b_r2_positive_control.py
```

The last two scripts write deterministic report outputs. An independent reviewer
should inspect them first or run read-only equivalents into its own report.

After fresh independent approval and a separate explicit root lane release only,
follow the prior R4B native recipe with this freeze and a NEW immutable raw root
`/workspace/sightbreak-touch-contrast-native-recovered-r4b-r2`. Keep pinned 4.7.2,
explicit unused Xvfb, private state/CPU selectors, original scene matrix and all
327-path before/after fences. The fixture and 2,816 PNGs/source plus sixteen new
shared backgrounds are unchanged. The actual per-pixel action_at receipt must
match replay exactly; preserve any mismatch as failure rather than relaxing the
rule or repairing that attempt.

Future frozen analyzer command, blocked and unexecuted:

```sh
python3 scripts/analyze_touch_contrast_r4b.py --baseline /workspace/sightbreak-touch-contrast-native-recovered-r4b-r2/baseline --candidate /workspace/sightbreak-touch-contrast-native-recovered-r4b-r2/candidate --backgrounds /workspace/sightbreak-touch-contrast-native-recovered-r4b-r2/backgrounds --freeze docs/reports/gauntlet/m6-touch-contrast-recovered/SOURCE_FREEZE-r4b-r2.json --out /workspace/sightbreak-touch-contrast-native-recovered-r4b-r2/recomputed.json
```

Retain actual commands, engine/renderer/source/CPU identity, every failure,
ownership witness, original PNG and cleanup in a hashed bounded archive. Root
assigns fresh actual-output and blind visual critics. No live HUD, physical
reach, custom-layout, complete accessibility or shipped-title gate is closed.
