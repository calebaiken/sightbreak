# G22 qualification: does the two-phase tick treat the two bot squads alike?

An independent measurement of the Codex v1 stack (`codex/v1-mission-playability`), whose two-phase tick resolves same-tick mutual kills as trades. Question: with ten identical bots, does the squad with ids 1-5 win about half the rounds? Before the fix it won about two thirds.

| Item | Value |
| --- | --- |
| Piece | Squad fairness of all-bot offline matches under the v1 stack's tick |
| Bar | B6 in `docs/roadmap/BARS.md` (own measurement; the target is a share compatible with 50%) |
| Source under test | `ad6cdc20` (stack tip when the run started) plus the tools commit `6153bf32` (measurement harness only; no game file differs from the stack) |
| Runs | 120 matches: normal and hard, seeds 41-46 and 61-84, each seed once with ids 1-5 attacking first and once with ids 6-10 (`--swap-start`). Command: `./scripts/godot.sh --headless --script res://tests/bot_objective_metrics.gd -- --difficulty=D --seed=S [--swap-start]` |
| Comparators | Before: 24 matches (normal and hard, seeds 41-46, both starts) on the stack before the two-phase tick. Reverse order: 8 normal matches with the old processing order reversed |
| Raw data | `data/after`, `data/before`, `data/reverse-order` (full logs, renamed `.log.txt` because `*.log` is ignored), hashes in `sha256.txt` |
| Checker | A fresh-context subagent parsed the raw lines with its own code (`data/independent-review/`), bootstrapped by match, and only then compared with `scripts/squad_balance.py`. Same model family as the author |
| Not covered | Humans, networked play, easy bots, other maps, other time scales |

## Result

Share of rounds won by the squad with ids 1-5 (95% interval from 10,000 match-level bootstrap draws; rounds within a match are not independent).

| Set | Matches | Rounds | Won | Share | 95% interval | Matches W-D-L |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| After, normal | 60 | 660 | 324 | 49.1% | 45.4 to 52.8 | 24-9-27 |
| After, hard | 60 | 624 | 327 | 52.4% | 47.8 to 57.0 | 25-14-21 |
| **After, all** | **120** | **1284** | **651** | **50.7%** | **47.8 to 53.6** | 49-23-48 |
| Before, normal | 12 | 114 | 81 | 71.1% | 62.2 to 80.8 | 9-3-0 |
| Before, hard | 12 | 123 | 76 | 61.8% | 52.7 to 71.9 | 8-2-2 |
| **Before, all** | **24** | **237** | **157** | **66.2%** | **59.5 to 73.5** | 17-5-2 |
| Reverse order, normal | 8 | 87 | 40 | 46.0% | 36.4 to 56.5 | 2-2-4 |

Before minus after: +15.5 points (95% interval +8.1 to +23.2). The author's script and the reviewer's independent parser agree on every count, share and W-D-L; interval ends differ by at most 0.2 points (different resampling seed and draw count).

## What the data support

- After the fix, the squad with ids 1-5 wins 50.7% of rounds, an interval that contains 50%. The advantage before the fix followed the squad: ids 1-5 won 64.5% of rounds attacking first and 68.1% defending first.
- Equivalence within plus or minus 5 points holds. Within plus or minus 3 does not (interval half-width about 2.9 points). Telling 0.7 points from zero would need about 2,000 matches.
- Log integrity: all 152 logs are complete (one `match_over` line, rounds 1 to n, scores sum to rounds, ended at 7 wins or round 12, longest run 857 s). Squad ownership of each round was derived three ways (round number with the halftime rule, the attacker `carrier` id, the final score line) and agrees in every log. One round (hard-61, round 4) has no carrier and cannot be cross-checked; defenders won it.

## A side effect worth knowing

The squad that attacks first wins only 47.0% of rounds (interval 44.2 to 49.9) in the after runs, which is why the unswapped normal runs show ids 1-5 at 44%. It is not a squad bias: attackers win only 25.5% of rounds in these bot matches and a match ends at 7 round wins, and a simulation of a perfectly fair game with those two features gives 47.5% for the side that attacks first. The paired start (60 matches each way) cancels it. Whether attackers winning one round in four is acceptable is a map-balance question; the layout work in PR #26 addresses route exposure but this record does not measure its effect on win rate.

## Limits

- Bots only, offline, normal and hard difficulty, time scale 4. `--swap-start` re-runs `_begin_round`, an artificial initial condition.
- The comparators are small (24 and 8 matches) and the commit of the "before" runs is not recorded in the logs (they lack the `reverse_order` key, so an older harness build). The before and after runs may differ in more than the tick fix.
- Seeds 47-60 are not part of the run plan; every match that was run is included, none was dropped.
- On the six seeds shared with the comparator the after share is 56.1% (48.6 to 64.2, 24 matches) against 49.4% on the 96 new-seed matches; the pooled 50.7% depends on the new seeds. This is within sampling noise but is stated because the intervals are wide.
- Hard has a design effect of about 1.4, so a plain binomial interval would be too narrow there.
- The reversed-order comparator gave 46.0%, not the roughly 34% a mirror image would predict; with 8 matches it cannot say whether order alone caused the before-fix bias.
- Same model family as the author checked the numbers.

## Reproduce

```
scripts/measure_relay_yard.sh OUT --seeds "41 42 43 44 45 46 61 ... 84" --difficulties "normal hard" --no-render --both-starts
python3 scripts/squad_balance.py OUT/bots
```

`scripts/squad_balance.py` attributes a round to a squad by round index (first six rounds before halftime) and the swap flag, then bootstraps by match.
