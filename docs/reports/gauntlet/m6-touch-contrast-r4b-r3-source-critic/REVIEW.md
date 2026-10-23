# Independent R4B R3 source and acquisition-admission verdict

**ACCEPT for source readiness and conditional admission of the frozen recipe.**
This approves the declared source-only correction and identity-only recipe.
Root still must separately release ONE actual attempt after its current lane
clears. Native compilation/import, rendering and product quality remain
UNOBSERVED. The explicit bool is a compiler hypothesis, not a verified fix.

Reviewed exact product/helper `108d1cdc6cf471daa7390298c234bb1c087ae865` and
full handoff `b9bd7e62c70d3f5a061c4177ede6c73c21dc9d35`. This critic's
preregistration `0434dca0` was committed and pushed before executing checks.
The earlier independently audited R2 acquisition/import FAIL and preservation
ACCEPT at `5c5837123a951ec12c3e2ea0f2c3ec76071e6413` remain unchanged.
Earlier R3 FAIL, R4 NO GO and R4B source rejection retain their original scope.

## Independently established source facts

The entire game delta from failed source `b001fc5` is the one declaration:

```diff
-var compact := key != "fire" and r < 32.0
+var compact: bool = key != "fire" and r < 32.0
```

The expression, operands/order, indentation and every other game byte are
identical. Product SHA-256 is
`e0b7caeef4a2b8f7e176438be4bfd02af2e90da1b253ee2f88c1501ea3f246c9`.
Both preregistrations are ancestors of the code commit. Across existing Python
implementation, only paint_program changes. Removing that function from the
old and new helper ASTs leaves identical programs. Both exact declaration
forms compile the same eight programs, with equal bytecode, constants, names
and variable names. Replaying the old parser on the new source retains its
AttributeError. Forty independent mutations reject: wrong explicit types,
unsupported spelling/spacing/comment, absent/duplicate declaration, and changed
expression/operator/operand/order/numeric spelling/wrapping in both forms.
This is a narrow source parser for the frozen declaration, not a general
GDScript parser.

The full 24-file freeze equals exact source Git bytes and its hash/size
receipts. Freeze SHA-256 is
`4282c67c984b1840ca43158b16c0ecb03f4254d01e5cb300478682cc8adbe921`.
Native analyzer bytes still equal the accepted R2 method, SHA-256
`c47bb2fd7a3b8eab83765fd75ee76885815fc5ae467ffac6b99859e72be05141`.
All geometry/math/paint/ownership predicates, original 4.5:1 active-label/count
and 3:1 meaningful-UI limits, complete glyph/one-code support, visibility,
occlusion and final-boundary semantics remain unchanged.

Each fresh stage has 323 exact original Git game paths, 327 verified source/
fixture/wrapper/UID paths, 138 unique copied UIDs and no .godot. All new source
and wrapper bytes equal the old stage bytes after only the declared candidate
annotation; all diagnostic instrumentation receipts agree. Manifests match:

| Stage | Exact source | SOURCE.json SHA-256 |
| --- | --- | --- |
| baseline | a52022169241df9ff662039547a375e1c46ac1c5 | 8769df11adb16daefd652d6694b2917cf4ecd95db59e77bccfb99cc5a651788f |
| candidate | 108d1cdc6cf471daa7390298c234bb1c087ae865 | 0c20422fbe00cad2179f02e7244fdbdb41c78bbf42b9f548cb4b89d3082383cc |

Both original R2 stages retain their exact original manifests and all 327
source/fixture/wrapper/UID paths. Every one of the 628 original raw files
(10,619,634 bytes) still matches the original handoff manifest by path, size
and SHA-256. Its failed acquisition status and zero PNGs are unchanged. This
review rehashed the raw tree; the earlier actual critic's complete archive
verification remains that earlier verdict, rather than a new archive run.
The future R3 raw root is still absent.

Independent checks pass in 3.073 seconds on CPU4. The fresh single replay of
all 60 supplied pure controls exits 0: 14.745 seconds inside unittest, 15.102
seconds wall time under the original timeout 60s / taskset CPU4 command.
Complete raw output, command and receipt are retained here. Genuine agreeing
wrong-owner/unclaimed baseline product failures remain valid and CLI
comparable; contradictory receipts invalidate provenance for either source.
Synthetic marker/array controls remain synthetic. No native pixel or physical
claim follows from them.

## Recipe admission and conditions for the later actual audit

The new controller equals the reviewed R2 controller byte for byte after
restoring exactly three freeze filename literals. SHA-256 is
`96caeec75bad50a32e8bf3dc8cef88f1e492ac3e167ebed9b676b731d7fcc02c`.
The archival script equals the reviewed failed-attempt script after only its
report and exact-source identity literals. All eight packet receipts agree;
all three inline admission/exit/post-run Python blocks compile as Python.
They were inspected and syntax-checked, not executed.

