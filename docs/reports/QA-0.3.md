# Independent QA — SIGHTBREAK 0.3.0-dev

## Review scope and acceptance rule

Starting source: `4f21dc14ef73c3d620f095065ab89a0035ddd1f2` (0.2.0-dev). The independent reviewer does not author gameplay, rendering, UI or economy implementation. Automated results establish their stated local scope; physical touch comfort, human enjoyment, mobile GPU performance, battery/thermal behavior and production security require separate evidence.

The requested visual threshold is **8.5/10**. Scores are visual reviewer judgments against actual native images, not a conversion of test counts or asset quantity. A higher aggregate cannot silently waive a weak category or an unverified release gate. Desktop software-rendered captures are never phone performance evidence.

## Explicit visual rubric

Each category uses the same anchors: 5 = recognizable development blockout; 7 = coherent playable alpha with visible simplifications; 8.5 = consistently polished, convincing mobile art direction with minor defects; 10 = exceptional executed quality. Equal weighting is used for the aggregate. Effects and animation require rendered sequence evidence; a still only supports visible appearance at that instant.

| Category | What is judged |
| --- | --- |
| Geometry and composition | Coherent original place, architectural scale and structure, silhouette hierarchy, cover integration, focal points and believable detail without clutter. |
| Materials and surfaces | Convincing roughness/metal distinction, texture scale and variation, edge treatment, appropriate wear, coherent finish and economical detail. |
| Lighting and atmosphere | Shape readability, stable grounding/contact shadows, controlled contrast, depth, plausible environment response and no distracting glare. |
| Models and animation presentation | First-person weapon proportions/placement, hand/arm integration, recognizable character silhouettes and equipment, smooth visible movement/reload/equip transitions. |
| Combat and cosmetic effects | Clear restrained muzzle/impact/smoke/casing feedback, legible hit confirmation, readable original 3D cases, satisfying committed reveals and inspection. |
| Identity and consistency | Graphite/crimson/muted-gold identity; coordinated map, models, typography, HUD and cosmetic presentation without placeholder clashes. |
| Competitive readability | Opponent/team separation, unobstructed aim, useful HUD hierarchy, legibility at landscape sizes, stable effects and safe reachable controls. |

## Five principal deficiencies found in the actual 0.2 captures

The reviewer inspected native `media/environment/{approach,site}-after.png`, `media/stabilization/mobile-hud-wide.png` and `item-inspector-fixture.png` before implementation review. These are historical native evidence; the fresh fixed-view 0.2 and 0.3 captures linked below provide direct comparisons.

1. **The map reads as an empty rectangular yard.** Broad flat walls and repeated containers dominate; structural connections, composed focal architecture and believable service detail are sparse.
2. **Surfaces look uniformly clean or speckled.** Concrete, painted metal and the first-person rifle lack convincing scale variation, edge definition and material separation.
3. **Lighting flattens the scene.** The plain sky/ambient wash reduces depth and physical grounding; large hard shadow shapes do little to establish atmosphere or focal hierarchy.
4. **Models expose their primitive construction.** The broad block rifle and sleeve/hand shapes dominate the view; tiny rudimentary character silhouettes and the flat small inspector weapon weaken tactical and cosmetic appeal.
5. **UI occupies excessive visual area without sufficient hierarchy.** Tall full-width HUD bands and thin outlined text circles obscure the environment; the inspector gives its small rifle less emphasis than surrounding form text.

The previous report's 7.5/10 whole-presentation score is retained as historical assessment. It is not silently recast as a score for this new seven-part rubric.

## Current review state

**Development milestone; release acceptance withheld.** Visual presentation improves substantially, but the independent seven-part visual assessment remains below 8.5. Physical-device performance/play, human gunplay enjoyment and production security remain unverified. Final native lifecycle and artifact checks are recorded below.

## Independently executed baseline and service checks

