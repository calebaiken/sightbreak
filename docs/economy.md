# Earned-only economy baseline

Settings live in `backend/config/economy.json`. Starting inventory and Credits are empty. Temporary round-buy cash is separate. Offline matches never mint online Credits/items. There are no real-money conversions, cashouts, purchases or external-market connectors.

A verified completed online match pays 100 Credits, a win 75 extra, and the first eligible daily match 150 extra. A level gained pays 250. Level is `1 + floor(sqrt(XP / 1000))`; XP is 200 per eligible match, 100 for a win, and 25 per validated objective contribution. A case costs 350 and a key 150. These are provisional tuning values. The current implementation pays match/daily-first/level rewards; daily/weekly challenge and achievement rewards remain unimplemented.

Case odds are exactly Common 58%, Uncommon 26%, Rare 11%, Epic 4%, Legendary 0.9%, Mythic 0.1%, version 1. The catalog discloses them before opening. Cases and keys are consumed atomically with the awarded item. The initial four collections each have six original finish definitions. No item supplies a combat advantage. Marketplace sellers receive ask minus a 3% integer-floor transaction fee. This provisional fee is configurable; no listing fee exists.

Run `python backend/simulate.py --players 5000 --days 30 --seed 2026 --output backend/config/simulation-baseline.json`. The committed baseline is deterministic fictional modeling, not measurements from actual players. It includes currency creation, case/key sinks, synthetic player exchanges and fees, rarity supply, progression and low-activity farming attempts. Account behavior and market asks are explicit assumptions in the output.

| Baseline metric | Result |
| --- | ---: |
| Hypothetical players / days | 5,000 / 30 |
| Attempted matches | 439,627 |
| Credits generated | 75,455,000 |
| Case/key sinks | 71,718,500 |
| Marketplace fee sinks | 77,524 |
| Credits per simulated play hour | 514.90 |
| Mean / median final balance | 731.80 / 563.50 |
| 95th percentile final balance | 1,976 |
| Openings | 143,437 |
| Openings/player/day | 0.9562 |
| Hours to earn case+key at mean income | 0.971 |
| Synthetic trades / median ask | 10,720 / 224 |
| Unrewarded/blocked match attempts | 64,872 |

Supply: 83,145 Common; 37,559 Uncommon; 15,579 Rare; 5,716 Epic; 1,285 Legendary; 153 Mythic. Seeded simulation selection deliberately uses a reproducible RNG; live case rewards use the OS cryptographic RNG. Assertions verify `all balances = issued − case/key sinks − fees`, total items equal openings, and no negative balances.

Mean balances rise from 329.73 on day one to about 700–740 in the latter half under these assumptions. Synthetic asks do not measure inflation: genuine supply/demand, retention and liquidity need live tests. Unlimited cosmetic accumulation remains a supply risk even when Credits stabilize; no claim of long-term equilibrium is justified. With the current model a new player can afford a 500-Credit opening after roughly two matches if at least one is a win, or three completed losses including first-play bonus. High-level XP rewards become less frequent with the quadratic curve; keep tracking income by tenure rather than treating aggregate means as fairness evidence.

The twelve paid matches/day cap, 75% participation floor, duplicate/overlap rejection and requirement for ten authenticated humans reduce simple AFK/bot farming. They do not prevent human collusion, multi-account farms, malicious server operators or spoofed activity if a trusted server is compromised. Challenges, account-age checks and independent fraud telemetry should be evaluated before opening tradable progression to public servers. Avoid rewarding excessive play or adding manipulative scarcity; adjust costs and optional sinks based on player study and monitored supply, not conversion pressure.


The account-bound path uses a short-lived, single-use server join ticket consumed over the trusted API before admission. Guest or bot sessions remain unranked and cannot earn tradable value. Live trusted results remain subject to the full ten-human, duration, activity, uniqueness and daily reward checks. A separate PostgreSQL bridge fixture is available for synthetic game-adapter testing; it never populates live wallets.

Collected rifle skins can now be equipped through the authoritative persistent `/loadout` API. The backend validates ownership and compatibility, and marketplace/trade transfers atomically clear the previous owner's slot. This connects collection to cosmetic presentation only; no economic item modifies combat statistics.
