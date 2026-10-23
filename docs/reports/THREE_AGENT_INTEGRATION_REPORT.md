# Three-agent development integration

**Development checkpoint; request changes, retain draft. The complete 8.5/10 acceptance gate is NOT met.** Native Godot execution, source-bound platform exports and real multiplayer recovery work in the measured paths. Independent AI behavior, visual quality and audio/cleanup failures remain. Passing economy/network groups do not override these failures. No main merge, source-branch rewrite, real-money purchase, public game server or physical-device test occurred.

## Recovery and source identity

The republished cloud environment started successfully. Shell, Git, GitHub fetch/push/API, five CPUs, about 17 GiB RAM and 30 GiB free storage were available. Backend dependencies import under Python 3.12.14. Existing Docker PostgreSQL 17 recovered and served isolated test databases; existing Xvfb/Mesa llvmpipe and Android SDK 36/Java 21 worked. Project launcher uses **Godot 4.7.2 ed1daf0bf**; the unrelated system `godot` is 4.6.3 and was not used for project tests. Existing engine/templates/tools were reused. `environment_status` observed running/current, but its policy enforcement state was unknown; actual permitted GitHub calls succeeded. Network-enabled executor commands were needed for GitHub and local sockets. The first default-sandbox attempts failed before network access was granted; they are not evidence of a broken repository.

Source PRs, descriptions, outstanding reviews and merge bases were fetched live. All 14 original PRs remained open. Main remained `e67f2c86777d98d3cb3ad6bc7e851ef1826af26d`.

| Input | Frozen source |
| --- | --- |
| PR11 base, unchanged | `11573e587f13dfd832613a0c09dbc615f46d3461` |
| PR1 foundation, already contained in PR11 | `148760e19ae14755ced379245df6c5510ad4cdd4` |
| PR10 reconnect, already contained in PR11 | `8100d350b0a7117e986a8d59a953c9bd33e47222` |
| PR14 Gemini tactical AI | `d66e72c763dfe4cdcbeb9f2a76a89ec97fdd1d26` |
| PR2 Claude graphics | `ed8575454452d8f67c006814a1917fa6cc24fb46` |
| PR12 Claude native UI | `7e41de635a92763bd608203faf2c4689255bf727` |
| PR13 research, documentation only | `7dd0628410589136a8ec128de1e1c9b0c1543133` |
| Separate Codex price guard, draft PR15 | `228c382` |
| Complete shipping runtime | `ed3711e` |
| Full regression matrix controller | `10fdba0` |
| Verified local exports | `d5ff8da85c9c1122676efdcab12502064a517657` |
| Frozen delivery/recovery follow-up checkout | `4316c58c8f5ae38ea924631fc48e4b1e7d5df873` |

Branch: `integration/sightbreak-three-agent-alpha`, isolated from PR11. Exact export game tree: `8af5ec1b628162dfb6d21a631e26f565b4915dad`; shipping content SHA256: `d04973b061f69dda6df7c55242555b25811093e0fcc53df82d9841d05814bb20`. These runtime identifiers remain identical through later tooling/evidence commits. AI comparisons used `4aa6263`; all four AI/arena/match/actor files are byte-identical to the final runtime. Complete identities and merge bases: [manifest](three-agent-evidence/environment/integration-source-manifest.json).

No previously implemented networking system was recreated. The new branch preserves PR11's recipient snapshots, interpolation, optional prediction, bounded admission, durable results and reconnect recovery. Original dependency PRs 3–8 remain independently reviewable.

## Shared-file reconciliation

