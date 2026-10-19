# V3 integration and independent validation — live progress

Status: **in progress; development only; no new candidate verified**.

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
| Astra durable-receipt recovery, PR #18 | `astra/systems-v3-recovery` | Source handoff received; not integrated or independently accepted |
| Astra trade-read batching, PR #19 | `4a8e9ea73aa8b286d9f1751b0a6b485479737294` | Neutral SQL-count verdict frozen; no introduced source defect found; source binding and retained actual-response/state proof still required |
| Astra input freshness / prediction | `f3ceaad` / separate prediction investigation | Reserved source modules acknowledged; independent handoff validation pending |

The published **74/74 matrix**, separate **12/12 ten-client campaign**, and
exported-client flows are **V2 results**, not V3 results. They must be repeated
on a clean frozen V3 commit before any corresponding V3 claim.

## Active slices

1. Bot input independently reproduced and blocked. [Exact-head source review](https://github.com/calebaiken/sightbreak/pull/14#pullrequestreview-5576455853) and [compact raw evidence](three-agent-evidence/development-v3/ai-input-review/REPORT.md) are published. External helper aliases are diagnostics, not working-match adapters or a measured integration win.
2. Graphics verdict frozen before mapping: 39 randomized matched pairs and six chronological sheets. [Published source-bound evidence](three-agent-evidence/development-v3/graphics-input-review/REPORT.md) finds candidate `79a9591` loses normal-pickup composition to V2 despite clearer shade cloth; the whole input is held. The conspicuous calm magazine entry belongs to the **old baseline**, not the candidate. [A separate corrected PR binding](three-agent-evidence/development-v3/graphics-pr-binding/README.md) verifies eleven visual blobs against the real PR #2 head without rewriting the packet's invalid-token failure. Separate incomplete continuity tests are not an acceptance claim.
3. Integration provenance/process/HUD corrections remain pre-freeze. Critics reproduced late-descendant false-success in the matrix and export watchdog; shared pre-launch containment now rejects it while retaining actual root exits. The campaign's real CPython control also rejects the escape; artifact verification is being updated to the same boundary. Passing tooling controls are not native campaign results.
4. Freeze the integration commit, run the full maintained matrix and separate twelve-condition ten-client campaign, then export and independently inspect the actual packaged bytes and executable entry points.
5. Run completion-driven exported network and living-player offline input flows. Publish exact source, all retained attempts, checksums, independent critique and development artifacts. Source defects return to their source PR; no runtime claim precedes a new frozen-source run.

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
| Backend neutral packet | Verdict frozen at `2026-10-19T19:46:36.4321805Z`; report SHA-256 `f76906b5b3ee735d65eedef6bf23998d274a614778fb9e76c196ba39957bfdfa`. Prefers K for statement counts only; no identity or general latency/state-safety acceptance. [Missing-receipt request](https://github.com/calebaiken/sightbreak/pull/19#issuecomment-6275871795) is posted |

## Current observations and limits

- Host: Windows; official Godot `4.7.2.stable.official.ed1daf0bf`. Installed Python 3.14 crashes at unittest shutdown on both frozen-baseline and new tooling; raw failures are retained. Explicit isolated CPython **3.13.15** exits normally for the controls above; it did not change the system registry/default interpreter.
  WSL is not installed. Linux/X11/PostgreSQL/export checks require the matching
  isolated CI host; local unavailability is not a pass or a waived gate.
- The initial low-storage/tool failure is retained in session history; free
  space recovered externally. This agent did not delete caches or user files.
- Windows checkout uses `core.autocrlf=true`. The historical Linux **on-disk**
  shipping-content digest is not expected to equal a CRLF checkout digest;
  record actual bytes and Git tree separately, and do not claim a hash match.
- Exact export identity now includes commit, game tree, physical runtime bytes and validation-source bytes. Re-attesting old exports, reusing evidence directories and packaging altered payloads/modes are rejected. These corrections still require the final frozen native/CI validation.
- Portable native Windows launching and process cleanup are implemented. Linux `/proc` resource measurements are explicitly unavailable/null on Windows, never fabricated zero measurements. Bash/X11-only matrix groups remain unavailable locally and require isolated Linux CI.
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
