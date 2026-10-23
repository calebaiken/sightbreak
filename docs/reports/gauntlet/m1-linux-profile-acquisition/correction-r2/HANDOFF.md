# Correction R2 source handoff

Ready for fresh exact-source review; runtime remains held. Implementation is
`a442523f`; the enclosing report freeze binds its exact source in `source.json`.
[Preregistration](PREREGISTRATION.md), committed and pushed at `149e6ddd`, preceded
code. The [R1 independent REJECT](retained-rejection/REVIEW.md), exact controls,
raw failures and initial metadata are retained from
`c339065c80e13a945b87c7f01a65655639be8281`. Original and R1 reports remain unchanged.

The correction has two changes to the outer acquisition:

- Log binding and validation read raw bytes once. Identity and strict-log
  analysis consume that same read; the observed identity must match the first
  accepted identity and any caller-supplied expected bytes. There is no later
  unchecked semantic `read_text` read.
- The existing complete source checker runs at one named boundary: **after
  output-manifest readback and before overall publication**. The receipt's
  `publication_source_observation` records its scope, source commit, start/end,
  original deadline and result. This observation remains under the original
  final/whole budget. Its claim covers the finite checker interval; it asserts
  no perpetual source immutability afterward or after return.

The last source check can create gate-bound Git command logs after
`outputs.json`. That manifest retains its original scope: files preceding its
publication. The complete `overall.validated_evidence` registry additionally
binds these terminal Git logs and the manifest itself, before overall is written.
Closed-set validation checks the complete registry. The manifest is neither
rewritten nor retried, and no prior evidence identity is replaced.

## Evidence

[Maintained acquisition suite](pure-controls/acquisition.txt): 31 methods pass,
zero errors/skips. It retains all ten original falsifiers and all 64 R1
publication mutations. Four new methods cover the same-read contract, final raw
log mutation, unchanged positive/source-drift controls, and source-observation
deadline boundaries. The positive finish at `60.999 < 61` passes; finishes at
`61` and `61.001` fail without moving the original deadline.
[Unchanged fixture suite](pure-controls/accepted-fixture.txt): 22 methods pass,
zero errors/skips.

[Isolated replay](replay.py) imports exact target source copies and asserts their
path belongs to the temporary tree. It writes only the R2 report directory:

| Source/control | Methods | Failing assertions | Errors |
| --- | ---: | ---: | ---: |
| Exact `04bc153e`, unchanged original controls | 3 | 10 | 0 |
| Exact `d0d94bec`, unchanged R1 boundary controls | 3 | 2 | 0 |
| R2 source, unchanged original controls | 3 | 0 | 0 |
| R2 source, maintained boundary controls | 4 | 0 | 0 |

All valid positives pass. [Replay summary](pure-controls/replay-summary.json)
binds the source/control hashes; each row has separate raw output and per-case
JSON. [Corrected boundary results](pure-controls/corrected-boundary.json) show
the raw validator really observes changed clean log bytes and exits 1/false.
They also show the source check count increase after manifest-time mutation,
the actual checker rejecting the dirty source, and exit 1/false.

The critic's exact old log falsifier injects through `Path.read_text`. R2 removes
that route. Its exact two-failure R1 reproduction is preserved; the corrected
test explicitly adapts the injection to before the real `Path.read_bytes` call.
The adapted hook must fire and the real raw read must observe the changed bytes.
A no-trigger old hook is not counted as a passing rejection control.

The first replay accidentally loaded current source through the retained
control's path-derived sys.path. Its [raw output](pure-controls/initial-replay-path-error.txt)
and JSON remain with an [explanation](pure-controls/INITIAL-HARNESS-NOTE.md).
The corrected runner loads byte-exact controls inside the isolated tree and
asserts the controller import path. No acquisition code changed for that harness
fix. The initial replay is not counted as a baseline result.

[Preservation check](pure-controls/source-preservation.json) verifies earlier
reports and retained review bytes, all nine pinned upstream files, unchanged
accepted fixture/controller/scene/tests and game tree
`55691684d31d44f1680141954bbe530443de9d1f`. Payload inspection/critical settings,
text packaging, graphics, one payload, OFF/ON/ON/OFF, 180-second condition caps,
phase caps and 1320-second whole cap are unchanged.

```sh
python3 -B -m unittest discover -s scripts -p 'test_linux_profile_acquire*.py' -v
python3 -B -m unittest discover -s scripts -p test_linux_profile_overhead.py -v
python3 -B docs/reports/gauntlet/m1-linux-profile-acquisition/correction-r2/replay.py
```

Only source inspection and pure Python ran, with fake/forbidden target Popen.
No engine/import/compile/UID/export/Xvfb/native/profiler/OCR/CI/service/heavy
process or nested agent ran. Actual export, GDScript compilation, graphics,
cleanup and cadence remain unjudged. Original Linux gameplay failures remain
failed. This is not a shipping improvement, complete-profiler-cost or gameplay
claim. Root must obtain fresh exact-source review before any runtime decision.
