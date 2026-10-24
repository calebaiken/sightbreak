# Claim verification, round 2 (claims C4 to C9), reports as received

Each report is from one fresh-context general-purpose Claude subagent, read-only, same model family as the author, asked to apply three lenses (re-derive from the code, robustness across seeds, hostile search for artifacts) to one finding as originally worded. They ran against the first harness version on the pre-two-phase base (`db3981e`); the findings they correct are about wording and conditions, and the weapon data and firing code are unchanged on the integrated stack. Round 1 (claims C1 to C3, all three lenses, and C4 re-derivation) is in `claim-verification-round1.json`. The reports below are verbatim.

## C4: moving spread

VERDICT: partly_supported. The spread numbers are right. The advance numbers are seed-7 highs, and the sentence invites a cause (spread) that is only half of it.

(1) RE-DERIVE
- current_spread = base + (speed/5.1)*0.026, with no per-weapon term. Walking is 0.029/0.035/0.028/0.027 (sidearm/smg/rifle/marksman). Standing is 0.003/0.009/0.002/0.001. Ratios are 9.7/3.9/14/27, so "4 to 27x" holds. The movement term is 74-96% of walking spread.
- I ported actor.gd (tick order, cooldown carry, vector recoil recovery, capsule and head ellipsoids, falloff) and the 28 m/s^2 velocity ramp to Python. Run against all 94 accuracy cells, it matches the pooled logs with no |z|>3 and no airborne term. That also argues against hidden airborne contamination in the harness.
- Rifle advance, one magazine, 20,000 trials per cell: 20 m 99.9%; 30 m 46.8% +-0.7; 45 m 18.2% +-0.5.

(2) ROBUSTNESS (200 trials per cell)
- 20 m: 200/199/200, i.e. 599/600, not strictly 100%.
- 30 m: 48.5/42.5/40.0%, pooled 43.7% (95% CI 39.8-47.7).
- 45 m: 20.5/15.0/18.0%, pooled 17.8% (CI 15-21).
- The seeds agree (chi-square p=0.21 and 0.36). "About 48%" and "20%" are the seed-7 values, the highest of the three. Best estimates are about 45% and 18%.

(3) HOSTILE: the collapse needs both walking spread and uncountered, accumulating recoil. Rifle kill rate at 30 m / 45 m:

| Condition | 30 m | 45 m |
|---|---|---|
| Walking, uncountered recoil (harness) | 47% | 18% |
| Walking, recoil countered | 100% | 97.5% |
| Walking, no recoil at all | 100% | 97.6% |
| Standing, uncountered recoil (hold mode) | 100% | 100% |
| Walking, uncountered, recoil x0.72 | 100% | 95% |
| Walking, uncountered, recoil x0.90 | 74% | 31% |

- The rifle is the only weapon whose recoil outruns recovery: +0.0044 rad per shot net. The SMG is -0.0004; the semi-autos clicked at their own rate are strongly negative.
- Walking spread alone gives about 25% hits per shot, so about 16 shots are needed, but the aim has climbed over the head by shot 8-10.
- The SMG has the largest walking spread (0.035) and still kills 93% at 30 m uncountered. The sidearm kills 96% and the marksman 100% at 30 m. Spread alone cannot explain the rifle result.

Problems with the wording:
1. "Moving spread dominates" followed by the rifle numbers reads as spread causing the collapse. It is spread times recoil, and it is rifle-specific.
2. "Dominates" is ambiguous. Airborne adds +0.045, which is larger than the movement term (0.026). It is only the largest part of walking spread.
3. "At 30 m" is the starting distance. The shooter closes on average 9 m (about 21 m remaining, or about 15 m if the magazine empties).
4. Unstated conditions: a stationary, non-firing, in-line target; perfect chest re-aim every tick; trigger held; recoil never pulled down (the "beginner" mode). The 100% at 20 m still has only 46% of shots landing.
5. Spread is the half-width of a uniform per-axis error (a square, not a cone). The 0.026 holds only at 5.1 m/s, and spread ramps up over the first 0.18 s.
6. "Within one magazine" is stated and correct. Extra rounds change little until point-blank (my model has no collision).

