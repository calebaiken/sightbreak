# M3: same-tick hitscan order candidate

Status: **IN PROGRESS; independent acceptance pending.** This is a bounded
correctness correction, not a claim that SIGHTBREAK matches are balanced.
Criteria were recorded before gameplay edits in [CRITERIA.md](CRITERIA.md).

## Reproduction and change

The frozen `6a0d8d5` baseline loses the later actor's return fire in every one of
32 deterministic mirrored rifle duels. Reversing Dictionary insertion order
reverses every winner. The same tick's moving and crouching targets are hit before
they advance in one insertion order and missed in the other. The corrected
candidate accepts both lethal shots in all 32 duels and uses the post-movement
pose in either order. The identical final harness passes 162 checks on the
candidate and intentionally fails 152 checks on the frozen baseline. After fresh
review, 16 explicit paired-pose assertions raise the oracle to 178 checks with a
0.1 mm tolerance; the observed first-pair floor difference was 78 µm. See
`after-reviewed.txt` and `before-reviewed-assertion.txt` for that revised oracle.

The match now advances all actor movement and stance, then runs existing action
logic and traces with a server-local hit sink, then resolves queued contacts before
objectives, round elimination checks, hit history and snapshots. One actor can
queue at most one contact per tick; the existing roster bounds the queue to ten.
Every trace retains living front-actor shielding for that batch. Contact resolution
skips an already eliminated victim, so repeated contacts do not duplicate deaths
or the 300-credit elimination reward. Standalone `SBActor.tick_authority` remains
an immediate movement/actions/damage wrapper. Weapon data, movement math,
prediction, protocol 6, rewind settings and privacy filters are unchanged.

Native engine output and provenance:

- [before-final-assertion.txt](before-final-assertion.txt): intentionally failing
  frozen baseline oracle, exit **1**, with [receipt](before-final-receipt.json).
- [after-final.txt](after-final.txt): final candidate, 162 checks, zero failures.
- [source-manifest.json](source-manifest.json): engine, branch and source hashes.
- [before.txt](before.txt) and [after.txt](after.txt): initial corrected fixture
  before/after runs, with 130 checks and raw CPU samples.
- Expanded runs retain the intermediate 162-check harness. Its first shield
  arrangement accidentally let the two shooters shield each other. The final
  arrangement separates their bodies and aims converging rays at the front target.
- `before-fixture-deferred-reset.txt` and `before-fixture-transform-flush.txt`
  are rejected fixture iterations. Deferred death collision-disable and teleported
  physics shapes needed to flush before fixture reuse. Their unstable poses are
  not evidence of product fairness or timing. Both are retained for audit.

The fixture uses ten real actors, the real authoritative tick and physics on a
simple floor. It suppresses bot decisions and transport to hold commands, actor
IDs, RNG seeds and geometry constant. This isolates the processing defect found
in Claude PR26 `5288a69`; it does not integrate that branch or edit arena/bot code.
The inspected external evidence is in the PR26 git blobs under
`docs/reports/gauntlet/relay-yard-layout`, especially `stats-review.md` and the
before/after summaries. Its 71% squad win report and reverse-order experiment
motivate this reproduction; they do not establish role or map balance.

## Ten-actor CPU cost

The harness warms 300 ticks and records seven sample means of 2,000 authoritative
ticks per condition. No-fire and held-trigger conditions have identical ten-actor
commands across builds. [cpu-summary.json](cpu-summary.json) retains every sample;
p95 below is the nearest-rank p95 of those seven sample means, not individual-tick
tail latency.

| Run pair | Baseline idle median / p95 (µs) | Candidate idle median / p95 (µs) | Baseline depleted-trigger median / p95 (µs) | Candidate depleted-trigger median / p95 (µs) |
| --- | --- | --- | --- | --- |
| Initial | 236.46 / 251.02 | 311.75 / 343.02 | 253.43 / 299.86 | 326.31 / 383.05 |
| Repeated expanded harness | 239.33 / 240.90 | 240.64 / 252.64 | 255.23 / 304.73 | 256.51 / 300.33 |

The fresh critic found that these original `fire=true` loops depleted the stock
ammunition during the first sample. The table therefore measures mostly empty
held-trigger attempts; it provides **no sustained-fire cost evidence**. The initial
increase exceeded the 25% investigation threshold and did not reproduce in the
adjacent repeat (+0.55% idle, +0.50% depleted trigger). Shared-host contention is
uncontrolled; an exact isolated overhead cannot be established from these runs.

The reviewed benchmark adds sufficient fixture ammunition, recoil-compensating
authoritative look inputs, and shot/damage event counts. It checks 3,170–3,180 shots
and equal damage events in every active 2,000-tick sample. Actual authority calls
are timed individually; control generation and deferred presentation/audio frame
flushes occur outside the measured intervals. The earlier unflushed active trial
is retained as `before-reviewed-cpu.txt` / `after-reviewed-cpu.txt`; final reviewed
measurements will be recorded separately. These are CPU measurements on a shared
headless host, never hardware frame rate or input latency.

## Remaining limitations and design questions

The largest remaining gap is **multiattacker attribution**. Sequential contact
commit preserves the existing actual-damage/last-hit rule. In the final shield
fixture, actor 1 earns the one kill in forward order and actor 2 earns it in
reverse order. Health, shielding, total deaths and total rewards agree, but killer,
assist contribution and lethal feedback can still depend on contact order. A
shared-kill, contribution or tie-break policy needs an explicit competitive design
decision. This candidate does not invent one or certify general order invariance.

The existing `_check_elimination` awards attackers when both teams reach zero in
the same tick. The change permits legitimate same-tick trades and exposes that
existing rule; a final-player trade/draw policy remains unsupported. Hitscan is
batched only inside the authority tick. Utility detonation retains its independent
physics callback and immediate damage. Actors alive at action time can deploy
utility during their accepted action before the queued hitscan damage kills them.
Godot `move_and_slide` contact resolution remains sequential, and exactly equal
overlapping trace-volume distances still use combatant group order. These tests
avoid overlapping bodies and do not prove collision permutation invariance,
sub-tick fairness, human/bot match balance or network latency quality.

## Re-run

Use the existing pinned toolchain; no installation is required here:

```sh
./scripts/godot.sh --headless --editor --import --quit
./scripts/godot.sh --headless --script res://tests/authority_order_test.gd
./scripts/godot.sh --headless --script res://tests/authority_order_test.gd -- --benchmark
./scripts/validate.sh
```

To reproduce the baseline, create a detached worktree at `6a0d8d5`, copy the exact
final `game/tests/authority_order_test.gd` into it, import, and run the same command.
Expect assertion exit 1. `--observe` reports the failed checks while exiting 0 and
is for exploratory observations only. It is never a passing maintained regression.
Full default maintained validation on product commit `470fad5` completed with
exit 0; [validate.txt](validate.txt) retains actual output. No rendered display was
used, catalog drift lacked backend Python, and three Windows publication checks
were skipped on Linux. Backend service validation was not requested by the default
command. The reviewed pose/benchmark harness is a subsequent test-only change. A fresh independent critic must judge source, evidence and limitations
before root considers integration. The builder has issued no acceptance verdict.
