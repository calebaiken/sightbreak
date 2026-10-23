#!/usr/bin/env python3
"""Independent source/raw-output audit. This script never launches game workloads."""
import argparse
import ast
from collections import Counter
import datetime as dt
import hashlib
import json
import importlib.util
import os
from pathlib import Path
import re
import subprocess
import traceback

ENGINE = "Godot Engine v4.7.2.stable.official.ed1daf0bf"
ERRORS = re.compile(r"^\s*(?:SCRIPT ERROR|ERROR:)|Parse Error|^Traceback|^FAILED\b|ObjectDB.*leaked|Leaked instance|resources? (?:are )?still in use|^Orphan StringName: [^\r\n]+ \(static: [0-9]+, total: [0-9]+\)\r?$|^StringName: [1-9][0-9]* unclaimed string names at exit\.\r?$", re.M | re.I)
WARNINGS = re.compile(r"^\s*WARNING:.*$", re.M)
SCOPES = ("game", "scripts", ".github", "backend", "server",
          "docs/reports/media/art-v9/hands/logs", "docs/reports/gauntlet/native-layout-ocr")
TAGS = {
    "hit-feedback": "HIT_FEEDBACK_TEST", "weapon-integrity": "WEAPON_INTEGRITY_TEST",
    "hit-volume": "HIT_VOLUME_TEST", "hit-history": "HIT_HISTORY_TEST",
    "render-budget": "RENDER_BUDGET_TEST", "smoke-presentation": "SMOKE_PRESENTATION_TEST",
    "authority-order": "AUTHORITY_ORDER", "state-privacy": "STATE_PRIVACY_TEST",
    "snapshot-buffer": "SNAPSHOT_BUFFER_TEST", "input-stream": "INPUT_STREAM_TEST",
    "activity-provenance": "ACTIVITY_PROVENANCE_TEST", "movement-replay": "MOVEMENT_PREDICTION_TEST",
    "input-lifecycle": "INPUT_LIFECYCLE_TEST", "peer-lifecycle": "PEER_LIFECYCLE_TEST",
    "result-outbox": "RESULT_OUTBOX_TEST", "reconnect-policy": "RECONNECT_POLICY_TEST",
    "reconnect-independent": "INDEPENDENT_RECONNECT_REVIEW", "resume-admission": "INDEPENDENT_RESUME_ADMISSION",
    "resume-alias": "INDEPENDENT_RESUME_ALIAS", "profile": "PROFILE_TEST", "touch": "TOUCH_TEST",
    "main": "MAIN_TEST", "input-mode": "INPUT_MODE_TEST", "menu-focus": "MENU_FOCUS_TEST",
    "offline-diagnostics": "OFFLINE_DIAGNOSTICS_TEST", "landscape": "LANDSCAPE_UI_TEST",
    "ux-contract": "UX_CONTRACT_TEST", "hud-overflow": "HUD_OVERFLOW_TEST",
    "weapon-art": "WEAPON_ART_TEST", "integration-actor-lifecycle": "INTEGRATION_ACTOR_LIFECYCLE",
    "reload-sequence": "RELOAD_SEQUENCE_TEST", "reload-audio": "RELOAD_AUDIO_TEST",
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def rows(raw, prefix):
    return [json.loads(line[len(prefix):]) for line in raw.splitlines() if line.startswith(prefix)]


def method_count(path):
    return sum(sum(isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)) and m.name.startswith("test")
                   for m in node.body)
               for node in ast.walk(ast.parse(path.read_text()))
               if isinstance(node, ast.ClassDef) and any(
                   isinstance(base, ast.Attribute) and base.attr == "TestCase" or
                   isinstance(base, ast.Name) and base.id == "TestCase" for base in node.bases))


