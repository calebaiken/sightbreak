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
| PR #14 bots | `48eb0586e273f96dc20b346ed444d00ab0f3ac30` | Native independent reproduction pending; not accepted from claims |
| PR #2 art | `bb5212dd596571653bd37eb85a4594a72bfd1abc` | Owner head refreshed |
| Art reconciliation on PR #16 | `79a9591350854373076e62a4707ec84edc803756` | Fixed-condition blinded native comparison pending |
| Native UI / research / expected-price guard | `7e41de6` / `7dd0628` / `228c382` | Already in V2; no new source change asserted |

The published **74/74 matrix**, separate **12/12 ten-client campaign**, and
exported-client flows are **V2 results**, not V3 results. They must be repeated
on a clean frozen V3 commit before any corresponding V3 claim.

## Active slices

1. Independently reproduce source-owner bot corrections and remaining regressions.
2. Generate unlabelled baseline/candidate native graphics pairs before reading
   the new candidate's quality/performance claims; retain mapping and verdict.
3. Fix integration-only provenance and Windows harness defects, with adversarial
   controls that fail on the old implementation and pass on the correction.
4. Freeze the integration commit, run the full maintained matrix and separate
   network campaign, then export and independently inspect actual packages.
5. Run the exported network and living-player offline input flows; obtain a
   fresh-context integration critic and publish raw evidence, checksums and
   development artifacts. Remaining source defects go back to their source PR.

## Current observations and limits

- Host: Windows; official Godot `4.7.2.stable.official.ed1daf0bf`, Python 3.14.
  WSL is not installed. Linux/X11/PostgreSQL/export checks require the matching
  isolated CI host; local unavailability is not a pass or a waived gate.
- The initial low-storage/tool failure is retained in session history; free
  space recovered externally. This agent did not delete caches or user files.
- Windows checkout uses `core.autocrlf=true`. The historical Linux **on-disk**
  shipping-content digest is not expected to equal a CRLF checkout digest;
  record actual bytes and Git tree separately, and do not claim a hash match.
- Integration source review found that export completion compares only runtime
  bytes, and packaging permits a different source commit with the same game
  tree/content. Adversarial reproduction and exact-identity correction pending.
- Native Windows network runners currently assume executable Bash wrappers,
  POSIX process groups and `/proc`; portability correction is in progress.

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
