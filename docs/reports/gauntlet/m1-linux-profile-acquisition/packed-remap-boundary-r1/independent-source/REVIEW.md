# Fresh independent packed import source review

**Verdict: ACCEPTED SOURCE ONLY** for exact candidate
`ec6b34ce9af4db1199cd5266b2f7cfcc9831f5ef`, implementation
`7965320db8fbac4598eeb86fc191e589d08b61de`. The candidate wins against
`216d39ada8f9d11e2d8544d01fde42da49607b14` for this byte boundary: it reads
the retained genuine exported remap and preserves the tested rejection gates.
The original reader raises `Extra data: line 4 column 1 (char 26)` on those same
bytes. This verdict does not accept an actual artifact, seal, native condition,
H1 result or release gate.

The largest remaining gap is the first complete R3 artifact inspection and
subsequent native acquisition. The positive here uses actual failed metadata
inside a synthetic ELF/PCK. It does not establish that every other resource,
seal, pixel/fingerprint comparison, condition, cadence result or cleanup will
pass. R2 stays FAILED; all four original performance conditions and H1 remain
unreached.

## Independence and ordering

Reviewer worktree `/workspace/reviews/linux-packed-import-fresh-source`, branch
`codex/linux-packed-import-fresh-source-critic-20261023`, started from exact
candidate. [Criteria](PREREGISTRATION.md) were committed as `5fe346a7` before
detailed candidate code, handoff or output inspection. Mission/NEXT, AGENTS,
installed original Gauntlet, No AI Slop/eval and project workflow were read and
reused. The parent supplied candidate identities and the known failure before
registration; this was a fresh independent code review, with no blind A/B claim
and no self-assigned score.

Only this exact report directory is authored. No canonical, candidate, native,
Godot, import/export, render, Xvfb, CI or nested-agent action ran. Python review
work ran on CPU 4. Maintained acquisition tests use fake processes, and the
independent harness forbids `subprocess.Popen`.

## Exporter evidence and original bytes

I independently fetched four files from Godot commit
`ed1daf0bf001b61586d9930840f2f1394092c079`. Full URLs, response status, sizes
and SHA-256 hashes are in [retrieval identities](upstream-retrieval.json).
Fetched third-party source stays untracked under `.local`.

- `editor/export/editor_export_platform.cpp:1693–1699` serializes the import
  configuration, converts it to `CharString`, then copies `cs.size()` bytes into
  the resource sent to `save_file`.
- `core/string/ustring.cpp:1968–2012` allocates UTF-8 length plus one and writes
  the trailing zero. `core/string/ustring.h:182–184` returns allocated size from
  `size()` and subtracts one only for `length()`.
- `core/io/config_file.cpp:123–143` writes LF after each encoded assignment.

Together these explain LF followed by a single terminal NUL in a nonempty
exported remap. This is evidence from the pinned implementation.

[Source audit](source-audit.json) compares the candidate's packed and staged
fixtures directly with immutable independent packet `eec4c7e1`; it compares the
retained reader with the exact original source blob. It also matches the packet's
resource MD5/size/SHA-256 and readback bytes. The packed input is 193 bytes,
SHA-256 `e8717d3311cb7cd3fb716324b219d948e6f7d68fbae1b33d9163add59b4c2203`;
the staged input is 1,020 bytes,
`9b48fb27282e20a5408a15c911b83134130c1fa359d172c35d02d46a7690d76f`.

The independent original reader reproduces the exact exception above. Candidate
parsing produces the staged remap value; the actual input also passes the full
inspector in a rebuilt synthetic pack with valid resource MD5s. No candidate
inspection continued the original R2 ELF or acquisition. The independent actual
R2 critic owns the full native/archive verdict; this source review makes no new
full-original-archive claim.

## Boundary and preserved defenses

The only production call to `packed_import_sections` comes from the packed
`.import` branch after `unpack_payload` has checked the template relationship,
ELF/PCK tables, resource bounds, overlap, names, flags and every resource MD5.
MD5 is a resource integrity check; source binding also relies on the pinned
template, frozen staged SHA-256 inventory, source ledger and exact resource
comparisons. MD5 alone is not an authenticity claim.

The helper requires a final `LF NUL` pair and exactly one NUL across the whole
input. It removes only that final representation byte, then uses strict UTF-8
and the import parser. It does not strip arbitrary whitespace or zero bytes.
The existing parser's accepted blank lines/comments remain part of its grammar.
This review does not claim byte-for-byte reconstruction of all exporter text.

Both staged and packed parsers reject raw C0/C1 controls except LF, duplicate
sections/assignments and duplicate JSON keys, including escaped aliases and
nested objects. The unchanged finite-number decoder runs before the added
duplicate-field pass. Packed/staged remap equality, expected section sets,
source identity, safe cache targets, cache bytes and closed resource set remain
enforced. Escaped value changes in packed metadata reject against the frozen
staged value; no general ban on every JSON string escape is claimed.

Staged import parsing now decodes `original_bytes`, the same bytes already
matched to the frozen size/SHA-256. An independent hook changes the staged file
immediately after its first byte read and forbids a separate text read: parsing
uses exactly that authenticated first observation, with one import byte read.
This is a same-read guarantee, not continued filesystem immutability.