Not checked: Godot was not run. The RNG streams differ, so agreement with the logs is distributional, not exact.

CORRECTED: The movement term adds 0.026 rad at full walking speed (5.1 m/s, linear in speed) to every weapon, so walking spread is 0.027-0.035 rad against 0.001-0.009 standing (4-27x), a per-axis uniform half-width, and the movement term is 74-96% of it; airborne adds more (+0.045). Advancing on a stationary, non-firing target while holding the trigger with recoil never pulled down, the rifle killed 99.8% of 600 trials starting 20 m away, about 44% (40-48% across seeds) from 30 m, and about 18% (15-21%) from 45 m, within one 30-round magazine; this needs both the walking spread and the rifle's accumulating recoil: with recoil countered, or standing, the rifle kills about 100% at 30 m, and the SMG, with larger walking spread but no net recoil climb, kills 93%.

## C5: the sidearm damage steps

VERDICT: partly_supported. The four numbers are right for the distance the code uses. The sentence mixes two distance frames, "cliff" is the wrong word, and the logs only bracket the breakpoints.

1. RE-DERIVATION
- Damage per hit is 27*(1-0.45*d/45) = 27-0.27d. Here d is the distance from the eye (1.62 m) to where the ray enters the target's body capsule (actor.gd lines 745-746, 789-817). It is not measured to the capsule centre.
- Kill when n*(27-0.27d) >= 100, and health<=0 counts as dead. That gives d <= 7.407 (4 hits), 25.926 (5), 38.272 (6), 47.09 (7). Range stops shots at d<45 first, so 7 hits hold to the range limit.
- The harness "distance" is origin to origin. For chest-centre aim (1.1 m), d = (D-0.31)*sqrt(1+(0.52/D)^2), so d is about 0.3 m less than D. Breakpoints in D: 7.70, 26.23, 38.58, 45.31 m.
- At D=8: d=7.706, 24.919 per hit, 0.323 health left after 4 hits. Sidearm spread of +/-0.003 rad moves that by only 0.321-0.325. Over every possible body hit point at D=8 it is 0.31 (top rim) to 0.64 (edge graze), so 4 body hits never kill at 8 m. Using d=8 naively would give 0.64, not 0.3.

2. LOGS (seeds 7, 8, 9)
- Sidearm hold and comp cells are identical in all three seeds, hit rate 1.00 and kill rate 1.00 in 200 trials each. Median shots to kill: 4 at 5 m, 5 at 10 m, 5 at 20 m, 6 at 30 m, 7 at 45 m.
- Sidearm-vs-sidearm duels: median win time 0.933 s at 8 m (5 shots), 0.933 s at 20 m, 1.4 s at 40 m (7 shots). Shots land 14 ticks apart, so 4/5/6/7 shots take 0.70/0.93/1.17/1.40 s. There were no trades or unresolved duels.
- All of this agrees with my breakpoints, but it only brackets them: 7.4 is somewhere in (5, 8], 25.9 in (20, 30), 38.3 in (30, 40). No cell samples near a threshold.
- The "0.3 health" figure is not in the logs. The logs contain no DUEL_TRIAL lines, so it is analytic.

3. HOSTILE
- Frame mix: 7.4 m is shot length, but "8 m" is operator separation. In one frame, 8 m is only 0.3 m beyond the 4-hit limit (7.70), not 0.6 m.
- "Cliff" is unfair. Damage falls linearly and gently, 27 to 14.85 over 45 m. Across the 7.4 m threshold it changes from 25.002 to 24.999 per hit. What steps is hits-to-kill, by one 0.233 s interval each (+33%, +25%, +20% time to kill), which is a three-step staircase.
- "Four hits" must say body hits. Two head hits kill out to about d=43.9 m (the logs show 3 head hits at 45 m).
- "Seven out to 45 m" is the range limit, not a falloff step.
- The claim holds for a standing shooter and target with centred chest aim. Spread, rounding and standing vs crouching do not break it.

