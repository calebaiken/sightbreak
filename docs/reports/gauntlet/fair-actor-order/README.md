# Evidence: no actor id gets a head start

Finding F2 from the Relay Yard layout work: in all-bot matches the squad of actors 1-5 won most rounds whichever side it played. This record covers the two causes found, the fixes, and what the measurements do and do not show.

| Item | Value |
| --- | --- |
| Piece | Authoritative actor processing order (`match.gd`) and per-bot habits (`bot_ai.gd`) |
| Bar | B3: the previous verified build, `codex/desktop-playability-p1` at `db3981e` (set A below). Proves improvement; says nothing about Counter-Strike 2 parity. |
| Candidate | Branch `claude/fair-actor-order-v1`: shuffle commit (set B) and bot-habit commit (set C onward) |
| Environment | Godot 4.7.2 official, headless, 4 vCPU, bots only, `Engine.time_scale` 4. Times are simulation seconds. |
| Builder / checker | Claude (lead session). Numbers recomputed from the raw logs by a separate fresh-context reviewer of the same model family: [independent-check.md](independent-check.md). |
| Not covered | Human play, networked play, any other map. The layout is the unchanged 48 m pad of `db3981e`. |

## Cause 1: the tick walked actors in id order

`_authority_tick` ran `tick_authority` for each actor in `actors.values()` order. A shot lands the moment its actor is processed, so in a same-tick trade the lower id fired and killed first.

Fix: a uniform Fisher-Yates shuffle each tick, from its own `RandomNumberGenerator`, so the gameplay random stream is untouched and diagnostic fixtures stay reproducible (`_order_rng` is seeded from the fixture seed when one exists). One shuffle per tick serves both the bot-input loop and the per-actor loop.

**A rotation was tried first and dropped.** Shifting the start by one place per tick makes every actor lead 10% of ticks, and a per-actor check passes. It is still unfair per pair: actor *i* precedes actor *j* in 1 - (j-i)/10 of ticks, so ids 5 and 6 would go in that order 90% of ticks. Averaged over squads it looks fair, which would have hidden the seat-level bias. The regression test therefore checks every one of the 45 pairs.

`game/tests/tick_order_test.gd` (registered in `scripts/validate.sh`): 20,000 ticks, every tick a permutation of the ten actors, every pair first 47% to 53% of the time, every actor leads about 10% of ticks, the same seed gives the same orders and a different seed does not, and shuffling leaves `_rng` alone. Negative controls, run against the same test:

| Order | Result | Worst pair | File |
| --- | --- | --- | --- |
| Shuffle (shipped) | 73 checks, 0 failures | ids 3,6: 0.9 points from 50% | `data/tick-order-test-shuffle.txt` |
| Fixed id order (original) | 57 checks fail | ids 1,2: 100% | `data/tick-order-test-fixed-order.txt` |
| One-place rotation | 42 checks fail | ids 1,2 and 5,6: 90% | `data/tick-order-test-rotation.txt` |

## Cause 2: bot habits keyed on raw id parity

After the shuffle, actors 1-5 still won 61% of rounds on both difficulties. Reading `bot_ai.gd` for id arithmetic found places that are not symmetric between ids 1-5 and ids 6-10:

| Habit | Code | Squad 1-5 | Squad 6-10 |
| --- | --- | --- | --- |
| Crouch in every fight | `actor_id % 3 == 0` | id 3 (one bot) | ids 6, 9 (two bots) |
| Throws smoke, attackers | `actor_id % 2 == 0` | ids 2, 4 | ids 6, 8, 10 |
| Unstick strafe direction | `actor_id % 2 == 0` | ids 2, 4 | ids 6, 8, 10 |
| Defender anchor | `(id - 6) % 5`, else `id % 5` | slot k gets anchor k+1 (wrapping) | slot k gets anchor k |
| Site pick without team comms (easy only) | `actor_id % 2` | three bots to site B, two to A | the reverse |

Fix: `SBBotAI.squad_index(actor)` = `(actor_id - 1) % 5`, the same 0-4 for both squads, used in those places. Uses of `% 5` (split flank, plant hold offsets, expensive buy) were already symmetric and are unchanged. `tick_order_test.gd` also asserts both squads have the same number of crouchers and smoke throwers.

## Measured effect

