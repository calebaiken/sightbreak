# V3 integration and independent validation — live progress

Status: **automated development candidate independently audited at `4099fac`; release and human/device/8.5 acceptance remain open**.

The [candidate report, exact checksums and downloads](DEVELOPMENT_V3_REPORT.md)
refer to source `4099facb21a9242d41df79fd9e75bbbea031f2e0` and successful
[run 40082291663](https://github.com/calebaiken/sightbreak/actions/runs/40082291663),
not to later documentation commits.

Sol owns this integration, independent QA, validation harnesses and development
packages. Source owners retain their branches. Main and PR #11/#16 are not
rewritten by this isolated continuation branch, `integration/sightbreak-v3-validation`.

## Frozen reference and refreshed inputs

The reference remains `701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd`, published
in [the V2 report](STABILIZATION_V2_REPORT.md) at documentation commit
`d2439acdd5f73df7bae5ada62ee1e3dec2cf30db`. Its game tree is
`2d2b174c2145e9755ddfc78a1369e74443fcc400`. Historical evidence is retained,
including failed/discarded trials and the unresolved original cancellation failure.

| Input | Refreshed exact head | Disposition |
| --- | --- | --- |
| PR #11 reliability | `11573e587f13dfd832613a0c09dbc615f46d3461` | Already in V2 dependency stack |
| PR #16 combined alpha | `d2439acdd5f73df7bae5ada62ee1e3dec2cf30db` | Starting integration commit |
| PR #14 bots | `48eb0586e273f96dc20b346ed444d00ab0f3ac30` | **Blocked** by independently reproduced native match/actor contract regressions; V2 runtime retained |
| PR #2 art | `bb5212dd596571653bd37eb85a4594a72bfd1abc` | Owner head refreshed |
| Art reconciliation on PR #16 | `79a9591350854373076e62a4707ec84edc803756` | **Held** after frozen blind comparison: clearer shade cloth, but worse normal-pickup sleeve obstruction; no overall win |
| Native UI / research / expected-price guard | `7e41de6` / `7dd0628` / `228c382` | Already in V2; no new source change asserted |
| Astra durable-receipt recovery, PR #18 | `7b6f379a3f8c809d0985a64e883cbadfdd78d135` | Frozen neutral three-price restart comparison favors recovery. Separate native component controls reproduce shallow success-result validation and an unpublished staging-lock leak; both findings were posted to the source PR. **Held**, not integrated |
| Astra trade-read batching, PR #19 | `4a8e9ea73aa8b286d9f1751b0a6b485479737294` | Qualified narrow read-batching slice and exact direct-bind/fixture-provenance assurance sources are included in audited `4099fac`. Not part of the older failed `2a026e6` source; not a general latency or backend-safety claim |
| Astra input freshness, PR #20 | `f3ceaad98e089aa393c7f5fa650a52695094d979` | Frozen neutral network and native component verdicts favor the narrow guard. Released network-source binding is complete and supports consideration for a future integration freeze. **Not included in audited `4099fac`**; no new combined-source CI claim |
| Astra prediction observability, PR #21 | `0fbce120d8c17db58596d280f7d8401ab2aa0937` | Included in audited `4099fac` for **additive observability only** after frozen neutral and 830-check source binding. Legacy projections tie; no prediction-accuracy, transport or performance claim |

The historical **74/74 matrix**, separate **12/12 ten-client campaign**, and
exported-client flows remain **V2 results**, not V3 results. The new V3
**83/83 matrix**, separate **12/12 campaign** and exported-client flows have
their own exact-source receipts and independent audit below.

## Active slices

1. Bot input independently reproduced and blocked. [Exact-head source review](https://github.com/calebaiken/sightbreak/pull/14#pullrequestreview-5576455853) and [compact raw evidence](three-agent-evidence/development-v3/ai-input-review/REPORT.md) are published. External helper aliases are diagnostics, not working-match adapters or a measured integration win.
2. Graphics verdict frozen before mapping: 39 randomized matched pairs and six chronological sheets. [Published source-bound evidence](three-agent-evidence/development-v3/graphics-input-review/REPORT.md) finds candidate `79a9591` loses normal-pickup composition to V2 despite clearer shade cloth; the whole input is held. The conspicuous calm magazine entry belongs to the **old baseline**, not the candidate. [A separate corrected PR binding](three-agent-evidence/development-v3/graphics-pr-binding/README.md) verifies eleven visual blobs against the real PR #2 head without rewriting the packet's invalid-token failure. Separate incomplete continuity tests are not an acceptance claim.
3. Integration provenance/process/HUD corrections were frozen at `7b6a71a683ec5d1ed42d7245395c640225058e20` for isolated CI. Critics reproduced late-descendant false-success in the matrix, export watchdog and artifact verifier; shared pre-launch containment now rejects it while retaining actual root exits. The campaign's real CPython control also rejects the escape. [Retained before/after process controls](three-agent-evidence/development-v3/process-boundary-controls/README.md) include the failures and corrected results. [The latest serial receipts](three-agent-evidence/development-v3/pre-freeze-tooling-review/README.md) retain the failed OCR cleanup attempt and its contained-worker correction. Exceptional Linux supervisor-death cleanup remains explicitly unverified and fails closed; it is not claimed to recover every detached descendant. Passing tooling controls are not native campaign results.
4. Completed for `4099fac`: full maintained matrix, separate twelve-condition ten-client campaign, exports and independent inspection of actual packaged bytes and executable entry points. This is automated development scope, not release acceptance.
5. Both completion-driven exported-client flows passed on that source. Publish exact source, retained failures, checksums, independent critique and development artifacts. PR18 contract findings remain on their source PR; any runtime correction needs a new freeze and run.

## Frozen-source CI attempts

- [Run 39879374637](https://github.com/calebaiken/sightbreak/actions/runs/39879374637), source `7b6a71a683ec5d1ed42d7245395c640225058e20`: **workflow rejected before any job started**. GitHub does not permit `runner.temp` in job-level `env`; no matrix, campaign, audio control or export ran. This is an integration workflow defect, not a game-test failure.
- The narrow correction declares the three isolated audio paths in a runtime step through `$GITHUB_ENV`, using `$RUNNER_TEMP`. Checksum-verified official **actionlint 1.7.12** rejects the original source (exit 1) and accepts the corrected workflow (exit 0). This is source validation only, not a CI/native pass. [Original rejection and before/after lint evidence](three-agent-evidence/development-v3/ci-attempts/workflow-rejected-7b6a71a/README.md) are retained.
- [Run 39880125007](https://github.com/calebaiken/sightbreak/actions/runs/39880125007), exact source `2a026e61cabee3c66334066d45e92eb3ec6c2641`: **completed with failure**. [Independent receipt audit](three-agent-evidence/development-v3/ci-attempts/run-39880125007/AUDIT.md) verified all three transport digests, 2,714 outer archive members, source digests and validation inventory. Matrix results are **82/83 groups passing**; the sole failure is the Linux unit fixture's global `subprocess` mock reaching `platform.platform()`. This is not a Godot gameplay failure, but the full matrix still fails. The separate **12 × 10-client × 18-second** campaign meets its frozen harness/data gates; individual child exit-code receipts were not retained. The disposable audio run passed **ten baseline groups / 386 checks** and genuinely caught A5/A6/A7 through eight expected assertion failures, with restoration proof retained.
- The same audit checked all 61 members of the three inner package ZIPs, including hashes, sizes, modes and receipt identities. Packaged-build inspections and actual extracted Linux ELF / console-wrapper smoke exits passed their recorded gates. **Both full exported-client flows failed**: network firing/reload reached the settled frame but normal close exceeded the 240.141-second watchdog; offline reload inspection correctly rejected a dead/spectating player after 48.805 seconds. Screenshots and OCR agree. Substep successes do not make either flow or the candidate pass.
- [Run 40082291663](https://github.com/calebaiken/sightbreak/actions/runs/40082291663), exact source `4099facb21a9242d41df79fd9e75bbbea031f2e0`: **all three jobs succeeded; independent artifact audit supports automated development-candidate scope**. [Full scoped audit](three-agent-evidence/development-v3/ci-attempts/run-40082291663/AUDIT.md): **83/83 matrix groups**, separate **12/12 × ten clients × 18 seconds**, ten audio baseline groups / **386 passing checks**, three genuinely caught mutations and source restoration, all delivery bytes/modes/receipts, and both actual exported-client flows. The network flow exits normally in 36.653 seconds; the inspection-paused offline flow exits normally in 50.191 seconds with positive health and ammunition conservation. Exact checksums/downloads and evidence limits are in the candidate report. This does not rewrite either earlier failure.

### Repairs exercised by the successful frozen Linux retry

[Retained repair controls and independent critique](three-agent-evidence/development-v3/ci-repair-followup/README.md) cover the isolated matrix mock, pre-launch X11 close-atom setup with advertised-protocol validation, and ordinary offline Field Menu pauses while OCR inspects the original live HUD frames. The local 19 matrix, 14 UI, six HUD and 28 export-flow tests all exit zero. The critic additionally ran 26 synthetic controller controls and four protocol/layout checks without finding a scoped false-pass blocker. Its HEAD-drift addendum is retained: all 22 reviewed source hashes stayed unchanged, but this was not an exact-new-commit native campaign.

The successful `4099fac` Linux/X11 receipts now corroborate pre-created and advertised close atoms, normal exit, and rendered offline pause proofs. The offline flow is explicitly **inspection-paused**, not continuous play; positive health, real input and ammunition conservation remain mandatory. No failed artifact or result is overwritten.

[Pre-commit custody receipts](three-agent-evidence/development-v3/retry-freeze/README.md) verify all 2,443 published payloads in six completed packets against both physical and staged bytes. All 44 Python files still match the latest 354-execution serial run; seven accepted upstream files match exact staged Git bytes. These are source/publication audits, not another test run or frozen Linux acceptance.

The successful freeze includes the qualified backend read slice and bounded snapshot observability. The latter records reconciled observations, not every accepted wire snapshot or consumption-time error. Instrumentation runs even with prediction disabled; its overhead is unmeasured. Its new UID was generated by the checksum-verified official engine in an isolated one-script import; the subsequent full-game validation is separately recorded in this frozen run.

### PR20 source binding completed after candidate publication

[The separate post-freeze review](three-agent-evidence/development-v3/input-network-binding/REPORT.md)
binds frozen sample H to executed `77f2040` and identical production scripts at
`f3ceaad`, and T to reference `701ce2c`. It checks all 362 neutral payloads,
316 original Git counterparts and eleven source artifacts. H's recorded
InputStream digest is reproduced exactly using the documented mixed line
endings. Those reconstructed bytes are not an original captured working file
or proof of loaded cache/process identity.

The interrupted review worker had sealed its packet before the restart. A
separate read-only recovery audit verified all 29 ledger payloads, both ZIP
inventories (401 binding members and 363 neutral members), 316 original Git
counterparts, eleven source artifacts and eighteen production/config objects.
No engine, campaign, export or CI job was repeated. The narrow fully-ACKed
replay guard is source-qualified for future integration consideration; it is
not added to the already audited candidate. The 120-command intent cap,
different simulation/wall clocks, unsigned historical capture, limited cleanup
counters and untested stock-client long-blackout recovery remain explicit.

## Pre-freeze control receipts

These are tooling controls on the uncommitted integration, **not a verified V3 candidate**. External attempt directories are under `C:\Users\blith\AppData\Local\Temp\opencode\sightbreak-v3-evidence\` and are never reused.

| Control | Observed result / retained receipt |
| --- | --- |
| Identical runtime, different exporter commit | Old packaging incorrectly succeeded (`provenance-before`); corrected exact-identity unit rejects it |
| Fresh-source Git boundaries | Seven real isolated-Git tests exit 0: staged/untracked/deleted source, untracked documentation, two dirty byte states, ignored outputs, same bytes/different commit (`real-git-controls-20261019T191905Z`) |
| Portable process/network controls | Initial 57 mocked controls retained; new 58-test suite includes real CPython exited-root/late-descendant rejection and exits 0 (`campaign-containment-20261019T194928Z`). No native workload executed |
| Living-player OCR | Initial unreadable ammunition substring failed a negative control; corrected four-test suite exits 0 (`hud-revision-20261019T191733Z`). Blank/zero/dead/ambiguous health is rejected |
| Prior correction batch | Manifest 23, matrix harness 8 and export UI 6 tests exit 0; the earlier OCR failure is retained in `tooling-revisions-20261019T191236Z`, not overwritten |
| Original harsh integration critique | `critic-before-20261019T190803.5556140Z-18b0b5af`: 77 evidence hashes checked; manifest SHA-256 `a66a6c06b5eb63cc7a6a33c6a76d66cff1763161acd565f4a8817d518b39ed75`. Reconstructed source is labelled; unavailable original fixture bytes/receipts are not invented |
| Export watchdog descendant control | `export-flow-descendant-20261019T1939301091253Z`: entry exit 1, actual worker exit 0, failed receipt, stopped descendant and no late output; serial 27-test retry passes. Paging-file-exhausted parallel attempt retained |
| Artifact verifier descendant control | `verifier-descendant-20261019-154834-904`: prior false pass reproduced; corrected root exit 0 is rejected with failed receipt and stopped descendant. Normal and optimized suites each run 74 tests, actual exit 0 |
| Final serial tooling batch | `final-tooling-serial-20261019T195617Z`: eight suites / 161 tests, all actual exit 0. Pre-freeze pure/synthetic controls only; artifact-verifier and audio suites are separate |
| Latest source-stable serial retry | `pre-freeze-tooling-20261019/attempt-20261019T201340147085Z`: ten normal suites / **272 tests**, plus **74 optimized verifier tests**, all actual exit 0 with unchanged Python source hashes. Its preceding OCR cleanup failure is retained. These 346 test executions are pure/synthetic tooling controls, not 346 native groups |
| Post-repair source-stable serial retry | [Retained latest receipts](three-agent-evidence/development-v3/retry-tooling-review/README.md), attempt `20261024T091611731546Z`: ten normal suites / **280 tests**, plus **74 optimized verifier tests**, all actual exit 0 with unchanged Python source hashes. Four transferred backend assurance files also pass AST and exact Git-normalized source checks; no PostgreSQL/backend test run is claimed |
| Last bounded critic / test-only follow-up | [Original failing reproduction and corrected control](three-agent-evidence/development-v3/freeze-followup/README.md): isolate the Windows mock from shared POSIX pathlib. The existing unit passes with POSIX-initialized stdlib on Windows; all 17 matrix-process tests exit 0. These pre-freeze controls remain distinct from the later actual Linux matrix |
| Audio-control harness | `negative-audio-harness-20261019T195154884107Z`: 32 pure/mocked tests exit 0; an earlier CRLF-control failure is retained. Independent source/contract critique ran those 32 tests plus nine guarded probes without finding a scoped false-pass blocker. Actual `2a026e6` and `4099fac` native captures are separately audited above |
| Backend neutral packet | Verdict frozen at `2026-10-19T19:46:36.4321805Z`; report SHA-256 `f76906b5b3ee735d65eedef6bf23998d274a614778fb9e76c196ba39957bfdfa`. Prefers K for statement counts only; owner disclosed K=candidate after the freeze. No general latency/state-safety acceptance. [Missing-receipt request](https://github.com/calebaiken/sightbreak/pull/19#issuecomment-6275871795) and [source-assurance feedback](https://github.com/calebaiken/sightbreak/pull/19#issuecomment-6275997901) remain open |

PR #19 subsequently retained actual canonical response bodies and full-table
before/after snapshots in documentation commit `89215fbd81e8a1fb5eede134d789cde61544eda3`.
The second neutral verdict was frozen before opening its mapping: report SHA-256
`1248f66b7b80e2acbf69595ef084b164957547497f7c40c2e56c4489847fcf3e`.
It verifies 168 actual response-event references and 336 table / 28 aggregate
hashes, preferring V for SQL work in five workloads with two ties. The two
smallest workloads regress in median latency by approximately 32% and 60%.
[Source-mapping and assurance handoff requested](https://github.com/calebaiken/sightbreak/pull/19#issuecomment-6354432171).
This is new evidence, not a retroactive repair of the first packet; eight empty
money/receipt-related tables add no money or retry qualification, net-equal rows
do not prove no transient writes, and shared-host timings are not production
latency evidence. After separate mapped source and assurance review, the narrow
shipping read-batching change was cherry-picked locally as `88bfc51`. Its direct
500-bind limit and actual imported-fixture guards were transferred from the
exact reviewed assurance commits; an independent AST and Git-normalized byte
check passes for all four transferred files, without executing backend tests.
The later combined `4099fac` matrix passes on its own frozen source.
This does not make the earlier CI source include it
or turn descriptive timings into a production claim.

[The first-round source-binding archive](three-agent-evidence/development-v3/backend-input-review/round1/binding/POST_FREEZE_ADDENDUM.md)
retains an additional attribution failure: the recorded measured candidate app
hash does not match the pinned Git app bytes or the tested newline constructions.
The cause is not established; a clean-worktree label does not repair it. The
historical SQL-count arithmetic remains auditable, but complete executed-app
byte binding must not be claimed. [The source review](three-agent-evidence/development-v3/backend-input-review/source-review/original/SOURCE_REVIEW.md)
remains inspection-only, with its saved controls explicitly unexecuted. A later
retained mutant can be reversed and its mixed line endings normalized to the
shipping app hash. That is a post-hoc reconstruction, not the missing original
execution-time app capture; the historical first-round attribution failure is
still retained.

## Current observations and limits

- Host: Windows; official Godot `4.7.2.stable.official.ed1daf0bf`. Installed Python 3.14 crashes at unittest shutdown on both frozen-baseline and new tooling; raw failures are retained. Explicit isolated CPython **3.13.15** exits normally for the controls above; it did not change the system registry/default interpreter.
  WSL is not installed. Linux/X11/PostgreSQL/export checks require the matching
  isolated CI host; local unavailability is not a pass or a waived gate.
- The initial low-storage/tool failure is retained in session history; free
  space recovered externally. This agent did not delete caches or user files.
- Windows checkout uses `core.autocrlf=true`. The historical Linux **on-disk**
  shipping-content digest is not expected to equal a CRLF checkout digest;
  record actual bytes and Git tree separately, and do not claim a hash match.
- Exact export identity includes commit, game tree, physical runtime bytes and validation-source bytes. Re-attesting old exports, reusing evidence directories and packaging altered payloads/modes are rejected. The successful `4099fac` source and package identities were independently reconciled; historical failures remain retained.
- Confirmed open presentation defect: the verified package metadata is `0.3.2-dev`, build 5, but the actual menu still renders a hard-coded `0.3.0-dev` label. Do not silently edit the tested source or call the label correct; a correction requires a new source freeze.
- Portable native Windows launching and pre-launch outer-runner containment are implemented. Standalone cleanup cannot prove ownership retroactively after a parent exits and reports that uncertainty as failure. Linux containment requires an affirmative cleanup receipt; exceptional supervisor death can still leave detached descendants outside recoverable ownership, so it cannot pass or be called verified cleanup. Linux `/proc` resource measurements are explicitly unavailable/null on Windows, never fabricated zero measurements. Bash/X11-only matrix groups remain unavailable locally and require isolated Linux CI.
- Shared-host memory pressure was reported by Astra. No new local ten-client campaign or editor import is being started concurrently; native bulk validation/builds are assigned to isolated CI. Existing failed/allocation-error attempts remain evidence, not gameplay regressions.

Reproduction and platform boundaries: [V3 validation guide](../engineering/DEVELOPMENT_V3_VALIDATION.md). Current actual-reference provenance: [CS2 references and unchanged rubric](three-agent-evidence/development-v3/CS2_REFERENCES_AND_RUBRIC.md).

## Acceptance remains unchanged

Use the seven-category rubric in [QA-0.3](QA-0.3.md#explicit-visual-rubric)
and [the specification](../SPECIFICATION.md): **8.5 in each applicable category**,
supported by current evidence. Historical scores are not new measurements.
Actual Valve-published CS2 reference images—not AI illustrations—inform visual
comparison; stills do not establish animation smoothness or device performance.

Physical Android/iOS installation and sustained GPU/thermal/battery behavior,
touch/gyro usability, human full-match/gunplay feedback, production deployment
and security remain **unverified**. A development package or passing assertion
count cannot waive them. Do not merge to main or call this release acceptance.