CORRECTED: The sidearm does 27 damage per body hit, falling smoothly by 0.27 per metre of shot length (eye to where the ray enters the body), to 14.85 at its 45 m range; the number of body hits needed to kill 100 health therefore steps from 4 to 5 beyond 7.41 m, to 6 beyond 25.93 m and to 7 beyond 38.27 m, each step adding one 0.233 s shot interval. Measured between operators' origins with chest-centre aim these steps fall at about 7.70, 26.23 and 38.58 m, and shots reach about 45.3 m. At 8 m apart, four chest hits leave the target on 0.32 health (0.31-0.64 for other body hit points).

## C6: headshots and time to kill

VERDICT: partly_supported. The rifle and marksman one-shot results are right. The closing "one-hit or two-hit" sentence is false by the harness's own logs, and the marksman was never tested at 100 m. I did not run Godot. I checked an independent Python port of the shot path (an earlier reviewer's sim.py) against every head cell in the logs, and it matches.

1. RE-DERIVED (damage x lerp(1, falloff, d/range) x head, 100 hp)
- Rifle: one headshot kills out to 45.9 m. At 45 m a hit does 100.45, a 0.45 hp margin. At 70 m a hit does 88.2, so two are needed.
- Marksman: 140 per headshot at 100 m, so one shot kills over the whole range. Only 5 to 70 m was run (DISTANCES tops out at 70).
- Sidearm: two headshots kill out to 43.9 m. At 45 m a hit does 49.0, so three are needed (logged: 3 shots, 0.467 s).
- SMG: two headshots kill out to 18.7 m. At 20 m a hit does 48.7 and at 30 m 39.0, so three are needed (logged: 3 shots at 20 m, median 6 shots at 30 m).
- Spread: the head is about 32 cm wide and 43 cm tall. I computed first-shot head probability by exact ray-ellipsoid integration:
  - Rifle, sidearm and marksman are 1.00 at 20, 30 and 45 m. Spread there is +-4/6/9 cm (rifle), +-6/9/14 cm (sidearm), +-2/3/4.5 cm (marksman).
  - The marksman is also 1.00 at 100 m (+-10 cm).
  - SMG (+-18/27 cm) is 0.845 at 20 m and 0.412 at 30 m. Logged: 0.834 pooled hit rate at 20 m; at 30 m 0.582 x 0.717 head share = 0.417.

2. ROBUSTNESS
- Every head cell killed in 600 of 600 trials (3 seeds x 200). The Wilson lower bound is 99.4%.
- The 100% cells are deterministic, because spread stays inside the head. The three seeds add nothing there.
- Hit rates below 100% by seed (7/8/9): SMG 20 m 0.819 / 0.855 / 0.830. SMG 30 m 0.572 / 0.583 / 0.591. Rifle 70 m 0.748 / 0.753 / 0.763. Pooled shot-level 95% intervals are roughly +-1.5 to 2 points.
- Medians hide the tails. SMG at 30 m has a mean of 0.48 s, p90 0.77 s and p99 1.1 s. It is slower than the chest-aim 0.60 s in 18% of trials.
- The rifle 70 m shortfall is a fixture artifact, not the weapon. The first shot hits the head 100% of the time. The harness counters only vertical recoil, and it leaves a 0.0018 rad residual because the recoil decays before the shot. Horizontal recoil of about 0.0026 rad puts shot 2 about 18 cm off the head. With full compensation the model needs 2 shots in 0.117 s, against 3 shots in 0.217 s in the harness. "Recoil countered" is therefore vertical only.