All sets: real engine, bots only, both start orders (actors 1-5 attacking first, then actors 6-10), `scripts/measure_relay_yard.sh --no-render --both-starts`. Share = rounds won by the squad of ids 1-5, whichever side it played. The interval resamples whole matches (4,000 resamples, fixed seed), because rounds inside a match are not independent. `scripts/squad_balance.py` computes it; "W-D-L" is the matches ids 1-5 won, drew and lost.

| Set | Code | Seeds | Difficulty | Matches | ids 1-5 won | Share (95% interval) | W-D-L |
| --- | --- | --- | --- | ---: | ---: | --- | --- |
| A | `db3981e`, stock | 41-46 | normal | 12 | 81 of 114 | 71.1% (62.1% to 80.8%) | 9-3-0 |
| A | | | hard | 12 | 76 of 123 | 61.8% (52.7% to 71.9%) | 8-2-2 |
| B | + shuffle | 41-46 | normal | 12 | 79 of 130 | 60.8% (54.7% to 68.9%) | 7-5-0 |
| B | | | hard | 12 | 74 of 122 | 60.7% (50.8% to 70.7%) | 7-4-1 |
| C | + squad-symmetric habits | 41-46 | normal | 12 | 67 of 140 | 47.9% (43.2% to 53.2%) | 3-3-6 |
| C | | | hard | 12 | 57 of 121 | 47.1% (35.7% to 59.5%) | 3-3-6 |
| D | same as C | 51-56 (fresh) | normal | 12 | 68 of 138 | 49.3% (43.7% to 54.3%) | 3-6-3 |
| D | | | hard | 12 | 65 of 115 | 56.5% (42.5% to 69.6%) | 7-2-3 |
| E | same as C | 61-84 (fresh) | normal | 48 | 262 of 517 | 50.7% (46.3% to 55.3%) | 17-14-17 |
| **C+D+E** | **final code** | | **normal** | **72** | **397 of 795** | **49.9% (46.8% to 53.1%)** | **23-23-26** |
| C+D+E | final code | | hard | 24 | 122 of 236 | 51.7% (42.6% to 60.9%) | 10-5-9 |

Differences, with the matches of both sets resampled independently (`data/diff-*.txt`, `data/squad-final-code-pooled-C-D-E.txt`):

| Comparison | All difficulties | Normal | Hard |
| --- | --- | --- | --- |
| B minus A (shuffle alone) | -5.5 points (-14.6 to +3.8) | -10.3 (-22.1 to +1.5) | -1.1 (-15.2 to +12.9) |
| C minus B (habits, on top) | -13.2 points (-21.8 to -4.5) | -12.9 (-22.4 to -4.7) | -13.5 (-29.0 to +3.0) |
| C+D+E minus A (both fixes) | -15.9 points (-23.8 to -8.6) | -21.1 (-31.5 to -11.8) | -10.1 (-23.5 to +3.1) |

Pacing is unchanged within noise, which is what a fairness fix should do (`data/pace-*.txt`):

| Set | Difficulty | Median live round | Plant rate | Attackers win | Median first kill |
| --- | --- | --- | ---: | ---: | --- |
| A | normal | 12.0 s | 9% | 26% | 1.6 s |
| C | normal | 11.6 s | 9% | 26% | 1.7 s |
| D | normal | 11.6 s | 10% | 21% | 1.7 s |
| E | normal | 11.9 s | 10% | 27% | 1.7 s |
| A | hard | 15.4 s | 2% | 21% | 0.4 s |
| C | hard | 13.0 s | 2% | 26% | 0.4 s |
| D | hard | 15.9 s | 3% | 38% | 0.5 s |

**Attacker win rate on the unchanged pad is about a quarter on normal** (21% to 27% in the three squad-symmetric sets). It is the first reading not confounded by the squad effect, and it says the open 48 m pad strongly favours defenders. The layout branch (`claude/relay-yard-tactical-layout-v1`) reported 59% and 67% attacker wins on its new layout; those numbers were confounded and need re-measuring on top of this fix.

## What this does and does not show

Supported by the numbers and the reviewer:

- The stock build has a clear squad effect: ids 1-5 won 66% of all rounds in A (interval 59% to 73%), and won 17 of 24 matches, drew 5 and lost 2.
- The shuffle alone is not enough. Its effect is not separable from the stock order at this sample size (B minus A is -5.5 points, interval -14.6 to +3.8), and the squad stays well above 50% (60.7%, interval 55.1% to 66.9%). Do not read set B as "the shuffle reduces it".
- Adding the symmetric habits is what moves the share: C minus B is -13.2 points (interval -21.8 to -4.5), and both fixes together are -15.9 points below stock (interval -23.8 to -8.6).
- On normal difficulty the final code gives 49.9% over 72 matches and 795 rounds, interval 46.8% to 53.1%: a residual squad effect of 5 points in either direction is excluded. The independent re-check of this pooled figure is in [independent-check.md](independent-check.md).

