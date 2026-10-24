# Gunplay measurements on the v1 stack

What the four weapons do in the real authority code, measured, with every statement checked by fresh-context reviewers. This is a **fixture** record: a bare floor, one operator that does not move or shoot back (except in duels), no armour. It measures weapons, not players, and says nothing about how the weapons feel.

| Item | Value |
| --- | --- |
| Piece | Weapon rules as the authority applies them: cadence, recoil, spread, falloff, headshots, reload and draw, kill time, duels |
| Bar | B3, the previous verified build, for regressions. B2b (partial, secondary, unverified Counter-Strike 2 figures from search summaries, see `docs/roadmap/BARS.md` on the mission branch) for regime checks only. No parity claim. |
| Source | Codex v1 stack `codex/v1-mission-playability` at `ad6cdc2` plus the harness commits of this branch. Weapon data and the firing code are unchanged from `db3981e` except that a tick is now resolved in phases. |
| Code state measured | Harness commit `c0c43bc` (`git diff` of the working tree at run start equals that commit) |
| Runs | Seeds 7, 8, 9; 200 trials per accuracy cell, 300 duels per ordered pair and distance. `data/gunplay-seed*.log`, 180 measurements each. Same seed gives byte-identical output. |
| Checkers | Fifteen fresh-context subagent reviews of the first harness version and wording (`data/claim-verification-*`), plus one review of the harness code against the game code. Same model family as the author: arithmetic and logic checks, not human acceptance. |
| Not covered | Human play and feel, networked play, moving or crouching targets, armour, grenades, any other map |

## How a tick resolves (changes the duel results)

The v1 stack resolves a tick in phases (`TacticalMatch._authority_tick`): every actor moves, every actor acts with its hits queued, then the queued hits land. Two operators who can both kill on the same tick therefore **trade**. The first run of this harness (on the older base, in `claude/gunplay-metrics-v1`) processed one actor's whole tick at a time and had to shuffle the order to break ties, so same-weapon duels came out as 50/50 coin flips. They are now trades, and the shuffle is gone. The duel table below uses the two-phase tick through `tick_authority_movement`, `tick_authority_actions` and `resolve_shot_hit`; `--resolution=sequential` keeps the older model for comparison.

## Findings

Each finding is the wording that survived verification. "Standing" means the shooter and target are still; "chest aim" is 1.1 m above the feet; "countered" means the shooter pulls the view down by exactly the recoil carried, on both axes.

**F-G1. The rifle beats every other weapon in a chest-aim duel at 8, 20 and 40 m.** Both operators stand still at full health with no armour and open fire on the same tick, aimed at the chest, recoil not countered. The Relay AR beat the sidearm, the SMG and the marksman in 900 of 900 duels per pair and distance (3 seeds x 300), from either seat, with no trade and none unresolved. The result is fixed by time to kill, not chance: the rifle's slowest kill (tick 13 at 8 and 40 m, tick 19 or 26 at 20 m) comes before every opponent's fastest (SMG tick 26 at 8 m and 31 at 20 m, marksman tick 50, sidearm tick 56 at 8 and 20 m and 84 at 40 m). The thinnest margin is 5 ticks (0.083 s) against the SMG at 20 m. The 40 m SMG cell is a walkover: the SMG's range is 35 m. At 40 m, and in most 20 m duels, the rifle's kill shot is a headshot lifted from the chest by uncountered recoil.

Measured order of the weapons, chest aim: at 8 and 20 m rifle > SMG > marksman > sidearm (900 of 900 for each pair); at 40 m rifle > marksman > sidearm > SMG, because the SMG cannot reach. Equal weapons trade: sidearm, marksman and (at 8 and 40 m) rifle duels end with both dead in 900 of 900; the rifle at 20 m splits 202 / 187 / 511 (row wins / column wins / trade). That symmetry across seats is the harness's check on itself.

**F-G2. Only the rifle carries appreciable climbing recoil into its shots.** From zero recoil, one magazine, trigger held (semi-automatics clicked at their own rate), the recoil carried by a shot is exactly 0 rad on every sidearm and marksman shot; the SMG carries 0 on shots 1 to 3 and then a residue of up to 0.0032 rad (0.18 degrees) on shot 30; the rifle carries 0.131 rad on shot 30 and its view peaks at 0.147 rad (8.4 degrees), under the 0.16 rad cap. Recovery is 0.11 rad/s along the length of the (yaw, pitch) recoil vector, above the nominal build-up of the sidearm (0.052 rad/s) and marksman (0.055), only 4% above the SMG's (0.106), and below the rifle's (0.152). Recoil is not reset by a weapon swap: a sidearm drawn straight after a rifle spray carries about 0.11 rad on its first shot.

