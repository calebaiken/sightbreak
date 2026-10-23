#!/usr/bin/env python3
"""Recompute frozen M4 raw records. This script never launches the engine."""
import argparse
from collections import Counter
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[4]
MEASURED = "49ae54b0e4f5d880bdf06e4eb783a616b2dff684"
STEP = 1 / 60
errors = []
checks = 0


def check(ok, label):
    global checks
    checks += 1
    if not ok:
        errors.append(label)


def close(a, b, tolerance=1e-5):
    return math.isfinite(a) and math.isfinite(b) and abs(a - b) <= tolerance


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args])


def source(commit, path):
    return git("show", f"{commit}:{path}")


def distance(a, b):
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def vector(text):
    return [float(x) for x in text.strip("()").split(",")]


def ceil(fraction):
    return -(-fraction.numerator // fraction.denominator)


def schedule(spec):
    interval = Fraction(spec["interval_text"])
    if not spec["automatic"]:
        return list(range(0, 1800, 2 * ceil(interval * 30)))
    return [at for i in range(1800) if (at := ceil(i * interval * 60)) < 1800]


def positive_roots(a, b, c):
    discriminant = b*b - 4*a*c
    if a <= 0 or discriminant < 0:
        return []
    return [t for t in [(-b - math.sqrt(discriminant))/(2*a), (-b + math.sqrt(discriminant))/(2*a)] if t >= 0]


def contact(origin, direction, actor_position):
    # Independent boundary intersections with the stock 0.31-radius, 1.8-high
    # capsule clipped at local y=1.38, plus the two stock head ellipsoids.
    o = [a-b for a, b in zip(origin, actor_position)]
    d = direction
    body = []
    for t in positive_roots(d[0]**2+d[2]**2, 2*(o[0]*d[0]+o[2]*d[2]), o[0]**2+o[2]**2-.31**2):
        if .31 <= o[1]+d[1]*t <= 1.38:
            body.append(t)
    for center_y, lower in [(.31, True), (1.49, False)]:
        shifted = [o[0], o[1]-center_y, o[2]]
        for t in positive_roots(sum(x*x for x in d), 2*sum(a*b for a, b in zip(shifted, d)), sum(x*x for x in shifted)-.31**2):
            y = o[1]+d[1]*t
            if y <= 1.38 and ((y <= .31) if lower else (y >= 1.49)):
                body.append(t)
    if abs(d[1]) > 1e-15:
        t = (1.38-o[1])/d[1]
        if t >= 0 and (o[0]+d[0]*t)**2+(o[2]+d[2]*t)**2 <= .31**2:
            body.append(t)
    head = []
    for center, radii in [([0, 1.56, 0], [.16, .195, .165]), ([0, 1.68, .005], [.175, .1175, .18])]:
        q = [(a-b)/r for a, b, r in zip(o, center, radii)]
        v = [x/r for x, r in zip(d, radii)]
        head += positive_roots(sum(x*x for x in v), 2*sum(a*b for a, b in zip(q, v)), sum(x*x for x in q)-1)
    candidates = [(t, False) for t in body] + [(t, True) for t in head]
    return min(candidates) if candidates else (math.inf, False)


def main(raw, output):
    lines = raw.read_text().splitlines()
    rows = [json.loads(line[13:]) for line in lines if line.startswith("GUNPLAY_CASE ")]
    source_rows = [json.loads(line[15:]) for line in lines if line.startswith("GUNPLAY_SOURCE ")]
    summaries = [json.loads(line[14:]) for line in lines if line.startswith("GUNPLAY_RULES ")]
    check(summaries == [{"checks":2840,"failures":[]}], "actual probe summary")
    check(len(source_rows) == 1 and source_rows[0]["physics_hz"] == 60 and source_rows[0]["engine"] == "4.7.2-stable (official)", "actual probe engine and 60 Hz source record")
    specs = {}
    weapon_text = source(MEASURED,"game/scripts/gameplay/weapons.gd").decode()
    for weapon, text in re.findall(r'^\s*"(sidearm|smg|rifle|marksman)": \{(.*)\}', weapon_text, re.M):
        spec = {k:float(re.search(rf'"{k}": ([0-9.]+)',text)[1]) for k in ["interval","reload","magazine","reserve","damage","head","range","falloff"]}
        spec["interval_text"] = re.search(r'"interval": ([0-9.]+)', text)[1]
        spec["automatic"] = '"automatic": true' in text
        specs[weapon] = spec
    key = lambda r:(r["weapon"],r["kind"],r.get("scenario",r.get("control","")))
    expected_keys = {(w,k,"") for w in specs for k in ["cadence","held_finite_magazine","partial_reload","reload_switch","switch_cycle"]} | {(w,"damage",s) for w in specs for s in ["body","head","lethal_body"]} | {(w,"negative",c) for w in specs for c in ["miss","friendly","dry","reload","deploy"]}
    check(len(rows)==52 and set(map(key,rows))==expected_keys and all(n==1 for n in Counter(map(key,rows)).values()), "all 52 unique cases, no missing/extra keys")
    records = {key(r):r for r in rows}
    results = {}
    for weapon,spec in specs.items():
        get = lambda kind,detail="":records[(weapon,kind,detail)]
        row = get("cadence"); expected = schedule(spec)
        check(row["shot_ticks"]==expected and row["remaining_ammo"]==10000-len(expected), f"{weapon}: every cadence tick and consumed round")
        check(row["ticks"]==1800 and row["expected_count"]==len(expected) and row["expected_last_tick"]==expected[-1], f"{weapon}: complete measurement window/count/final")
        gaps=[(b-a)*STEP for a,b in zip(expected,expected[1:])]
        phase=max(abs(t*STEP-i*spec["interval"]) for i,t in enumerate(expected)) if spec["automatic"] else 0
        check(close(row["minimum_gap"],min(gaps)) and close(row["maximum_gap"],max(gaps)) and close(row["maximum_phase_error"],phase) and phase <= STEP+1e-6, f"{weapon}: recomputed cadence gaps/phase")
        finite=get("held_finite_magazine"); emitted=int(spec["magazine"]) if spec["automatic"] else 1
        check((finite["shots"],finite["ammo"],finite["reserve"])==(emitted,int(spec["magazine"])-emitted,0), f"{weapon}: held finite magazine")
        reload=get("partial_reload"); timeline=reload["timeline"]; completed=reload["completion_ticks_after_start"]
        check(len(timeline)==completed+1 and [s["tick"] for s in timeline]==list(range(completed+1)), f"{weapon}: complete reload tick series")
        check(spec["reload"] <= completed*STEP+1e-6 <= spec["reload"]+STEP+2e-6, f"{weapon}: bounded reload duration")
        remaining=spec["reload"]
        for i,s in enumerate(timeline):
            if i: remaining=max(0,remaining-STEP)
            transferred=3 if i==completed else 0
            check(s["ammo"]==int(spec["magazine"])-5+transferred and s["reserve"]==3-transferred and s["ammo"]+s["reserve"]==int(spec["magazine"])-2 and close(s["remaining"],remaining,1e-12), f"{weapon}: reload conservation/timer/transfer tick {i}")
            check(s["weapon"]==weapon and s["watched_ammo"]==s["ammo"] and s["watched_reserve"]==s["reserve"] and s["shot_count"]==0, f"{weapon}: reload sample authority tick {i}")
        check(remaining==0 and (reload["ammo"],reload["reserve"])==(int(spec["magazine"])-2,0), f"{weapon}: exact partial reserve result")
        cancel=get("reload_switch"); timeline=cancel["timeline"]; half=int(spec["reload"]/STEP*.5); switch=completed+half; alternate="rifle" if weapon=="sidearm" else "sidearm"
        check(cancel["switch_tick"]==switch and cancel["alternate"]==alternate and cancel["initial_shots"]==0, f"{weapon}: cancel schedule/alternate")
        stages=["restarted"]+["before_cancel"]*half+["switch_action"]+["deploy"]*39+["returned"]+["after_return"]*240
        check([s["stage"] for s in timeline]==stages and [s["tick"] for s in timeline]==list(range(completed,completed+len(stages))), f"{weapon}: full cancel/deploy/return timeline")
        relative_shots=[18,26,34] if alternate=="rifle" else [18,32]
        shot_ticks=[switch+t for t in relative_shots]
        check(cancel["shot_ticks"]==shot_ticks and cancel["deploy_ticks"]==18, f"{weapon}: actual alternate shot ticks/deploy")
        remaining=spec["reload"]
        for i,s in enumerate(timeline):
            shot_count=sum(t<s["tick"] for t in shot_ticks)
            check((s["watched_ammo"],s["watched_reserve"],s["shot_count"])==(int(spec["magazine"])-5,7,shot_count),f"{weapon}: cancelled ammo and shot count tick {s['tick']}")
            if s["stage"] in ["restarted","before_cancel"]:
                if i: remaining=max(0,remaining-STEP)
                current=weapon; expected_ammo=int(spec["magazine"])-5; expected_reserve=7; deploy=0
            elif s["stage"] in ["switch_action","deploy"]:
                remaining=0; current=alternate; expected_ammo=int(specs[alternate]["magazine"])-shot_count; expected_reserve=int(specs[alternate]["reserve"]); deploy=max(0,.3-(s["tick"]-switch-1)*STEP)
            else:
                remaining=0; current=weapon; expected_ammo=int(spec["magazine"])-5; expected_reserve=7; deploy=max(0,.3-(s["tick"]-(switch+41))*STEP)
            check(s["weapon"]==current and s["ammo"]==expected_ammo and s["reserve"]==expected_reserve and close(s["remaining"],remaining,1e-12) and close(s["deploy_remaining"],deploy,1e-12),f"{weapon}: actual cancel/deploy ammo/timers tick {s['tick']}")
        cycle=get("switch_cycle"); expected_gap=51 if weapon=="marksman" else 21
        check(cycle["shot_gap_ticks"]==expected_gap and cycle["shot_gap_ticks"]*STEP>=spec["interval"] and cycle["return_switch_tick"]==2 and cycle["deploy_seconds"]==.3, f"{weapon}: reported switch gap matches sampled timing")
        damage_results=[]
        for scenario in ["body","head","lethal_body"]:
            row=get("damage",scenario); origin=row["ray_origin"]; direction=row["ray_direction"]; impact=row["impact_position"]
            victim=row["target_before"]; health=5 if scenario=="lethal_body" else 100; head=scenario=="head"
            actual_distance=distance(origin,impact); t,classified_head=contact(origin,direction,vector(victim["position"]))
            check(close(distance(direction,[0,0,0]),1,2e-7) and close(actual_distance,row["distance"]) and close(t,actual_distance) and classified_head==head, f"{weapon}/{scenario}: independent actual ray distance/body/head geometry")
            check(distance([o+d*t for o,d in zip(origin,direction)],impact)<1e-5,f"{weapon}/{scenario}: impact lies on emitted ray at front volume")
            amount=spec["damage"]*(1+(spec["falloff"]-1)*actual_distance/spec["range"])*(spec["head"] if head else 1)
            lost=min(health,amount); after_health=max(0,health-amount); lethal=after_health==0
            check(victim["health"]==health and victim["alive"] and close(row["applied_damage"],lost) and close(row["expected_damage"],amount) and close(row["target_after"]["health"],after_health) and row["target_after"]["alive"]==(not lethal), f"{weapon}/{scenario}: actual stock damage/health/alive")
            check(row["damage_recipients"]==[2] and row["head"]==head and row["confirmation"]=={"head":head,"lethal":lethal}, f"{weapon}/{scenario}: intended actual confirmation")
            check(row["feedback_initial"]=={"head":head,"lethal":lethal,"remaining":.18} and row["feedback_after_remaining"]==0 and row["authority_after_visual_matches"] is True, f"{weapon}/{scenario}: actual feedback startup/expiry and reported noninterference")
            check(row["shooter_before"]["ammo"]==spec["magazine"] and row["shooter_after"]["ammo"]==spec["magazine"]-1 and row["shooter_before"]["reserve"]==row["shooter_after"]["reserve"]==spec["reserve"], f"{weapon}/{scenario}: actual shot ammunition")
            for k in victim:
                if k not in ["health","alive"]: check(victim[k]==row["target_after"][k],f"{weapon}/{scenario}: victim {k} preserved")
            for k in row["shooter_before"]:
                if k not in ["ammo","recoil"]: check(row["shooter_before"][k]==row["shooter_after"][k],f"{weapon}/{scenario}: shooter {k} preserved")
            damage_results.append({"scenario":scenario,"distance":actual_distance,"damage":lost,"health_after":after_health,"head":head,"lethal":lethal})
        for control in ["miss","friendly","dry","reload","deploy"]:
            row=get("negative",control); fired=control in ["miss","friendly"]
            check(row["damage_events"]==row["confirmations"]==0 and row["shots"]==int(fired) and row["ammo"]==row["ammo_before"]-int(fired),f"{weapon}/{control}: negative shot/ammo/confirmation")
            if control=="friendly":
                c=row["friendly_contact"]; front,head=contact(c["ray_origin"],c["ray_direction"],[0,.01,-2]); rear,_=contact(c["ray_origin"],c["ray_direction"],[0,.01,-4])
                check(close(front,c["friendly_distance"]) and close(rear,c["enemy_behind_distance"]) and front<rear and close(distance(c["ray_origin"],c["impact_position"]),front) and close(c["actual_distance"],front),f"{weapon}: independently reconstructed friendly shield geometry")
                check(c["friendly_health"]==c["enemy_behind_health"]==100,f"{weapon}: friendly and shielded enemy retain health")
        results[weapon]={"cadence_count":len(expected),"last_shot_tick":expected[-1],"maximum_phase_error_seconds":phase,"reload_ticks":completed,"reload_timeline_samples":len(reload["timeline"]),"cancel_timeline_samples":len(timeline),"alternate_shot_ticks":shot_ticks,"deploy_ticks":18,"reported_switch_gap_ticks":cycle["shot_gap_ticks"],"damage":damage_results}

    report={"source_commit":MEASURED,"checks":checks,"failures":errors,"case_count":len(rows),"case_keys":[list(k) for k in sorted(expected_keys)],"weapons":results,"log_sha256":hashlib.sha256(raw.read_bytes()).hexdigest(),"scope":"Independent read-only recomputation of this actual Windows source-probe log using frozen production weapon specifications; no engine or OCR.","limitations":["Post-visual authority equality is a recorded boolean plus frozen source assertion; separate post-visual snapshots are absent.","Switch-cycle records the gap rather than both original shot timestamps.","Headless source engineering measurement does not establish exported controls, physical latency, listening, rendered gunfeel or CS2 parity."]}
    output.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({"checks":checks,"failures":errors,"case_count":len(rows)}))
    raise SystemExit(bool(errors))

if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("raw",type=Path);parser.add_argument("--output",type=Path,required=True);args=parser.parse_args();main(args.raw,args.output)
