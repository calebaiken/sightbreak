# M5 squad-symmetric bot habits

This is a bounded bot-behavior adaptation on root `42ff3dc`, preserving reviewed
phased authority `f13ed03`. Whole bot quality G2 and competitive fairness stay
open. No matched match-balance claim is made.

## Product and source

`06092d0` adapts only Claude's authored PR28 `bot_ai.gd` delta from
`0871bc92b014fdb020cb1ac681fe70637f6cf6cd`, preserving author and co-author
attribution. Its bot blob exactly matches that source. `c2b3ded` separately
normalizes the two remaining raw-ID sine phases, as root authorized before
product edits. This gives each squad the same per-slot crouch, smoke, unstick,
defender destination, combat strafe and idle scan habits.

The only changed product file is `game/scripts/gameplay/bot_ai.gd`. Profiles,
attack/hold roles, command authority, arena, movement/action/contact phases,
objectives, privacy, protocol 6, prediction/rewind defaults, economy and platform
files are unchanged. [Source audit](SOURCE_AUDIT.md) records the exact mapping,
remaining identity uses and why PR28's shuffled-authority statistics do not apply.

## Declared and executed comparison

[PLAN.md](PLAN.md) was committed before product adaptation. The oracle runs the
real pinned native Godot 4.7.2 engine headlessly, with production TacticalMatch,
RelayYard, SBActor perception and `_bot_input`. It compares complete command
dictionaries plus roles/destinations for IDs 1/6 through 5/10 at equal poses,
role, RNG state and time. It exercises easy/normal/hard, both tactical roles,
close/long combat, travel, staged unstick, actual idle, utility boundaries and
carrier/defuse/cover decisions. These are artificial fixtures, not human play.

The final fixture is `1b88349`. Independent candidate output records 960 samples,
2,722 checks, zero failures and zero unequal pairs out of 480. All 60 idle
samples actually remain stationary. Repeated real decision calls verify the
smoke-used transition, suppression and production bot-state reset re-arm. Actual
reaction cadence first permits fire on ticks 5/3/2 for easy/normal/hard at 0.12s.

Final baseline reproduces 300 expected failing checks and 181 unequal pairs out
of 480; candidate has zero. Raw-byte hashes and archived log paths are in
`final-comparison.json`; `SHA256SUMS` hashes compressed artifacts and JSON.
Both sources use the exact final fixture. The baseline product bot
blob is root `42ff3dc`; the sparse baseline checkout at `643d022` adds only the
test fixture, which was replaced with the identical final fixture before running.

The initial baseline actual commands show one versus two habit crouchers per
squad, and two versus three eligible normal/hard noncarrier attacker smoke
commands. Final candidate counts are two crouchers and three support smokers in
each squad, retaining easy utility suppression and carrier/defender exceptions.

## Maintained and independent verification

Full `scripts/validate.sh` completed exit 0 on frozen `8ef757e`, with the same
final product bot blob and earlier r2 fixture. Raw output is archived as
`candidate/validate.log.gz`; `candidate/validate-markers.txt` keeps the summary
markers. This includes bot AI, bot match/lifecycle, actor, weapons, hit-volume,
authority order (178), privacy (55), objectives, network/lifecycle, UI/economy and
tooling checks. The landscape suite reports 9,217 checks with zero failures.

The later fixture-only changes in `1b88349` were independently rerun with source
and hash guards: final oracle, bot AI, authority, match (75), actor (73), weapon,
hit-volume and privacy all pass. Independent evidence and verdict live on the
critic's branch under the same milestone's `independent-critic` directory.

Full validation retains its ordinary omissions: no DISPLAY means rendered
reload checks are skipped; backend SQL is not requested, the new worktree has no
backend Python for catalog drift, and three native-Windows observer cases skip
on Linux. No new Windows/Mac/mobile export or physical-device claim follows.

The maintained stock lifecycle observes 10 rounds, 7:3, 60 kills, halftime, one
result and a plant at seed 1847/time scale 4, finishing after 325.9 simulation
seconds. This is one bounded observation, not a matched improvement or closure
of the historical F1 objective-quality finding.

## Failed iterations and limits

- R1 used a 30 m long-range target outside easy vision's unchanged 28 m limit.
  Candidate paired outputs matched, but 28 fixture expectations failed. Both r1
  sources are retained; r2 corrects the target to 26 m.
- R2 passed candidate 2,566 checks, but 26 of 60 nominal idle samples still moved
  after escort logic selected a hold offset. Builder and independent critic
  identified this coverage gap. Final r3 resolves the stable destination and
  explicitly requires zero movement, adding repeated-smoke controls.
- The optional predeclared eight-match seed/start/source set was omitted before
  any sample started, per root priority. Retained observation tooling is for
  future qualification; no measurements or broad balance statistics are claimed.

The largest remaining deficiency is complete-match bot objective/cooperation
quality and competitive balance on this phased stack. Equal commands under
equal fixture state do not establish equal random exposure, player feel, match
balance, device performance or earned online progression. The builder does not
approve this change; integration depends on the fresh independent critic.

## Reproduce

Use `SIGHTBREAK_TOOLS_DIR=/workspace/tools ./scripts/godot.sh --headless
--audio-driver Dummy --script res://tests/bot_squad_symmetry_test.gd` on the
candidate. On an isolated baseline with the identical test file, append
`-- --observe` to retain expected baseline failures with exit 0. Run
`./scripts/validate.sh` for maintained validation. All raw log archives are gzip;
`gzip -dc <path>` restores the exact recorded bytes before hash comparison.