- The immutable starting commit was exported with `git archive` into `.local/v03-baseline`; its code was not shared with active implementation edits. `SIGHTBREAK_TOOLS_DIR=/workspace/tools ./scripts/validate.sh --backend` passed: **267 counted native assertions**, **39 PostgreSQL tests**, **8 packaging tests**, two real ENet clients, a short bot round and a naturally completed **12-round 6–6 draw**, **89 kills**, halftime, a plant and exactly one results report, **381.9 simulated seconds**. Timers and actor decisions were active; this was an accelerated offline simulation, not a human earning match. See [unaltered baseline output](evidence-v03/immutable-baseline.txt).
- Independently repeated existing account admission, replay/reclaim and HTTP retry/redirect suites pass on the intermediate 0.3 checkout. Actual Godot → HTTP → PostgreSQL reward settlement also passes: ten exact wallets, ten ledger grants, ten records and no extra value on replay. That reward test uses synthetic eligibility/duration fixtures, not observed ten-human gameplay. The isolated service was stopped afterward.
- The formerly workspace-only real native economy regression is now reproducible as `.venv/bin/python scripts/test_native_economy.py`. It creates a uniquely named disposable PostgreSQL database and loopback API, keeps fictional fixture credentials temporary, runs native UI transaction calls, and removes the service/database. Its **14/14 checks** pass on the intermediate checkout: persisted loadout, case/key consumption and one minted result, marketplace debit/proceeds/fee, actual revised two-sided item trade, unique inventory owners and transferred-item loadout cleanup. It does not add a seed/grant API or change transaction implementation. The final-source repetition is recorded below.

## Screenshot loop — first implementation review

Fresh 0.2 fixed-view captures in `builds/qa/v03/before/environment/` and `profile-before/run-1/` were inspected, including the close operator arrangement. The first 0.3 `world-pass1` approach/site/overview renders visibly improve container fittings, transfer doors, crane structure, utility routing and first-person receiver shape. The reviewer identified two concrete new presentation defects: one rooftop ventilation unit visibly floated beyond its supporting roof, and new garage doors obscured the old building wordmark, leaving disconnected text fragments. These were sent to the environment owner for correction before final captures.

The first-pass geometry/material/lighting observations remain below the requested threshold: broad clean planes and even ambient illumination still flatten the yard, and additional small details alone do not establish commercially credible composition. Final scoring awaits correction and the character/effects/cosmetic/mobile evidence.

An intermediate complete regression execution passed **408 counted native assertions**, **39 PostgreSQL tests**, the maintained **14-assertion native HTTP economy roundtrip**, **10 packaging tests**, two ENet clients and a natural **12-round 5–7 match**, **81 kills**, halftime, observed plant and one result, **371.0 simulated seconds**. This is [intermediate evidence](evidence-v03/aggregate-intermediate.txt), not a final-source signoff; implementation was still changing.

The first combat sequence (`builds/qa/v03-combat/`) shows a clearer chamfered receiver, discrete muzzle flash, ejected casing and different reload/reseat poses. Close operator frames exposed an overly bright pastel full-body palette and white visors that read as toy figures; the smoke capture exposed opaque bright overlapping lobes resembling foam or boulders. These were reported to the combat owner for another focused art pass. Frame sequences establish the captured poses/effects, not a measured human assessment of animation smoothness, responsiveness or sound quality.

The first native economy renders exposed a missing knife blade (subsequently isolated to unindexed triangles being lost during mixed indexed/unindexed mesh batching), visibly blurry half-resolution weapon/box views and insufficient item emphasis relative to the large stage. The reviewer requested corrected mesh indexing/winding with regression coverage, bounded native-resolution demand rendering, stronger product framing and a smaller reference-model affordance. The case reward remains committed server-side before any animation; the knife is explicitly labeled an unowned reference and does not expand the authoritative reward table.

## Independent native resource and mobile review

The reviewer independently executed the new `cosmetic_lifecycle_test.gd` on the actual GLES3 renderer: **19/19 passed** over six complete studio/reveal cycles. Each cycle switches rifle→case→knife, releases the selected mesh hierarchy, closes its inspector/SubViewport, opens/skips/closes a reveal, and checks weak references. All warmed tracked texture samples were **4,350,915 bytes**; no script or renderer error was emitted. [Unedited output](evidence-v03/cosmetic-lifecycle.txt).

