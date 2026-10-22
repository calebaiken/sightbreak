# Next session

Updated 2026-10-22, 05:58 UTC. Continue **SIGHTBREAK — Steam-Ready v1.0**,
IN PROGRESS / PRIMARY, [issue25](https://github.com/calebaiken/sightbreak/issues/25).
No native Codex goal API is exposed. Read AGENTS.md, the mission and the canonical
G1–G20 progress matrix. Reuse the installed original quality skills. Continue
implementation after each verified increment; these corrections do not finish v1.

## Root and source checkpoints

- Root: `/workspace/sightbreak-v1-execution`, `codex/v1-mission-playability`.
  Current checkpoint before this note: `609913e`; last pushed: `3b97a00`.
- [Draft PR27](https://github.com/calebaiken/sightbreak/pull/27) targets PR24
  `c84eaf3` → PR23 `db3981e` → PR22 `82a03fc` → PR16 `d2439ac`.
  No shared branch was merged or rewritten. Fetch live refs before integration.
- Complete unmodified aggregate **PASSES at `b85f93600e122b36e8dcd70edd9bc168e9820b08`**.
  Frozen worktree `/workspace/sightbreak-validate-a23e349` has that actual HEAD;
  its directory name is historical. Raw output `builds/combined-validation-r2`,
  logs `.local/validation/run-utj57N`. Game tree `e877ba16bdc7f63994930a77f32e484e8f12d890`,
  content SHA256 `db3c976711ef8d91b75604fdfe05309599445cfc5bdf59e5f6fbdf669a859fc5`,
  validation SHA256 `0fd96995226efdf47fb351860eedda3a8ca1b0086b3ef291a5e99f640766abc3`.
  Before/after source is clean and identical. Independent evidence `609913e`:
  `docs/reports/gauntlet/combined-validation-b85f936/independent-critic/REVIEW.md`.
  All52 required Godot logs, ENet2/2, lifecycle cleanup, catalog29 and Python groups
  pass. Five rendered checks, three Windows unit cases and optional backend SQL
  are not covered. Later Mac tools change validation identity; do not relabel this
  pass as the whole latest HEAD. Shipping game/backend/server equal `3b97a00`.
- First aggregate at `a23e349` failed because root sparse checkout omitted tracked
  reload CSV/hash fixtures. Original57-file archive/exit1 remains in `0e63ada`.
  Restore `docs/reports/media/art-v9/hands/logs` in every aggregate checkout.

## Actual native runs

| Run / exact source | Accepted output and failure |
| --- | --- |
| [39725980732](https://github.com/calebaiken/sightbreak/actions/runs/39725980732), `872a576`, single Linux119649852989 | Raw independent source/input/ordinary journey, defuse,9-round stock match/earned restart and four-size201.314 s pass. Player plants180 ticks, +1objective/+300credits, but later15 s role-guidance wait fails amid notifications before death. Natural resolution/restart in that plant scenario are unreached. FullQA46 MB untransferred; original per-size PNGs available. Evidence `b85f936`, report `m1-native-ci-39725980732/remote`. |
| [39727011693](https://github.com/calebaiken/sightbreak/actions/runs/39727011693), `e7718ee`, single ARM119653125533 | Actual no-event readiness and unsigned iOS compile independently pass. All four permission APIs true; exact preflight PID6968/window34/internal PNG valid, profile absent, normal0/no remaining group. No input posted. Evidence `e6c323a`, `m2-macos-input/native-run-39727011693`. |
| [39728129445](https://github.com/calebaiken/sightbreak/actions/runs/39728129445), `a8eb7eb`, single Windows119656711230 | Overall FAIL only plant by final metadata. Independent raw ordinary journey now passes, all16 original OCR outputs/strict LEAVE call retained. Defuse/full match pass; raw archive is being finalized. Its own180-tick plant/reward/living PNG pass, followed by notification starvation/death in15 s role wait. Critic `native_ci_outcome_critic` retains original fullQA22.7 MB and bounded3.3 MB. |
| [39729489971](https://github.com/calebaiken/sightbreak/actions/runs/39729489971), `3b97a00`, single ARM119661018459 | New real-menu attempt FAILS before events. Swift compiles; gamePID3996 cannot be verified foreground within5 s (last observedPID3721),0CGpost attempts, no helper invocation/OS capture. Ordinary close0/groups gone. Own helper permission/geometry/Vision unreached. Separate preflightPID3571/window35 cannot stand in for3996. All12 native suites actually pass4,461 assertions. Fresh critic `mac_native_menu_outcome_critic` is committing raw report. |

Earlier `0ca125d` run39719407304 and `6a0d8d5` run39712752860 failures remain
historical. Intel default/OpenGL and all five feature ablations time out120 s;
minimal controls pass, no winning variant supports a shipping renderer change.
Physical Intel/Mac GPU qualification stays open. Actual unsigned iOS compilations
succeed under probed process-local Xcode26.3/SDK26.2, with native attestation and raw
linker/codesign/PCK receipts; large app binaries were not independently transferred.
Installation, runtime, older OS and physical mobile play remain open.

## Active execution queue

1. **M1 objective-guidance priority.** Builder `/root/offline_journey_builder`,
   `/workspace/sightbreak-postplant-priority`, branch `fix/postplant-guidance-priority`.
   Criteria `aedb7e6`, candidate `3c4d921` based on integrated `93ec98b`.
   Only status selection and typed presentation connection-notice callbacks change;
   RPC/privacy/economy/authority/timers and accepted touch/feed functions stay intact.
   Actual HUD flood comparison: candidate1,535/0 versus baseline1,492 failures;
   fresh critic independently recomputes all1,458 flood frames, plus1,559 controls.
   Recorded native round3 passes180-tick plant, living DEFEND THE DEVICE pixels and
   genuine natural defuse, but FAILS unchanged12 s next-round wait with0.65sim left.
   Genuine130.6 s/10Hz silent X11 MP47,961,368 bytes is retained; SHA256
   `9527ba7f05d288c1545ea8dbc3723a83d5e19774118af099119fb6c7b0dfb7cc`.
   Raw `.local/postplant-priority/round-3`. One final same-source/no-recorder retry
   is authorized under unchanged180/15/12 s budgets. No timer/seed/state injection.
   Critic `/root/postplant_guidance_critic` owns independent source/pixels/video
   review. Integrate only after scoped independent acceptance; whole plant gate
   stays failed until actual resolution/next-round/restart pass. Preserve two
   external recorder setup failures (no gameplay started) and round3 failure.
2. **M3 corrected account match.** Prepared `/workspace/sightbreak-account-activity`,
   branch `codex/m3-account-activity-qualification`, provisional `3b97a00`, no runtime.
   Builder `/root/account_match_builder` is idle and needs reactivation after a
   slot frees. Fresh `/root/account_activity_qualification_critic` has read-only
   live-DB observer ready; prep commit `664a699` is not acceptance.
   After M1 releases its lane, name exact integrated final source, freeze it, and
   run unchanged final `scripts/test_account_match.py` with ten NEW fake accounts,
   isolated owned PostgreSQL/API/ports/spool and original stock rules/recovery.
   Roughly9 min plus import. Critic must query actual ownedDB before ACK and after
   replay, then verify cleanup. Fifteen controls already pass; do not repeat unless
   source changes. Prior471fbd8 result (one operation/10rewards/2,875credits/2,650XP)
   does not qualify post-activity product. Yaw-only policy remains allowed, with no
   AFK-resistance/human-participation claim; inherited UDP listener is wildcard.
3. **M2 Mac focus observer.** Builder `/root/mac_input_builder`, own sparse
   `/workspace/sightbreak-macos-focus`, branch `codex/m2-macos-focus-observer`,
   base609913e. Inspect actual run39729489971 before revising. Original raw base:
   `/workspace/sightbreak-mac-menu-native-review/docs/reports/gauntlet/m2-macos-menu-input/native-run-39729489971/full-qa/macos-menu-input`.
   Public SDK header says NSRunningApplication time-varying values update on main
   run-loop turns: this proves an observer risk, not that run's failure cause.
   Prepare truthful selected-window/activation-return/before-after run-loop/state
   receipts with the same single public activation and5 s guard. Independent owned
   background capture may decouple capture permission/geometry from focus; critique
   revised criteria before native use. Never substitute window order for focus,
   bypass/request TCC, mutate securityDB or use unsupported flags/alternate identity.
   Need fresh source critic, then root dispatches ARM lane on clean source.
4. **M6 touch transition accepted.** Integrated `66bcc5e`/`a06017b`, final native
   source589a52a. Initial candidate visually wins but is rejected for existing-row
   clipping. Revision passes462 checks vs prior16 failures, independent4/4 clipping
   probe, and original71.891 s native on/off flow. Fresh final blind judge chooses
   final candidate for clear MENU/device spacing and correct hints. Evidence
   `9efaf63`, `4a1205c`/followup and `93ec98b`; report `m6-touch-hud-transition`.
   Control contrast over weapon/pavement remains open. Full game tree is covered by
   the b85 aggregate; no G7/G10/physical/8.5 presentation closure.

## Tools, recovery and constraints

Pinned engine4.7.2 is `/workspace/tools/godot-4.7.2/Godot_v4.7.2-stable_linux.x86_64`
through `scripts/godot.sh`; `/usr/local/bin/godot` is wrong4.6.3. Tools are shared.
Exports can use `SIGHTBREAK_STATE_DIR=/workspace/sightbreak/.local` for templates;
aggregate tests use a private per-checkout state. Never expose development keys.
Xvfb: `/workspace/tools/xvfb/usr/bin/Xvfb`. Use fresh output directories and clean,
unchanging source; validators reject dirty/changed HEAD. Coordinate local native
workloads. All7 agent slots can be occupied; reactivate waiting builders after
completed critics free slots, without inventing independent reviews.

```sh
cd /workspace/sightbreak-v1-execution
git fetch origin '+refs/heads/*:refs/remotes/origin/*'
gh workflow run desktop-alpha.yml --repo calebaiken/sightbreak --ref codex/v1-mission-playability -f lane=windows
# Use arm-macos-ios or linux for a separately selected native lane.
# In a clean frozen checkout with required tracked fixtures present:
SIGHTBREAK_TOOLS_DIR=/workspace/tools SIGHTBREAK_BACKEND_PYTHON=/workspace/sightbreak/.venv/bin/python ./scripts/validate.sh
```

Safe sparse updates recovered6.69 GB from eleven clean completed own worktrees;
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