- Gemini merge `9f730dc`: `match.gd` merged automatically; validation inventory conflict retained all network/reconnect suites plus the new AI suite. Runtime compilation exposed published API mismatches. Narrow match adapters call `create_team_state`, `create_state`, `choose_buy_weapon`/authoritative `buy_weapon`, `compute_bot_input`, and the actual damage/elimination dictionary/time signatures. Round reset now invokes the published round-plan selector. One module property changes `smoke_charges` to existing `actor.smokes`.
- Published AI tests also called nonexistent profile/destination/hold/damage APIs, used nonexistent `reserves`, and expected historical protocol 2. Tests now use actual APIs, authoritative reserve and protocol 6. Real wall queries wait for physics synchronization; incidental match ticks are disabled in unit fixtures. The failing attacker-hearing assertion remains intact. No negative assertion was removed.
- Graphics merge `0345a18`: only development-status/validation inventory conflicts; retain both records and every suite. **Against exact Claude graphics, `actor.gd` differs only in movement constants/delegation to SBMovementStep.** ViewmodelShading, rigs, shaders, assets, reload phases and presentation remain Claude's. No art source was rebuilt or rewritten by Codex.
- UI merge `cad5c0c`: validation inventory conflict retained connection lifecycle and fixture drift checks. Research merge `4aa6263` is clean. Client price binding is a separate narrow payload change, after backend review.
- Independent method comparisons prove network/server files are byte-identical to PR11, ordered RPC declarations unchanged and only seven AI hooks differ in match. Authority reload/fire/ammo/purchase methods are unchanged. See [independent integration review](three-agent-evidence/integration/REPORT.md).

## First independent native AI validation

Frozen PR14 fails Godot parsing: match hooks call methods absent from its own module; the regression also calls absent APIs. After compatibility adapters, native execution reaches the retained failure: **non-carrier attacker bots do not investigate nearby audible gunfire**. Details, minimal native probes and baseline data: [independent AI review](three-agent-evidence/ai/REVIEW.md).

Other reproduced source defects remain assigned to Gemini: three defender anchors lie inside expanded solids and can still yield a zero navigation step; unseen damage-direction turning is overwritten by later movement/scan logic; Easy's 18 m hearing cap is bypassed by a second hardcoded 22 m loop; difficulty sound-noise values are unused. This is not a recipient-snapshot leak. The contact/LOS paths retain smoke and wall tests, but the original memory-expiration role assertion is vacuous and does not establish complete memory correctness. Additional long-horizon fairness testing is still required.

Same native harness, real 60 Hz physics, ten bots, seeds 1847/2026/3141, all difficulties and two naturally resolved opening rounds per condition: **18 baseline + 18 integrated rounds**. No injected winner/objective state. RNGs are seeded; this is a small observational sample, not a balance study or device benchmark.

| Baseline → integration | Easy | Normal | Hard |
| --- | ---: | ---: | ---: |
| Target switches / engaged decisions |9.46% →4.21%|9.36% →13.17%|17.08% →25.67%|
| Commanded-movement stall ratio |6.05% →5.75%|5.58% →7.24%|2.97% →15.65%|
| Plants / defuses |0/0 →0/0|2/1 →2/2|3/1 →0/0|
| Mean CPU microseconds / bot decision |50.5 →91.7|53.6 →124.7|54.2 →134.6|

Easy improvements do not generalize. No independent 8.5 AI acceptance is granted. CPU measurements are on a shared software-rendering host. Both comparison harness processes emitted exit-only ObjectDB warnings, 43 baseline/4 integrated; attribution remains unresolved. The focused AI regression fails only its hearing assertion. Natural full-match/halftime testing is separate in the maintained matrix. Offline bot rewards remain training-only; ranked payload gates remain unchanged.

## Native presentation and UI

Four fresh native 60Hz stepped reload captures cover sunlit, shade, backlight and default reduced motion, with authoritative timers, ammo and event CSVs. Twenty saved stages per run plus individual original frames were independently inspected. Sparse saved stages do not establish smoothness at every unsaved frame. [Contact sheets/CSV](three-agent-evidence/visual/) and [visual review](three-agent-evidence/integration/VISUAL_REVIEW.md).

Rendering compatibility and sampled material-tint stability pass; required rig, two distinct magazines, dedicated projection, fallback resources and finishes survive. The replacement is correctly transform-attached, yet at tick 74 it enters view before its hand becomes visible: a framing/staging defect, not evidence of a detached procedural magazine. Shade glove/receiver detail remains crushed; sunlit metal looks uniformly matte; hand anatomy remains synthetic. Default reduced motion retains substantial rigged roll/lift. Independent visual judgment stays approximately **5.5/10**, below 8.5. No broad white finish flip was observed. Audio synthesis/listening quality and physical accessibility remain unverified.