3. HOSTILE
- The 100% result needs very small aim error. Rifle at 45 m hits the head 100% within 5 cm sideways. It drops to 84% at 10 cm, 56% at 15 cm and 0% at 30 cm.
- A walking shooter (spread +0.026) lands the rifle's first shot in the head 38% of the time at 10 m, 9.5% at 20 m and 4% at 30 m.
- A crouching target breaks it. Crouch scales the hitbox instantly to 0.72, so the head sits at 0.98 to 1.29 m. A crosshair at 1.6 m misses everything, since the body top is also only 0.99 m.
- Kill time is counted from the first shot, so one-shot kills read 0.00 s and aim acquisition is excluded.
- The target is hitscan, so target movement matters only through the shooter's tracking.
- Chest-aim TTK is 0.21 to 1.4 s against 0 to 0.47 s for headshots, so the head multiplier is the big lever. The harness measures that conditional effect, not how often players land headshots. In its moving-shooter chest-aim runs, head share was 0 to 22%.

PROBLEMS WITH THE WORDING
- "Tested up to 100 m (marksman)" is false.
- "Every headshot kill is a one-hit or two-hit kill" is false for the SMG beyond 18.7 m and the sidearm beyond 43.9 m.
- The sidearm and SMG distances are not stated.
- The rifle's 45 m limit is a 45.9 m cliff, and nothing between 45 and 70 m was run.
- "Decide the time to kill" is conditional on landing the headshot.

CORRECTED: Against a stationary, standing target, with a stationary shooter aiming at the exact head centre and vertical recoil countered, one headshot kills with the rifle at 5 to 45 m (limit 45.9 m; 600 of 600 trials) and with the marksman at 5 to 70 m (to 100 m by calculation, not run). The sidearm needs two headshots (0.23 s) at 5 to 30 m (limit 43.9 m) and three at 45 m (0.47 s). The SMG needs two (0.10 s) at 5 to 10 m (limit 18.7 m) and three beyond, but spread puts only 84% of shots at 20 m and 41% at 30 m in the head (median 3 shots, 0.18 s at 20 m; 6 shots, 0.43 s at 30 m). Headshots shorten the kill by 0.2 to 1.2 s against chest hits, but the harness does not measure how often a moving player lands one.

## C7: the rifle's uncountered spray at long range

VERDICT: partly_supported. The 0.217 s vs 0.317 s numbers and the third-shot mechanism are correct. "Rewarded", "spray", "long range" and the comparator mislead.

1. RE-DERIVE. I wrote a Python replica of the cooldown, recoil, trace and falloff code. It reproduces the logs within noise: at 45 m hit rate 0.972 vs 0.960-0.968 and head share 0.347 vs 0.349-0.350; at 70 m kill rate 0.62 vs 0.565-0.645. Shots fire on ticks 0, 7, 13, 19. Recoil carried is 0, 0.0047, 0.0097, 0.0152 rad, and ray height is about 1.1 m + d x recoil. With zero spread:
- Shot 2 is never a head hit inside 70 m. With spread it is a head hit 4% of the time at 45 m and 23% at 70 m.
- Shot 3 is a head hit from 28.8 to 69.9 m.
- Shot 4 is a head hit from 19.9 to 33.0 m. Sideways recoil sway (x of -0.0047 rad) caps the band.
- At 45 m shot 1 lands at 1.100 m (body), shot 2 at 1.313 m (body), shot 3 at 1.538 m (head). Body damage is 28.74 and head damage is 100.53.

Kill distribution of the model, with the logged hold kill time first and comp second:
- 5 m, 10 m: 3 body shots, 0.217 s hold, 0.217 s comp.
- 20 m: 4 shots, 0.317 s hold, 0.317 s comp. Head share is 19% but changes nothing.
- 30 m: 61% on shot 3, 24% on shot 4, 15% on shot 5. The 0.217 s median hides a 0.217-0.417 s spread. Comp is 0.317 s.
- 45 m: 96% on shot 3, 4% on shot 2. Comp is 0.317 s.
- 70 m: 62% kill (shot 2 23%, shot 3 39%) and 38% never kill. Comp is 0.433 s at 100%.
Head mode is 0.0 s up to 45 m and 0.217 s at 70 m.