**F-G3. The marksman needs two body hits at every distance, and always kills 0.83 s after the first shot.** For a stationary shooter on a standing target: two body hits at each of 5, 10, 20, 30, 45, 70 and 100 m (600 of 600 trials in every one of those cells, identical on all seeds), the second shot 50 ticks (0.833 s; the data say 0.82 s) after the first. The rifle kills the same target in 0.217 s with three body hits up to about 12 m and in 0.317 s with four hits from there to its 70 m range (recoil countered; uncountered, 0.217 s at 5, 10, 30 and 45 m, with a recoil-lifted headshot at 30 and 45 m, and 0.317 s at 20 m). So on body hits the marksman is slower than the rifle at every range, while costing more (3200 against 2400). That ordering reverses for a walking shooter at 30 m and beyond, where the rifle's uncountered recoil makes it kill in only 44% of magazines at 30 m and 18% at 45 m while the marksman still kills 97 to 100% (F-G5). With headshots the two tie: both kill in one shot up to 45.9 m (F-G6).

**F-G4. The sidearm's body hits-to-kill steps with distance.** The sidearm does 27 damage per body hit, falling smoothly by 0.27 per metre of shot length (eye to where the ray enters the body) to 14.85 at its 45 m range. The number of body hits needed to kill 100 health therefore steps from 4 to 5 beyond 7.41 m, to 6 beyond 25.93 m and to 7 beyond 38.27 m, each step adding one 0.233 s shot interval. Measured between the operators' origins, with chest-centre aim, the steps fall at about 7.70, 26.23 and 38.58 m, and shots reach about 45.3 m. At 8 m apart four chest hits leave the target on 0.32 health (0.31 to 0.64 for other body hit points): a player who lands four hits at 8 m and does not kill will notice. The word "cliff" was rejected by the reviewers: damage itself falls gently; what steps is the hit count.

**F-G5. Moving accuracy: walking spread is large for every weapon, but only the rifle collapses, because of its recoil.** The movement term adds 0.026 rad at full walking speed (5.1 m/s, linear in speed) to every weapon, so walking spread is 0.027 to 0.035 rad against 0.001 to 0.009 standing (4 to 27 times), a per-axis uniform half-width; airborne adds a further 0.045. Advancing on a stationary target with the trigger held and the view re-aimed at the chest every tick, within one magazine:

| Kill rate, 600 trials per cell | 20 m | 30 m | 45 m |
| --- | ---: | ---: | ---: |
| Rifle, recoil not countered | 99.8% | 43.8% | 17.8% |
| Rifle, recoil countered | 100% | 100% | 99.0% |
| SMG (largest walking spread, 0.035), not countered | 100% | 93.3% | out of range |
| Sidearm, not countered | 100% | 95.8% | 30.7% |
| Marksman, not countered | 100% | 100% | 97.3% |

So the collapse needs both the walking spread and the rifle's accumulating recoil, and it is rifle-specific. Starting distance is the table's distance; the shooter closes about 9 m on average during the magazine.

**F-G6. Headshots decide the time to kill, when they land.** Aimed at the head centre, standing target, recoil countered, one magazine: the rifle kills with one shot at 5 to 45 m (limit 45.9 m; 600 of 600 per cell) and in 0.117 s median at 70 m (88% of shots hit; two needed); the marksman with one shot at 5 to 100 m (600 of 600 per cell); the sidearm with two shots (0.233 s) at 5 to 30 m (limit 43.9 m) and three at 45 m (0.467 s); the SMG with two shots (0.10 s) at 5 to 10 m (limit 18.7 m) and three beyond, but its spread puts only 84% of shots at 20 m and 58% at 30 m on the head (median 0.18 s at 20 m, p90 0.35 s; median 0.43 s at 30 m, p90 0.77 s). The fixture's aim is exact and the target does not move: a walking shooter lands the rifle's first shot on the head 38% of the time at 10 m and 4% at 30 m, and a crouching target moves its head to 0.98 to 1.29 m (the harness does not test that). The measurement is therefore the conditional effect of the head multiplier (chest-aim kill times of 0.21 to 1.4 s against 0 to 0.47 s), not how often a player lands a headshot.

**F-G7. Uncountered rifle fire is not penalised at medium range, because the recoil climb carries shots through the head.** Standing, trigger held, aimed at the chest of a standing target, recoil not countered: at 45 m the rifle kills in 0.217 s (3 shots, 600 of 600 trials); a shooter who counters the recoil perfectly on the same chest aim needs four shots (0.317 s). The 0.0097 rad of recoil carried by shot 3 lifts it from the chest into the head after two chest hits. A head aim kills in one shot up to 45.9 m, so this is a side effect of the chest aim point, not an advantage over aimed fire. It is absent at 20 m or closer, holds roughly from 32 to 60 m, and at 70 m only 60% of uncountered magazines kill at all.

