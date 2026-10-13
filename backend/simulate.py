"""Deterministic fictional economy scenarios, not player telemetry.
Run: python backend/simulate.py --players 5000 --days 30 --seed 2026
"""
import argparse
import json
import random
import statistics
from pathlib import Path
from collections import Counter

CFG=json.loads((Path(__file__).parent/'config/economy.json').read_text())
def simulate(count=5000,days=30,seed=2026):
    rng=random.Random(seed)
    players=[dict(credits=0,xp=0,items=[],matches=0,earned=0,hours=0) for _ in range(count)]
    rarity_supply=Counter(); issued=0; sinks=0; fees=0; opens=0; trade_volume=0; market_prices=[]; rejected=0; attempted=0; daily_balances=[]
    weights=list(CFG['rarities'].values()); rarity_names=list(CFG['rarities'])
    for day in range(days):
        for index,p in enumerate(players):
            farmer=index%50==0
            matches=24 if farmer else rng.randint(0,5)
            paid=0
            for m in range(matches):
                attempted+=1
                active=rng.random()>0.8 if farmer else rng.random()>0.02
                p['matches']+=1; p['hours']+=1/3
                if not active or paid>=CFG['daily_reward_match_cap']:
                    rejected+=1; continue
                won=rng.random()<0.5
                xp=CFG['xp_per_match']+CFG['xp_per_win']*won+CFG['xp_per_objective']*rng.randint(0,3)
                old_level=1+int((p['xp']/CFG['xp_level_base'])**0.5); p['xp']+=xp
                new_level=1+int((p['xp']/CFG['xp_level_base'])**0.5)
                earned=CFG['match_completion']+CFG['match_win']*won+(CFG['daily_first'] if paid==0 else 0)+CFG['level_reward']*(new_level-old_level)
                p['credits']+=earned; p['earned']+=earned; issued+=earned; paid+=1
                cost=CFG['case_price']+CFG['key_price']
                # Assumption: independent 50% purchase preference after each eligible match.
                if p['credits']>=cost and rng.random()<0.5:
                    p['credits']-=cost; sinks+=cost; opens+=1
                    rarity=rng.choices(rarity_names,weights=weights)[0]
                    p['items'].append(rarity); rarity_supply[rarity]+=1
        # Toy peer market: one attempted exchange per 10 players/day, prices are
        # exogenous synthetic asks, never presented as measured market behavior.
        for _ in range(count//10):
            seller,buyer=rng.sample(players,2)
            if not seller['items']: continue
            index=rng.randrange(len(seller['items'])); rarity=seller['items'][index]
            ask=rng.randint(80,300)*(1+rarity_names.index(rarity))
            if buyer['credits']<ask: continue
            fee=ask*CFG['market_fee_basis_points']//10000
            buyer['credits']-=ask; seller['credits']+=ask-fee; fees+=fee
            buyer['items'].append(seller['items'].pop(index)); trade_volume+=1; market_prices.append(ask)
        daily_balances.append(round(statistics.mean(p['credits'] for p in players),2))
    balances=[p['credits'] for p in players]; hours=sum(p['hours'] for p in players)
    assert sum(balances)==issued-sinks-fees
    assert sum(len(p['items']) for p in players)==opens
    assert min(balances)>=0
    return dict(seed=seed,players=count,days=days,config_version=CFG['version'],assumptions={'match_minutes':20,'legitimate_matches_per_day':'uniform integer 0–5','synthetic_farming_share':0.02,'case_purchase_probability':0.5,'market':'synthetic asks; no empirical demand or inflation claim'},matches_attempted=attempted,credits_issued=issued,case_key_sinks=sinks,market_fees=fees,credits_per_play_hour=round(issued/hours,2),average_balance=round(statistics.mean(balances),2),median_balance=statistics.median(balances),p95_balance=sorted(balances)[int(count*.95)],case_openings=opens,case_openings_per_player_day=round(opens/count/days,4),hours_per_case_at_average_income=round((CFG['case_price']+CFG['key_price'])/(issued/hours),3),rarity_supply=dict(rarity_supply),synthetic_market_volume=trade_volume,synthetic_market_median_price=statistics.median(market_prices) if market_prices else None,rejected_or_unrewarded_matches=rejected,suspected_farming_account_fraction=0.02,daily_average_balance=daily_balances,currency_conservation=True,item_conservation=True)
if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--players',type=int,default=5000); parser.add_argument('--days',type=int,default=30); parser.add_argument('--seed',type=int,default=2026); parser.add_argument('--output')
    args=parser.parse_args()
    if args.players<2 or args.days<1: parser.error('at least 2 players and 1 day required')
    result=json.dumps(simulate(args.players,args.days,args.seed),indent=2)
    if args.output: Path(args.output).write_text(result+'\n')
    print(result)
