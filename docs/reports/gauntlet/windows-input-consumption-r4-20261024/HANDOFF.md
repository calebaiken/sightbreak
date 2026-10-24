# R4 offline input-reader builder handoff

Frozen source is `642dd0e0543698cae5d90b9046d5875beabed111`, pushed on
`codex/windows-input-consumption-r4-20261024`. Base is rejected R3
`342c3641ab2fccd1fc875c84188a8395a9b93a96`. Independent source approval is
pending. This builder evidence qualifies no native execution, actual input,
disconnect cause, gameplay, physical device or whole release gate.

The new reader rejects all eleven source-impossible histories from fresh R3
critique `f8049be40286fff4ce8fe09159dbcf2db6874caf` and accepts its five valid
controls. It preserves coalesced second-peer acceptance, malformed input before
authority validation, unordered/duplicate endpoints and immutable queued input.
It checks cumulative/lifecycle history, persistent metadata, synchronous
receive/outcome counts and current accepted/consumed queue/ACK/actor state.
It does not reconstruct packets or claim complete acquisition coverage.

## Frozen scope and preregistration

Preregistration `74a55156`, expansions `3e906607` and `dd8d4c78` precede source
edits. Final critic corpus arrived before implementation; its unchanged exact
rig was replayed with the old reader in `old-reader-final-controls/`.
That replay reproduces historical38/38 and new5/16 (43/54 overall), with all
eleven false accepts retained. The old reader SHA-256 is
`cb5897cb61d774499af0d4ac17252773ecaf91a954f75968f5eddebb26983eea`.
Final reader SHA-256 is
`207beebe124a1ad5928a154fb77c99d2e43864ce236751dc7ce985878181bcb2`.

Exactly five tracked non-document paths change: the analyzer, shared declared
fixture, identity fixture construction, lifecycle restamping and the new
`test_input_consumption_state.py`. The original 32 test methods and all59
assertion-call ASTs remain unchanged. The positive malformed-payload mutation
uses equal negative count1 endpoints, with a real hidden rejection and later
valid receive. Historical unequal-endpoint data remains untouched.

The shared fixture now retains cumulative latest/welcome/snapshot metadata,
uses queue1 at acceptance, has no pre-pop ACK and reflects popped actor controls.
Restamping carries persistent metadata through lifecycle transitions. The reader
checks required global pipeline stages before state history, preserving existing
missing-stage error assertions. New tests add13 methods, with multiple adversarial
subcases and paired source-valid controls.

The full tracked non-document base/source union is bound in
`final-source-bindings.json`: 512 paths, 516 unique verified blobs, exact modes,
five allowed changes and507 protected paths. Both views materialize472 paths
and retain40 exact sparse omissions. Runtime, transport, RPC, authority, privacy,
economy, native/controller paths, CI and canonical documents are unchanged.

## Actual frozen checks

All checks run on CPU4. `run_pure.py` preserves the old union and adds the
lifecycle/state groups. Its existing platform-parser fixtures are pure tests;
this work performs no Mac file-handling review.

| Check | Actual checkout | Initialized depth-one |
| --- | ---: | ---: |
| Maintained pure union plus new tests | 219 methods, 3 inherited Windows skips, exit0 | 219 methods, same3 skips, exit0 |
| Shell syntax | exit0 | exit0 |
| Exact final fresh R3 controls | 16/16 | 16/16 |
| Source-corrected version of original38 | 38/38 | 38/38 |
| Required historical verdicts, explicitly adjudicated | 38/38 | 38/38 |
| Combined required verdicts | 92/92 | 92/92 |

The final outputs are `final-full-pure/`, `final-depth-pure/`,
`final-full-controls/` and `final-depth-controls/`, with adjacent stdout/stderr.
All full/depth control verdicts and result bodies are identical.

The exact historical38 expectations are retained, not redefined. Their31
negative cases still reject and their source-valid unordered positive still
passes. Six obsolete positive cases now reject because their observations
contradict the actual source: five independent25 positives and additional9
`coherent_control`. Thus unchanged historical expectations match32/38; it would
be false to claim38 unchanged expectations still pass. `replay_controls.py`
retains each original expected value and separately records the required
source-consistent rejection for those six cases.