Not supported, and not claimed:

- Hard difficulty. 24 matches give an interval 18 points wide (42.6% to 60.9%). It is compatible with no effect and with a 10-point effect.
- "Exactly fair". The deterministic property, every pair first 50% of the time to within one point over 20,000 ticks, is what `tick_order_test.gd` proves. The bot numbers corroborate it; they cannot show a residual of a point or two.
- Set C on seeds 41-46 as a confirmation. Those seeds exposed the second cause (set B's residual sent me to read the bot code), so C was fitted by looking at them. Sets D and E, which use seeds nobody had looked at, are the confirmation.
- Any benefit or harm in networked play. The shuffle runs on the authority in every mode, but this session had no multi-client run.

Cautions on the metric:

- The share mixes squad with side exposure. Defenders win about three rounds in four on this pad, and matches end at seven round wins, so a squad that starts as attacker plays fewer defending rounds in a match it loses. Pooling both start orders cancels most of it; the by-start-order rows in `data/squad-*.txt` are not mirror images (the reviewer's simulation puts the artefact at about +-3 points) and should not be over-read.
- Seeds 41-46 are the seeds the layout work used for its "before" numbers.
- Sets D and E were added after set C's interval looked too wide to support a claim, which is a data-dependent decision to collect more. The size was fixed from the reviewer's power estimate (72 normal matches) before the new data existed, all sets are reported, and none was dropped. D and E on their own, which saw none of the diagnosis: normal 330 of 655 rounds, 50.4% (46.8% to 54.1%), 20 matches won, 20 drawn, 20 lost.
- Split by start order, the pooled final-code normal matches read 46.5% (ids 1-5 attacking first) and 53.5% (ids 6-10 attacking first). The reviewer's simulation of equal squads under first-to-7 produces about +-3 points, so the 7-point gap is at the edge of that artifact. Read it as the artifact, not as proof of one; it is the one number in this record that could hide a start-order effect.
- Set A is the archive `bots-before-both-starts-seeds41-46.tar.gz` of the layout evidence, regenerated here from the unchanged source files of `db3981e`.
- Which code each set ran: `data/source-states.txt` (hashes of the working-tree diff recorded at the start of each run, reproduced from the final commits).

The deeper fix is two-phase resolution: gather every actor's shot against the start-of-tick state, then apply damage, so a same-tick trade is a true trade (both die) rather than a coin flip. That changes the shared authority simulation and the lag-compensation contract, so it is a proposal for Codex, not part of this change.

## Reproduce

```sh
export SIGHTBREAK_TOOLS_DIR=/home/user/tools SIGHTBREAK_STATE_DIR=/home/user/sightbreak/.local
./scripts/setup.sh
./scripts/godot.sh --headless --script res://tests/tick_order_test.gd
scripts/measure_relay_yard.sh out/fair --no-render --both-starts --seeds "61 62 63 64" --difficulties "normal" --jobs 4
python3 scripts/squad_balance.py out/fair/bots --against path/to/stock/bots
```

To get set A, run the same measurement from a checkout of `db3981e` with the harness files from commit `a5ad1e9` copied in. The script always runs a route-exposure probe first (about ten minutes), then each match takes about two to three minutes on four vCPUs.

## Files

| Path | What it is |
| --- | --- |
| `data/bots-A-stock-order.tar.gz`, `bots-B-shuffle-only.tar.gz`, `bots-C-shuffle-and-symmetric-habits.tar.gz`, `bots-D-heldout-seeds51-56.tar.gz`, `bots-E-normal-seeds61-84.tar.gz` | Raw per-match logs: 24, 24, 24, 24 and 48 files |
| `data/squad-*.txt`, `data/squad-final-code-pooled-C-D-E.txt`, `data/diff-*.txt` | `scripts/squad_balance.py` output per set, pooled, and set-to-set differences |
| `data/pace-*.txt` | `scripts/summarize_bot_metrics.py` output per set |
| `data/tick-order-test-*.txt` | The regression test against the shuffle and against both broken orders |
| `data/source-states.txt` | The code state each set ran on, with reproducible hashes |
| `independent-check.md` | The reviewer's recomputation and critique |
| `sha256.txt` | Checksums of everything above |
