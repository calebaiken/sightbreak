#!/usr/bin/env python3
"""Audit original Linux aggregate files without launching runtime workloads."""
import argparse
import ast
from collections import Counter
import datetime as dt
from fractions import Fraction
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tarfile
import traceback
import zipfile


ENGINE_SHA256 = "8d106cbe6144c2dc7e881d61d2429c1a8a76e6b22ef48bd5e48dcf934953f71e"
ERRORS = re.compile(r"^\s*(?:SCRIPT ERROR|ERROR:|WARNING:)|Parse Error|^Traceback|^FAILED\b|ObjectDB.*leaked|Leaked instance|resources? (?:are )?still in use", re.M | re.I)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def native_rows(text, prefix):
    return [json.loads(line[len(prefix):]) for line in text.splitlines() if line.startswith(prefix)]


def method_count(path):
    count = 0
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.ClassDef) and any(
                (isinstance(base, ast.Attribute) and base.attr == "TestCase") or
                (isinstance(base, ast.Name) and base.id == "TestCase") for base in node.bases):
            count += sum(isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef))
                         and method.name.startswith("test") for method in node.body)
    return count


def processes_and_ports(paths, pids, ports):
    found = []
    for process in Path("/proc").iterdir():
        if not process.name.isdigit():
            continue
        try:
            argv = (process / "cmdline").read_bytes().replace(b"\0", b" ").decode(errors="replace")
            if int(process.name) in pids or ("Godot" in argv and any(path in argv for path in paths)):
                found.append({"pid": int(process.name), "argv": argv})
        except OSError:
            pass
    sockets = []
    for name in ("tcp", "tcp6", "udp", "udp6"):
        for line in Path("/proc/net", name).read_text().splitlines()[1:]:
            columns = line.split()
            local_port = int(columns[1].split(":")[1], 16)
            if local_port in ports and (name.startswith("udp") or columns[3] == "0A"):
                sockets.append({"family": name, "port": local_port, "state": columns[3], "inode": columns[9]})
    return {"observed_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "matching_processes": found, "matching_bound_sockets": sockets,
            "checked_paths": paths, "checked_pids": sorted(pids), "checked_ports": sorted(ports),
            "scope": "Read-only current /proc and listening/bound socket observation; no signals sent."}


