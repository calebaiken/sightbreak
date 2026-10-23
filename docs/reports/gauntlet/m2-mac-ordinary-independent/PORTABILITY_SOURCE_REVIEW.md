# Independent test-root portability source review

Verdict: **APPROVE SOURCE** at
`3730273b65717c91565771beda700f66366c0346` for the narrow test-root correction.
Root must still supply the exact combined integration before another ARM
dispatch. No repeat or native gameplay result is accepted by this verdict.

Original run `39904830917`, job `120254254021`, at `34dbd97` failed the first
ordinary source-control command: 14 helper tests, four errors. Each original
traceback rejects the `/var` ancestor of a freshly created test temporary root.
The second controller command and actual ordinary Deploy/gameplay step did not
execute. The decoded original log is retained in `native-39904830917/`.

The frozen delta resolves only freshly owned existing TemporaryDirectory roots
in the two pure test modules, adds a two-test regression wrapper, and adds its
command to the same workflow source-control step. No assertions, original test
cases, runtime path guards, gameplay, controller, helpers, app staging or userdata
checks are relaxed. `macos_ordinary_input.py`, `verify_macos_ordinary.py`, the
existing Mac dependencies and the entire game tree remain byte-identical to
approved `bd9ac47`. The workflow has one additional pure command and no other
delta from that approval.

The new wrapper creates an owned physical directory and symlink, points the
test process's tempfile root at that alias, and reexecutes the complete 14-test
helper and seven-group mocked-controller suites. It requires exactly 21 cases,
success and zero skips. It separately requires the unchanged production
inventory guard to reject both the raw alias and an uncreated descendant.
Canonicalization occurs before test fixtures are passed to production functions;
production functions still reject caller-supplied symlinks.

The reviewer independently extracted `3730273` with `git archive` and ran:

| Pure check | Actual result |
| --- | --- |
| All normal candidate/original Mac controls | 59 top-level tests PASS |
| Helper/controller/new wrapper under an externally aliased TMPDIR | All three commands PASS |
| Independent actual-controller predicates and cleanup | 9 groups PASS |
| Original `bd9ac47` helper suite under the same alias | Expected FAIL: 14 tests, four errors |
| Original controller suite under the same alias | Expected FAIL: seven groups, 19 errors |
| Mutant restoring unresolved fixture roots in both corrected modules | Expected FAIL: wrapper detects 23 nested errors |
| Code/workflow diff whitespace | PASS |

The mutation changes only copied test files in the reviewer's disposable source
snapshot; the wrapper and runtime stay unchanged. Thus the added wrapper detects
the original defect rather than passing merely because its own fixture resolved.
Commands, explicit process exit codes and complete transcripts are retained in
`portability-3730273/`. `source.json` binds the tested source/workflow files and
the unchanged runtime hashes.

The largest remaining gap remains the unexecuted exported ordinary component:
private app/userdata isolation, real living fire/reload and original pixels,
FIELD MENU/LEAVE, and ordinary close within original bounds. The first run's
completed native suites/menu/iOS evidence belongs only to `34dbd97`; this pure
correction cannot acquire that source's native result. No engine, compiler,
service, OCR, CI dispatch or native input ran during this review.
