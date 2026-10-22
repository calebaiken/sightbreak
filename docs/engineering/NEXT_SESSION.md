# Next session

Updated 2026-10-22, 05:07 UTC. Continue **SIGHTBREAK — Steam-Ready v1.0**,
IN PROGRESS / PRIMARY, [issue25](https://github.com/calebaiken/sightbreak/issues/25).
No native Codex goal API is exposed. Read AGENTS.md, the mission and the single
G1–G20 progress matrix; reuse both original installed quality skills. Continue
implementation after each verified increment. No whole RC gate is closed here.

## Repository checkpoint

- Root `/workspace/sightbreak-v1-execution`, branch `codex/v1-mission-playability`.
- [Draft PR27](https://github.com/calebaiken/sightbreak/pull/27) targets PR24
  `claude/mission-foundation-v1` (`c84eaf3`), then PR23 `db3981e` → PR22 `82a03fc`
  → PR16 `d2439ac`. Do not merge or rewrite shared/contributor branches.
- Integrated checkpoint before this documentation commit: `3d172a1`. This includes
  accepted account validator/recovery evidence, layout OCR/PNG packaging/Linux
  workflow lane, latest Windows raw review and six bot habit corrections.
- Last remote CI source is `dc2a198372b2e5da51ca1618f16d8249e44ec485`, Windows-only.
  Later source must receive its own export and receipts; never relabel old builds.
- Fetch live refs before integration. Main last observed `4d8cdb3`. PR17 V3 and
  PR18/19/21 remain unqualified. PR26 map at `778c89a` is not integrated. PR28
  `2641ddf` includes bot delta `0871bc9`, adapted with Claude attribution here;
  its authority shuffle is excluded in favor of reviewed phased authority.

## Current native results and exact failures

1. [Combined run39719407304](https://github.com/calebaiken/sightbreak/actions/runs/39719407304),
   source `0ca125dfba637868e6e8e9772ff9c40400413e32`: all four jobs fail overall,
   while all ten source suites pass on all four native hosts (1,281 checks each).
   Windows/Linux ordinary plant, defuse, stock match and earned restart pass.
   Linux ordinary journey passes 229.587 s; 12-round 6:6 draw persists exactly
   120 XP / 250 offline credits. Linux layout fails three original timing gates:
   960/1920 menu confirmation exceeds deadlines; 1280×720 OCR exceeds its remaining
   budget; 1280×800 passes. Full PNG artifact exceeds 32 MiB transfer cap, so new
   per-size originals need an actual run. Windows journey dies during old settings
   scheduling; corrected in later source. Intel default/OpenGL and all five
   feature ablations time out at 120 s with no completed capture. Minimal 2D/3D
   controls pass. No winning graphics variant supports a shipping change.
2. [ARM run39721286005](https://github.com/calebaiken/sightbreak/actions/runs/39721286005),
   source `2a2b732c9f4637e9c2c68890cdd0f13d8fa89906`: exactly one ARM job passes.
   Actual unsigned generic-device iOS compile/link succeeds under Xcode26.3 /
   SDK26.2 after a real forced-symbol SDK selection probe. Link takes 36.953 s;
   codesign says unsigned; native source/PCK/Mach-O receipts agree. Independent
   critic checked all 142 indexed files, six PNGs and raw logs, but did not transfer
   or reparse the 102 MB executable. Installation, runtime, physical play,
   simulator and older OS behavior remain open. Earlier SDK18.5 linker failure
   is retained; no deployment-target bump is inferred from its five symbols.
3. [Windows run39723283770](https://github.com/calebaiken/sightbreak/actions/runs/39723283770),
   source `dc2a198372b2e5da51ca1618f16d8249e44ec485`, job119641410526: FAIL.
   All ten source suites, explicit inner HUD fixture cleanup, startup/input/reload,
   plant180 ticks, defuse300 ticks, 12-round stock 7:5 local defeat and earned
   restart (120 XP / 250 offline credits) pass. Settings/resume now preserves
   living actor/round at 100 HP through real Escape acknowledgment and two frames.
   Complete ordinary journey fails later at `Native UI text not found: LEAVE`
   after 87.516 s; later focus/restart gates are unreached. Exact retained failed
   `ocr-current.png` visibly has LEAVE MATCH. Supporting Linux Tesseract replay
   reads LEAYE MATCH; original Windows TSV is unavailable. Full raw review is
   `docs/reports/gauntlet/m1-native-ci-39723283770/README.md`, root commit `2cc1063`.
   Actual image: `/workspace/reviews/native-ci-39723283770/windows-full/offline-input/ocr-current.png`,
   SHA256 `e62116a4c42c7b09ca947a7eb1cb3551865c4d6f4ffecff36066f8e7d4bee635`.

## Accepted implementation and engineering evidence

- FIELD MENU focus `8de7331`/`aa0b0a4`, ordinary native objective controller
  `44cb081`, X11 lifetime `2e158e2`: fresh independent actual OS-input tests.
  Queued objective pulse has a 1.5 s-delay counterexample outside its tested
  0–0.2 simulation-second envelope; retain that limitation.
- Freshness `0917771`: consumed replays cannot renew authority/idle clocks. Blind
  native comparison 8/8 versus 4/8; eight snapshot stops 316–334 ms under 350 ms.
  These same-host results do not establish remote competitive feel.
- Two-phase authority `f13ed03`, oracle `8571c78`: movement then all action traces
  against common living roster, then contact commit. Independent 178 checks pass
  versus 152 baseline failures. Corrected CPU samples include real shots/damage
  and bounded pools. Multiattacker credit, simultaneous wipe and contact policies
  remain open. No protocol/privacy/economy change.
- Source-suite isolation `05d9b43`/`9290154` and inner HUD fixture correction
  `f7d1779`/`483a8b0` independently pass failure/negative controls. Latest actual
  Windows confirms owned fixture removed and caller restored. Do not generalize
  outer-suite cleanup receipts to historical inner fixtures or hard-kill safety.
- Account match source `471fbd8`: ten real HTTP identities, stock 7-round match,
  six ordinary plants, automatic halftime, all ten replicas; 525.962 s wall.
  Earned production payload survives Godot/worker kills, PostgreSQL outage, lost
  reply and duplicate spool replay. Exactly one operation / ten rewards / ten
  ledger rows, 2,875 credits / 2,650 XP. Independent critic queried the actual owned
  database and verified cleanup. Fifteen final validator controls/raw replay pass.
  Test-only changes; nine clients turn at spawn, no meaningful-participation or
  AFK-resistance qualification. Client traffic is loopback; inherited ENet server
  listens on wildcard UDP, API/database on loopback. All children/container removed.
  Evidence: `docs/reports/gauntlet/m3-account-match`.
- Network frozen `0ca`: 11 soak reports/80 recoveries, twelve synthetic campaign
  conditions, protocol8/8 and hostile8/8 independently reviewed. Original impaired
  18-second lost-close trial FAILS3/10; distinct 30-second diagnostic recovers10/10
  within the existing20 s episode (ACK upper14.890 s). No runtime patch justified.
  Prediction hard corrections/feel and 60 s reservation expiry remain unqualified.
  Evidence: `docs/reports/gauntlet/m3-network-qualification/independent-critic`.
- Six bot habits integrated `2cbf778`/`ca6b9b9`, final fixture `aa2a3cd`, independent
  evidence `27b67b5`. Final exact-engine oracle 960 samples / 2,722 checks:
  candidate0 failures/0 unequal pairs, baseline300 failures/181 of480 unequal.
  Both final idle sets are truly stationary. Nine independent focused steps pass.
  Full maintained suite passed earlier candidate `8ef757e`; a new combined suite
  is required after account + bot integration. Optional eight-match tool did not
  run and needs before/after source/harness guards before future measurements.
  Whole G2/cooperation/fairness remains open. Evidence: `m5-bot-squad-symmetry`.
- Layout child-only OMP limit `a579a36` independently yields identical TSVs in
  176 actual calls, CPU47.861→22.521 s (52.94% less), wall22.927→22.577 s (1.5%).
  This is bounded resource improvement, not a proven timeout fix. Original520/120 s
  aggregate/case and recognition/source/frame safeguards stay unchanged. Per-size
  PNG packaging `f5872e6` and explicit Linux lane `b536542`/`807b56b` are independently
  accepted, source review `8588f80`; actual source-bound rerun is next.

## Immediate execution queue

1. Commit/push a clean checkpoint, freeze it in a new sparse worktree, export
   Linux and run actual four-size `capture_desktop_layouts.py --touch-toggle`
   under original520/120 s limits. Coordinate the local CPU lane. Then run the
   maintained suite on that frozen combined source; preserve skips/failures.
2. Dispatch registered `desktop-alpha.yml` with `lane=linux` on the own branch.
   Verify actual returned HEAD and exactly one Ubuntu job. Download bounded raw
   receipts and new per-size original PNGs, independently review actual outputs.
3. Continue LEAVE observer iteration: agent `offline_journey_builder`, branch
   `fix/offline-journey-leave-397232`, preregistered criteria `3a37b4d`. Exact
   production pixel replay reproduces LEAYE MATCH. Preserve full-caption/readability,
   menu/source/life/frame guards and real OS inputs; no fuzzy acceptance or relaxed
   deadlines. Require fresh separate critic and exact full Windows retry.
4. New `mac_input_builder` is implementing read-only Darwin CoreGraphics preflight
   in its own sparse worktree, based on `e38ec3c`. Check non-requesting post-event,
   screen-capture and accessibility permissions, exact exported-PID window/display.
   Never modify TCC/security databases, bypass denied APIs or trigger unattended
   permission prompts. Current NativeUI supports only X11/Win32. No actual Mac
   input claim yet; `--borderless` and `--user-data-dir` are unsupported in pinned
   engine. macOS user:// does not honor HOME/XDG. If input is allowed, ordinary
   menu→Settings→Escape can prove navigation without changing persistent values.
   Review the helper separately before dispatching actual ARM CI.
5. Reassess next product blocker after new outputs. Refresh Android export after
   core changes if resources permit; retain upstream simulator mismatch. Do not
   import PR26 map/PR28 shuffle or rewrite Gemini bots without separate qualification.

## Commands and storage

Pinned Godot4.7.2 is `/workspace/tools/godot-4.7.2/Godot_v4.7.2-stable_linux.x86_64`
through `scripts/godot.sh`; `/usr/local/bin/godot` is wrong4.6.3. Use
`SIGHTBREAK_TOOLS_DIR=/workspace/tools`, `SIGHTBREAK_STATE_DIR=/workspace/sightbreak/.local`.
Xvfb is `/workspace/tools/xvfb/usr/bin/Xvfb`. Never read/print/commit development keys.
Use fresh outputs and clean exact HEAD; exports/validators reject dirty or changing
sources. Source-bound tests run in an immutable checkout while root docs advance.

```sh
cd /workspace/sightbreak-v1-execution
git fetch origin '+refs/heads/*:refs/remotes/origin/*'
gh workflow run desktop-alpha.yml --repo calebaiken/sightbreak --ref codex/v1-mission-playability -f lane=linux
# In a separate frozen checkout with shared tool/state variables:
SIGHTBREAK_BUILDS_DIR="$PWD/builds/new-linux" python3 scripts/export.py linux
SIGHTBREAK_BUILDS_DIR="$PWD/builds/new-linux" XVFB_BIN=/workspace/tools/xvfb/usr/bin/Xvfb LIBGL_ALWAYS_SOFTWARE=1 LP_NUM_THREADS=2 python3 scripts/capture_desktop_layouts.py --touch-toggle --output builds/new-layouts
./scripts/validate.sh
```

Disk reached ENOSPC during this session. Root recovered4.1 GB only by sparse-excluding
tracked historical docs in seven clean completed own worktrees; all HEADs and
untracked builds were preserved. Receipt: root `builds/session-storage-recovery.json`.
Frozen `/workspace/sightbreak-v1-qualification`, `...-mobile6a`, `...-ios-compile`
and several completed review worktrees now omit docs. Git retains those files;
`git sparse-checkout disable` restores them if space permits. Create new worktrees
with `--no-checkout` then sparse patterns (all game/scripts/.github/.claude/backend/
server, root instructions and required docs); avoid copying600 MB of old archives.
Root/contributor active worktrees remain intact. Check `df -h` before exports.

Physical GPU/input latency, mobile/controller devices, human play/listening and
Steam credentials remain external blockers. CS2 official/media hosts returned
access denials; `docs/research/cs2-access-2026-10-22` records them. No visual parity,
8.5/10 quality or background execution is claimed.