2. ROBUSTNESS. The 45 m hold cell is 0.217 s on all three seeds, with 200/200 kills. Head share is 0.350/0.350/0.349 and hit rate 0.960/0.965/0.968. The seeds only change the spread draws. Recoil is deterministic (the PROFILE lines are identical), so this is not independent replication.

The 100.4 worry does not apply to this row. Shots 1-2 already deal 57.5, so shot 3 needs only 42.5, and any head hit gives at least 88. The 100.53 figure matters only for the head row, where a one-shot kill holds to a target distance of 46.07 m, about 1 m beyond the cell.

The fragile inputs are geometric:
- Distance: P(kill by shot 3) is at least 94% from 35 to 55 m, 62% at 30 m, 14% at 25 m, 63% at 70 m.
- Aim height at 45 m: 0.9 m gives 26%, 1.0 m gives 81%, 1.1-1.2 m gives 100%.
- Spread: 0.004 gives 80%, 0.006 gives 53%, 0.010 gives 30%. Walking spread is 0.028.
- Shooter eye height: no effect (1.13 m and 1.62 m give identical results).

3. HOSTILE. This is the weapon combined with a fixture. The chest aim point at 1.1 m puts shot 3 almost at the window's centre, so 45 m is the best measured cell. The target never moves and the shooter is stationary, which is also a fixture condition. In the walking "advance" mode at 45 m, kill rate is 15-20%.

The comparator is a straw man. The comp shooter only hits the chest by construction. The harness's own head row kills in one shot (0.0 s) at 45 m, and at 70 m it ties hold at 0.217 s with a 100% kill rate where hold manages 57-65%. A player aiming at the head does not see the effect.

"Spray" is wrong. The kill comes at 0.21 s with 0.56 degrees of climb, and burst3 gives the same 0.217 s and 0.35 head share. A player who does not know the range gets the effect only by coincidence. There is none at 20 m or closer, and it is unreliable beyond 60 m.

Not checked: the real Godot RNG and engine, and crouched targets.

CORRECTED: With the shooter standing still (spread 0.002 rad), the trigger held, recoil not countered, and the aim fixed at chest height (1.1 m) on a stationary standing target, the rifle at 45 m kills in 0.217 s (3 shots, 200/200 trials on seeds 7, 8, 9). The 0.0097 rad of recoil carried by shot 3 lifts it from the chest into the head, after two chest hits. A shooter who counters recoil perfectly on the same chest aim needs 4 shots (0.317 s). A head aim kills in one shot (0.0 s) up to about 46 m, so this is a side effect of that aim point, not an advantage over aimed fire. It holds roughly from 32 to 60 m, is absent at 20 m or closer, and at 70 m 35-44% of magazines never kill.

## C8 and C9: cadence quantisation and harness symmetry

C8: partly_supported (quantisation supported; "automatics within 0.1%" not supported)

- Cause is the game code, not the harness.
  - `_fire` carries a remainder only when `_fire_previous` is true. A semi-auto shot needs `_fire_previous` false (rising edge), so carry is always 0 for it.
  - The cooldown therefore restarts at the full interval. Ready after ceil(0.23*60)=14 ticks and ceil(0.82*60)=50 ticks.
  - The harness cadence is not binding: 14 and 50 are even, and it clicks on even ticks.
  - I ported the cooldown logic to Python. It reproduces all four logged intervals and seconds_to_empty (196, 148, 183, 350 ticks). A "greedy" clicker that presses on every possible tick gets the same 14 and 50.
  - So no player gets 0.23 s. The floor is 0.2333 s (+1.45%) and 0.8333 s (+1.63%). The code comments suggest this is intended ("every burst starts from the same phase"), so it is a design property, not a bug.
- Automatics fail "within 0.1%".

