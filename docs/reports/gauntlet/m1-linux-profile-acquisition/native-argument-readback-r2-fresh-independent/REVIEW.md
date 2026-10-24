# Independent verdict

**ACCEPT SOURCE ONLY** at exact
`8da2add4279f3087320d4708c047f500baffd0ee`.

Fresh reviewer `/root/linux_thread_types_review_20261024` preregistered the
review in `4dbce79d` before inspecting changed code or test results. The reviewer
did not build this correction. No account, model or task switch occurred.

The four retained false accepts in rejected `93f32edf` are closed. For each
initial and terminal fingerprint, the candidate verifies the serialized-byte
hash, parses strict JSON, then requires both thread fields to be literal `True`
and identical to the already-strict outer observations. It then retains full
settings equality and exact initial/terminal fingerprint equality. Rehashed
integer `1` and float `1.0` values now fail the type guard. Corrupt hashes fail
before that guard. Literal true values pass under rebuilt hashes; differently
serialized initial and terminal snapshots still fail their existing equality
gate.

The direct source audit passes 9,622 predicates. Exactly three existing
non-document paths differ from rejected `93f32edf`:

- `scripts/linux_profile_overhead.py` adds precisely the five-line guard in
  `validate_condition`; removing it recovers the rejected bytes.
- `scripts/linux_profile_acquire.py` changes only the controller SHA-256 pin,
  from `d601956d...` to the exact corrected `3498d701...`; substituting the old
  hash recovers the rejected bytes. All supervisor function ASTs are identical.
- `scripts/test_linux_profile_thread_readback.py` expands one existing method.

All other 491 existing non-document paths retain their Git modes/types/blobs,
as do all 8,690 pre-existing document paths. This protects runtime, APIs,
diagnostic, graphics, engine pin, formulas, sample counts, order, selectors,
deadlines, CPU/display/LP settings, strict logs, source/payload/cache seals and
other supervisor pins. Builder preregistration `602980d7` is an ancestor of the
correction. All 45 original independent-report files are preserved exactly in
the retained rejection, including its failed outputs and unchanged rig.

Both the initialized own checkout and independently initialized depth-one view
pass, with zero skips:

| Controls | Methods | Result |
| --- | ---: | --- |
| Maintained acquisition | 38 | PASS |
| Maintained fixture/controller | 22 | PASS |
| Maintained readback | 9 | PASS |
| Unchanged original independent rig | 10 | PASS |
| Fresh adversarial rig | 7 / 190 cases | PASS |

The fresh rig covers both fields, each snapshot and both together; numeric true
equivalents; false, missing, null, string and container values; malformed or
missing inner settings; synchronized wrong outer/inner types; rebuilt literal
true positives; hash-before-type order; and preserved snapshot-byte equality.
The original rig is byte-for-byte `a8cf0d0` at its required relative depth.

The shallow view is exact `8da2add4`, shallow=true, one reachable commit, with all
494 non-document mode/blob identities matching the candidate. Its sparse checkout
physically verifies 124 materialized non-document files. It uses an explicit
shared local object alternate and stores zero local objects. This is a genuine
initialized shallow source view, not an independent network clone; the rejected
base object remains visible through the alternate. After moving the preserved
untracked harness outside the source view, both independent rigs pass again,
all loaded candidate module paths/hashes bind to that view, and source status is
clean. Acquisition, identities, raw outputs and the initial harness layout are
retained with their limits in [AUDITOR-SETUP-NOTE.md](AUDITOR-SETUP-NOTE.md).

Original evidence also verifies directly: all 370 R3 files / 276,747,038 bytes,
three outer records and the 58,661,240-byte R3 archive retain their original
hashes. All 377 archive member identities match the original independent
manifest. Archive SHA-256 is
`b3868bc6659e22cdf03ef2111c60e9e5d2c290552bc51ecddda57dcda19d0025`.
R4 output remains absent. Earlier tracked reports and archives retain exact Git
identities; this review does not substitute a fresh live audit of older R1/R2
process behavior.

The largest remaining gap is strict native qualification. The unchanged V-Sync
warning remains an explicit software-driver blocker. No Godot/native run was
made, no R4 release is authorized, and effective runtime readback, performance
and H1 remain unqualified. Original failures remain failures.
