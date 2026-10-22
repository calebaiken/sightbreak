# M3: same-tick hitscan order candidate

Status: **Independent critic accepted the bounded correction; integrated as f13ed03 with reviewed oracle 8571c78.** This is a bounded
correctness correction, not a claim that SIGHTBREAK matches are balanced.
Criteria were recorded before gameplay edits in [CRITERIA.md](CRITERIA.md).

## Reproduction and change

The frozen `6a0d8d5` baseline loses the later actor's return fire in every one of
32 deterministic mirrored rifle duels. Reversing Dictionary insertion order
reverses every winner. The same tick's moving and crouching targets are hit before
they advance in one insertion order and missed in the other. The corrected
candidate accepts both lethal shots in all 32 duels and uses the post-movement
pose in either order. The identical reviewed harness passes 178 checks on the
candidate and intentionally fails 152 checks on the frozen baseline. Its paired
pose assertions allow 0.1 mm of native floor-solver settling; the observed largest
first-pair residue was 78 µm.

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

- [before-reviewed-assertion.txt](before-reviewed-assertion.txt): reviewed frozen
  baseline oracle, expected exit **1**, with [receipt](before-reviewed-receipt.json).
- [after-reviewed-final.txt](after-reviewed-final.txt): reviewed candidate, 178
  checks, zero failures, from the frozen `d593d7b` harness.
- [reviewed-source-manifest.json](reviewed-source-manifest.json): engine, exact
  product/harness commits, hashes, complete default validation result and skips.
- `before-final-assertion.txt`, `after-final.txt` and `source-manifest.json` retain
  the earlier 162-check oracle and its original provenance.
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
is retained as `before-reviewed-cpu.txt` / `after-reviewed-cpu.txt`.

The final identical `--benchmark-only` pair passes 14 assertions on each build.
Every active sample records 3,170 or 3,180 shots and the same number of damage
events. Final raw files are `before-reviewed-flushed-cpu.txt` and
`after-reviewed-flushed-cpu.txt`; [reviewed-cpu-summary.json](reviewed-cpu-summary.json)
retains all samples.

| Condition | Baseline median / p95 (µs) | Candidate median / p95 (µs) |
| --- | --- | --- |
| Idle | 246.74 / 259.08 | 245.49 / 249.94 |
| Active shots and damage | 487.29 / 503.48 | 462.88 / 466.55 |

The relative medians are -0.51% idle and -5.01% active in this pair. This shows no
regression in the measured conditions; shared-host noise prevents a speed-up or
exact-overhead claim. These are headless CPU measurements, never hardware frame
rate or input latency. Deferred audio allocations occur inside the timed calls;
their cleanup and visual/render work occur outside. This measures only the narrow
headless authority call, not total simulation-frame cost.

The independent instrumented pair is retained under [independent/](independent/).
It also passes 14/14 active assertions on each build, with median idle/active costs
249.42/480.22 µs baseline and 247.22/475.68 µs candidate. Nodes (448), audio nodes
(60), resources (69), effect slots (24/40/12) and message-buffer maximum (4,096)
stay fixed. Temporary objects return to about 2,346 after each two-frame flush.
The small post-flush static-memory increase tracks the test's recorded-shot array
(22,700 entries), rather than new gameplay nodes. These short runs do not certify
long-session memory or frame-time quality.

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
command. The reviewed pose/benchmark harness is a subsequent test-only change.
The fresh critic accepted the bounded correction in [independent/REPORT.md](independent/REPORT.md),
using known source identities and native reproduction, without a blind comparison.
Its complete raw top-level artifacts and checksums are in
[independent/review-raw.tar.gz](independent/review-raw.tar.gz). Root owns integration;
this acceptance closes no general fairness or ten-client qualification gate.
