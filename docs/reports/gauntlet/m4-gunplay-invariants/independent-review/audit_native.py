#!/usr/bin/env python3
"""Recompute frozen M4 raw records. This script never launches the engine."""
import argparse
from collections import Counter
import datetime as dt
from fractions import Fraction
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import tarfile
import zipfile

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent
MEASURED = "fc5d677396930f1e84523b3726525dcbf6ea6b83"
REVIEWED = "d1e89edfbd474a04d6759300141880566b1559e3"
REGISTRATION = "26871f76dafb30854294e09d6377340a631fa0da"
GAME = "41abd17652a89c554463faa5b216a7af59aec0e7"
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


def main(raw):
    data = {}
    for name in ["source-before", "source-measurement-before", "source-after", "cleanup"]:
        data[name] = json.loads((raw/f"{name}.json").read_text())
    before, after, initial = data["source-measurement-before"], data["source-after"], data["source-before"]
    check(before["head"] == after["head"] == MEASURED, "measured HEAD before/after")
    check(before["game_tree"] == after["game_tree"] == GAME, "measured game tree before/after")
    check(before["status"] == after["status"] == "", "measured clean source before/after")
    check(before["tracked_game_sha256"] == after["tracked_game_sha256"], "all source receipt hashes equal")
    product_root = Path(initial["root"])
    for path, digest in after["tracked_game_sha256"].items():
        check(hashlib.sha256((product_root/path).read_bytes()).hexdigest() == digest, f"current bytes match measured game hash: {path}")
    delta = git("diff", "--name-only", REVIEWED, MEASURED).decode().splitlines()
    check(delta == ["game/tests/gunplay_rules_probe.gd.uid"], "only reviewed-to-measured change is generated UID")
    check(source(MEASURED, delta[0]).decode().strip() == "uid://cakg78qe7a0d0", "generated UID")
    check(set(after["tracked_game_sha256"])-set(initial["tracked_game_sha256"]) == set(delta), "one additional measured game file")
    for path, digest in initial["tracked_game_sha256"].items():
        check(after["tracked_game_sha256"][path] == digest, f"pre-import source unchanged: {path}")
    engine = Path(initial["engine"])
    engine_sha256 = hashlib.sha256(engine.read_bytes()).hexdigest()
    check(engine_sha256 == initial["engine_sha256"], "engine binary unchanged from pre-run receipt")
    check((raw/"engine-version.log").read_text().strip() == "4.7.2.stable.official.ed1daf0bf", "actual pinned engine version output")
    toolchain=source(MEASURED,"scripts/toolchain.py").decode()
    pinned=re.search(r'"linux": \("linux.x86_64", "Godot_v4.7.2-stable_linux.x86_64", "([a-f0-9]+)"',toolchain)[1]
    engine_archive=engine.parent/"godot.zip"
    check(hashlib.sha512(engine_archive.read_bytes()).hexdigest()==pinned,"engine archive checksum matches pinned toolchain")
    with zipfile.ZipFile(engine_archive) as archive:
        check(hashlib.sha256(archive.read(engine.name)).hexdigest()==engine_sha256,"pinned archive contains measured binary bytes")

    labels = ["engine-version", "import", "gunplay-rules", "actor", "weapon-integrity", "hit-feedback", "authority-order"]
    stage_results, previous_finish = {}, None
    for label in labels:
        launch = json.loads((raw/f"{label}-launch.json").read_text())
        result = json.loads((raw/f"{label}-result.json").read_text())
        log = (raw/f"{label}.log").read_bytes()
        check(all(result[k] == v for k, v in launch.items()), f"{label}: launch and result identity agree")
        check(result["exit_code"] == 0 and not result["timed_out"] and not result["detected_errors"], f"{label}: real successful exit")
        check(len(log) == result["log_bytes"] and hashlib.sha256(log).hexdigest() == result["log_sha256"], f"{label}: raw log bytes/hash")
        check(not re.search(r"(?im)^\s*(?:SCRIPT ERROR|ERROR:|WARNING:)|Parse Error|orphan|leaked", log.decode()), f"{label}: no engine errors/warnings/leaks")
        check(result["cwd"] == str(product_root) and result["pid"] == result["pgid"], f"{label}: owned process group/cwd")
        check(result["explicit_environment"]["GODOT_BIN"] == str(engine), f"{label}: explicit pinned binary")
        check(result["explicit_environment"]["SIGHTBREAK_STATE_DIR"] == str(Path(initial["output"])/"private-state"), f"{label}: isolated state")
        start = dt.datetime.fromisoformat(result["started_utc"])
        finish = dt.datetime.fromisoformat(result["finished_utc"])
        check(finish >= start and (previous_finish is None or start >= previous_finish), f"{label}: native stages sequential")
        previous_finish = finish
        stage_results[label] = {"checks": None, "pid": result["pid"], "exit_code": result["exit_code"], "wall_seconds": result["wall_seconds"], "log_sha256": result["log_sha256"], "command": result["command"]}
    owned = set(data["cleanup"]["owned_process_groups"])
    check(owned == {v["pid"] for v in stage_results.values()} and not data["cleanup"]["owned_processes_remaining"], "cleanup covers all seven native groups")
    remaining = []
    for item in Path("/proc").iterdir():
        if item.name.isdigit():
            try:
                if os.getpgid(int(item.name)) in owned:
                    remaining.append(int(item.name))
            except ProcessLookupError:
                pass
    check(not remaining, "independent live /proc check finds no owned group")
    check(not data["cleanup"]["external_services_started"] and not data["cleanup"]["ports_bound_by_harness"], "no harness service or port scope")
    for label, pattern, count in [("actor",r"ACTOR TESTS: (\d+) checks, (\d+) failures",73),("weapon-integrity",r"WEAPON_INTEGRITY_TEST checks=(\d+) failures=(\d+)",28),("hit-feedback",r"HIT_FEEDBACK_TEST checks=(\d+) failures=(\d+)",10),("authority-order",r"AUTHORITY_ORDER checks=(\d+) failures=(\d+) mode=assertion",178)]:
        match = re.findall(pattern, (raw/f"{label}.log").read_text())
        check(match == [(str(count), "0")], f"{label}: actual unambiguous native summary")
        stage_results[label]["checks"] = count

    lines = (raw/"gunplay-rules.log").read_text().splitlines()
    rows = [json.loads(line[13:]) for line in lines if line.startswith("GUNPLAY_CASE ")]
    source_rows = [json.loads(line[15:]) for line in lines if line.startswith("GUNPLAY_SOURCE ")]
    summaries = [json.loads(line[14:]) for line in lines if line.startswith("GUNPLAY_RULES ")]
    check(summaries == [{"checks":2840,"failures":[]}], "actual probe summary")
    check(len(source_rows) == 1 and source_rows[0]["physics_hz"] == 60 and source_rows[0]["engine"] == "4.7.2-stable (official)", "actual probe engine and 60 Hz source record")
    stage_results["gunplay-rules"]["checks"] = 2840
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

    # Review registration as source only; the full validate invocation was not run.
    validation=source(REGISTRATION,"scripts/validate.sh").decode(); prior=source(MEASURED,"scripts/validate.sh").decode()
    addition="run_godot gunplay-rules --headless --audio-driver Dummy --script res://tests/gunplay_rules_probe.gd\n"
    check(validation.replace(addition,"")==prior and validation.count(addition)==1,"maintained validation is exactly one added invocation")
    check(addition.strip().split()[2:]==stage_results["gunplay-rules"]["command"][1:],"registration arguments match actual measured probe")
    check(validation.index(addition)==validation.index("run_godot weapon-integrity --headless --script res://tests/weapon_integrity_test.gd\n")+len("run_godot weapon-integrity --headless --script res://tests/weapon_integrity_test.gd\n"),"registration follows weapon integrity")
    syntax=subprocess.run(["bash","-n"],input=validation.encode(),capture_output=True)
    check(syntax.returncode==0 and not syntax.stdout and not syntax.stderr,"registration shell syntax check")
    check(git("rev-parse",f"{REGISTRATION}:game").decode().strip()==GAME,"registration commit retains measured game tree")
    inputs={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in raw.iterdir() if p.is_file() and (p.suffix==".log" or p.name.endswith("-launch.json") or p.name.endswith("-result.json") or p.name in ["source-before.json","source-measurement-before.json","source-after.json","cleanup.json","run_stage.py"])}
    for name,digest in inputs.items():
        check(hashlib.sha256(source(REGISTRATION,"docs/reports/gauntlet/m4-gunplay-invariants/native-round-2/"+name)).hexdigest()==digest,"committed raw evidence equals original input: "+name)
    report={"measured_commit":MEASURED,"game_tree":GAME,"reviewed_commit":REVIEWED,"registration_commit":REGISTRATION,"mode":"independent file-only actual-output recomputation; no native rerun","checks":checks,"failures":errors,"case_count":len(rows),"case_keys":[list(k) for k in sorted(expected_keys)],"engine_sha256":engine_sha256,"pinned_engine_archive_sha512":pinned,"tracked_game_files":len(after["tracked_game_sha256"]),"owned_process_groups":sorted(owned),"remaining_owned_processes":remaining,"native_stages":stage_results,"weapons":results,"input_sha256":inputs,"limitations":["Post-visual authority equality is a recorded boolean plus inspected source assertion; separate post-visual snapshots are absent.","Switch-cycle output records the gap, not both original shot timestamps; independent verification checks the reported gap against stock timing.","This is a standalone headless rules measurement, not a played-feel, hardware, audio, CS2, network or whole aggregate qualification."]}
    (OUT/"native-audit.json").write_text(json.dumps(report,indent=2)+"\n")
    with tarfile.open(OUT/"native-raw.tar.gz","w:gz") as archive:
        for name in sorted(inputs): archive.add(raw/name,arcname=name)
    print(json.dumps({"independent_checks":checks,"failures":errors,"actual_cases":len(rows),"expected_counts":{w:v["cadence_count"] for w,v in results.items()},"reload_ticks":{w:v["reload_ticks"] for w,v in results.items()}}))
    raise SystemExit(bool(errors))


if __name__=="__main__":
    parser=argparse.ArgumentParser(); parser.add_argument("raw",type=Path); args=parser.parse_args(); main(args.raw.resolve())