def audit_private_native(run, frozen, engine, before, aggregate_command, check):
    native = run / "native-two-suites"
    launch = json.loads((run / "strict-new-native-command.json").read_text())
    result = json.loads((run / "strict-new-native-result.json").read_text())
    isolation = json.loads((native / "isolation.json").read_text())
    suites = json.loads((native / "results.json").read_text())
    expected_command = ["python3", "scripts/run_native_regressions.py", "--output", str(native),
                        "--suites", "transaction_journal", "gunplay_rules"]
    check(launch["command"] == expected_command and all(result[key] == value for key, value in launch.items()), "exact selected two-suite native launch/result")
    check(result["exit_code"] == 0 and result["source_after"] == before and result["source_unchanged"], "selected native command zero exit and exact unchanged source")
    check(result["completed_utc"] <= aggregate_command["started_utc"], "private selected suites finish before aggregate starts")
    check([row["suite"] for row in suites] == ["transaction_journal", "gunplay_rules"], "only declared two suites ran")
    check(isolation["passed"] and isolation["failure"] is None and not isolation["finalization_failures"], "strict isolation finalization passes")
    check(isolation["engine"] == "4.7.2.stable.official.ed1daf0bf", "native runner verifies pinned engine")
    check(isolation["suite_timeout_seconds"] == 120 and isolation["probe_timeout_seconds"] == 30, "original strict suite/probe budgets preserved")
    check(all(isolation[key] for key in ("source_resources_unchanged", "copied_resources_unchanged", "temporary_project_removed")), "native runner source/copy/cleanup receipts pass")
    actual_resources = {path.relative_to(frozen / "game").as_posix(): sha(path.read_bytes())
                        for path in sorted((frozen / "game").rglob("*"))
                        if path.is_file() and ".godot" not in path.relative_to(frozen / "game").parts}
    check(actual_resources == isolation["source_resources_sha256"], "all 319 original native source resources independently match actual frozen files")
    namespace = isolation["namespace"]
    check(bool(re.fullmatch(r"SIGHTBREAK-native-tests-[a-f0-9]{32}", namespace)), "unique native namespace format")
    producer_names = ["producer-01-bootstrap", "producer-02-before-transaction_journal", "producer-03-after-transaction_journal",
                      "producer-04-before-gunplay_rules", "producer-05-after-gunplay_rules"]
    check(sorted(path.stem for path in native.glob("producer-*.json")) == sorted(producer_names), "all five original engine-produced user-directory receipts")
    projects, roots, producers = set(), set(), []
    for name in producer_names:
        receipt = json.loads((native / (name + ".json")).read_text())
        # The suffix is the actual source-suite identifier, including underscores.
        suffix = "bootstrap" if name.endswith("bootstrap") else name.split("-", 3)[3]
        user = Path(receipt["data_dir"]) / namespace / suffix
        project = Path(receipt["project_path"])
        check(receipt["uses_custom_user_dir"] and receipt["custom_user_dir"] == namespace + "/" + suffix
              and Path(receipt["user_data_dir"]) == user and receipt["os"] == "Linux", "actual native producer namespace: " + name)
        check(not receipt["profile_exists"] and not receipt["diagnostics_exist"], "producer sees no existing save or diagnostics: " + name)
        check(not project.exists() and not user.parent.exists(), "actual private project and native namespace absent: " + name)
        projects.add(str(project)); roots.add(str(user.parent)); producers.append(receipt)
    check(len(projects) == len(roots) == 1, "one owned private project/namespace with distinct suite children")
    check(len(isolation["cleanup"]) == 1 and isolation["cleanup"][0]["removed"] and isolation["cleanup"][0]["user_namespace"] in roots, "owned native namespace cleanup receipt")
    check(isolation["import"]["exit"] == 0 and isolation["import"]["clean_log"], "private native import actual clean exit")
    for path in sorted(native.rglob("*.log")):
        check(bool(path.read_bytes()) and not ERRORS.search(path.read_text()), "all original private native logs clean: " + path.relative_to(native).as_posix())
    for row in suites:
        suite = row["suite"]
        check(row["exit"] == 0 and row["clean_log"] and row["before"]["user_data_dir"] == row["after"]["user_data_dir"], "strict selected suite actual result: " + suite)
        arguments = ["--headless", "--script", "res://tests/transaction_journal_test.gd"] if suite == "transaction_journal" else ["--headless", "--audio-driver", "Dummy", "--script", "res://tests/gunplay_rules_probe.gd"]
        check(row["command"] == [str(engine), "--path", next(iter(projects)), *arguments], "actual suite arguments match maintained mapping: " + suite)
        for phase in ("before", "after"):
            producer = row[phase]
            original_receipt = json.loads(Path(producer["producer_receipt"]).read_text())
            check(all(producer[key] == value for key, value in original_receipt.items()), "inline native receipt equals original producer: " + suite + " " + phase)
            check(producer["run"]["exit"] == 0 and producer["run"]["clean_log"], "native producing probe clean result: " + suite + " " + phase)
        userdata = native / (suite + "-userdata")
        produced = {path.relative_to(userdata).as_posix(): sha(path.read_bytes()) for path in sorted(userdata.rglob("*")) if path.is_file()}
        check(produced == row["produced_files_sha256"], "retained native produced user bytes match original hashes: " + suite)
    journal = (native / "transaction_journal.log").read_text()
    check("TRANSACTION_JOURNAL 41/41 passed" in journal, "strict native journal 41/41")
    child_stream = native_rows(journal, "COMPETING_PROCESS ")
    child = [value for stream in child_stream for text in stream for value in native_rows(text, "OWNER_BLOCKED ")]
    check(len(child) == 1 and all(child[0][key] == 22 for key in ("claim", "clear", "stage")) and child[0]["unchanged"], "actual competing native child fails all writes without changing receipt")
    gunplay = (native / "gunplay_rules.log").read_text()
    check(native_rows(gunplay, "GUNPLAY_RULES ") == [{"checks": 2840, "failures": []}], "strict selected native gunplay 2840 checks")
    check(len(native_rows(gunplay, "GUNPLAY_CASE ")) == 52, "strict selected native gunplay 52 actual records")
    defaults = None
    for node in ast.parse((frozen / "scripts/run_native_regressions.py").read_text()).body:
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "SUITES" for target in node.targets):
            defaults = ast.literal_eval(node.value)
    original_twelve = ("actor", "match", "authority_order", "state_privacy", "movement_prediction", "peer_lifecycle", "input_mode", "menu_focus", "offline_diagnostics", "hud_objective_hint", "activity_provenance", "bot_squad_symmetry")
    check(defaults == original_twelve + ("transaction_journal", "gunplay_rules"), "fourteen default suites preserve original twelve in order")
    pids = {launch["pid"], child[0]["pid"]}
    remaining_group = []
    for path in Path("/proc").iterdir():
        if path.name.isdigit():
            try:
                if os.getpgid(int(path.name)) == launch["pgid"]:
                    remaining_group.append(int(path.name))
            except (ProcessLookupError, PermissionError):
                pass
    check(not remaining_group, "actual selected native process group has no remaining members or listeners")
    return {"command": launch, "result": result, "isolation": isolation, "suites": suites,
            "producer_receipts": producers, "competing_child": child, "defaults": defaults,
            "remaining_group_members": remaining_group}, projects, pids


