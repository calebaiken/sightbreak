#!/usr/bin/env python3
"""Audit original aggregate evidence; never start Godot, OCR, SQL or input work."""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import re
import subprocess
import tarfile


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frozen", type=Path, required=True)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--comparison-ref", default="b72badd")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    frozen, repo, out = (p.resolve() for p in (args.frozen, args.repository, args.output))
    out.mkdir(parents=True, exist_ok=True)

    def git(*parts):
        return subprocess.check_output(["git", "-C", str(frozen), *parts])

    run = frozen / "builds/combined-validation"
    command = json.loads((run / "command.json").read_text())
    result = json.loads((run / "result.json").read_text())
    before = json.loads((run / "source-before.json").read_text())
    after = json.loads((run / "source-after.json").read_text())
    stdout = (run / "stdout.log").read_text()
    head = "b09cfe1b661ec153f2bd57d45e695cc70e9717b0"
    assert before == after and before["source_commit"] == head
    assert not before["source_dirty"] and not before["source_game_dirty"]
    assert git("rev-parse", "HEAD").decode().strip() == head
    assert command["command"] == result["command"] == ["./scripts/validate.sh"]
    assert command["cwd"] == result["cwd"] == str(frozen)
    assert command["selected_environment"]["DISPLAY"] is None
    assert command["selected_environment"]["SIGHTBREAK_BACKEND_PYTHON"] == "/workspace/sightbreak/.venv/bin/python"
    assert result["exit_code"] == 0 and result["source_unchanged"] is True
    assert abs(result["seconds"] - 465.033044934) < 0.000001
    engine = Path(command["selected_environment"]["SIGHTBREAK_TOOLS_DIR"]) / "godot-4.7.2/Godot_v4.7.2-stable_linux.x86_64"
    with engine.open("rb") as stream:
        engine_hash = hashlib.file_digest(stream, "sha256").hexdigest()
    assert engine_hash == command["pinned_engine_sha256"] == result["pinned_engine_sha256"]
    assert "Godot Engine v4.7.2.stable.official.ed1daf0bf" in stdout
    completion = re.search(r"^Validation completed\. Logs: (.+)$", stdout, re.M)
    assert completion
    log_dir = Path(completion[1])
    assert log_dir == frozen / ".local/validation/run-3uEIWG"
    strict_errors = r"^SCRIPT ERROR|^ERROR:|Parse Error|^Traceback|^FAILED \(|ObjectDB.*leaked|Leaked instance"
    assert not re.search(strict_errors, stdout, re.M)
    assert not re.search(r"^WARNING:", stdout, re.M)
    assert "reload-visibility skipped: no DISPLAY" in stdout
    assert "SKIPPED catalog fixture" not in stdout
    assert "backend_world.json matches the backend (29 definitions)" in stdout
    assert stdout.count("NETWORK_CLIENT_PASS movement snapshots reconnect authority-hit-and-impact-feedback") == 2
    assert "CONNECTION_LIFECYCLE_TEST three native scenarios and server cleanup passed" in stdout
    assert [int(n) for n in re.findall(r"^Ran (\d+) tests? in ", stdout, re.M)] == [11, 4, 15, 24, 7, 4, 5]
    assert "OK (skipped=3)" in stdout

    script = (frozen / "scripts/validate.sh").read_bytes()
    assert script == git("show", f"{head}:scripts/validate.sh")
    commands, display_scope = [], False
    for line_number, line in enumerate(script.decode().splitlines(), 1):
        if line.startswith('if [[ -n "${DISPLAY:-}" ]]'):
            display_scope = True
        if display_scope and line == "fi":
            display_scope = False
        match = re.search(r"\brun_godot ([a-z0-9-]+) (.*)", line)
        if not match:
            continue
        label = match[1]
        entry = {"line": line_number, "label": label, "command": line.strip(), "scope": "DISPLAY" if display_scope else "unconditional"}
        path = log_dir / f"{label}.log"
        if display_scope:
            assert not path.exists()
            entry["result"] = "skipped: no DISPLAY"
        else:
            data = path.read_bytes()
            text = data.decode()
            assert data and not re.search(strict_errors, text, re.M), label
            assert not re.search(r"^WARNING:", text, re.M), label
            entry.update(result="reached with original nonempty log; no error/leak/warning signature",
                         log=path.relative_to(frozen).as_posix(), bytes=len(data), sha256=digest(data),
                         summaries=[s for s in text.splitlines() if re.search(r"checks[=:]|checks[,;]|checks,|failures|passed|PASS:|_RESULT|TESTS_OK|HUD_PRIORITY_BENCHMARK", s)][-5:])
        commands.append(entry)
    assert len([c for c in commands if c["scope"] == "unconditional"]) == 52
    assert len([c for c in commands if c["scope"] == "DISPLAY"]) == 5
    assert "INPUT_MODE_TEST checks=462 failures=0" in (log_dir / "input-mode.log").read_text()

    hud_text = (log_dir / "objective-hud.log").read_text()
    samples = [json.loads(line.split(" ", 1)[1]) for line in hud_text.splitlines() if line.startswith("HUD_PRIORITY_SAMPLE ")]
    benchmarks = [json.loads(line.split(" ", 1)[1]) for line in hud_text.splitlines() if line.startswith("HUD_PRIORITY_BENCHMARK ")]
    assert len(samples) == 1458
    assert all(s["correct"] and s["actual"] == s["expected"] and s["game_tick"] == 0 for s in samples)
    expected_samples = {(touch, role, connection, sample) for touch in (False, True)
                        for role in ("attacker", "defender", "spectator")
                        for connection in ("offline", "hosting", "connected") for sample in range(81)}
    assert {(s["touch"], s["role"], s["connection"], s["sample"]) for s in samples} == expected_samples
    for sample in samples:
        role_text = {"attacker": "DEFEND THE DEVICE", "spectator": "SPECTATING YOUR SQUAD",
                     "defender": "HOLD USE NEAR THE DEVICE TO DEFUSE" if sample["touch"] else "HOLD E NEAR THE DEVICE TO DEFUSE"}
        assert sample["actual"] == role_text[sample["role"]]
    assert sorted((b["touch"], b["samples"], b["wrong_frames"]) for b in benchmarks) == [(False, 729, 0), (True, 729, 0)]
    assert "checks=1535 failures=0" in hud_text
    hud_cleanup = json.loads(next(line.split(" ", 1)[1] for line in hud_text.splitlines() if line.startswith("HUD_OBJECTIVE_HINT_TEST_CLEANUP ")))
    assert hud_cleanup["exit"] == 0 and hud_cleanup["original_exit"] == 0
    assert hud_cleanup["removed"] and hud_cleanup["owned"] and hud_cleanup["original_user_dir_restored"]
    assert not Path(hud_cleanup["native_user_dir"]).exists()

    lifecycle = {}
    for scenario in ("silent", "idle", "reject"):
        for role in ("server", "client"):
            path = log_dir / "connection-lifecycle" / f"{scenario}-{role}.log"
            text = path.read_text()
            assert not re.search(strict_errors, text, re.M)
            value = json.loads(text.strip().splitlines()[-1].split(" ", 1)[1])
            assert value["ok"] is True
            if role == "server":
                assert value["peer_entries"] == 0
            else:
                assert value["scenario"] == scenario and value["admitted"] == (scenario == "idle")
            lifecycle[f"{scenario}-{role}"] = value

    additional_inventory = []
    names = [row.split("\t", 1)[1] for row in git("ls-tree", "-r", head, "--", "backend", "server").decode().splitlines() if row.split()[1] == "blob"]
    names += ["scripts/validate.sh", "scripts/test_reload_contact.py", "docs/reports/media/art-v9/hands/logs/clip_contact.csv", "docs/reports/media/art-v9/hands/logs/clip_contact.glb.sha256", "game/assets/weapons/relay_ar/relay_ar_arms.glb"]
    for name in names:
        data = (frozen / name).read_bytes()
        assert data == git("show", f"{head}:{name}"), name
        additional_inventory.append({"path": name, "bytes": len(data), "sha256": digest(data), "matches_git_head": True})
    assert (frozen / names[-2]).read_text().split()[0] == digest((frozen / names[-1]).read_bytes())
    assert "RELOAD_CONTACT_TEST checks=24 failures=0" in stdout

    comparison = git("rev-parse", args.comparison_ref).decode().strip()
    trees = {name: {"validated": git("rev-parse", f"{head}:{name}").decode().strip(), "comparison": git("rev-parse", f"{comparison}:{name}").decode().strip()} for name in ("game", "backend", "server", "scripts", ".github")}
    previous_diff = git("diff", "b85f936", head, "--", "scripts/validate.sh").decode()
    assert previous_diff.count("+python3 ") == 1 and "+python3 scripts/test_offline_role_guidance.py -v" in previous_diff

    mac_relative = "docs/reports/gauntlet/m2-macos-focus/native-run-39732825169/full-qa"
    mac = repo / mac_relative
    mac_paths = ["macos/source.json", "regressions/results.json", "regressions/isolation.json", "regressions/input_mode.log"]
    for name in mac_paths:
        actual = (mac / name).read_bytes()
        tracked = subprocess.check_output(["git", "-C", str(repo), "show", f"{comparison}:{mac_relative}/{name}"])
        assert actual == tracked, name
    mac_source = json.loads((mac / mac_paths[0]).read_text())
    for key, value in before.items():
        assert mac_source[key] == value, key
    mac_results = json.loads((mac / mac_paths[1]).read_text())
    assert isinstance(mac_results, list) and len(mac_results) == 7
    mac_input = next(r for r in mac_results if r["suite"] == "input_mode")
    assert mac_input["exit"] == 0 and mac_input["clean_log"] is False
    mac_text = (mac / mac_paths[-1]).read_text()
    assert "INPUT_MODE_TEST checks=462 failures=0" in mac_text
    assert "WARNING: 2 ObjectDB instances were leaked at exit" in mac_text
    mac_isolation = json.loads((mac / mac_paths[2]).read_text())
    assert mac_isolation["passed"] is False

    smoke_dir = Path(re.search(r"^NETWORK_LOG_DIR=(.+)$", stdout, re.M)[1])
    smoke_logs = sorted(smoke_dir.glob("*.log"))
    assert len(smoke_logs) == 4
    for path in smoke_logs:
        assert not re.search(strict_errors, path.read_text(), re.M)
    cleanup_text = (smoke_dir / "cleanup.log").read_text()
    smoke_pids = [int(n) for n in re.findall(r"pid=(\d+)", cleanup_text)]
    assert smoke_pids and not any((Path("/proc") / str(pid)).exists() for pid in smoke_pids)
    survivors = []
    for path in Path("/proc").iterdir():
        if not path.name.isdigit():
            continue
        try:
            argv = (path / "cmdline").read_bytes().split(b"\0")
        except OSError:
            continue
        if argv and b"Godot" in argv[0] and str(frozen / "game").encode() in argv:
            survivors.append(int(path.name))
    assert not survivors
    process_after = {"observed_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "smoke_cleanup_pids": smoke_pids,
                     "smoke_cleanup_pids_present": [], "godot_processes_for_frozen_game_path": survivors,
                     "scope": "read-only /proc check; no runtime workload launched"}

    originals = [(p, p.relative_to(frozen).as_posix(), "Linux aggregate") for p in sorted(run.iterdir()) if p.is_file()]
    originals += [(p, p.relative_to(frozen).as_posix(), "Linux aggregate") for p in sorted(log_dir.glob("*.log"))]
    originals += [(p, p.relative_to(frozen).as_posix(), "Linux aggregate") for p in sorted((log_dir / "connection-lifecycle").glob("*.log"))]
    originals += [(p, "network-smoke/" + p.name, "Linux aggregate") for p in smoke_logs]
    assert len(originals) == 68
    originals += [(mac / name, "platform-context/macos-39732825169/" + name, "separate same-source Mac run") for name in mac_paths]
    inventory = []
    with tarfile.open(out / "raw-logs.tar.gz", "w:gz") as archive:
        for path, archive_name, origin in originals:
            data = path.read_bytes()
            archive.add(path, arcname=archive_name)
            inventory.append({"path": archive_name, "original_path": str(path), "origin": origin, "bytes": len(data), "sha256": digest(data)})
    (out / "MANIFEST.json").write_text(json.dumps(inventory, indent=2) + "\n")
    (out / "archive-sha256.txt").write_text(digest((out / "raw-logs.tar.gz").read_bytes()) + "  raw-logs.tar.gz\n")
    audit = {"validated_source": before, "source_before_after_equal": before == after, "command": command, "result": result,
             "actual_engine_sha256_matches_receipt": engine_hash, "validate_sh_sha256": digest(script), "godot_commands": commands,
             "python_test_counts_in_order": [11, 4, 15, 24, 7, 4, 5], "windows_observation_skips": 3,
             "connection_lifecycle": lifecycle, "hud_flood_samples": len(samples), "hud_flood_benchmarks": benchmarks, "hud_cleanup": hud_cleanup,
             "actual_additional_source_files_matching_git": additional_inventory, "comparison_commit": comparison, "comparison_tree_ids": trees,
             "code_delta_to_comparison": git("diff", "--name-status", head, comparison, "--", "game", "backend", "server", "scripts", ".github").decode().splitlines(),
             "validate_delta_since_b85": previous_diff,
             "mac_context": {"source": {k: mac_source[k] for k in before}, "completed_suites": [r["suite"] for r in mac_results],
                             "input_mode_exit": mac_input["exit"], "input_mode_clean_log": mac_input["clean_log"],
                             "warning": "WARNING: 2 ObjectDB instances were leaked at exit (run with `--verbose` for details).",
                             "isolation_passed": mac_isolation["passed"], "cause": "unknown; Linux absence does not explain or clear the Mac failure"},
             "original_files": len(inventory), "linux_original_files": 68, "separate_mac_context_files": 4}
    (out / "audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    (out / "process-after.json").write_text(json.dumps(process_after, indent=2) + "\n")
    for name in ("command.json", "result.json", "source-before.json", "source-after.json"):
        (out / name).write_bytes((run / name).read_bytes())
    print(json.dumps({"source": head, "exit": result["exit_code"], "godot_logs": 52, "display_skips": 5,
                      "archive_files": len(inventory), "mac_failure_preserved": True}, indent=2))


if __name__ == "__main__":
    main()
