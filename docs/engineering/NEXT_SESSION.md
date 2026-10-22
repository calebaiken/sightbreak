# Next session

Updated 2026-10-22, 06:48 UTC. Continue **SIGHTBREAK — Steam-Ready v1.0**,
IN PROGRESS / PRIMARY, [issue #25](https://github.com/calebaiken/sightbreak/issues/25).
No native Codex goal API is exposed. Read AGENTS.md, the mission and the canonical
G1–G20 progress matrix. Reuse the installed original quality skills. Continue
implementation after each verified increment; these corrections do not finish v1.

## Root and source checkpoints

- Root: `/workspace/sightbreak-v1-execution`, `codex/v1-mission-playability`.
  Current checkpoint before this note: `961aa73`; last pushed: `3b5cf76`.
- [Draft PR27](https://github.com/calebaiken/sightbreak/pull/27) targets PR24
  `c84eaf3` → PR23 `db3981e` → PR22 `82a03fc` → PR16 `d2439ac`.
  No shared branch was merged or rewritten. Fetch live refs before integration.
- Latest complete unmodified aggregate **PASSES at exact `b09cfe1`**, including
  the new guidance source, in 465.033 seconds. Independent evidence `c4c38a7`:
  `docs/reports/gauntlet/combined-validation-b09cfe1/independent-critic/REVIEW.md`.
  All 52 required Godot logs, seven Python groups, ENet, lifecycle and catalog
  checks pass. Source stays clean and identical. Linux input_mode is 462/0 with
  no leak warning; this does not clear the separate actual Mac failure.
- Earlier complete aggregate **PASSES at `b85f93600e122b36e8dcd70edd9bc168e9820b08`**.
  Frozen worktree `/workspace/sightbreak-validate-a23e349` has that actual HEAD;
  its directory name is historical. Raw output `builds/combined-validation-r2`,
  logs `.local/validation/run-utj57N`. Game tree `e877ba16bdc7f63994930a77f32e484e8f12d890`,
  content SHA256 `db3c976711ef8d91b75604fdfe05309599445cfc5bdf59e5f6fbdf669a859fc5`,
  validation SHA256 `0fd96995226efdf47fb351860eedda3a8ca1b0086b3ef291a5e99f640766abc3`.
  Before/after source is clean and identical. Independent evidence `609913e`:
  `docs/reports/gauntlet/combined-validation-b85f936/independent-critic/REVIEW.md`.
  All52 required Godot logs, ENet 2/2, lifecycle cleanup, catalog 29 and Python groups
  pass. Five rendered checks, three Windows unit cases and optional backend SQL
  are not covered. Later Mac tools change validation identity; do not relabel this
  pass as the whole latest HEAD. Shipping game/backend/server equal `3b97a00`.
- First aggregate at `a23e349` failed because root sparse checkout omitted tracked
  reload CSV/hash fixtures. Original 57-file archive/exit1 remains in `0e63ada`.
  Restore `docs/reports/media/art-v9/hands/logs` in every aggregate checkout.

## Actual native runs

| Run / exact source | Accepted output and failure |
| --- | --- |
| [39725980732](https://github.com/calebaiken/sightbreak/actions/runs/39725980732), `872a576`, single Linux119649852989 | Raw independent source/input/ordinary journey, defuse,9-round stock match/earned restart and four-size201.314 s pass. Player plants180 ticks, +1objective/+300credits, but later15 s role-guidance wait fails amid notifications before death. Natural resolution/restart in that plant scenario are unreached. FullQA46 MB untransferred; original per-size PNGs available. Evidence `b85f936`, report `m1-native-ci-39725980732/remote`. |
| [39727011693](https://github.com/calebaiken/sightbreak/actions/runs/39727011693), `e7718ee`, single ARM119653125533 | Actual no-event readiness and unsigned iOS compile independently pass. All four permission APIs true; exact preflight PID6968/window34/internal PNG valid, profile absent, normal0/no remaining group. No input posted. Evidence `e6c323a`, `m2-macos-input/native-run-39727011693`. |
| [39728129445](https://github.com/calebaiken/sightbreak/actions/runs/39728129445), `a8eb7eb`, single Windows119656711230 | Overall FAIL only plant, independently audited. Original ordinary journey passes233.547 s; all 16 original OCR outputs/strict LEAVE call retained. Defuse/full ten-round match and exact120 XP  / 325 credits restart pass; raw archives and independent review are committed as 3f74e20/317410a (`m1-native-ci-39728129445/REPORT.md`). Its own180-tick plant/reward/living PNG pass, followed by notification starvation/death in15 s role wait. Critic `native_ci_outcome_critic` retains original fullQA22.7 MB and bounded3.3 MB. |
| [39729489971](https://github.com/calebaiken/sightbreak/actions/runs/39729489971), `3b97a00`, single ARM119661018459 | New real-menu attempt FAILS before events. Swift compiles; gamePID3996 cannot be verified foreground within5 s (last observedPID3721),0CGpost attempts, no helper invocation/OS capture. Ordinary close0/groups gone. Own helper permission/geometry/Vision unreached. Separate preflightPID3571/window35 cannot stand in for3996. All12 native suites actually pass4,461 assertions. Independent raw rejection is committed as `a172934`/`5378b1f`; report `m2-macos-menu-input/native-run-39729489971/REPORT.md`. |

Earlier `0ca125d` run 39719407304 and `6a0d8d5` run 39712752860 failures remain
historical. Intel default/OpenGL and all five feature ablations time out120 s;
minimal controls pass, no winning variant supports a shipping renderer change.
Physical Intel/Mac GPU qualification stays open. Actual unsigned iOS compilations
succeed under probed process-local Xcode26.3/SDK26.2, with native attestation and raw
linker/codesign/PCK receipts; large app binaries were not independently transferred.
Installation, runtime, older OS and physical mobile play remain open.

## Active execution queue

1. **M1 planted-role source accepted; complete journey FAILS.** Source `3c4d921`
   is integrated as `d7dc1be`; criteria 7686a7e, builder evidence 87c12d4/21f99e2,
   independent review e2c61ac. Review: `m1-postplant-guidance/independent-critic/REVIEW.md`.
   All 1,458 flood frames are correct versus none on baseline; 1,559 independent
   controls pass. Both native rounds 3/4 pass 180-tick ordinary plant, +1/+300,
   living DEFEND pixels and natural defender defuse, then FAIL unchanged 12 s
   next-round wait: only 247 ticks  / 4.116667 sim seconds in 12.053 wall, POST 0.65 left.
   Restart is unreached. Round4 has no recorder and also fails; no recorder-only
   cause is supported. Both explicitly select LP_NUM_THREADS=2/llvmpipe; outer
   parent env is not client readback. No fixed-fps/physics override. Arena/sky
   blobs and graphics selection lines match pre-integration9f730dc; source-only
   comparison cannot establish a UI/render regression. The b09 candidate aggregate now passes independently; exact-source Windows
   output is under review. No unbounded retry or deadline
   increase is authorized merely to find a pass.
   Original H.264 video 130.400 s  / 1,304 frames  / 7,961,368 bytes is retained, SHA256
   `9527ba7f05d288c1545ea8dbc3723a83d5e19774118af099119fb6c7b0dfb7cc`.
   Builder and critic have exited their engine lane; preserve both failures.
2. **M3 first corrected-account trial: harness PASS / independent BLOCKED.**
   Immutable source `e2c61ac2ecbd38ab55bc9edb712b028322c1490f`, game tree
   `fb6be859e05812d8707be1ef5c6f747d2588c1e9`, completes in 529.336562 seconds.
   Seven stock/recovery checks pass, with one operation / ten rewards and ledger
   rows, 2,875 credits / 2,650 XP. New payload is a62c9357…; prior trial payload
   was not reused. Critic sees actual committed SQL before the lost-worker
   checkpoint, exact source/eleven native processes/socket and owned cleanup.
   However, final retained SQL clock 50.186645 precedes replay 50.187242 by 0.597 ms.
   Deduplication discarded later identical samples. Do not infer the missing
   post-replay witness: qualification stays BLOCKED. All resources are removed;
   local engine lane is released. Evidence: `f8b7e82`, independent rejection
   `71f430e`, reports `m3-account-activity` and `m3-account-activity-qualification`.
   Separate v2 observer is independently source-accepted (16 controls), hash
   `d1ec8562d95f614cb6e3e996febb66cf6e4dda1cce5ab8a3e94f7639fd949179`;
   oracle 09599411… requires every recovery stream row and a distinct owned
   read-only query started after replay. Original v1 remains unchanged.
   **Trial2 is executing**, source `3b5cf7640e256dff404b401bf2b27ffaff157bdd`,
   game fb6be859…, new worktree `/workspace/sightbreak-account-activity-r2`,
   output `builds/account-activity-stock-2`, driver 108257 / session 5448,
   started 06:38:57 UTC. New container `sightbreak-account-match-f1672c68d71a`,
   API 127.0.0.1:36727, game UDP 40937. Critic was armed before runtime and has
   independently seen ten disjoint zero-wallet IDs/tickets, eleven engine
   children and socket ownership. Match reaches automatic halftime; final
   recovery/SQL/cleanup acceptance remains pending. This run owns local CPU.
   Builder `/root/account_match_builder`; critic `/root/account_activity_qualification_critic`.
   Preserve source until critic source-after, then archive originals; never
   infer the pre-ACK/post-replay SQL or successful cleanup.
   Keep stock rules, yaw policy, no AFK-resistance or whole G3/G16 claim.
3. **M2 actual Mac focus/capture advances; automatic journey still FAILS.**
   Run 39732825169 at exact `b09cfe1b661ec153f2bd57d45e695cc70e9717b0`, single
   ARM job 119671543697, now observes current PID 4062/window 45 [40,32,960,568],
   background capture-only success, accepted public activation, exact foreground
   and five actual events. Original 01/02/03 PNGs visibly show menu/settings/menu.
   Final automatic gate rejects merged header confidence 0.5 under unchanged 0.8.
   Keep this FAILED; a visible image does not change the automatic result.
   A separate source gate runs only seven suites  / 1,584 assertions: input_mode
   is 462/0, exit 0 but strict log rejects two ObjectDB instances leaked at exit.
   Five later suites are UNREACHED. No verbose object types/cause are known.
   iOS unsigned compile passes separately. Independent raw report is committed
   as `b72badd`; all 127 receipts and original phase PNGs are audited.
   Original base: `/workspace/sightbreak-mac-menu-native-review/docs/reports/gauntlet/m2-macos-focus/native-run-39732825169/full-qa`.
   Next source is independently accepted: a866c73, integrated through `961aa73`.
   Home identity requires unique exact SIGHTBREAK / OPERATOR RECORD / SETTINGS,
   unchanged confidence 0.8 and original geometry, rejecting settings/mixed
   screens. Separate verbose input_mode repeat runs only after the evidenced
   strict leak failure, on an isolated private project/user namespace, within
   240 seconds. Original strict gate stays failed. All 35 root controls pass;
   fresh critic 146 screen cases  / 14 mocked lifecycle runs pass. Prior rejected
   bounds/diagnostic cases are retained. Push clean source and dispatch one ARM
   attempt, verify returned exact SHA/job, then independently review actual
   navigation and verbose object types. Failed bootstrap preserves unvalidated
   namespace honestly. No new native result or leak cause is claimed.
4. **M6 touch transition accepted.** Integrated `66bcc5e`/`a06017b`, final native
   source 589a52a. Initial candidate visually wins but is rejected for existing-row
   clipping. Revision passes 462 checks vs prior 16 failures, independent 4/4 clipping
   probe, and original 71.891 s native on/off flow. Fresh final blind judge chooses
   final candidate for clear MENU/device spacing and correct hints. Evidence
   `9efaf63`, `4a1205c`/followup and `93ec98b`; report `m6-touch-hud-transition`.
   Control contrast over weapon/pavement remains open. Full game tree is covered by
   the b85 aggregate; no G7/G10/physical/8.5 presentation closure.

5. **M1 capture phase fences source accepted and integrated.** Source 65c3b8b
   integrates as 802ce4c, independent archive d72c815. Fifteen groups plus eight
   independent scheduling controls pass. Rejected aaa1929 is preserved. Only
   observation changes; original 160/30/300 budgets and input contracts remain.
   Actual output is running in Windows CI 39735001567 at exact 3b5cf764, single
   job 119678513156. Metadata passes source/input/journey/plant/defuse and reaches
   stock full match; raw evidence is not yet available. Critic
   `/root/native_ci_outcome_critic` owns source/PID/frame/phase/profile/OCR and
   original PNG review in sparse `codex/review-native-ci-39735001567`.
   Neither corrected 06c nor 10 pixels are accepted from metadata alone.
6. **M4 gunplay rules measurement awaits actual engine output.** Own worktree
   `/workspace/sightbreak-gunplay-invariants`, `codex/m4-gunplay-invariants`.
   Criteria 395b602, rejected probe b6c2ccd, revised source
   `d1e89edfbd474a04d6759300141880566b1559e3`, game tree 20b03e37….
   No shipping change or supported product defect. Fresh review 890d87d accepts
   revised harness for bounded measurement: forty independent pure controls,
   complete stock schedules 129/353/286/36, real health/alive and feedback
   predicates, raw reload/deploy timelines, all-four lethal and friendly shield
   cases. These are source controls/predictions, not actual engine results.
   Preserve original rejection 5606f1e. Builder is idle; reactivate after account
   cleanup, authorize one import/probe plus relevant authority/weapon/feedback
   controls, then separate critic recomputes all 52 actual records. No feel,
   latency, device, CS2 parity or whole M4 acceptance claim.
7. **Combined aggregate independently accepted.** Exact frozen
   `/workspace/sightbreak-validate-b09cfe1`, source b09cfe1; raw
   `builds/combined-validation`, `.local/validation/run-3uEIWG`. Exit 0 in 465.033 s,
   before/after clean/identical. Root session 5200 is completed and closed; no
   engine remains. Source and engine hashes are in the command receipts.
   Independent 72-file archive (68 Linux  + 4 clearly separate Mac context files)
   is `c4c38a7`. Five rendered/three Windows/optional backend checks remain
   outside this run. Later capture/Mac observer revisions have focused controls
   and their own identity; don't relabel the b09 full pass as latest whole HEAD.

## Tools, recovery and constraints

Pinned engine 4.7.2 is `/workspace/tools/godot-4.7.2/Godot_v4.7.2-stable_linux.x86_64`
through `scripts/godot.sh`; `/usr/local/bin/godot` is wrong 4.6.3. Tools are shared.
Exports can use `SIGHTBREAK_STATE_DIR=/workspace/sightbreak/.local` for templates;
aggregate tests use a private per-checkout state. Never expose development keys.
Xvfb: `/workspace/tools/xvfb/usr/bin/Xvfb`. Use fresh output directories and clean,
unchanging source; validators reject dirty/changed HEAD. Coordinate local native
workloads. All 7 agent slots can be occupied; reactivate waiting builders after
completed critics free slots, without inventing independent reviews.

```sh
cd /workspace/sightbreak-v1-execution
git fetch origin '+refs/heads/*:refs/remotes/origin/*'
gh workflow run desktop-alpha.yml --repo calebaiken/sightbreak --ref codex/v1-mission-playability -f lane=windows
# Use arm-macos-ios or linux for a separately selected native lane.
# In a clean frozen checkout with required tracked fixtures present:
SIGHTBREAK_TOOLS_DIR=/workspace/tools SIGHTBREAK_BACKEND_PYTHON=/workspace/sightbreak/.venv/bin/python ./scripts/validate.sh
```

Earlier safe sparse updates recovered 6.69 GB from eleven clean completed own worktrees;
a third pass on five additional clean completed checkouts recovered at least 1.804 GB
more, plus an unmeasured partial first pass. Its initial cone-path error and exact
HEAD/untracked-size preservation receipts are retained in third JSON. No payload
was deleted. Disk has about 5.2 GB free. In all passes,
all HEADs and ignored/untracked builds were preserved. Root receipts are
`builds/session-storage-recovery*.json`. Restore omitted tracked docs with
`git sparse-checkout disable` if space permits. New worktrees should be created
with `--no-checkout` then sparse game/scripts/.github/.claude/backend/server plus
required docs/fixtures, avoiding650 MB of old archives. Check disk before exports.

Preserve Godot4.7.2/protocol6, opt-in prediction/live rewind off, privacy,
authoritative results and earned-only/offline boundaries. Do not import PR26 map
(`778c89a`), PR28 shuffle (`2641ddf`) or Gemini rewrite without new qualification.
PR17/V3 and PR18/19/21 remain unqualified. No protected merge, force push,
production deployment, Steam publication, paid action or live credential change.
Human play/listening, physical GPUs/mobile/controllers, CS2 media access and Steam
credentials remain explicit external gates. No background execution is promised.
