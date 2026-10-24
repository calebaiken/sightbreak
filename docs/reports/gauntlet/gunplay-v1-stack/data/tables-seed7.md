### Data and what it implies (analytic, from weapons.gd; 100 health, no armour)

A dash means the shot does not reach that far. Shots to kill use the damage after falloff at that distance.

| Weapon | Cost | Damage | Head x | Interval | Rounds/min | Damage/s | Body shots to kill at 0 / 20 / 40 m | Time to kill, body, 0 m | One-shot headshot up to | Magazine | Reload |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- | ---: | ---: |
| sidearm | 0 | 27 | 3.3 | 0.230 s | 261 | 117 | 4 / 5 / 7 | 0.69 s | never | 15 | 1.45 s |
| smg | 1100 | 22 | 3.1 | 0.085 s | 706 | 259 | 5 / 7 / - | 0.34 s | never | 30 | 1.85 s |
| rifle | 2400 | 35 | 3.5 | 0.105 s | 571 | 333 | 3 / 4 / 4 | 0.21 s | 45.9 m | 30 | 2.25 s |
| marksman | 3200 | 74 | 2.2 | 0.820 s | 73 | 90 | 2 / 2 / 2 | 0.82 s | 100.0 m | 8 | 2.80 s |

### Cadence and recoil, one magazine held down from rest (measured)

