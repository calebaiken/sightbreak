# Packed import text boundary preregistration

Source-only candidate, 2026-10-23. Exact base is
`216d39ada8f9d11e2d8544d01fde42da49607b14`; own worktree is
`/workspace/sightbreak-linux-packed-import-boundary`, branch
`codex/linux-packed-import-boundary-20261023`. Commit this record before
implementation. The builder cannot approve the candidate.

The original Linux R2 acquisition under root release `90a9cab6` remains failed,
exit 1. Import and export returned 0; artifact inspection rejects the final
metadata value of packed `assets/icon.svg.import` with `Extra data: line 4
column 1 (char 26)`. Seal, block and all four conditions were unreached. Preserve
the R2 source, raw outputs, claim, original failure and independent critic report.
No manual continuation or retry of R2 is permitted.

## Inspected reference

Godot 4.7.2 source at exact
`ed1daf0bf001b61586d9930840f2f1394092c079`, retrieved 2026-10-23 from
`https://raw.githubusercontent.com/godotengine/godot/` followed by that SHA:

| File | SHA-256 | Relevant behavior |
| --- | --- | --- |
| `editor/export/editor_export_platform.cpp` | `91d3c3866198da92686067b8bf72cbb1c29649494582aa3920dd5d9b79210516` | Lines 1685–1699 erase deps/params, encode import text, copy `cs.size()` UTF-8 bytes and save `path + ".import"`. |
| `core/string/ustring.cpp` | `fc403ff50652c5258bcf28d4b5ab5ac377301b656763c7ad87d9cf748bbbb903` | `String::utf8`, lines 1920–2031, allocates `fl + 1` and writes one trailing zero. |
| `core/io/config_file.cpp` | `8fc1b33c2cd9f827069e8289423d286524db3984be6ca45053fbe8736e908e82` | `encode_to_text`, lines 123–144, appends LF after every assignment. |

These are retrievable upstream source references, not a paraphrased format
assumption. Local fetched copies are outside the repository at
`/tmp/sightbreak-packed-import-upstream`. No third-party source is copied into
the candidate.

Independent critic failure inputs are packed 193 bytes SHA-256
`e8717d3311cb7cd3fb716324b219d948e6f7d68fbae1b33d9163add59b4c2203`, staged
1020 bytes SHA-256
`9b48fb27282e20a5408a15c911b83134130c1fa359d172c35d02d46a7690d76f`.
The critic's `native-r2-independent/payload-failure-readback.json` binds the
original ELF/PCK/table and original reader reproduction. Copy these two small
unchanged fixtures into this new report with their identities and retain the
exact original reader as an executable negative reference, independent of Git
history availability.

## Bounded change and measurable gates

1. Decode only the MD5-authenticated packed `.import` resource at its existing
   inspector call site. Require exactly one terminal NUL immediately after LF,
   remove that single representation byte, reject every embedded/repeated NUL,
   invalid UTF-8, raw control except LF, malformed value and trailing extra value.
   Staged import text receives no NUL exception. Keep section/key uniqueness,
   exact remap equality and every cache/source path check.
2. Reject raw controls in import section text so skipped whitespace/comments
   cannot hide a NUL or another forbidden control. Preserve ordinary LF-delimited
   Godot import text and strict JSON duplicate/nonfinite-value checks.
3. Use actual packed/staged bytes for the positive boundary test and original
   reader falsifier. Add valid-MD5 rebuilt-payload negatives for malformed
   boundaries, metadata, remap, source/cache and unauthenticated mutations. No
   synthetic permissive fixture may replace the observed failure.
4. Run all existing acquisition and fixture/controller/evaluator pure suites
   plus new tests on CPU 4 in a proper fresh depth-one fixture with required
   tracked game/report paths. Retain setup failures if any; repair setup before
   fresh passing output. Tests must not rely on historical `git show` objects.
5. Leave runtime fixture, Godot/editor/templates, protocol/gameplay, ECFG,
   MD5/SHA, source ledgers, path/privacy checks, caps/deadlines, formulas,
   selectors, OFF/ON/ON/OFF order, graphics and CPU/display pins unchanged.
   The sole supervisor delta besides the reader is fresh fixed output
   `builds/linux-profile-acquisition-r3`, so any separately admitted future
   acquisition cannot reuse R2. No new native wrapper is executed here.

Only source inspection, pure Python and Git operations are authorized here.
No native/Godot/import/export/Xvfb/CI/dispatch, nested agents, original evidence
mutation or canonical/root/contributor documentation edits. A fresh independent
source review and a separate root release must precede any R3 native attempt.
Passing the source gates does not qualify actual R3 packing, seal, conditions,
cleanup, cadence or performance.