def main(args):
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    frozen, logs, stdout_path = args.frozen.resolve(), args.logs.resolve(), args.stdout.resolve()
    report = {"mode": "Independent source/raw-output audit; no engine, export, OCR, service or CI execution",
              "checks": 0, "failures": [], "warnings": {}}

    def check(value, label):
        report["checks"] += 1
        if not value:
            report["failures"].append(label)

    def git(*parts):
        return subprocess.check_output(["git", "-C", str(frozen), *parts])

    def clean(raw, name):
        check(bool(raw) and not ERRORS.search(raw), "nonempty error/leak-free original: " + name)
        report["warnings"][name] = WARNINGS.findall(raw)

    try:
        head = git("rev-parse", "HEAD").decode().strip()
        check(head == args.expected_source, "exact frozen HEAD")
        check(not git("status", "--porcelain", "--untracked-files=all", "--", *SCOPES), "clean executable/fixture scopes after run")
        inventory = []
        for record in git("ls-tree", "-rz", head, "--", *SCOPES).split(b"\0"):
            if not record:
                continue
            meta, name = record.split(b"\t", 1)
            mode, kind, blob = meta.decode().split()
            name = name.decode()
            path = frozen / name
            check(path.exists(), "actual tracked input present: " + name)
            if not path.exists():
                continue
            data = os.readlink(path).encode() if mode == "120000" else path.read_bytes()
            actual_blob = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
            check(kind == "blob" and actual_blob == blob, "actual input equals frozen Git blob: " + name)
            inventory.append({"path": name, "bytes": len(data), "sha256": sha(data), "git_blob": blob, "actual_git_blob": actual_blob})
        report["source_inventory"] = inventory
        source_paths = {r["path"] for r in inventory}
        for scope in SCOPES:
            check(any(p.startswith(scope + "/") for p in source_paths), "required source/fixture scope populated: " + scope)
        stamp = frozen / "docs/reports/media/art-v9/hands/logs/clip_contact.glb.sha256"
        glb = frozen / "game/assets/weapons/relay_ar/relay_ar_arms.glb"
        check(stamp.read_text().split()[0] == sha(glb.read_bytes()), "contact stamp matches actual shipped arms GLB")
        stdout = stdout_path.read_text()
        clean(stdout, "aggregate stdout")
        script = (frozen / "scripts/validate.sh").read_bytes()
        check(script == git("show", head + ":scripts/validate.sh"), "maintained validator committed bytes")
        contract, groups, display = [], [], False
        for number, line in enumerate(script.decode().splitlines(), 1):
            if line.startswith('if [[ -n "${DISPLAY:-}" ]]'):
                display = True
            if display and line == "fi":
                display = False
            match = re.search(r"\brun_godot ([a-z0-9-]+) (.*)", line)
            if match:
                contract.append({"line": number, "label": match[1], "command": line, "scope": "DISPLAY" if display else "mandatory"})
            if line == "python3 -m unittest discover -s server/tests -v":
                paths = sorted((frozen / "server/tests").glob("test*.py"))
            elif re.match(r"^python3 scripts/test_.*\.py", line):
                paths = [frozen / line.split()[1]]
            else:
                continue
            count = sum(method_count(p) for p in paths)
            if count:
                groups.append({"line": number, "command": line, "methods_from_source": count})
        mandatory = [r for r in contract if r["scope"] == "mandatory"]
        rendered = [r for r in contract if r["scope"] == "DISPLAY"]
        check(len(mandatory) == 56 and len(rendered) == 5, "56 mandatory and five DISPLAY-only source invocations")
        check({p.name for p in logs.glob("*.log")} == {r["label"] + ".log" for r in mandatory} | {"reload-contact.log"}, "exact mandatory plus reload-contact top-level original log inventory")
        for item in rendered:
            check(not (logs / (item["label"] + ".log")).exists(), "declared rendered omission: " + item["label"])
        texts = {}
        for item in mandatory:
            label = item["label"]
            raw = (logs / (label + ".log")).read_text()
            texts[label] = raw
            clean(raw, label)
            check(ENGINE in raw, "pinned actual version: " + label)
            item["summary_lines"] = [s for s in raw.splitlines() if re.search(r"checks|failures|passed|_RESULT|TESTS_OK|BENCHMARK|PASS:|_REVIEW|_OBSERVATION", s)][-6:]
            if label in TAGS:
                found = re.findall(r"^" + re.escape(TAGS[label]) + r" checks=(\d+) failures=(0|\[\])(?=\s|$)", raw, re.M)
                check(len(found) == 1 and int(found[0][0]) > 0, "own zero-failure suite marker: " + label)
        special = {
            "actor": r"^ACTOR TESTS: [1-9]\d* checks, 0 failures$",
            "world": r"^WORLD_TEST [1-9]\d* checks; 0 failures$",
            "bot-ai-regression": r"^BOT_AI_REGRESSION_TESTS_OK$",
            "bot-lifecycle": r"^BOT_LIFECYCLE_RESULT passed=true .*halftime=true plant_observed=(?:true|false) reports=1 ",
            "objective-hud": r"^HUD_OBJECTIVE_HINT_TEST .* checks=1535 failures=0$",
            "economy-ui": r"^PASS: Economy native screens, offline separation, URL policy, UUIDs$",
            "armory-ui": r"^PASS: Armory states, money terms, trade sides and collection order \([1-9]\d* checks\)$",
            "armory-state": r"^PASS: Armory account, text-size and transaction behaviour \([1-9]\d* checks\)$",
            "menu-state": r"^PASS: Menu account lines and resize handling \([1-9]\d* checks\)$",
            "economy-recovery": r"^PASS: [1-9]\d* economy recovery and cosmetic material assertions$",
            "transaction-journal": r"^TRANSACTION_JOURNAL 41/41 passed$",
            "cosmetics": r"^Cosmetic presentation: [1-9]\d* assertions / 0 failures$",
        }
        for label, pattern in special.items():
            check(len(re.findall(pattern, texts[label], re.M)) == 1, "own successful suite marker: " + label)
        match = re.findall(r"^MATCH_TEST: (\d+)/(\d+) passed$", texts["match"], re.M)
        check(len(match) == 1 and int(match[0][0]) > 0 and match[0][0] == match[0][1], "match all-checks-passed marker")
        for label, scenario, checks in (("reload-audio-capture", "reload", 14), ("reload-audio-cancel", "cancel", 11), ("reload-audio-shot", "shot", 15)):
            check(re.findall(r"^RELOAD_AUDIO_CAPTURE scenario=(\S+) reduced=(\S+) checks=(\d+) failures=(\d+)$", texts[label], re.M) == [(scenario, "false", str(checks), "0")], "real Dummy mixer scenario checks: " + scenario)
        lost = rows(texts["lost-welcome"], "LOST_WELCOME_REVIEW ")
        check(len(lost) == 1 and all(lost[0].get(k) is True for k in ("fixture_valid", "welcome_suppressed_after_authority_commit", "old_credential_retained_by_client", "restored_same_actor")) and lost[0].get("final_state") == "connected", "lost-welcome actual recovery fields")
        auth = rows(texts["resume-auth-loss"], "AUTH_LOSS_REVIEW ")
        check(len(auth) == 1 and all(auth[0].get(k) is True for k in ("fixture_valid", "recovered_same_actor", "passed")) and auth[0].get("suppressed_server_hellos") == 1 and auth[0].get("fresh_accepted_tick", -1) >= 0 and auth[0].get("state") == "connected", "one-hello auth-loss actual recovery fields")
        bots = re.findall(r"^BOT_MATCH_OBSERVATION elapsed=([0-9.]+) kills=(\d+) planted=(true|false) score=(\d+):(\d+)$", texts["bots"], re.M)
        check(len(bots) == 1 and int(bots[0][1]) > 0, "short bot observation has actual kills; plant value retained")
        report["short_bot_observation"] = bots
        lifecycle_observation = re.findall(r"^BOT_LIFECYCLE_RESULT passed=(true|false) rounds=(\d+) score=(\d+):(\d+) kills=(\d+) halftime=(true|false) plant_observed=(true|false) reports=(\d+) simulated_seconds=([0-9.]+)$", texts["bot-lifecycle"], re.M)
        check(len(lifecycle_observation) == 1 and lifecycle_observation[0][0] == lifecycle_observation[0][5] == "true" and 7 <= int(lifecycle_observation[0][1]) <= 12 and int(lifecycle_observation[0][4]) > 0 and lifecycle_observation[0][7] == "1", "stock lifecycle meets frozen source predicates; plant observation retained separately")
        report["stock_bot_lifecycle_observation"] = lifecycle_observation
        check("reload-visibility skipped: no DISPLAY (needs a native rendering display)" in stdout, "explicit no-DISPLAY rendering omission")
        check(re.findall(r"^Validation completed\. Logs: (.+)$", stdout, re.M) == [str(logs)], "actual maintained completion bound to these log paths")
        actual_counts = [int(x) for x in re.findall(r"^Ran (\d+) tests? in ", stdout, re.M)]
        check(actual_counts == [r["methods_from_source"] for r in groups] == [11, 7, 4, 15, 24, 5, 7, 4, 5, 15, 16, 8, 8], "13 actual Python group counts/order equal frozen source")
        check(len(re.findall(r"^OK(?: \(skipped=3\))?$", stdout, re.M)) == 13 and len(re.findall(r"^OK \(skipped=3\)$", stdout, re.M)) == 1, "all 13 groups OK and exactly one documented three-skip group")
        check(len(re.findall(r"\.\.\. skipped ", stdout)) == 3, "exactly three actual Windows-only reader skips")
        check("backend_world.json matches the backend (29 definitions)" in stdout and "SKIPPED catalog fixture" not in stdout, "backend serializer catalog actually runs, all 29 definitions")
        contact = (logs / "reload-contact.log").read_text()
        clean(contact, "reload-contact")
        check("RELOAD_CONTACT_TEST checks=24 failures=0" in contact, "actual reload-contact 24/0")

        hud = rows(texts["objective-hud"], "HUD_PRIORITY_SAMPLE ")
        expected_hud = {(touch, role, conn, sample) for touch in (False, True) for role in ("attacker", "defender", "spectator") for conn in ("offline", "hosting", "connected") for sample in range(81)}
        hud_keys = [(r["touch"], r["role"], r["connection"], r["sample"]) for r in hud]
        check(len(hud) == 1458 and set(hud_keys) == expected_hud and all(v == 1 for v in Counter(hud_keys).values()), "complete unique 1458 HUD Cartesian samples")
        for r in hud:
            expected = {"attacker": "DEFEND THE DEVICE", "spectator": "SPECTATING YOUR SQUAD", "defender": "HOLD USE NEAR THE DEVICE TO DEFUSE" if r["touch"] else "HOLD E NEAR THE DEVICE TO DEFUSE"}[r["role"]]
            check(r["correct"] is True and r["actual"] == r["expected"] == expected and r["game_tick"] == 0, "raw HUD expected role text and zero tick")
        cleanup = rows(texts["objective-hud"], "HUD_OBJECTIVE_HINT_TEST_CLEANUP ")
        check(len(cleanup) == 1 and all(cleanup[0].get(k) is True for k in ("removed", "owned", "original_user_dir_restored")) and cleanup[0].get("exit") == cleanup[0].get("original_exit") == 0, "HUD owned namespace/restoration actual receipt")
        if cleanup:
            check(not Path(cleanup[0]["native_user_dir"]).exists(), "actual HUD private namespace absent")

        gunplay = rows(texts["gunplay-rules"], "GUNPLAY_CASE ")
        key = lambda r: (r["weapon"], r["kind"], r.get("scenario", r.get("control", "")))
        expected_gunplay = {(weapon, kind, "") for weapon in ("sidearm", "smg", "rifle", "marksman") for kind in ("cadence", "held_finite_magazine", "partial_reload", "reload_switch", "switch_cycle")}
        expected_gunplay |= {(weapon, "damage", case) for weapon in ("sidearm", "smg", "rifle", "marksman") for case in ("body", "head", "lethal_body")}
        expected_gunplay |= {(weapon, "negative", case) for weapon in ("sidearm", "smg", "rifle", "marksman") for case in ("miss", "friendly", "dry", "reload", "deploy")}
        check(len(gunplay) == 52 and set(map(key, gunplay)) == expected_gunplay and all(v == 1 for v in Counter(map(key, gunplay)).values()), "52 unique actual gunplay case keys")
        check(rows(texts["gunplay-rules"], "GUNPLAY_RULES ") == [{"checks": 2840, "failures": []}], "gunplay 2840 zero-failure checks")
        dry_script = Path(__file__).with_name("recompute_dry_observable.py")
        accepted_oracle = git("show", "138a1ab:docs/reports/gauntlet/m5-dry-weapon-recovered-independent/recompute_observable.py")
        check(dry_script.read_bytes() == accepted_oracle, "reused accepted dry observable oracle byte-for-byte")
        dry = subprocess.run(["python3", str(dry_script), "--mode", "candidate", str(logs / "bot-dry-weapon.log"), "--output", str(out / "dry-observable-recompute.json")], capture_output=True, text=True)
        (out / "dry-observable-recompute.stdout").write_text(dry.stdout)
        (out / "dry-observable-recompute.stderr").write_text(dry.stderr)
        dry_result = json.loads((out / "dry-observable-recompute.json").read_text())
        check(dry.returncode == 0 and dry_result["observable_comparison_passed"] and not dry_result["errors"], "actual dry fixture observable recomputation")
        report["additional_dry_observable_predicates"] = dry_result["predicates"]

        exhausted_path = Path(__file__).with_name("recompute_exhausted_rows.py")
        accepted_exhausted = git("show", "28a3e294:docs/reports/gauntlet/m5-exhausted-primary-selection/native-independent-r1/audit_rows.py")
        check(exhausted_path.read_bytes() == accepted_exhausted, "prior independent all-row oracle reused byte-for-byte; acceptance recomputed")
        spec = importlib.util.spec_from_file_location("independent_exhausted", exhausted_path)
        exhausted_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(exhausted_module)
        exhausted_records, other = exhausted_module.parse(logs / "bot-exhausted-primary.log")
        exhausted = exhausted_module.audit(exhausted_records, frozen)
        (out / "exhausted-observable-recompute.json").write_text(json.dumps(exhausted, indent=2) + "\n")
        check(exhausted["row_counts"] == {"CASE": 567, "STEP": 576, "SEQUENCE": 72, "CONTROL_STEP": 96, "CONTROL": 5, "POLICY_RANGE": 9, "POLICY_RESERVE_STEP": 20}, "new maintained exhausted-primary complete raw action set")
        check(rows(texts["bot-exhausted-primary"], "BOT_EXHAUSTED_POLICY_HEADER ") == [{"range_cases_expected": 9, "reserve_steps_expected": 20, "total_policy_rows_expected": 1268, "common_fixture_sha256": "540d24dda8e58f4685030e81b55ac3778ccbf31a89f76f9873ac598c32770731"}], "exhausted source-bound supplement header")
        check(rows(texts["bot-exhausted-primary"], "BOT_EXHAUSTED_POLICY_RESULT ") == [{"policy_rows": 1268, "range_rows": 9, "reserve_rows": 20, "failures_so_far": []}], "exhausted supplement terminal completion")
        report["additional_exhausted_observable_predicates"] = exhausted["independent_predicates"]
        report["exhausted_fixture_checks"] = exhausted["reported_fixture_checks"]
        report["exhausted_event_totals"] = exhausted["all_row_totals"]

        symmetry = rows(texts["bot-squad-symmetry"], "BOT_SQUAD_SAMPLE ")
        samples = {(r["difficulty"], r["team"], r["kind"], r["slot"], r["id"]): r["output"] for r in symmetry}
        kinds = ("close", "long", "travel", "stuck", "stuck_low", "stuck_jump", "idle", "smoke", "spent_smoke", "empty_smoke", "smoke_near", "smoke_far", "carrier_smoke", "carrier", "defuser", "cover")
        expected_samples = {(d, team, kind, slot, slot + offset) for d in ("easy", "normal", "hard") for team in (0, 1) for kind in kinds for slot in range(5) for offset in (1, 6)}
        check(len(symmetry) == len(samples) == 960 and set(samples) == expected_samples, "all 960 unique symmetry samples")
        for d, team, kind, slot in {(d, team, kind, slot) for d in ("easy", "normal", "hard") for team in (0, 1) for kind in kinds for slot in range(5)}:
            check(samples[d, team, kind, slot, slot + 1] == samples[d, team, kind, slot, slot + 6], "raw squad pair equal: " + str((d, team, kind, slot)))
        check("BOT_SQUAD_SYMMETRY_RESULT samples=960 checks=2722 failures=0 mode=assertion" in texts["bot-squad-symmetry"], "symmetry actual 2722/0 assertion summary")

        lifecycle = {}
        expected_lifecycle = set()
        for scenario in ("silent", "idle", "reject"):
            for role in ("server", "client"):
                name = f"{scenario}-{role}.log"
                expected_lifecycle.add(name)
                raw = (logs / "connection-lifecycle" / name).read_text()
                clean(raw, name)
                value = json.loads(raw.strip().splitlines()[-1].split(" ", 1)[1])
                check(value.get("ok") is True, "actual lifecycle successful terminal marker: " + name)
                check(value.get("peer_entries") == 0 if role == "server" else value.get("scenario") == scenario and value.get("admitted") is (scenario == "idle"), "lifecycle terminal peer/admission state: " + name)
                lifecycle[name] = value
        check({p.name for p in (logs / "connection-lifecycle").glob("*.log")} == expected_lifecycle, "exact six lifecycle original logs")
        check("CONNECTION_LIFECYCLE_TEST three native scenarios and server cleanup passed" in stdout, "native lifecycle command completes")
        smoke_dirs = re.findall(r"^NETWORK_LOG_DIR=(.+)$", stdout, re.M)
        check(len(smoke_dirs) == 1, "exact one original smoke log directory receipt")
        smoke = Path(smoke_dirs[0])
        check({p.name for p in smoke.glob("*.log")} == {"server.log", "client-a.log", "client-b.log", "cleanup.log"}, "exact four original smoke logs")
        for p in smoke.glob("*.log"):
            clean(p.read_text(), "network/" + p.name)
        for name in ("client-a.log", "client-b.log"):
            check("NETWORK_CLIENT_PASS movement snapshots reconnect authority-hit-and-impact-feedback" in (smoke / name).read_text(), "actual network client completion: " + name)
        cleanup_text = (smoke / "cleanup.log").read_text()
        check(bool(re.findall(r"NETWORK_CLEANUP pid=\d+ wait_exit=\d+", cleanup_text)), "owned smoke wait receipt retained")
        report.update(source=head, validate_sha256=sha(script), godot_commands=contract, python_groups=groups,
                      actual_python_counts=actual_counts, hud_samples=len(hud), hud_cleanup=cleanup,
                      gunplay_records=len(gunplay), symmetry_samples=len(symmetry), lifecycle=lifecycle,
                      smoke_directory=str(smoke), smoke_cleanup=cleanup_text,
                      source_changes_since_preregistered=git("diff", "--name-status", "28a3e294c850482475b7ab74067c08538ae6310d", head, "--", *SCOPES).decode().splitlines())
    except BaseException:
        report["failures"].append("Audit exception; original traceback retained")
        (out / "audit-exception.txt").write_text(traceback.format_exc())
    report["passed"] = not report["failures"]
    (out / "audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ("passed", "checks", "failures")}))
    return int(not report["passed"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frozen", type=Path, required=True)
    parser.add_argument("--logs", type=Path, required=True)
    parser.add_argument("--stdout", type=Path, required=True)
    parser.add_argument("--expected-source", required=True)
    parser.add_argument("--output", type=Path, required=True)
    raise SystemExit(main(parser.parse_args()))