The controller retains the exact producer order: pinned version; baseline and
candidate import; shared backgrounds; baseline and candidate controls; touch
and input_mode regressions for each source; frozen analyzer. It retains one
attempt, original 30/300/600-second waits, CPU0-3, two thread selectors,
private per-producer state, explicit :131, source/UID/background fences and
cleanup behavior. Ten possible engine invocations have wait caps totaling
3,330 seconds. Analyzer, final cleanup wait and archival compression have no
whole-operation hard timeout; this review claims none.

Source admission does not establish current lane availability or execute the
admission command. On root release, the existing preflight must recheck the
pinned binary/archive/member, current cgroup/CPU selectors, unused :131,
absent raw/archive/report, cache absence, every frozen file and both complete
stages. A nonempty release variable alone is not authority. Any failed
admission must be retained separately, without weakening its checks.

The fresh actual-output critic must preregister and then verify these facts
from the original new attempt, rather than inheriting this source verdict:

1. Exact root release precedes admission. Commands, source/UID pre/post fences,
   engine binary/archive/member/version, actual renderer/capture metadata,
   CPU/cgroup/thread/display/private-state selectors and producer order agree.
   Import exit 0 cannot override native compiler errors. Any additional compile
   issue stops the new attempt; no repair, retry, cap extension or later manual
   producer is allowed after STOP.
2. Recursively inspect every original native/private-state log with strict
   warning/error/leak checks, including orphan or unclaimed StringNames and
   resource reports. The controller's narrower SCRIPT ERROR / Parse Error /
   ERROR regex is not a strict-cleanliness certificate. Preserve every finding,
   even with native exit 0, and reject strict-clean claims when any such finding
   exists. Controller acquisition completion, numeric quality and strict log
   cleanliness are separate observations.
3. Observe actual PID/PGID identity/membership where available; independently
   scan all available /proc records for terminal members and check :131 socket
   and lock absence. Recorded leader absence alone cannot prove descendants
   are gone. Disclose missing live observations and unreadable records; derived
   PGIDs from start_new_session are source inference rather than live getpgid
   evidence. Never kill unrelated processes or remove unrelated display locks.
4. Require the exact original 32 scenes/source and all 2,816 PNGs/source plus
   sixteen fresh shared backgrounds (5,648 PNGs), original dimensions/insets/
   requested and source-derived effective scales/backgrounds/states/actions,
   every original/wrapped normal equality, and every image/scene/capture/hash
   and background receipt. Partial captures remain archived failed attempts.
5. Independently replay the complete native ownership map for both sources.
   Counts, coordinates and winning identities must all agree without duplicate,
   unsupported or malformed samples. A truthful failing baseline remains
   comparable; receipt contradiction invalidates provenance. Run the unchanged
   frozen analyzer and reconcile its original JSON/log/exit, all 608 candidate
   gated rows and all 48 retained intermediate rows per source, with complete
   glyph/one-code visibility/occlusion/affordance/contour support. No threshold
   change, hidden-pixel exclusion, footprint shrinking or favorable subset.
6. Verify full immutable raw/archive/member/part/reassembly hashes and exact
   acquisition status/error, with actual cleanup and packaging exit retained.
   Preservation can pass while acquisition or quality fails. Inspect original-
   size dark surrounds, heavy plates, glyph collisions and scene occlusion;
   select independent worst-row pixel witnesses. A separate fresh blind judge
   receives comparable actual normal-image pairs, without the key. This critic
   knows the sources and cannot supply that blind verdict.

## Largest remaining gap and retained limits

The immediate largest gap is pinned native compiler observation of the new
explicit-bool source. The old failure log supports the hypothesis but cannot
observe its outcome. All actual pixels, complete native ownership, contrast,
visibility, font/occlusion and fresh blind-image gates remain unqualified.

The three final-boundary identifiability falsifiers remain applicable: opaque
P/B/W cannot identify U; an inward contrasting band can approve an invisible
outer contour; component minimum alpha cannot prove every interior primitive
survives. The historical 32-case / 2,482-interval certificate retains its
original source scope and was not regenerated. Neither it nor this exact-byte
review establishes new native rounding or physical touch behavior.

Live HUD, dynamic joystick/custom layouts, physical touch/reach, complete
accessibility, human play, broad integration and RC/release acceptance remain
open. Recorded CS2 reference-host restrictions still block shipped-game parity.
No whole acceptance gate advances from this source verdict.

Read AGENTS/CLAUDE, current mission/ownership records and the installed original
GauntletLoop, SIGHTBREAK gauntlet and No AI Slop/eval workflows. No engine,
import, render, UID generation, OCR, native execution, CI, service, heavy test
or nested agent ran. Only this critic's report directory changed. Initial
staging of the preregistration hit the sparse-path guard; adding this own
report path to the sparse selection resolved that setup failure before the
preregistration commit and before substantive checks.

Reproduction, source/pure only:

```sh
timeout 60s taskset -c 4 python3 docs/reports/gauntlet/m6-touch-contrast-r4b-r3-source-critic/checks.py
timeout 60s taskset -c 4 env PYTHONPATH=scripts python3 -m unittest -v test_touch_geometry_r4b test_touch_method_r4b test_touch_receipts_r4b_r2 test_touch_declaration_r4b_r3
```