**F-G8. Semi-automatic cadence is rounded up to whole ticks.** The game's cooldown carries a sub-tick remainder only for a held trigger, and a semi-automatic shot always starts on a rising edge, so the sidearm cannot fire faster than 14 ticks (0.2333 s against 0.23 s of data, +1.4%) nor the marksman faster than 50 ticks (0.8333 s against 0.82 s, +1.6%), however fast the player clicks. Automatics carry the remainder and measure 0.0851 s (SMG, +0.1%) and 0.1052 s (rifle, +0.2%) over a 30-round magazine, the excess being one-tick endpoint rounding that shrinks in longer strings. Reload and draw read up to two ticks (0.033 s) above their data (reload 1.48, 1.88, 2.28 and 2.83 s; draw 0.317 s for every weapon against 0.30 s).

## What the reviewers changed

The first drafts of the claims were all returned "partly supported" by the three-lens reviewers (15 of 15 completed reviews). The changes that mattered: "only the rifle" recoil was wrong for the SMG (a small climbing residue); "moving spread dominates" blamed spread for a collapse that needs recoil as well (the SMG has the larger walking spread and kills 93%); "cliff" was wrong for a smooth falloff; the marksman claim was body-hit only and was never measured at 100 m; "every headshot kill is a one- or two-hit kill" was false for the SMG beyond 18.7 m and the sidearm beyond 43.9 m; the same-weapon duel cells mostly tested the harness's own order shuffle; "recoil countered" had removed only the vertical component. All of these are fixed in the harness or the wording above. Reports: `data/claim-verification-round1.json`, `data/claim-verification-round2.md`.

## Limits

- **Fixture, not play.** A still target, exact aim, no armour, no reaction time, no movement except F-G5. Nothing here is a feel claim, a balance verdict or a statement about how often anything happens in a match.
- **Seeds.** Three seeds agree closely (largest spread in any accuracy cell: kill rate 0.080, rifle at 70 m held; in any duel cell: 0.037, `data/seed-stability.txt`), but recoil and cadence are deterministic, so for those the seeds are not independent replicates.
- **Duels** are a same-tick start of two operators in a vacuum. A rifle start more than four ticks (0.067 s) late no longer wins every duel against the SMG at 20 m.
- **Distances** are between operators' origins, chest aim at 1.1 m; shot length is about 0.3 m shorter.
- **Same model family** as the author did the checking.

## Observations for the design owner (no verdicts)

These follow from the numbers; choosing among them needs people playing, which has not happened.

1. The marksman has no unique role on a 48 m map. The rifle also one-shots a headshot out to 45.9 m, and a body hit kills slower with the marksman at every range. A marksman that one-shots the body (damage of 100 or more), or armour that stops the rifle's headshot kill, would give it one.
2. With no armour, every rifle or marksman headshot is a one-shot kill. Whether that is intended is a design question.
3. Recoil is only a mechanic for the rifle. The SMG, sidearm and marksman have effectively none to learn.
4. The sidearm's four-hit kill lasts only to 7.4 m of shot length.
5. Same-tick mutual kills are real under the two-phase tick; equal weapons trade every time at close range.

## Reproduce

```sh
export SIGHTBREAK_TOOLS_DIR=/home/user/tools SIGHTBREAK_STATE_DIR=/home/user/sightbreak/.local
./scripts/setup.sh && ./scripts/godot.sh --headless --editor --import --quit
timeout 3000 ./scripts/godot.sh --headless --script res://tests/gunplay_metrics.gd -- --trials=200 --duels=300 --seed=7 > seed7.log
python3 scripts/summarize_gunplay.py seed7.log                         # the tables
python3 scripts/summarize_gunplay.py seed7.log --stability seed8.log seed9.log
```

A full seed takes about eight minutes on four vCPUs.

## Files

| Path | What it is |
| --- | --- |
| `data/gunplay-seed7.log`, `gunplay-seed8.log`, `gunplay-seed9.log` | Raw harness output, 180 measurements each |
| `data/tables-seed7.md` | Every table, rendered from seed 7 |
| `data/seed-stability.txt` | Largest seed-to-seed spread per kind of cell |
| `data/claim-verification-round1.json`, `claim-verification-round2.md` | The reviewers' reports |
| `sha256.txt` | Checksums |