The reviewer then executed `DISPLAY=:99 LIBGL_ALWAYS_SOFTWARE=1 ./scripts/test_render.sh`: the real demo captured/exited cleanly and **11/11 menu/match lifecycle checks passed**. All five warmed tracked texture samples were **61,272,326 bytes**; prior worlds were released. [Unedited output](evidence-v03/native-render.txt). Both checks use Godot 4.7.2 GLES3/Mesa llvmpipe on Linux Xvfb. These short plateaus do not establish indefinite memory stability or mobile GPU behavior.

Actual [mobile landscape captures](media/v03-mobile/README.md) were independently inspected at 1600×720 and 960×720, plus the menu and settings views. Fading edge backdrops replace the oversized solid bars, action glyphs clarify the controls, the centered score/reticle remain distinct, device status clears pause, and ammunition/instructions clear the touch buttons. The settings screen remains legible and scrollable. The capture owner's four-ratio run records 156 assertions (144 layout checks plus 12 image writes); the independent headless layout run separately passed 144. Physical reach, tactile comfort, notches, gyro, aim feel and interruption/resume are still unverified.

## Authority and currency boundary review

A source diff against the starting commit shows no backend transaction/probability/reward changes. The positive creation path remains trusted eligible-match settlement, including server-calculated daily-first and level bonuses; new accounts start at zero and offline training balances cannot import. Marketplace sale proceeds transfer existing Credits minus the fee. Daily/weekly challenges are still absent. The local adversarial PostgreSQL, actual native transaction and trusted reward replay tests support those boundaries; they do **not** establish an observed ten-human legitimate earning journey or protection against a compromised trusted server. No payments, IAP, redemption or real-money integration has been added.

## Final independently executed gameplay and service regressions

Command: `taskset -c 2,3,4 timeout 720 ./scripts/validate.sh --backend`. The completed run is `.local/validation/run-CpaiY1`; [full output](evidence-v03/final-aggregate.txt) is preserved. Source is the final 0.3 implementation; the last subsequent gameplay-file edit during this run was the smoke shader's triplanar seam treatment, which requires the separate final native renderer check.

| Check | Observed result | What it establishes |
| --- | --- | --- |
| Counted native assertion suites | **443 passed**: actor 72, world 25, confirmed feedback 10, match 75, profile 10, touch 34, main 35, landscape 144, response recovery/materials 12, cosmetic presentation 26 | Maintained gameplay, ownership-neutral presentation, world collision/layout, mesh indexing, UI/input, smoke quality and authority boundaries. Passing assertions are not human quality scores. |
| Short and complete natural bot simulations | **PASS**; complete match **12 rounds, 7–5, 92 kills, halftime, plant observed, one results report, 369.2 simulated seconds** | Real bot decisions/physics with accelerated time; no forced winner, round completion or reward eligibility. Earlier baseline and intermediate runs completed 6–6 and 5–7. |
| Two actual ENet clients | **Both passed** movement, snapshots, reconnect, authoritative hit and impact feedback | Actual local transport and newly replicated feedback, not ten-human or adverse-WAN validation. |
| PostgreSQL economy | **39 tests passed**, 3.93 seconds, one dependency deprecation warning | Original transaction/probability/ownership/session/ledger/replay invariants retained on a disposable real PostgreSQL database. |
| Actual native HTTP economy journey | **14/14 passed** | Real case consumption/result, marketplace debit/proceeds/fee, revised two-sided trade, persisted loadout and ownership cleanup, using isolated fictional seed balances. |
| Packaging regression unit tests | **10 passed** | Manifest/source/version validation logic; actual export verification is separate below. |
| [Account ticket transport](evidence-v03/final-account-network.txt) | **PASS** | Guest rejection, authoritative identity, waiting roster, replay rejection and fresh-ticket account reclaim. |
| [Privileged HTTP fault transport](evidence-v03/final-bridge-transport.txt) | **PASS** | Exactly three identical bounded retry requests for temporary failure; redirect rejected without credential forwarding. |
| [Actual reward bridge settlement](evidence-v03/final-reward-bridge.txt) | **PASS** | Ten exact wallets, ten ledger grants, ten match records, replay creates no extra value. Synthetic policy/time fixtures; not an observed ten-human earning match. |