The additional versioned38 fixtures preserve intended falsifiers while correcting
immediate queue/ACK/actor state. The two malformed-receive positives explicitly
include hidden rejection and later valid receive; the old impossible count1
projection is corrected to equal negative endpoints. The consumption-outside-
direct-batch positive includes a later coalesced acceptance and persistent
consumed metadata. Each versioned receipt lists its source anchors and exact
fixture changes. These are new fixtures, never edits to the historical corpus.

## Retained failures and provenance

`r3-critic-frozen/` is byte-identical to the corresponding files in critic commit
`f8049be4`, including original38, final54 results, source adjudication, manifest,
review and executable rig. `evidence-bindings.json` verifies every copied file
against its committed Git blob, all historical fixture hashes, exact old source
copies and unchanged assertion ASTs.

The original raw Windows client/server logs remain at their R2 tracked paths,
SHA-256 `ec5fe22c681a9bd5ea0577773e9421d7f0eca6d2711b77c8c124f4cdefff4ba4`
and `61937ac0d1c75f29f790ffc339a4dabaa0a29eac65e9c5da5b4c526835ed0757`.
The historical critic newline-normalized derivation is separately bound.
Original untraced Windows logs remain incomplete in all replays.

Preserved intermediate failures are:

- First implementation: three old-suite failures from stale fixture restamping
  and error-order expectations. Corrected fixture construction and initial
  required-stage checks restore the original assertions without weakening them.
- First versioned control replay:91/92. The consumption-outside-batch fixture
  changed its popped sequence then reverted its retained latest metadata on the
  next row. The explicit new version now retains that consumed metadata.
- First source freeze `3e688c8c` passes219 methods and92 verdicts in both views.
  Readback found a new test helper failed to advance inserted client snapshot
  age, making one old-reader counter subcase reject for unrelated freshness.
  Final freeze `642dd0e0` fixes only that helper. The old reader now fails20
  assertions across the13 new methods; the first19-failure run is retained too.
- The initial report `git add` refused the new sparse path; adding only this
  component report directory corrected setup before the preregistration commit.
- Packaging whitespace checks flag nine trailing spaces in preserved raw unittest
  stderr from failing subtests. Those bytes remain intact. Authored Python,
  Markdown and JSON pass the separate whitespace check; the raw finding is in
  `packaging-raw-whitespace-check.log`.

Both initialized depth views are preserved. Final setup uses
`.local/depth-one-final`, exact final HEAD, clean status, shallow=true, one
visible commit and a complete11728-path tracked index. It shares the explicit
alternate `/workspace/sightbreak/.git/objects`; it is not a self-contained clone
or independent object-closure proof. The builder worktree also shares the
existing repository object store. No full clone was made.

## Independent reproduction

From the R4 checkout, use fresh output paths:

```sh
taskset -c 4 python3 docs/reports/gauntlet/windows-input-consumption-r4-20261024/run_pure.py --source . --output /tmp/r4-pure-fresh
taskset -c 4 python3 docs/reports/gauntlet/windows-input-consumption-r4-20261024/replay_controls.py --source . --output /tmp/r4-controls-fresh
taskset -c 4 python3 docs/reports/gauntlet/windows-input-consumption-r4-20261024/bind_source.py --source 642dd0e0543698cae5d90b9046d5875beabed111 --depth .local/depth-one-final --output /tmp/r4-bindings-fresh.json
taskset -c 4 python3 docs/reports/gauntlet/windows-input-consumption-r4-20261024/verify_evidence.py --output /tmp/r4-evidence-fresh.json
```

`initialize_depth.py --source <exact source> --depth <fresh directory> --output
<fresh receipt>` creates another initialized sparse depth-one view with disclosed
alternates, if needed. The final control replay intentionally distinguishes
historical expectations from source-corrected requirements. The unchanged
historical R3 rig can also be run directly, where exit1 reflects the six obsolete
positive expectations; do not interpret that exit as an unexplained regression.

The largest remaining limitation is what these debug observations expose:
cumulative counters and coalesced stage projections do not identify packets,
prove terminal capture coverage, establish actual delivery, or explain the old
disconnect. A different independent critic must assess the frozen correction
and its explicit fixture changes before source acceptance. No native attempt,
dispatch, release or retry follows from this builder handoff.
