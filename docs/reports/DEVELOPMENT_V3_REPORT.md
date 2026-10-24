# V3 development candidate — frozen-source validation

**Status: independently audited automated development candidate.** This is not
a release approval or an 8.5-quality acceptance. The frozen source below must not
be confused with later documentation commits.

## Source and run

| Item | Identity |
| --- | --- |
| Candidate source | `4099facb21a9242d41df79fd9e75bbbea031f2e0` |
| Integration branch | `integration/sightbreak-v3-validation` |
| Draft integration | [PR #17](https://github.com/calebaiken/sightbreak/pull/17) |
| Completed Linux run | [40082291663](https://github.com/calebaiken/sightbreak/actions/runs/40082291663) |
| CI conclusion | Success; all three jobs and both exported-client flow steps succeeded |
| Package metadata | `0.3.2-dev`, build `5`; the menu has a stale `0.3.0-dev` label, recorded below |
| Historical V2 reference | `701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd` |

The [fresh-context independent audit](three-agent-evidence/development-v3/ci-attempts/run-40082291663/AUDIT.md)
checked the collected source identities, matrix, separate network campaign,
audio controls, packaged bytes/modes and actual exported-client evidence. It
found no blocking contradiction within **automated development-candidate
scope**. Its 319 static audit predicates are not additional game tests or scores.
No downloaded executable, backend, network or native workload was rerun by the
offline reviewer. Original CI execution and independent receipt inspection are
distinct records.

| Frozen source fingerprint | Value |
| --- | --- |
| Game Git tree | `9624d64bab5da8fc32b74c79b3d2997ac2eabf3f` |
| Linux checkout shipping-content SHA-256 | `f3c1e5681180640b391da1ca811b4b9be9b07045ff035d27f126c4b5a3bfeb4d` |
| Validation-source SHA-256 | `90c81de87900ef776a68fbcac37f17bc0e74e7ed135154bf40a014ec992e68c5` |

The manifest indexes 368 validation-source files; the shipping digest covers
126 game files. These are actual Linux checkout bytes, not a claim that a
Windows CRLF checkout has the same physical digest.

## Verified execution scope

| Slice | Audited outcome | Boundary |
| --- | --- | --- |
| Maintained matrix | **83/83 groups**: 81 command groups with complete exit-zero/cleanup receipts and two audit groups | A larger tooling inventory is not a gameplay-performance gain |
| Separate network campaign | **12/12 conditions**, ten clients each, 18 seconds; 132 client/server reports and logs inspected | Twelve parent exit/containment receipts; individual child numeric OS exit receipts were not retained; synthetic loopback, not cellular/device qualification |
| Disposable audio controls | Ten baseline groups, **386 checks / zero failures**; A5/A6/A7 caught through **6 / 1 / 1 expected assertion failures** | Five actual PCM16 mono 44.1-kHz WAVs inspected; expected exit-one assertions, not crashes; source restored; no separate root OS receipt |
| Package verification | All three delivery ZIP inventories, bytes, modes and source receipts match; extracted Linux ELF and console wrapper smoke exits are zero | Android debug-signature/metadata inspection; unsigned iOS project inspection, not physical-device or Xcode build acceptance |
| Actual exported network client | **36.653 s** within a 240-s watchdog; six authority-observed shots, rendered **30/90 → 30/84** after native-key reload; normal exit zero | Only `08-settled` is reload-ready; the earlier completion-named frame still shows animation. Not frame-synchronous timing or animation-quality evidence |
| Actual exported offline client | **50.191 s** within a 300-s watchdog; rendered health **100**, sidearm **14/60 → 15/59**, ammunition conserved; normal exit zero | Live HUD frames inspected during ordinary offline Field Menu pauses; not continuous play or a manually completed match |

Both UI flows use the same verified ELF. The window advertises the delete
protocol, receives the standard X11 client message and exits normally; neither
frame-limited quitting nor cleanup termination is counted as a pass. Source
checks after UI use are enforced by the controllers, although a separate
serialized UI-after source snapshot was not retained.

The strict scan covers 402 logs: 27 matching lines in nine files are explicitly
classified as expected negative controls, injected backend outage, cross-version
rejections or a historical archived texture leak. There are **zero unclassified
matches**, not an assertion that every archived log is error-free.

## Development downloads and checksums

These are expiring GitHub Actions artifacts for the exact source above, not a
public release. Sign-in/repository access may be required. The collected
transport digests match GitHub's published digests; no later availability check
is implied.

| Download | Transport SHA-256 | Recorded expiry (UTC) |
| --- | --- | --- |
| [Development packages, manifest and verification](https://github.com/calebaiken/sightbreak/actions/runs/40082291663/artifacts/12555294271) | `dbf76bc50deb2555a9b6de992b4855b245202db449f83da51688749bf85e5f8d` | 2026-11-07 09:34:58 |
| [Matrix and separate network evidence](https://github.com/calebaiken/sightbreak/actions/runs/40082291663/artifacts/12556088968) | `28e628481544cc2f2b527569b41285616e87efafb489fa0af91b3c3afb6feb67` | 2026-11-07 10:00:44 |
| [Disposable audio-control evidence](https://github.com/calebaiken/sightbreak/actions/runs/40082291663/artifacts/12555647143) | `04e15d2ae44097170c7301c0f2f9169514eb7d2cab92e58931d6ab4d9d17d6a1` | 2026-11-07 09:37:00 |

The development artifact contains these independently checked delivery payloads:

| Payload | Bytes | SHA-256 |
| --- | ---: | --- |
| Linux ZIP | 36,501,474 | `dca1e4a0869bc7ae626df018c0957121e6e4fe1f89ff5af579747c10ecd09526` |
| Linux ELF | 84,208,840 | `638b86b04c68174b96c3c7e8cef50d978c0deaf331fda190ca40052d38ca105e` |
| Android ZIP | 62,893,372 | `70e459a1350d83e57494ba6e01c0adb82e3604fcc6d8c169ae28bfce4869b23a` |
| Android APK | 67,465,751 | `309ebd3787f881068f552f3c6c369f865f35bd30fa374b34699a266ba0754b12` |
| Unsigned iOS ZIP | 129,588,216 | `f2c111d6295e763fb62710e2a39d0678eb7c088702b4a4c0bddb784c8e31ee4c` |

Android is a debug-signed API 24–36 ARM64/x86_64 package. iOS is an unsigned
Xcode project, **not an IPA**. The original manifest, checksums and verification
receipts are retained with the artifacts and compact audit packet.

## Changes included in this freeze

- **Participant-private trade reads:** the bounded batching change from
  `4a8e9ea`, with the reviewed bind-cap, imported-fixture provenance, and retained
  artifact verification sources. This is a query-work improvement for the
  reviewed slice, not a universal latency or backend-safety claim. Small-read
  timing regressions and the historical capture-attribution limits remain in
  the [mapped review](three-agent-evidence/development-v3/backend-input-review/round2-mapped/README.md).
  Its retained matched 40-trade/20-item workload reduces SQL statements from
  **1,643 to 8**; five reviewed workloads improve and two tie on query count.
  These are the mapped slice's measurements, not a new production-latency
  benchmark from the combined candidate.
- **Additive snapshot observability:** `0fbce120`, plus an engine-generated UID.
  The [frozen review](three-agent-evidence/development-v3/snapshot-observability-review/REPORT.md)
  supports additional diagnostic information and a captured legacy-output tie,
  not improved movement accuracy. Observations are reconciliations, not every
  accepted wire snapshot or consumption-time positions. Instrumentation cost
  with prediction disabled remains unmeasured.
- **Validation repairs:** isolated subprocess mocks, X11 close-protocol setup
  before client launch, advertised-protocol checks, and ordinary offline menu
  pauses while OCR inspects already-captured live HUD frames. Positive health,
  ammunition conservation, authority evidence, clean normal exit, source
  identity, timeouts, and process containment remain required.

Prediction remains default-off, protocol remains `6`, and live shots remain
non-rewound. Offline OCR inspection pauses do not establish continuous-play
performance or a manually played complete match.

## Retained failures and pre-freeze controls

The [previous `2a026e6` run](three-agent-evidence/development-v3/ci-attempts/run-39880125007/AUDIT.md)
remains **failed**: 82 of 83 matrix groups passed, the matrix-harness unit failed,
and both exported-client flows failed. The network flow timed out during normal
close; the offline flow correctly rejected an eliminated player. Its successful
network, audio, and package substeps do not turn that candidate into a pass.
The earlier [zero-job workflow rejection](three-agent-evidence/development-v3/ci-attempts/workflow-rejected-7b6a71a/README.md)
is also retained.

Before this retry, [280 normal and 74 optimized tooling-test executions](three-agent-evidence/development-v3/retry-tooling-review/README.md)
passed under isolated CPython 3.13.15. These are tooling controls, not native or
device qualification. [Pre-commit custody checks](three-agent-evidence/development-v3/retry-freeze/README.md)
verified 2,450 publication payloads, 44 Python source hashes, and seven accepted
upstream source bindings. The independent CI-repair review includes its
source-custody drift addendum; it is not represented as an exact-commit native
execution audit.

Exceptional Linux supervisor death can still leave detached descendants whose
ownership is no longer provable. The harness reports cleanup uncertainty as a
failure; a successful ordinary run is not proof of durable recovery from that
exceptional path.

## Inputs held and gates still open

- **Confirmed presentation defect:** the menu still renders `0.3.0-dev` from a
  hard-coded label while the verified manifest/APK identify `0.3.2-dev`, build 5.
  This is not a different executable. It is retained as an open defect; correcting
  it requires a new source freeze rather than silently changing this candidate.
- PR18 receipt recovery remains excluded: successful original-commit recovery
  examples do not override the reproduced partial-success validation and
  unpublished journal-owner lock findings posted to its source review. The
  [native component controls and outcome review](three-agent-evidence/development-v3/recovery-contract-review/REPORT.md)
  keep predicate execution distinct from caller-source inference and retain the
  original failed native economy test separately from its DNS-calibrated fixture.
- PR20 input freshness remains excluded from this source. Its separate native
  component and neutral network evidence must not be credited to this run.
- The newer bot and graphics inputs remain held. The graphics comparison is
  mixed, including a normal-reload composition regression; it did not clear the
  repository's seven-category 8.5 bar.
- Human gunplay and full-match evaluation, physical-device installation and
  sustained performance, touch/gyro usability, signed iOS delivery, production
  infrastructure, and every unverified 8.5 criterion remain open.

See the [evidence index](three-agent-evidence/development-v3/EVIDENCE_INDEX.md),
[live progress](DEVELOPMENT_V3_PROGRESS.md), and
[reproduction guide](../engineering/DEVELOPMENT_V3_VALIDATION.md).