Native UI includes menu, inventory, cosmetic inspection, case odds, market, trading, account loading/stale/expired states, transaction rejection/unknown outcome handling, retained receipt retries, confirmations, simulated safe areas, text scale and resize tests. Fixture drift is checked against real backend serializers. Simulated dimensions/insets and desktop frames are not phone/touch/screen-reader acceptance.

## Backend/economy correction

[Draft PR15](https://github.com/calebaiken/sightbreak/pull/15) is separate from the integration. Controlled authoritative listing repricing 400→900 reproduced a consent mismatch with the old receipt-only client. Current seller APIs cannot reprice the same UUID; cancel/relist creates a new UUID. The optional strict positive bounded `expected_price` guard compares inside the existing serialized transaction after receipt replay and before writes; successful charging still uses the server price. Omitted/null legacy requests retain pre-guard fingerprints. The native confirmation sends its captured price, and unknown-outcome retries retain the whole payload.

61 isolated PostgreSQL tests pass; an independent reviewer separately passes 15 market tests and 8 frozen consent/concurrency probes. Atomic mismatches, strict types/bounds, duplicate/concurrent settlement, pre-guard receipt replay, trade confirmation and wallet conservation are covered. See [security review](three-agent-evidence/economy/GUARD_REVIEW.md). Economy remains earned-Credits-only with fictional test fixtures; no live account values were used.

## Multiplayer and regression disposition

Protocol 6 remains required; prediction remains opt-in/default false and live rewind damage remains disabled. Ten real Godot clients are tested under normal loopback, 50/100/150/200 ms RTT, jitter, 3% loss, 5% reordering, combined impairment, blackout and simultaneous reconnect. Success requires accepted fresh snapshots and input acknowledgments, bounded capacity and unique ownership, not just connection status. Lost disconnect, interrupted welcome, retry aliases, ticket/account identity, generation cleanup, terminal mismatch and ranked-disconnect gates are covered by maintained and independent suites.

The original twelve-condition campaign passed all conditions. It recorded exact source metadata per condition while tooling/evidence commits advanced; shipping game tree/content never changed. A frozen-checkout follow-up is recorded separately. Two maintained soak runs completed their process checks but were invalidated by source-identity changes during tooling commits. Those runs remain failures in the original matrix; pinned 2/10-client reruns are separate evidence, never relabeled original passes.

Final group totals, all commands/exits/durations and remaining failures are recorded in [matrix summary](three-agent-evidence/matrix/summary.json). **Final original result: 64/70 groups pass.** Six failed groups are retained: AI hearing; reload sequence exit leaks; reload audio exit leaks; loaded audio-capture early-sound assertion; and two source-invalidated soak runs. Separate frozen soak reruns pass, leaving four unresolved test groups plus the nested protocol-client cleanup warning. [Complete group table](three-agent-evidence/matrix/MATRIX.md). No overall green acceptance is claimed.

## Playable artifacts and practical limits

Local export source `d5ff8da` produced Linux debug package, Android debug APK/package and unsigned iOS Xcode project. [Manifest](three-agent-evidence/builds/manifest.json), [SHA256](three-agent-evidence/builds/checksums.txt), [artifact inspection](three-agent-evidence/builds/inspection.json). Required imported rifle/arms/textures plus compiled bot_ai, reload_audio, reload_phases, confirm_sheet and network/movement modules are present on all three targets. Tests are excluded. APK v2/v3 debug signatures, package `com.sightbreak.game`, API 24–36, arm64-v8a/x86_64, landscape launcher and unsigned iOS project metadata are checked.

Actual Linux ELF native interaction passes with clean client/server exits: menu→inventory→menu→dedicated server, authoritative input ACK 1303, six shots, ammo 24→30 via real R-key reload, predictionfalse/protocol 6. [Native result](three-agent-evidence/builds/native-network/results.json). Early driver attempts are retained; pointer timing and a menu/connect pixel collision were corrected. An overlong frame-exit budget timed out; the final 200-frame run exits normally. The unsupported desktop-close experiment was removed from the maintained driver.

Actual offline ELF captures show menu→5v5, movement/aim, requisition state, live firing 13/60 ammo and reload 15/58, pause and return to menu. [Offline evidence](three-agent-evidence/builds/native-offline/). Its ad hoc driver hit a teardown AttributeError after return and was terminated; do not count it as an automated clean-exit pass. Native network and independent menu/demo artifact checks establish clean exit separately. Equipment purchase authority and plant/defuse/full rounds run in maintained native source tests; a full manually driven exported objective match remains UNVERIFIED.

Local packages: `/workspace/sightbreak-three-agent-build/builds/`. Release upload to `uploads.github.com` returned **401 Bad credentials**, although GitHub API and pushes work; the new draft release has no assets. No credential values were read or substituted. Supported fallback: isolated [Actions delivery run](https://github.com/calebaiken/sightbreak/actions/runs/38846961471) on frozen 4316c58, using pinned official toolchains, all three exports, resource/signature checks and artifact upload. Its final distribution result is appended below.

No phone installation, mobile frame budget, physical accessibility, human gameplay feel, macOS/Xcode compile/signing or public Internet security is claimed. Development playability is established only in the described paths. Production readiness is not established.

## Next integration sequence

1. Gemini corrects published API wiring, hearing/navigation/damage-direction defects and strengthens positive/memory/difficulty controls; rerun the same native seeds and full lifecycle.
2. Claude corrects reload staging, reduced-motion default, anatomy/lighting/material weaknesses and audio/cleanup failures; rerun actual native sequences and listening review.
3. Review/land the separately scoped price guard through the owner-approved dependency order; client/server rollout preserves legacy receipts.
4. Reconcile PR1, 3→8, 10 and presentation/UI dependencies with owner approval; refresh the aggregate only from new frozen SHAs and repeat affected adversarial gates. Keep PR11 and this aggregate draft until constituents and remaining failures are accepted.
5. Physical Android/iOS, human playtests, mobile performance and Internet security gates precede production acceptance. Nothing in this report authorizes merging main.

## Independent acceptance limits

Separate read-only Codex reviewers examined AI, economy, authority integration and actual visual frames. They did not author the inspected Claude/Gemini source. This is AI review, not human acceptance; scores remain judgments with unknown calibration.

| Category | Development evidence | 8.5/10 or production disposition |
| --- | --- | --- |
| Shared integration / authority | Narrow adapters and independent native probes accepted | Scoped development acceptance only |
| Network reliability / privacy | Loopback impairments, capacity and resume checks | Internet/mobile conditions UNVERIFIED |
| AI / objectives / difficulty | Native comparisons and retained hearing failure | FAIL acceptance |
| Economy / transaction integrity | Isolated PostgreSQL and independently reviewed price guard | Production security UNVERIFIED |
| UI / accessibility | Native state/layout/confirmation suites and captures | Physical touch/screen reader UNVERIFIED |
| Visual quality | Fresh native sequence review about 5.5/10 | FAIL 8.5 target |
| Audio / resource cleanup | Functional assertions pass, exit leaks and timing-control failure retained | FAIL complete regression acceptance |
| Performance | Shared-host CPU observations and software renderer | Mobile/GPU budget UNVERIFIED |
| Platform packaging | Linux runtime, debug APK and unsigned project inspected | Physical Android / Xcode / iOS UNVERIFIED |

## Final frozen network and distribution results

The frozen `4316c58` follow-up passes **12/12 conditions**, each with ten clients, no recorded campaign failures, and a clean unchanged source checkout. Both separate pinned soak reruns pass: two clients and ten clients repeatedly resume the same actors, accept fresh snapshots/ACKs and retain bounded transports. Raw original soak failures remain in the matrix. See [frozen campaign](three-agent-evidence/network-pinned/campaign.json), [two-client soak](three-agent-evidence/pinned-soak-two/summary.json), [ten-client soak](three-agent-evidence/pinned-soak-ten/summary.json).

The isolated audio capture repeats pass **3/3** with every original assertion intact. The loaded matrix's early-sound assertion still failed, so the timing control is nondeterministic under this campaign; neither a universally broken scheduler nor a clean gate is established. The separate reload sequence/audio tests consistently report exit-only AudioStreamWAV/AudioStreamPlaybackWAV leaks despite zero functional assertion failures. Test teardown/mixer lifetime requires source-owner follow-up.

**Distribution is complete through GitHub Actions**, not Releases. [Download development bundle](https://github.com/calebaiken/sightbreak/actions/runs/38846961471/artifacts/12023941005). Run 38846961471 completed successfully on `4316c58`; all three exports, actual artifact inspection and packaging steps passed. Artifact 12023941005 is 287,259,147 bytes, SHA256 `5f9235dd55f4570a058eb7599e3805905cf8241b9b52db7623f5c70297018869`, with 14-day retention. Its own inner manifest/checksums cover its CI-generated files; do not substitute local APK hashes because CI uses a newly generated debug key. The connected GitHub artifact download also succeeded. Decoded [job evidence](three-agent-evidence/builds/actions-job.txt) confirms the same game tree and shipping content hash as local exports. CLI log retrieval was separately denied by the results-receiver host; supported connected GitHub retrieval worked. No credential extraction or route bypass was used.

Final live-head check: PR2 advanced during the frozen campaign to **`f4a763a3c9712c15ae0c369e4f7ee65adf9d38dd`**, changing the arms GLB, hip-retrieval staging and related probes. That newer source was fetched/inspected but is **UNVERIFIED and not integrated** in these artifacts. PR12, PR14, PR11 and main retain their original frozen heads. The magazine first-draw finding in this report is specifically on `ed85754`; Claude's later fix needs fresh native validation. This avoids silently relabeling an untested changed asset as the tested build.

A recursive child-log audit also finds an ObjectDB exit leak in the matched current/current protocol-client fixture. The protocol matrix's eight compatibility outcomes pass; this nested warning remains an additional cleanup failure and is not overridden by that group count. See `three-agent-evidence/nested-leak-diagnostics.json` and the retained child log. Real account recovery independently passes all seven checks: ten exact account/actor bindings, ten consumed tickets, fresh post-recovery authority, bounded transports, preserved ranked policy and zero rewards/Credits issued.

The completed matrix includes native renderer lifecycle, native HUD overflow coverage, paint visibility, full 10-round bot lifecycle (70 kills, halftime, exactly one report), 61 PostgreSQL tests, 37/37 real HTTP native economy checks, eight protocol pairings, hostile handshake controls, account capacity, seven full-account reconnect checks, and durable-result SIGKILL/outage/lost-ack/replay coverage. A normal natural lifecycle run observed no plant; the separate deterministic Normal comparison observed plants/defuses, so this is not claimed as universal objective participation.

Reproduction entry points from a matching toolchain checkout:

```sh
scripts/godot.sh --headless --editor --import --quit
DISPLAY=:99 .venv/bin/python scripts/validate_matrix.py --backend --protocol --render --out /tmp/sightbreak-matrix
python3 scripts/run_network_campaign.py --clients 10 --seconds 18 --out /tmp/sightbreak-network
scripts/export.sh linux
scripts/export.sh android
scripts/export.sh ios
python3 scripts/verify_builds.py
python3 scripts/build_manifest.py package
```

Use a running loopback development PostgreSQL for backend checks and a free Xvfb display for native rendering; these commands do not install or configure missing dependencies. The matrix JSON contains the exact executed commands, durations, return codes and log names. AI and native-export probes have separate source-bound reproduction records. Build delivery CI intentionally builds/inspects packages; its success does not assert the regression matrix is green.

## Published review checkpoint

[Integration draft PR16](https://github.com/calebaiken/sightbreak/pull/16), based on PR11, and separate [marketplace guard draft PR15](https://github.com/calebaiken/sightbreak/pull/15) are published. Source-owner review comments were actually posted: [PR14](https://github.com/calebaiken/sightbreak/pull/14#pullrequestreview-5542908108), [PR2](https://github.com/calebaiken/sightbreak/pull/2#pullrequestreview-5542908229), [PR12](https://github.com/calebaiken/sightbreak/pull/12#pullrequestreview-5542908318). They are COMMENTED review records with actionable requests, not approvals. The integration remains a development draft; main and original source branches were preserved.
