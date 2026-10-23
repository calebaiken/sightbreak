# R4B R3 source-only declaration correction handoff

Fresh independent SOURCE REVIEW REQUIRED. No engine, import, render, OCR,
UID generation, CI or services ran. The local native lane remains reserved by
root for other work. This handoff authorizes no runtime and claims no native
compilation or pixel success.

Exact new source/method:
`108d1cdc6cf471daa7390298c234bb1c087ae865` on
`codex/m6-touch-contrast-recovered`. Product preregistration was pushed first
at `439bd2597836d3bb881e8e2c7711eb44efca6cb8`; the separately authorized
lexical accommodation was preregistered/pushed before code at `08548776`.
[Preregistration](R4B_R3_PREREGISTRATION.md) preserves both scopes.

The independently audited R2 failure is unchanged: handoff `384d17d`, exact
failed candidate/method `b001fc5`, actual verdict `5c5837123a951ec12c3e2ea0f2c3ec76071e6413`
is acquisition/import FAIL and failed-attempt preservation ACCEPT. Its raw
root and original stages remain immutable. All 628 raw paths/hashes/sizes and
both old 327-path source sets were rechecked unchanged while preparing this
handoff. No earlier R3/R4/R4B failure was rewritten or relabeled.

The product delta is **one declaration only**:

```diff
-var compact := key != "fire" and r < 32.0
+var compact: bool = key != "fire" and r < 32.0
```

[Exact product diff](r4b-r3-product.diff) and
[source-delta receipt](r4b-r3-source-delta.json) prove every other product byte
and the complete expression unchanged from the failed candidate. New product
SHA-256: `e0b7caeef4a2b8f7e176438be4bfd02af2e90da1b253ee2f88c1501ea3f246c9`.
The Godot log supports this hypothesis but has not observed the annotation.

The frozen pure helper previously required the inferred declaration spelling
and rejected an explicit bool declaration with AttributeError. That exact
[pre-correction rejection](r4b-r3-declaration-parser-precheck.json) is retained.
Root authorized the narrowly necessary lexical accommodation before code.
[Complete helper diff](r4b-r3-lexical-helper.diff) adds acceptance of exactly
the old inferred and new explicit-bool declarations, requires the original
compact expression, and rejects wrong type, changed expression, missing,
duplicate or unsupported declaration. No other paint declaration parser was
relaxed. Removing only paint_program from both helper ASTs yields identical
programs. Eight compiled expression bytecodes/constants/names agree for both
accepted spellings. Mathematical/geometry/paint/ownership predicates are
unchanged. Helper SHA-256:
`3462bb2c11fa168949295f436d9b2e3d954893df3119af972e11324880cbaf89`.

The native analyzer is byte-identical to the accepted R2 analyzer, SHA-256
`c47bb2fd7a3b8eab83765fd75ee76885815fc5ae467ffac6b99859e72be05141`.
Fixture, instrumentation, source/UID/background fences, ownership receipt
reconciliation, original 4.5:1/3:1 limits, complete glyph/one-code support,
visibility/occlusion and final-boundary semantics are unchanged. A genuinely
failing baseline remains comparable only with valid complete evidence.

[Sixty pure controls](r4b-r3-pure-freeze.log) passed, exit 0, in 13.854 seconds
under a 60-second outer pure-test cap on CPU4. These are the original 54
source/geometry/method/receipt controls plus six declaration controls with
subcases for wrong types, changed expressions, missing/duplicate/unsupported
declarations, old-parser rejection and identical compiled paint expressions.
The exact command and selector are in [the command receipt](r4b-r3-pure-command.json).
Synthetic receipt/pixel controls remain explicitly synthetic, not native.
The historical 32-case/2,482-interval certificate keeps its original source
scope; it was not regenerated or represented as new native/physical evidence.

New source-only stages:
`/workspace/sightbreak-touch-contrast-fixture-recovered-r4b-r3/{baseline,candidate}`.
Each has 323 exact original Git game paths, 327 verified source/fixture/UID
paths, 138 unique copied UIDs and no `.godot`. The new wrappers differ from
the original R2 wrappers only by the declared annotation for candidate; all
diagnostic draw receipts and fixture bytes are unchanged.

| Variant | Exact source | SOURCE.json SHA-256 |
| --- | --- | --- |
| baseline | a52022169241df9ff662039547a375e1c46ac1c5 | 8769df11adb16daefd652d6694b2917cf4ecd95db59e77bccfb99cc5a651788f |
| candidate | 108d1cdc6cf471daa7390298c234bb1c087ae865 | 0c20422fbe00cad2179f02e7244fdbdb41c78bbf42b9f548cb4b89d3082383cc |

[Staging audit](r4b-r3-staging-audit.json) and
[audit source](audit_r4b_r3_staging.py) compare every original path to exact
Git bytes, reconstruct wrappers and check UID uniqueness. The audit writes
deterministic report receipts; a reviewer should inspect it first or use a
read-only equivalent in its own report.

[SOURCE_FREEZE-r4b-r3.json](SOURCE_FREEZE-r4b-r3.json) binds 24 exact source,
method, fixture, control and preregistration files, with SHA-256:

`4282c67c984b1840ca43158b16c0ecb03f4254d01e5cb300478682cc8adbe921`

The [concrete blocked recipe](acquisition-r4b-r3/PLAN.md) reuses the reviewed
controller. Compared with the reviewed R2 controller, it changes only three
freeze filename literals. Controller SHA-256:
`96caeec75bad50a32e8bf3dc8cef88f1e492ac3e167ebed9b676b731d7fcc02c`.
The archival script has only report/source identity changes from the reviewed
failed-attempt recipe. Its full and identity-only diffs are exposed. Source
checks verify AST equality after those exact identity restorations and syntax
of all three admission/post-run inline Python snippets.

Keep the original producer order, one attempt, 30/300/600-second caps,
CPU0–3/threads2, explicit unused :131, private userdata and all source/UID/
background fences. Original analyzer/final wait/archive lack a whole-operation
hard timeout; no whole bound is claimed. Preserve strict orphan/unclaimed
StringName/resource failures and actual current PGID/display checks, including
observation limits. Do not add a native wrapper, retry, extension or later
manual producer after STOP.

Future raw root remains ABSENT:
`/workspace/sightbreak-touch-contrast-native-recovered-r4b-r3`.
The future original matrix remains 32 scenes/source, 2,816 PNGs/source plus
16 fresh shared backgrounds, full ownership maps and complete original gates.
Root must separately release that one new attempt after fresh source review.
No compile/import pass, pixel count, contrast, visual preference or physical
result is inferred from this source-only correction.

The biggest remaining blocker is unobserved pinned native compilation of the
new source. All actual glyph/visibility/ownership/contrast, dark-surround,
heavy-plate, scene-occlusion and fresh blind-image gates remain unqualified.
Keep the final-boundary identifiability falsifiers and failed comparisons.
Live HUD, dynamic joystick/custom layouts, physical touch/reach, accessibility,
human play and release acceptance remain open. CS2 reference-host restrictions
remain explicit; no shipped-game parity claim follows.

Pure reproduction only:

```sh
timeout 60s taskset -c 4 env PYTHONPATH=scripts python3 -m unittest -v test_touch_geometry_r4b test_touch_method_r4b test_touch_receipts_r4b_r2 test_touch_declaration_r4b_r3
```