The [exact source diff](source-diff.json) preserves the reviewed delta.
The complete tracked union has 9,142 paths, including 493 non-doc paths.
[Every non-doc path/mode/blob](complete-source-union.json) is inventoried: 489
are unchanged; exactly four differ. All other changes are inside the builder's
component report directory. Candidate source equals implementation source.

| Path | Audited scope |
| --- | --- |
| `scripts/linux_profile_payload.py` | Import control/duplicate checks, new packed boundary, two import read replacements. Other top-level functions/classes are AST-identical. |
| `scripts/linux_profile_acquire.py` | Exactly one replacement: fixed output R2 to fresh R3. Reversing it yields original bytes. |
| `scripts/test_linux_profile_acquire.py` | Exactly one synthetic remap terminal NUL; reversing it yields original bytes. |
| `scripts/test_linux_profile_acquire_remaps.py` | Added byte-pinned actual-failure regression and malformed-input controls. |

The supervisor's remaining bytes, controller/evaluator/scene/fixture, pins,
shipping game, toolchain, selectors, graphics, source ledgers and formulas are
unchanged. This preserves Godot 4.7.2, protocol/economy/privacy constraints,
CPUs 0,1 for future native work, display `:99127`, OFF/ON/ON/OFF, 1,320-second
whole cap, original phase caps, 180-second condition caps, 10% warm-up/median
criteria and 5% within-mode drift criteria. No threshold was relaxed.

## Tests and retained failures

| Fresh execution | Own sparse checkout | Initialized depth-one exact candidate |
| --- | --- | --- |
| Maintained acquisition | 38 pass | 38 pass |
| Maintained fixture/controller/evaluator | 22 pass | 22 pass |
| Independent controls | 10 pass | 10 pass |

Raw outputs: [own acquisition](own-acquisition.txt), [own fixture](own-fixture.txt),
[own controls](own-controls.txt), [depth-one acquisition](depth-one-acquisition.txt),
[depth-one fixture](depth-one-fixture.txt), [depth-one controls](depth-one-controls.txt).
The [independent harness](independent_controls.py) records [66 cases](own-controls.json)
and an equivalent [depth-one result](depth-one-controls.json): 64 expected
rejections and two positive observation rows. Fifty-two adversarial cases first
pass the complete resource-MD5 unpacker, then fail semantic/staged/ECFG/ledger
inspection. Eleven additional structural mutations rebuild resource hashes
before corrupting path/table/bounds/overlap/template/trailer structure. One
invalid-MD5 control proves zero packed-remap parser calls before rejection.

The maintained new remap method separately rejects the builder's 82 rebuilt-MD5
boundary/value/control mutations. Independent attacks add invalid UTF-8 forms,
escaped and nested duplicate fields with equal decoded values, JSON tails and
overflow, matching staged/packed unsafe targets, rehashed staged controls,
unbound resources, changed cache, ECFG selectors/types/count/tail, source ledger
changes, and structural binary attacks. No independent counterexample remained.

The first own acquisition discovery failed with two import errors after 30
methods because the sparse selection omitted the tracked correction-r1/r2
retained-rejection helpers. [Original failure output](own-acquisition-initial-sparse-failure.txt)
is preserved. I restored those exact tracked directories and reran the same
suite; I did not skip or reinterpret the failed run. An initial file search also
reported `rg: tests: No such file or directory`; maintained tests reside in
`scripts`. This search error did not alter a test result.

A first precommit whitespace check also failed on single-space blank context
lines in the raw unified diff evidence. The [exact failure](precommit-diff-check-failure.json)
is retained. I preserved the complete diff bytes in JSON, then reran the check.
This representation change did not change candidate source or test outputs.

The builder's earlier duplicate-object acceptance failure remains in
`../retained-failure/initial-duplicate-object.txt`. The current import-local
duplicate check corrects that failure; the shared decoder stays unchanged.
The original R2 artifact exception and its actual acquisition failure remain
preserved. This review did not rerun native work or reinterpret failure as pass.

The initialized fixture is `.local/depth-one`, with exact candidate HEAD,
shallow=true, one reachable commit and clean status. Its complete Git tree
equals the candidate. Original, implementation and preregistration commit
objects are absent, verified by expected negative probes in the source audit.
The tests use retained bytes and do not require historical Git.

## Conditions for a separately admitted actual R3

The source correction has no remaining source-review condition. It still needs
a separate root lane release and actual critic preregistration before ONE new
R3 supervisor invocation at the approved full SHA. Verify that source remains
clean, create `.local` before wrapper redirection, and retain the initial and
terminal outer tool results. Preserve the R2 output, claim, receipts and failures.
No retry, manual continuation, fallback, selector change or formula change is
admitted by this review.

The unchanged supervisor requires the R3 output to be absent and creates a new
exclusive `attempt.claim`; it cannot resume an existing output. A read-only
[pre-release observation](pre-release-observation.json) found exact clean builder
HEAD and no R3 output or claim at 2026-10-23T11:43:58Z. This observation has a
timestamp; root must check its actual admission state before execution.

All full artifact/seal/native/H1 conclusions require the fresh original outputs
and independent actual review. Source approval alone closes none of those gates.