All temporary QA native-economy services/databases were removed by the maintained runner. The dedicated reward fixture service was stopped after settlement review. No production or normal development-account balances/items were seeded.

## Visual assessment and remaining quality gate

The reviewer inspected the fresh fixed-view before/after environment images, two iterations of operator/combat frames, final common/Legendary native cosmetic fixtures, and the native landscape views. [World comparisons](media/v03-world/README.md), [combat iterations and final frames](media/v03-combat/README.md), [cosmetic comparisons](media/v03-cosmetics/README.md) and [landscape evidence](media/v03-mobile/README.md) retain provenance. Combat fixtures show rendered poses/effects, not human play or an audio listening session.

| Explicit rubric category | Score / 10 | Evidence and remaining limitation |
| --- | --- | --- |
| Geometry and composition | **8.1** | Transfer doors, structural piers, crane/trolley, supported service equipment, cargo fittings and correctly oriented wayfinding make the yard more convincing. Broad rectangular masses and limited landmark variation remain visible. |
| Materials and surfaces | **7.9** | Mipmapped surface response, restrained paint/metal variation, resurfaced lanes and collection finishes improve separation. Many large surfaces remain uniformly clean/simple; production wear/edge/material variety is incomplete. |
| Lighting and atmosphere | **7.7** | Directional shadows and warmer key/cooler ambient give readable structure at conservative cost. Flat broad illumination and plain sky still limit depth and atmosphere; no unsupported AO/mobile-lighting claim is made. |
| Models and animation presentation | **7.8** | Chamfered shared weapons, gloves/sleeves, graphite operator kit, smaller dark goggles and visible reload/equip poses improve the original blockout. Body proportions, cloth, weapon silhouette detail and animation breadth remain visibly simplified; smoothness and satisfying human gunplay are not established by stills. |
| Combat and cosmetic effects | **7.6** | Muzzle flashes/casings, bounded impact pools and hinged committed-result cases are more legible. Smoke now has a softer boundary, but its opaque central mass still looks spherical, and effect variation/animation artistry remain limited. |
| Identity and consistency | **8.6** | Graphite, crimson and muted gold connect menu, architecture, compact HUD and collection finishes; corrected signage and original models maintain a coherent identity. |
| Competitive readability | **8.7** | Native views retain clear cover lanes, centered reticle/score, restrained flashes, separated status/ammo/action controls and identifiable team accents. Physical display readability, touch reach and long-range human target acquisition remain unverified. |

**Equal-weight visual mean: 8.1/10, rounded to one decimal. The 8.5 target is not met.** The previous 7.5 whole-presentation rating is historical; it was not retroactively assigned this new rubric. Passing local correctness checks does not raise the visual score or waive any unverified release gate.

The next visual work should prioritize professional character/weapon proportion and animation refinement, surface/lighting depth, and smoke/effect art under measured device fill-rate budgets. Additional small props alone will not close this gap. Broader acceptance still requires actual Android/iOS installation/play, sustained thermal/frame-time measurements, human full-match feedback and production security review.

## Independent final artifact verification

The reviewer independently reran `python3 scripts/verify_builds.py` and `(cd builds && sha256sum --check checksums.txt)`: both checks passed. [Verifier output](evidence-v03/artifact-verification.txt), [all five checksum results](evidence-v03/artifact-checksums.txt), and [exact build hashes](../builds.md) are retained.

Verified exported source: commit `538f52f9a9dfb5dac38209b7541bde145fc01976`, game tree `ab35c845326fe859c86f3d0b4e37038e82e18c44`, source content SHA-256 `2c6cf58b4c49914d5d8901bc81e73e4e3734c939fcf11464448fbae39e72d60a`. Documentation commits after export do not alter that game payload.

Linux menu startup and 120 headless demo frames pass. Linux/iOS packs contain 66 resources; Android contains 68 packaged assets; test harnesses are excluded. APK v2/v3 signatures, version `0.3.0-dev (3)`, API 24 minimum/API 36 target, ARM64/x86_64 libraries, landscape orientation and launcher alias pass inspection. The exported iOS project has its expected plist and empty signing team. **No physical Android install/play, macOS/Xcode compilation/signing, signed IPA or iPhone test is claimed.**

