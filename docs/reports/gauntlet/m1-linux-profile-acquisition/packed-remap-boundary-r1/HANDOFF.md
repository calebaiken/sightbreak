# Packed import boundary source handoff

Unreviewed source/pure candidate. Code commit is
`7965320db8fbac4598eeb86fc191e589d08b61de`; the complete source/evidence freeze
is the commit containing this handoff. Preregistration `2e486554` was committed
and pushed before implementation. The builder has not approved a native run or
any acceptance gate.

The original R2 acquisition remains FAILED, exit 1, under root release
`90a9cab6`. Original import/export exit 0; artifact inspection stops at packed
`assets/icon.svg.import` with `Extra data: line 4 column 1 (char 26)`.
Seal, block and all four conditions were unreached. The independent failure
packet is pushed at `eec4c7e1` on
`review/linux-profile-acquisition-r2-actual-20261023`; its separate full archive
audit is outside this candidate. No R2 wrapper, claim, source or raw evidence
was changed. [Read-only preservation](original-preservation.json) binds the
original clean HEAD, wrapper/overall receipts, actual `attempt.claim`, ELF and
staged failing input. It is not a substitute for the independent full archive.

## Exact scope and reference

The [preregistration](PREREGISTRATION.md) identifies retrievable Godot source
at exact `ed1daf0bf001b61586d9930840f2f1394092c079` and SHA-256 identities of
the three inspected upstream files. Export lines 1693–1699 copy
`encode_to_text().utf8().size()` into packed `.import` bytes. `String::utf8`
allocates encoded length plus one and writes the trailing zero;
`ConfigFile::encode_to_text` appends LF after assignments. The observed packed
input ends LF + one NUL; its original staged form has no NUL.

`packed_import_sections` accepts exactly one terminal NUL after LF, removes
that one representation byte and parses strict UTF-8. Only the existing packed
`.import` branch calls it, after the full ELF/PCK parser verifies resource MD5s
and bounds. Staged metadata parses the same bytes already matched to the frozen
source inventory. Both import parsers reject raw C0/C1 controls except LF,
duplicate sections/assignments and duplicate JSON object fields. The shared
finite-number decoder remains unchanged; a second import-local JSON pass adds
duplicate-field rejection.

The first malformed-metadata run revealed that the shared decoder accepts
duplicate fields, contrary to an assumption in preregistration gate 2. Its
[failed output](retained-failure/initial-duplicate-object.txt) remains retained.
The import-local duplicate check fixes that negative without changing the
pinned shared evaluator. No other code failure or setup failure occurred.

The supervisor changes only fixed output `r2` to fresh `r3`. The synthetic
acquisition fixture gains the same one terminal zero as the pinned exporter.
New tests retain the actual 193-byte packed and 1,020-byte staged inputs,
their [identities](fixture-identities.json), the byte-exact original reader,
and the original independent failure readback. No third-party source was copied.

[Source audit](audit_source.py) and [source pins](source.json) verify the complete
unchanged tracked tree outside this new report and four listed source paths.
Of those four, three existing files change and one test file is added. It also
verifies the supervisor's complete original bytes after reversing only `r3`
to `r2`, and the original synthetic test after removing only its new terminator.
All shipping game source, pinned controller/fixture/scene, ECFG, payload hashes,
source ledgers, paths, privacy, strict logs, budgets, formulas, selectors,
graphics, CPU/display pins and OFF/ON/ON/OFF remain exact.

## Source/pure results

Both the own checkout and a fresh depth-one checkout pass all 38 acquisition
methods and 22 fixture/controller/evaluator methods, no errors or skips.
Seven new methods pin actual bytes, retain the original reader failure, prove
the actual boundary positive, run actual metadata through a synthetic valid-MD5
ELF/PCK, reject 82 rebuilt-valid-MD5 boundary/value/control mutations, reject an
unauthenticated resource before text parsing, and reject changed staged bytes
before parsing. Rehashed staged NUL also rejects. Existing source/cache/ledger,
MD5/ELF/ECFG/path, deadline, sealing, publication and ten original independent
falsifier controls remain passing.

The fresh fixture is `/workspace/fixtures/linux-packed-import-boundary-depth-one`
at code commit `7965320d`, with one reachable commit, shallow=true, clean status,
and sparse scripts/game/instructions/component reports. It contains the original
reader and actual bytes directly, so tests require no historical Git objects.
All Python checks ran under `taskset -c 4`.

```sh
taskset -c 4 python3 -B -m unittest discover -s scripts -p 'test_linux_profile_acquire*.py' -v
taskset -c 4 python3 -B -m unittest discover -s scripts -p test_linux_profile_overhead.py -v
taskset -c 4 python3 -B docs/reports/gauntlet/m1-linux-profile-acquisition/packed-remap-boundary-r1/audit_source.py
```

Saved evidence: [own acquisition](pure-controls/acquisition.txt),
[own fixture](pure-controls/fixture.txt), [own source](pure-controls/source-audit.json),
[depth-one acquisition](pure-controls/depth-one-acquisition.txt),
[depth-one fixture](pure-controls/depth-one-fixture.txt) and
[depth-one source](pure-controls/depth-one-source-audit.json).

## Held R3 recipe and remaining gap

Fresh independent exact-source approval and a separate root lane release are
required before one new R3 attempt. The new output and claim are absent. After
those separate conditions, use the final approved full source SHA in this own
clean worktree; root owns the terminal tool receipt and original whole/phase
boundaries:

```sh
cd /workspace/sightbreak-linux-packed-import-boundary
mkdir -p .local
python3 -B scripts/linux_profile_acquire.py --execute-frozen-source FINAL_APPROVED_FULL_SHA > .local/linux-profile-acquisition-r3-wrapper.stdout 2> .local/linux-profile-acquisition-r3-wrapper.stderr
```

Retain initial and terminal results in a new
`.local/linux-profile-acquisition-r3-outer-tool-receipt.json`. Preserve R2 in
full; no retry, manual continuation, fallback or selector/formula change.

The largest remaining uncertainty is the first complete artifact-inspection
and subsequent native boundary: this work exercised the actual failed remap
inside a synthetic pack, not a continued R2 inspection. Other packed resources,
seal, conditions, fingerprints/pixels, cleanup and overhead cadence remain
unobserved for R3. No Godot/native/import/export/Xvfb/CI/dispatch ran here, no
nested agents ran, and no root/contributor/canonical documents were edited.