| Weapon | Printed vs data | Unrounded (29 intervals) |
|---|---|---|
| SMG | 0.0851 vs 0.085 = +0.12% | 0.085057 = +0.07% |
| Rifle | 0.1052 vs 0.105 = +0.19% | 0.105172 = +0.16% |

  - The rifle exceeds 0.1% either way, and the SMG does only if unrounded.
  - The excess is the one-tick endpoint rounding of a 29-interval window (up to 0.68% SMG, 0.55% rifle). It is not a rate error.
  - Simulated sustained fire is +0.02% (SMG) and +0.05% (rifle) at 100 shots, and +0.002% and +0.005% at 1000.
  - Seeds 7, 8 and 9 give identical PROFILE values. The cadence is deterministic, so that is one measurement, not three replicates.

C9: partly_supported (the shuffle is unbiased; the wording and the inference are not)

- Cells. There are 36 same-weapon cells.
  - 3 are SMG 40 m (all seeds): 0 wins, 0 wins, 300 unresolved, because SMG range is 35 m. They are not duels, and the Wilson interval [0, 1.3%] excludes 50%.
  - Of the other 33, 32 contain 50%. One does not: seed 9 marksman 8 m, 168/300 = 56.0%, [50.3, 61.5], exact p = 0.043.
  - The chance miss rate per cell is 5.66% (exact, for Wilson at n=300). Expected misses over 33 cells are 1.87, and P(at least one) is 85%. The one miss is unremarkable, but "in all of them" is false.
  - Pooled, the row (blue) side won 4,943 of 9,900 = 49.9% [48.9, 50.9], z = -0.14. Chi-square across cells is 24.2 on 33 cells.
- Most of the 50/50 is one coin flip.
  - In 30 of the 33 cells both actors reach the lethal shot on the same tick: marksman 50, sidearm 56/84, rifle 13 (8 and 40 m), SMG 26/31. The winner is whoever is processed first on that tick, which is the parity of the order RNG's draw at that tick.
  - I reimplemented PCG32 and the djb2 salt. It reproduces `a_wins` exactly in all 30 logged cells (for example 168, 159, 143).
  - So these cells test only the order RNG. They cannot detect any other asymmetry: blue always team 0 at z=0 and red team 1 at z=-d, ids 100+ vs 200+, spread-seed offsets (a gets even seeds, b odd), or geometry. Only rifle 20 m (3 cells, 445/900) has random kill timing.
  - With a fixed order these cells would be 100/0. The order decides every duel, and the shuffle makes that fair. "Does not favour a side" holds only in that sense.
- Other gaps.
  - Cross-weapon pairs run only with the lower-indexed weapon as blue (`index_b` starts at `index_a`). The table's lower triangle is a transpose, so side-swapped duels were never run.
  - Per-cell resolution is about +-5.7 pp.
  - The harness comment says the match shuffles order. I found no shuffle in game/scripts; `match.gd:276` loops `actors.values()`. So the harness shows nothing about the game's tick-order fairness.
- Not checked. I could not run Godot. The PCG32 and hash port is mine, though its exact match to 30 cells supports it. I did not check the engine's hit geometry or `is_on_floor` on the first tick.

CORRECTED C8: Semi-automatic fire is rounded up to whole 60 Hz ticks by the game's cooldown code, because the sub-tick carry only applies to a held trigger and a semi-auto shot always starts on a rising edge: the sidearm cannot fire faster than 14 ticks (0.2333 s vs 0.23 s data, +1.4%) nor the marksman faster than 50 ticks (0.8333 s vs 0.82 s, +1.6%), however fast the player clicks. Automatics, which do carry, measure 0.0851 s (SMG, +0.1%) and 0.1052 s (rifle, +0.2%) over a 30-round magazine, the excess being one-tick endpoint rounding that shrinks in longer strings.

CORRECTED C9: In 33 of the 36 same-weapon duel cells (the three SMG 40 m cells are out of range and unresolved), the row weapon's 95% Wilson interval contains 50% in 32 (the exception is seed 9 marksman 8 m, 56.0%, about 1.9 misses being expected by chance), and pooled over 9,900 duels blue won 49.9% [48.9, 50.9]. In 30 of those cells the winner is simply whoever the per-tick shuffle processes first on the shared lethal tick, so the result shows the shuffle is unbiased and tests nothing else about the harness.