## Performance evidence limits

The [reproducible rendering report](PERFORMANCE-0.3.md) records fixed cameras, three runs per preset, raw counters and short frame-time distributions. The reviewer inspected its retained results and methodology; these were executed by the integration owner, not independently rerun a second time by QA. The final Standard scene submits more art and costs approximately 15–40% more software frame time in the measured static views, with increased draw/primitive counts. This is a documented cost, not an overall optimization claim. Low reduces shadows/MSAA/material lookups; device selection and image quality still need physical testing.

The separate opaque-armory experiment has identical visible screenshot hashes while draws fall 358→33; this supports removing hidden yard work. Neither that controlled local saving nor llvmpipe frame times establish mobile FPS, GPU timings, thermal behavior, battery use or ten-human online performance. Distance LOD/streaming and sustained device shader/loading measurements remain outstanding.

The final combat captures were independently inspected after the last shader correction: the impact is visible clear of the first-person weapon, operator fixtures no longer contain the previous unused local rifle/leftover effect, and the smoke texture seam is gone. Its rounded opaque central volume remains visible and is included in the effects score; the correction does not close the broader 8.5 art gate.

## Scoped system decisions

These judgments apply to the stated local implementation scope; they do not convert assertion counts to quality or certify an untested deployment/device.

| System | Independent local assessment | Broader gate |
| --- | --- | --- |
| Gameplay state correctness | **8.8/10** — maintained combat/rule checks and three naturally completed baseline/intermediate/final bot matches, including halftime and single result delivery | Human enjoyment, map balance, sound/animation feel and long-session bot behavior unverified. |
| Renderer/resource lifecycle | **9.0/10 in the measured configuration** — scene weak references release and repeated tracked allocations plateau; real renderer logs inspected | Device GPUs, OS lifecycle and indefinite soak unverified. |
| Touch input/layout implementation | **8.8/10 in synthetic/native-layout scope** — simultaneous input, cancellation, finite input, maximum-scale separation, four landscapes and actual HUD inspection | Physical reach, latency, gyro, notches and interruptions unverified. |
| Economy transaction correctness | **9.0/10 in local PostgreSQL scope** — authority/replay/probability tests, real native ownership/ledger roundtrip and trusted reward replay retained | Ten-human earning observation, durable recovery, challenge system and production throughput remain incomplete. |
| Multiplayer integrity | **8.5/10 in tested local boundary scope** — actual two-client state/reconnect/feedback and account ticket/retry tests | WAN behavior, public transport encryption, ten humans and abuse/load review unverified. |
| Visual presentation | **8.1/10** — explicit seven-part native-image rubric above | **Below 8.5; not accepted.** |
| Mobile performance, human game feel, production security/operations | **UNVERIFIED / NOT ACCEPTED for release** | Requires actual devices, people, sustained measurements and independent production review. |

No full release or product phase meets the requested 8.5 threshold across every applicable category.

## Final native renderer regression

After the final smoke shader change, the independent reviewer reran the maintained combined `DISPLAY=:99 LIBGL_ALWAYS_SOFTWARE=1 ./scripts/test_render.sh` against the frozen source. **PASS, exit 0**: actual demo capture, **11/11 scene lifecycle** and **19/19 cosmetic lifecycle** assertions. All five scene texture samples were **61,272,326 bytes**; all six cosmetic samples were **4,350,915 bytes**, matching the earlier plateaus. Weak references released, and the log contains no `ERROR`, `SCRIPT ERROR` or texture leak report. Full output: [final native renderer log](evidence-v03/final-native-render.txt), local run `.local/validation/native-iRpKdZ`.

The first demo startup logged one **“Failed to load cached shader, recompiling”** warning and continued successfully. The software display also logged the known unsupported VSync warning. These warnings are preserved rather than called a warning-free run; shader cache/startup stutter on physical devices remains unmeasured. This final check closes the local regression run, not mobile stability or indefinite memory-soak acceptance.