def main(args):
    frozen, run, out = (path.resolve() for path in (args.frozen, args.run, args.output))
    out.mkdir(parents=True, exist_ok=True)
    report = {"mode": "Independent original-file/source audit; no runtime execution", "checks": 0, "failures": []}
    originals = {}

    def check(condition, label):
        report.setdefault("checks", 0)
        report["checks"] += 1
        if not condition:
            report["failures"].append(label)

    def git(*parts):
        return subprocess.check_output(["git", "-C", str(frozen), *parts])

    def original(path, name):
        data = path.read_bytes()
        originals[name] = (path, data)
        return data

    try:
        for path in sorted(run.rglob("*")):
            if path.is_file():
                original(path, "sequential-driver/" + path.relative_to(run).as_posix())
        command, result, before, after = [json.loads((run / name).read_text()) for name in
                                        ("aggregate-command.json", "aggregate-result.json", "source-before.json", "source-after.json")]
        driver = json.loads((run / "driver.json").read_text())
        overall = json.loads((run / "result.json").read_text())
        engine_receipt = json.loads((run / "engine.json").read_text())
        head = args.expected_source
        check(before == after and before["source_commit"] == head, "exact source receipts equal frozen expected source")
        check(not before["source_dirty"] and not before["source_game_dirty"], "clean source receipts")
        check(git("rev-parse", "HEAD").decode().strip() == head, "frozen checkout still at measured source")
        check(not git("status", "--porcelain", "--untracked-files=all"), "actual frozen checkout remains clean")
        check(command["command"] == result["command"] == ["./scripts/validate.sh"], "unmodified maintained aggregate argv")
        check(command["cwd"] == result["cwd"] == str(frozen), "actual command cwd is frozen checkout")
        environment = driver["selected_environment"]
        check(environment["DISPLAY"] is None, "no DISPLAY")
        check(environment["SIGHTBREAK_TOOLS_DIR"] == "/workspace/tools", "declared pinned tools directory")
        check(environment["SIGHTBREAK_BACKEND_PYTHON"] == "/workspace/sightbreak/.venv/bin/python", "actual catalog interpreter selected")
        check(result["exit_code"] == 0 and result["source_unchanged"] is True, "actual zero exit and unchanged-source result")
        check(all(result[key] == value for key, value in command.items()), "original aggregate launch/result fields agree")
        check(result["source_after"] == before, "aggregate result independently binds unchanged exact source")
        check(overall["passed"] and overall["failure"] is None and overall["source_unchanged"] and overall["remaining_godot_count"] == 0, "whole sequential driver completed successfully")
        check(driver["expected_source"] == head, "driver source expectation agrees")
        check((run / "driver.py").read_bytes() == Path(args.driver).read_bytes(), "archived launch wrapper equals original wrapper")
        stdout = (run / "aggregate.log").read_text()
        check(not ERRORS.search(stdout), "complete original stdout has no strict error/warning/leak predicate")
        for path in run.glob("*.log"):
            check(not ERRORS.search(path.read_text()), "driver log clean: " + path.name)
        completions = re.findall(r"^Validation completed\. Logs: (.+)$", stdout, re.M)
        check(len(completions) == 1, "one maintained completion marker")
        logs = Path(completions[0])
        check(logs.parent == frozen / ".local/validation", "actual command log path belongs to frozen checkout")

        engine = Path(environment["SIGHTBREAK_TOOLS_DIR"]) / "godot-4.7.2/Godot_v4.7.2-stable_linux.x86_64"
        engine_hash = sha(engine.read_bytes())
        check(engine_hash == ENGINE_SHA256 == engine_receipt["sha256"] and engine_receipt["path"] == str(engine), "actual pinned executable hash")
        toolchain = (frozen / "scripts/toolchain.py").read_text()
        pinned_archive = re.search(r'"linux": \("linux.x86_64", "Godot_v4.7.2-stable_linux.x86_64", "([a-f0-9]+)"', toolchain)[1]
        archive_path = engine.parent / "godot.zip"
        check(hashlib.sha512(archive_path.read_bytes()).hexdigest() == pinned_archive, "installed archive matches pinned toolchain SHA512")
        with zipfile.ZipFile(archive_path) as archive:
            check(sha(archive.read(engine.name)) == engine_hash, "pinned archive contains actual executable bytes")

        script = (frozen / "scripts/validate.sh").read_bytes()
        check(script == git("show", head + ":scripts/validate.sh"), "executed maintained script equals committed bytes")
        commands, python_groups, display = [], [], False
        for number, line in enumerate(script.decode().splitlines(), 1):
            if line.startswith('if [[ -n "${DISPLAY:-}" ]]'):
                display = True
            if display and line == "fi":
                display = False
            match = re.search(r"\brun_godot ([a-z0-9-]+) (.*)", line)
            if match:
                label = match[1]
                path = logs / (label + ".log")
                row = {"line": number, "label": label, "command": line, "scope": "DISPLAY" if display else "mandatory"}
                if display:
                    check(not path.exists(), "rendered command honestly unreached: " + label)
                else:
                    text = original(path, "aggregate-logs/" + path.name).decode()
                    check(bool(text) and not ERRORS.search(text), "mandatory original log clean: " + label)
                    check("Godot Engine v4.7.2.stable.official.ed1daf0bf" in text, "pinned version in mandatory log: " + label)
                    row["summaries"] = [entry for entry in text.splitlines() if re.search(r"checks|failures|passed|_RESULT|TESTS_OK|BENCHMARK|PASS:|_REVIEW|_OBSERVATION", entry)][-5:]
                commands.append(row)
            if line == "python3 -m unittest discover -s server/tests -v":
                paths = list((frozen / "server/tests").glob("test*.py"))
            elif re.match(r"^python3 scripts/test_.*\.py", line):
                paths = [frozen / line.split()[1]]
            else:
                continue
            count = sum(method_count(path) for path in paths)
            if count:
                python_groups.append({"line": number, "command": line, "methods_from_source": count})
        check(sum(row["scope"] == "mandatory" for row in commands) == 54, "54 source-derived mandatory Godot commands")
        check(sum(row["scope"] == "DISPLAY" for row in commands) == 5, "five rendered commands outside no-DISPLAY scope")
        expected_logs = {row["label"] + ".log" for row in commands if row["scope"] == "mandatory"} | {"reload-contact.log"}
        check({path.name for path in logs.glob("*.log")} == expected_logs, "actual aggregate log inventory is exactly the 54 mandatory commands plus contact")
        actual_counts = [int(value) for value in re.findall(r"^Ran (\d+) tests? in ", stdout, re.M)]
        check(actual_counts == [row["methods_from_source"] for row in python_groups], "actual Python unittest counts/order match frozen source methods")
        check("OK (skipped=3)" in stdout, "three explicitly recorded Windows-only observation-reader skips")
        check("reload-visibility skipped: no DISPLAY" in stdout, "rendered block skip recorded")
        check("SKIPPED catalog fixture" not in stdout and "backend_world.json matches the backend (29 definitions)" in stdout, "actual backend catalog fixture check reached")
        check("RELOAD_CONTACT_TEST checks=24 failures=0" in stdout, "actual reload contact check reached")
        original(logs / "reload-contact.log", "aggregate-logs/reload-contact.log")

        hud = (logs / "objective-hud.log").read_text()
        samples = native_rows(hud, "HUD_PRIORITY_SAMPLE ")
        keys = {(touch, role, connection, sample) for touch in (False, True) for role in
                ("attacker", "defender", "spectator") for connection in ("offline", "hosting", "connected") for sample in range(81)}
        check(len(samples) == 1458 and {(s["touch"], s["role"], s["connection"], s["sample"]) for s in samples} == keys, "all 1458 unique HUD context samples")
        for sample in samples:
            text = {"attacker": "DEFEND THE DEVICE", "spectator": "SPECTATING YOUR SQUAD", "defender":
                    "HOLD USE NEAR THE DEVICE TO DEFUSE" if sample["touch"] else "HOLD E NEAR THE DEVICE TO DEFUSE"}[sample["role"]]
            check(sample["correct"] and sample["actual"] == text and sample["expected"] == text and sample["game_tick"] == 0, "raw HUD role/text/tick agreement")
        hud_cleanup = native_rows(hud, "HUD_OBJECTIVE_HINT_TEST_CLEANUP ")
        check(len(hud_cleanup) == 1 and all(hud_cleanup[0][key] for key in ("removed", "owned", "original_user_dir_restored")) and hud_cleanup[0]["exit"] == hud_cleanup[0]["original_exit"] == 0, "HUD owned cleanup succeeded")
        check(not Path(hud_cleanup[0]["native_user_dir"]).exists(), "actual HUD private native directory absent")
        check("TRANSACTION_JOURNAL 41/41 passed" in (logs / "transaction-journal.log").read_text(), "new mandatory journal native checks pass")

        gunplay = (logs / "gunplay-rules.log").read_text()
        rows = native_rows(gunplay, "GUNPLAY_CASE ")
        key = lambda row: (row["weapon"], row["kind"], row.get("scenario", row.get("control", "")))
        expected = {(weapon, kind, "") for weapon in ("sidearm", "smg", "rifle", "marksman") for kind in
                    ("cadence", "held_finite_magazine", "partial_reload", "reload_switch", "switch_cycle")}
        expected |= {(weapon, "damage", value) for weapon in ("sidearm", "smg", "rifle", "marksman") for value in ("body", "head", "lethal_body")}
        expected |= {(weapon, "negative", value) for weapon in ("sidearm", "smg", "rifle", "marksman") for value in ("miss", "friendly", "dry", "reload", "deploy")}
        check(len(rows) == 52 and set(map(key, rows)) == expected and all(count == 1 for count in Counter(map(key, rows)).values()), "all 52 unique new mandatory gunplay cases")
        check(native_rows(gunplay, "GUNPLAY_RULES ") == [{"checks": 2840, "failures": []}], "actual mandatory M4 summary")

        lifecycle = {}
        for scenario in ("silent", "idle", "reject"):
            for role in ("server", "client"):
                path = logs / "connection-lifecycle" / (scenario + "-" + role + ".log")
                text = original(path, "aggregate-logs/connection-lifecycle/" + path.name).decode()
                value = json.loads(text.strip().splitlines()[-1].split(" ", 1)[1])
                check(not ERRORS.search(text) and value["ok"] is True, "real ENet lifecycle log succeeds: " + path.name)
                check(value.get("peer_entries") == 0 if role == "server" else value["scenario"] == scenario and value["admitted"] == (scenario == "idle"), "real lifecycle terminal state: " + path.name)
                lifecycle[path.name] = value
        check({path.name for path in (logs / "connection-lifecycle").glob("*.log")} == set(lifecycle), "actual lifecycle log inventory is exactly six declared roles")
        check("CONNECTION_LIFECYCLE_TEST three native scenarios and server cleanup passed" in stdout, "lifecycle command completion")
        smoke = Path(re.findall(r"^NETWORK_LOG_DIR=(.+)$", stdout, re.M)[0])
        for path in sorted(smoke.glob("*.log")):
            text = original(path, "network-smoke/" + path.name).decode()
            check(not ERRORS.search(text), "smoke original log clean: " + path.name)
        for client in ("client-a.log", "client-b.log"):
            check("NETWORK_CLIENT_PASS movement snapshots reconnect authority-hit-and-impact-feedback" in (smoke / client).read_text(), "real smoke client completed: " + client)
        cleanup_text = (smoke / "cleanup.log").read_text()
        cleanup_pids = {int(value) for value in re.findall(r"pid=(\d+)", cleanup_text)}
        check(bool(cleanup_pids), "original owned smoke cleanup PID receipt exists")

        inventory = []
        records = git("ls-tree", "-rz", head, "--", "game", "backend", "server", "scripts", ".github").split(b"\0")
        fixture_names = ["docs/reports/media/art-v9/hands/logs/clip_contact.csv", "docs/reports/media/art-v9/hands/logs/clip_contact.glb.sha256"]
        records += git("ls-tree", "-rz", head, "--", "docs/reports/media/art-v9/hands/logs").split(b"\0")
        content, validation = hashlib.sha256(), hashlib.sha256()
        for record in records:
            if not record:
                continue
            metadata, name = record.split(b"\t", 1)
            mode, kind, blob = metadata.decode().split()
            name = name.decode()
            path = frozen / name
            data = os.readlink(path).encode() if mode == "120000" else path.read_bytes()
            actual_blob = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
            check(kind == "blob" and actual_blob == blob, "actual source bytes equal frozen Git object: " + name)
            inventory.append({"path": name, "bytes": len(data), "sha256": sha(data), "git_blob": blob, "actual_git_blob": actual_blob})
        launch_inputs = json.loads((run / "tracked-inputs.json").read_text())
        current_hashes = {row["path"]: row["sha256"] for row in inventory}
        check(all(current_hashes.get(name) == digest for name, digest in launch_inputs.items()), "all 341 independently rehashed tracked launch inputs equal before-run receipt")
        for path in sorted((frozen / "game").rglob("*")):
            relative = path.relative_to(frozen / "game")
            if path.is_file() and ".godot" not in relative.parts and "tests" not in relative.parts:
                content.update(relative.as_posix().encode() + b"\0" + path.read_bytes() + b"\0")
        for directory in ("scripts", ".github", "game/tests"):
            for path in sorted((frozen / directory).rglob("*")):
                if path.is_file() and not any(part in ("__pycache__", ".godot") for part in path.parts) and path.suffix != ".pyc":
                    validation.update(path.relative_to(frozen).as_posix().encode() + b"\0" + path.read_bytes() + b"\0")
        check(content.hexdigest() == before["source_content_sha256"], "independently recomputed shipping content digest")
        check(validation.hexdigest() == before["source_validation_sha256"], "independently recomputed validation digest")
        glb = frozen / "game/assets/weapons/relay_ar/relay_ar_arms.glb"
        check((frozen / fixture_names[1]).read_text().split()[0] == sha(glb.read_bytes()), "restored CSV stamp bound to actual shipped GLB")
        private_native, private_paths, native_pids = audit_private_native(run, frozen, engine, before, command, check)
        ready_ports = {int(value) for path, data in originals.values() if path.suffix == ".log"
                       for value in re.findall(r"SIGHTBREAK_SERVER_READY port=(\d+)", data.decode(errors="replace"))}
        observation = processes_and_ports([str(frozen / "game"), *sorted(private_paths)], cleanup_pids | native_pids | {command["pid"], driver["pid"]}, ready_ports | {27991, 29900, 29901, 29902})
        observation["ports_from_original_ready_lines"] = sorted(ready_ports)
        observation["aggregate_process_group"] = command["pgid"]
        observation["aggregate_group_members"] = []
        for path in Path("/proc").iterdir():
            if path.name.isdigit():
                try:
                    if os.getpgid(int(path.name)) == command["pgid"]:
                        observation["aggregate_group_members"].append(int(path.name))
                except (ProcessLookupError, PermissionError):
                    pass
        check(not observation["aggregate_group_members"], "actual aggregate process group has no remaining members")
        check(not observation["matching_processes"] and not observation["matching_bound_sockets"], "actual aggregate processes and ports absent")
        write(out / "process-after.json", observation)
        report.update(source=before, command=command, result=result, driver=driver, overall_result=overall, engine_sha256=engine_hash, private_native=private_native,
                      godot_commands=commands, python_groups=python_groups, actual_python_counts=actual_counts,
                      lifecycle=lifecycle, hud_samples=len(samples), hud_cleanup=hud_cleanup,
                      additional_source_inventory=inventory, validate_sha256=sha(script), smoke_cleanup=cleanup_text,
                      source_differences_from_b09=git("diff", "--name-status", "b09cfe1", head, "--", "game", "backend", "server", "scripts", ".github").decode().splitlines())
    except BaseException:
        report["failures"].append("Audit exception; raw traceback retained")
        (out / "audit-exception.txt").write_text(traceback.format_exc())
    manifest = []
    with tarfile.open(out / "raw-logs.tar.gz", "w:gz") as archive:
        for name, (path, data) in sorted(originals.items()):
            archive.add(path, arcname=name)
            origin = ("original strict private selected two-suite Linux check" if "/native-two-suites/" in name or "/strict-new-native" in name
                      else "original integrated Linux aggregate" if name.startswith(("aggregate-logs/", "network-smoke/")) or "/aggregate" in name
                      else "original shared sequential driver/source receipts")
            manifest.append({"path": name, "original_path": str(path), "bytes": len(data), "sha256": sha(data), "origin": origin})
    write(out / "MANIFEST.json", manifest)
    (out / "archive-sha256.txt").write_text(sha((out / "raw-logs.tar.gz").read_bytes()) + "  raw-logs.tar.gz\n")
    report.update(original_files=len(manifest), passed=not report["failures"])
    write(out / "audit.json", report)
    print(json.dumps({key: report[key] for key in ("passed", "checks", "failures", "original_files")}))
    return int(bool(report["failures"]))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frozen", type=Path, required=True)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--expected-source", required=True)
    parser.add_argument("--driver", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    raise SystemExit(main(parser.parse_args()))
