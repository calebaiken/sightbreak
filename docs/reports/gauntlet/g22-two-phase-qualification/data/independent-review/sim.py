import random
rng=random.Random(1)
def share(p, N=400000):
    w=n=0
    for _ in range(N):
        a=b=0  # a = first-attacker squad
        for r in range(1,13):
            att_first = r<=6
            att_won = rng.random()<p
            if att_won==att_first: a+=1
            else: b+=1
            if max(a,b)>=7: break
        w+=a; n+=a+b
    return w/n
for p in (0.255,0.30,0.5):
    print(p, round(100*share(p),2))