Recoil at fire is what the shot itself carries (the climb from earlier shots, before this shot's own kick). Recoil after the shot is the view kick the player sees.

| Weapon | Interval data | Interval measured | Seconds to empty | Peak view climb | Recoil carried by shots 1-6 (rad) | Carried by the last shot | Time to clear after release |
| --- | ---: | ---: | ---: | ---: | --- | ---: | ---: |
| sidearm | 0.230 s | 0.2333 s | 3.27 s | 0.012 rad (0.7 deg) | 0.000, 0.000, 0.000, 0.000, 0.000, 0.000 | 0.000 rad | 0.13 s |
| smg | 0.085 s | 0.0851 s | 2.47 s | 0.012 rad (0.7 deg) | 0.000, 0.000, 0.000, 0.001, 0.001, 0.001 | 0.003 rad | 0.12 s |
| rifle | 0.105 s | 0.1052 s | 3.05 s | 0.147 rad (8.4 deg) | 0.000, 0.005, 0.010, 0.015, 0.018, 0.024 | 0.131 rad | 1.35 s |
| marksman | 0.820 s | 0.8333 s | 5.83 s | 0.045 rad (2.6 deg) | 0.000, 0.000, 0.000, 0.000, 0.000, 0.000 | 0.000 rad | 0.47 s |

### Spread, radians and centimetres of scatter at 20 m (each axis, uniform +-)

| Weapon | Standing | Crouched | Walking | Airborne |
| --- | ---: | ---: | ---: | ---: |
| sidearm | 0.0030 (6 cm) | 0.0018 (4 cm) | 0.0290 (58 cm) | 0.0480 (96 cm) |
| smg | 0.0090 (18 cm) | 0.0054 (11 cm) | 0.0350 (70 cm) | 0.0540 (108 cm) |
| rifle | 0.0020 (4 cm) | 0.0012 (2 cm) | 0.0280 (56 cm) | 0.0470 (94 cm) |
| marksman | 0.0010 (2 cm) | 0.0006 (1 cm) | 0.0270 (54 cm) | 0.0460 (92 cm) |

### Reload and draw (measured in 60 Hz ticks)

Measured values include the tick that requests the action and the tick that completes it, so they read up to two ticks (0.033 s) above the data.

| Weapon | Reload data | Reload measured | Draw data | Draw measured |
| --- | ---: | ---: | ---: | ---: |
| sidearm | 1.45 s | 1.483 s (89 ticks) | 0.30 s | 0.317 s (19 ticks) |
| smg | 1.85 s | 1.883 s (113 ticks) | 0.30 s | 0.317 s (19 ticks) |
| rifle | 2.25 s | 2.283 s (137 ticks) | 0.30 s | 0.317 s (19 ticks) |
| marksman | 2.80 s | 2.833 s (170 ticks) | 0.30 s | 0.317 s (19 ticks) |

### Standing target, aimed at the chest, trigger held, recoil not countered (semi-auto: clicked at its own rate) (200 trials per cell)

Each cell: hit rate of fired shots / share of trials that killed within one magazine (95% Wilson interval) / median (and 90th percentile) seconds from first shot to kill, over the trials that killed. Cells where fewer than 30 trials killed show the count, because the median then describes only the lucky trials.

| Weapon | 5 m | 10 m | 20 m | 30 m | 45 m | 70 m | 100 m |
| --- | --- | --- | --- | --- | --- | --- | --- |
| sidearm | 100% / 100% (98%-100%) / 0.70 s (p90 0.70) | 100% / 100% (98%-100%) / 0.93 s (p90 0.93) | 100% / 100% (98%-100%) / 0.93 s (p90 0.93) | 100% / 100% (98%-100%) / 1.17 s (p90 1.17) | 100% / 100% (98%-100%) / 1.40 s (p90 1.40) | beyond range | beyond range |
| smg | 100% / 100% (98%-100%) / 0.35 s (p90 0.35) | 100% / 100% (98%-100%) / 0.43 s (p90 0.43) | 100% / 100% (98%-100%) / 0.52 s (p90 0.52) | 98% / 100% (98%-100%) / 0.60 s (p90 0.68) | beyond range | beyond range | beyond range |
| rifle | 100% / 100% (98%-100%) / 0.22 s (p90 0.22) | 100% / 100% (98%-100%) / 0.22 s (p90 0.22) | 95% / 100% (98%-100%) / 0.32 s (p90 0.43) | 95% / 100% (98%-100%) / 0.22 s (p90 0.43) | 96% / 100% (98%-100%) / 0.22 s (p90 0.22) | 16% / 64% (58%-71%) / 0.22 s (p90 0.22) | beyond range |
| marksman | 100% / 100% (98%-100%) / 0.83 s (p90 0.83) | 100% / 100% (98%-100%) / 0.83 s (p90 0.83) | 100% / 100% (98%-100%) / 0.83 s (p90 0.83) | 100% / 100% (98%-100%) / 0.83 s (p90 0.83) | 100% / 100% (98%-100%) / 0.83 s (p90 0.83) | 100% / 100% (98%-100%) / 0.83 s (p90 0.83) | 100% / 100% (98%-100%) / 0.83 s (p90 0.83) |

### Standing target, aimed at the chest, trigger held, the shooter pulls down by exactly the recoil carried (the weapon's ceiling under perfect spray control) (200 trials per cell)

Each cell: hit rate of fired shots / share of trials that killed within one magazine (95% Wilson interval) / median (and 90th percentile) seconds from first shot to kill, over the trials that killed. Cells where fewer than 30 trials killed show the count, because the median then describes only the lucky trials.

| Weapon | 5 m | 10 m | 20 m | 30 m | 45 m | 70 m | 100 m |
| --- | --- | --- | --- | --- | --- | --- | --- |
| sidearm | 100% / 100% (98%-100%) / 0.70 s (p90 0.70) | 100% / 100% (98%-100%) / 0.93 s (p90 0.93) | 100% / 100% (98%-100%) / 0.93 s (p90 0.93) | 100% / 100% (98%-100%) / 1.17 s (p90 1.17) | 100% / 100% (98%-100%) / 1.40 s (p90 1.40) | beyond range | beyond range |
| smg | 100% / 100% (98%-100%) / 0.35 s (p90 0.35) | 100% / 100% (98%-100%) / 0.43 s (p90 0.43) | 100% / 100% (98%-100%) / 0.52 s (p90 0.52) | 100% / 100% (98%-100%) / 0.60 s (p90 0.60) | beyond range | beyond range | beyond range |
| rifle | 100% / 100% (98%-100%) / 0.22 s (p90 0.22) | 100% / 100% (98%-100%) / 0.22 s (p90 0.22) | 100% / 100% (98%-100%) / 0.32 s (p90 0.32) | 100% / 100% (98%-100%) / 0.32 s (p90 0.32) | 100% / 100% (98%-100%) / 0.32 s (p90 0.32) | 100% / 100% (98%-100%) / 0.32 s (p90 0.32) | beyond range |
| marksman | 100% / 100% (98%-100%) / 0.83 s (p90 0.83) | 100% / 100% (98%-100%) / 0.83 s (p90 0.83) | 100% / 100% (98%-100%) / 0.83 s (p90 0.83) | 100% / 100% (98%-100%) / 0.83 s (p90 0.83) | 100% / 100% (98%-100%) / 0.83 s (p90 0.83) | 100% / 100% (98%-100%) / 0.83 s (p90 0.83) | 100% / 100% (98%-100%) / 0.83 s (p90 0.83) |

### Standing target, aimed at the centre of the head, recoil countered (every kill here is a headshot kill) (200 trials per cell)

Each cell: hit rate of fired shots / share of trials that killed within one magazine (95% Wilson interval) / median (and 90th percentile) seconds from first shot to kill, over the trials that killed. Cells where fewer than 30 trials killed show the count, because the median then describes only the lucky trials.

| Weapon | 5 m | 10 m | 20 m | 30 m | 45 m | 70 m | 100 m |
| --- | --- | --- | --- | --- | --- | --- | --- |
| sidearm | 100% / 100% (98%-100%) / 0.23 s (p90 0.23) | 100% / 100% (98%-100%) / 0.23 s (p90 0.23) | 100% / 100% (98%-100%) / 0.23 s (p90 0.23) | 100% / 100% (98%-100%) / 0.23 s (p90 0.23) | 100% / 100% (98%-100%) / 0.47 s (p90 0.47) | beyond range | beyond range |
| smg | 100% / 100% (98%-100%) / 0.10 s (p90 0.10) | 100% / 100% (98%-100%) / 0.10 s (p90 0.10) | 82% / 100% (98%-100%) / 0.18 s (p90 0.35) | 56% / 100% (98%-100%) / 0.43 s (p90 0.77) | beyond range | beyond range | beyond range |
| rifle | 100% / 100% (98%-100%) / 0.00 s (p90 0.00) | 100% / 100% (98%-100%) / 0.00 s (p90 0.00) | 100% / 100% (98%-100%) / 0.00 s (p90 0.00) | 100% / 100% (98%-100%) / 0.00 s (p90 0.00) | 100% / 100% (98%-100%) / 0.00 s (p90 0.00) | 88% / 100% (98%-100%) / 0.12 s (p90 0.22) | beyond range |
| marksman | 100% / 100% (98%-100%) / 0.00 s (p90 0.00) | 100% / 100% (98%-100%) / 0.00 s (p90 0.00) | 100% / 100% (98%-100%) / 0.00 s (p90 0.00) | 100% / 100% (98%-100%) / 0.00 s (p90 0.00) | 100% / 100% (98%-100%) / 0.00 s (p90 0.00) | 100% / 100% (98%-100%) / 0.00 s (p90 0.00) | 100% / 100% (98%-100%) / 0.00 s (p90 0.00) |

### Standing target, aimed at the chest, three-round bursts, 0.3 s apart (200 trials per cell)

Each cell: hit rate of fired shots / share of trials that killed within one magazine (95% Wilson interval) / median (and 90th percentile) seconds from first shot to kill, over the trials that killed. Cells where fewer than 30 trials killed show the count, because the median then describes only the lucky trials.

| Weapon | 5 m | 10 m | 20 m | 30 m | 45 m | 70 m | 100 m |
| --- | --- | --- | --- | --- | --- | --- | --- |
| sidearm | not run (semi-automatic) | not run (semi-automatic) | not run (semi-automatic) | not run (semi-automatic) | not run (semi-automatic) | not run (semi-automatic) | not run (semi-automatic) |
| smg | 100% / 100% (98%-100%) / 0.62 s (p90 0.62) | 100% / 100% (98%-100%) / 0.70 s (p90 0.70) | 100% / 100% (98%-100%) / 1.03 s (p90 1.03) | 100% / 100% (98%-100%) / 1.13 s (p90 1.13) | beyond range | beyond range | beyond range |
| rifle | 100% / 100% (98%-100%) / 0.22 s (p90 0.22) | 100% / 100% (98%-100%) / 0.22 s (p90 0.22) | 100% / 100% (98%-100%) / 0.55 s (p90 0.55) | 100% / 100% (98%-100%) / 0.22 s (p90 0.55) | 97% / 100% (98%-100%) / 0.22 s (p90 0.22) | 71% / 100% (98%-100%) / 0.22 s (p90 1.10) | beyond range |
| marksman | not run (semi-automatic) | not run (semi-automatic) | not run (semi-automatic) | not run (semi-automatic) | not run (semi-automatic) | not run (semi-automatic) | not run (semi-automatic) |

### Standing target, aimed at the chest, trigger held while walking at the target, re-aimed every tick, recoil not countered (200 trials per cell)

Each cell: hit rate of fired shots / share of trials that killed within one magazine (95% Wilson interval) / median (and 90th percentile) seconds from first shot to kill, over the trials that killed. Cells where fewer than 30 trials killed show the count, because the median then describes only the lucky trials.

| Weapon | 5 m | 10 m | 20 m | 30 m | 45 m | 70 m | 100 m |
| --- | --- | --- | --- | --- | --- | --- | --- |
| sidearm | 100% / 100% (98%-100%) / 0.70 s (p90 0.70) | 100% / 100% (98%-100%) / 0.93 s (p90 0.93) | 67% / 100% (98%-100%) / 1.40 s (p90 1.87) | 45% / 96% (92%-98%) / 2.10 s (p90 2.80) | 27% / 34% (28%-41%) / 2.80 s (p90 3.27) | beyond range | beyond range |
| smg | 100% / 100% (98%-100%) / 0.35 s (p90 0.35) | 96% / 100% (98%-100%) / 0.43 s (p90 0.52) | 50% / 100% (98%-100%) / 0.85 s (p90 1.28) | 30% / 93% (89%-96%) / 1.70 s (p90 2.13) | beyond range | beyond range | beyond range |
| rifle | 100% / 100% (98%-100%) / 0.22 s (p90 0.22) | 98% / 100% (98%-100%) / 0.22 s (p90 0.22) | 46% / 100% (98%-100%) / 0.53 s (p90 1.27) | 12% / 48% (42%-55%) / 0.43 s (p90 0.95) | 7% / 20% (15%-27%) / 0.63 s (p90 0.85) | 5% / 8% (5%-12%) / 0.32 s (p90 0.63) (n=15) | beyond range |
| marksman | 100% / 100% (98%-100%) / 0.83 s (p90 0.83) | 100% / 100% (98%-100%) / 0.83 s (p90 0.83) | 86% / 100% (98%-100%) / 0.83 s (p90 1.67) | 63% / 100% (98%-100%) / 1.67 s (p90 3.33) | 42% / 98% (94%-99%) / 3.33 s (p90 5.00) | 25% / 60% (53%-66%) / 3.33 s (p90 5.83) | 15% / 22% (16%-28%) / 3.33 s (p90 5.83) |

### Standing target, aimed at the chest, trigger held while walking at the target, re-aimed every tick, recoil countered exactly (200 trials per cell)

Each cell: hit rate of fired shots / share of trials that killed within one magazine (95% Wilson interval) / median (and 90th percentile) seconds from first shot to kill, over the trials that killed. Cells where fewer than 30 trials killed show the count, because the median then describes only the lucky trials.

| Weapon | 5 m | 10 m | 20 m | 30 m | 45 m | 70 m | 100 m |
| --- | --- | --- | --- | --- | --- | --- | --- |
| sidearm | 100% / 100% (98%-100%) / 0.70 s (p90 0.70) | 100% / 100% (98%-100%) / 0.93 s (p90 0.93) | 66% / 100% (98%-100%) / 1.40 s (p90 1.87) | 45% / 96% (92%-98%) / 2.10 s (p90 2.80) | 26% / 36% (29%-42%) / 2.57 s (p90 3.27) | beyond range | beyond range |
| smg | 100% / 100% (98%-100%) / 0.35 s (p90 0.35) | 97% / 100% (98%-100%) / 0.43 s (p90 0.52) | 51% / 100% (98%-100%) / 0.85 s (p90 1.37) | 31% / 96% (93%-98%) / 1.70 s (p90 2.22) | beyond range | beyond range | beyond range |
| rifle | 100% / 100% (98%-100%) / 0.22 s (p90 0.22) | 100% / 100% (98%-100%) / 0.22 s (p90 0.22) | 63% / 100% (98%-100%) / 0.53 s (p90 0.85) | 44% / 100% (98%-100%) / 0.75 s (p90 1.27) | 25% / 99% (96%-100%) / 1.37 s (p90 2.42) | 11% / 48% (41%-54%) / 2.22 s (p90 2.85) | beyond range |
| marksman | 100% / 100% (98%-100%) / 0.83 s (p90 0.83) | 100% / 100% (98%-100%) / 0.83 s (p90 0.83) | 82% / 100% (98%-100%) / 0.83 s (p90 1.67) | 64% / 100% (98%-100%) / 1.67 s (p90 3.33) | 45% / 97% (94%-99%) / 2.50 s (p90 5.00) | 24% / 56% (50%-63%) / 3.33 s (p90 5.83) | 16% / 24% (19%-30%) / 3.33 s (p90 5.00) |

### Duels at 8 m: both fire on the same tick at the other's chest (300 duels per ordered pair, resolution two_phase)

Hits are queued until every actor has acted, as in the match, so a same-tick mutual kill is a trade. Each cell: row weapon (blue, team 0) wins / column weapon (red, team 1) wins / both dead / neither dead after the magazines. Every ordered pair is run, so the two seat orders of a pair should mirror each other. A trade is the whole outcome when the two kill on the same tick. The 95% Wilson interval of the row weapon's wins is in brackets.

| Row vs column | sidearm | smg | rifle | marksman |
| --- | --- | --- | --- | --- |
| sidearm | 0% / 0% / 100% / 0% [0%-1%] | 0% / 100% / 0% / 0% [0%-1%] | 0% / 100% / 0% / 0% [0%-1%] | 0% / 100% / 0% / 0% [0%-1%] |
| smg | 100% / 0% / 0% / 0% [99%-100%] | 0% / 0% / 100% / 0% [0%-1%] | 0% / 100% / 0% / 0% [0%-1%] | 100% / 0% / 0% / 0% [99%-100%] |
| rifle | 100% / 0% / 0% / 0% [99%-100%] | 100% / 0% / 0% / 0% [99%-100%] | 0% / 0% / 100% / 0% [0%-1%] | 100% / 0% / 0% / 0% [99%-100%] |
| marksman | 100% / 0% / 0% / 0% [99%-100%] | 0% / 100% / 0% / 0% [0%-1%] | 0% / 100% / 0% / 0% [0%-1%] | 0% / 0% / 100% / 0% [0%-1%] |

### Duels at 20 m: both fire on the same tick at the other's chest (300 duels per ordered pair, resolution two_phase)

Hits are queued until every actor has acted, as in the match, so a same-tick mutual kill is a trade. Each cell: row weapon (blue, team 0) wins / column weapon (red, team 1) wins / both dead / neither dead after the magazines. Every ordered pair is run, so the two seat orders of a pair should mirror each other. A trade is the whole outcome when the two kill on the same tick. The 95% Wilson interval of the row weapon's wins is in brackets.

| Row vs column | sidearm | smg | rifle | marksman |
| --- | --- | --- | --- | --- |
| sidearm | 0% / 0% / 100% / 0% [0%-1%] | 0% / 100% / 0% / 0% [0%-1%] | 0% / 100% / 0% / 0% [0%-1%] | 0% / 100% / 0% / 0% [0%-1%] |
| smg | 100% / 0% / 0% / 0% [99%-100%] | 0% / 0% / 100% / 0% [0%-1%] | 0% / 100% / 0% / 0% [0%-1%] | 100% / 0% / 0% / 0% [99%-100%] |
| rifle | 100% / 0% / 0% / 0% [99%-100%] | 100% / 0% / 0% / 0% [99%-100%] | 23% / 20% / 57% / 0% [19%-28%] | 100% / 0% / 0% / 0% [99%-100%] |
| marksman | 100% / 0% / 0% / 0% [99%-100%] | 0% / 100% / 0% / 0% [0%-1%] | 0% / 100% / 0% / 0% [0%-1%] | 0% / 0% / 100% / 0% [0%-1%] |

### Duels at 40 m: both fire on the same tick at the other's chest (300 duels per ordered pair, resolution two_phase)

Hits are queued until every actor has acted, as in the match, so a same-tick mutual kill is a trade. Each cell: row weapon (blue, team 0) wins / column weapon (red, team 1) wins / both dead / neither dead after the magazines. Every ordered pair is run, so the two seat orders of a pair should mirror each other. A trade is the whole outcome when the two kill on the same tick. The 95% Wilson interval of the row weapon's wins is in brackets.

| Row vs column | sidearm | smg | rifle | marksman |
| --- | --- | --- | --- | --- |
| sidearm | 0% / 0% / 100% / 0% [0%-1%] | 100% / 0% / 0% / 0% [99%-100%] | 0% / 100% / 0% / 0% [0%-1%] | 0% / 100% / 0% / 0% [0%-1%] |
| smg | 0% / 100% / 0% / 0% [0%-1%] | 0% / 0% / 0% / 100% [0%-1%] | 0% / 100% / 0% / 0% [0%-1%] | 0% / 100% / 0% / 0% [0%-1%] |
| rifle | 100% / 0% / 0% / 0% [99%-100%] | 100% / 0% / 0% / 0% [99%-100%] | 0% / 0% / 100% / 0% [0%-1%] | 100% / 0% / 0% / 0% [99%-100%] |
| marksman | 100% / 0% / 0% / 0% [99%-100%] | 100% / 0% / 0% / 0% [99%-100%] | 0% / 100% / 0% / 0% [0%-1%] | 0% / 0% / 100% / 0% [0%-1%] |
