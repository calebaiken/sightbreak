#!/usr/bin/env python3
"""Recheck the retained combined validation without launching runtime workloads."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import subprocess
import tarfile


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frozen", type=Path, required=True)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--comparison-ref", default="3b97a00")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    frozen = args.frozen.resolve()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)

    def git(*parts):
        return subprocess.check_output(["git", "-C", str(frozen), *parts])

    run = frozen / "builds/combined-validation-r2"
    before = json.loads((run / "source-before.json").read_text())
    after = json.loads((run / "source-after.json").read_text())
    exit_code = int((run / "exit.txt").read_text())
    full = (run / "validate.log").read_text()
    assert before == after
    assert not before["source_dirty"] and not before["source_game_dirty"]
    assert exit_code == 0
    head = before["source_commit"]
    assert git("rev-parse", "HEAD").decode().strip() == head
    script_bytes = (frozen / "scripts/validate.sh").read_bytes()
    assert script_bytes == git("show", f"{head}:scripts/validate.sh")
    completed = re.search(r"^Validation completed\. Logs: (.+)$", full, re.M)
    assert completed
    log_dir = Path(completed[1])
    assert log_dir.parent == frozen / ".local/validation"
    assert not re.search(r"^SCRIPT ERROR|^ERROR:|Parse Error|^Traceback|^FAILED \(", full, re.M)
    assert "reload-visibility skipped: no DISPLAY" in full
    assert "SKIPPED catalog fixture" not in full
    assert "backend_world.json matches the backend" in full
    assert full.count("NETWORK_CLIENT_PASS movement snapshots reconnect authority-hit-and-impact-feedback") == 2
    assert "CONNECTION_LIFECYCLE_TEST three native scenarios and server cleanup passed" in full
    assert "OK (skipped=3)" in full
    assert [int(n) for n in re.findall(r"^Ran (\d+) tests? in ", full, re.M)] == [11, 4, 15, 24, 7, 5]

    commands = []
    display_scope = False
    for number, line in enumerate(script_bytes.decode().splitlines(), 1):
        if line.startswith('if [[ -n "${DISPLAY:-}" ]]'):
            display_scope = True
        if display_scope and line == "fi":
            display_scope = False
        match = re.search(r"\brun_godot ([a-z0-9-]+) (.*)", line)
        if not match:
            continue
        label = match[1]
        path = log_dir / f"{label}.log"
        entry = {"line": number, "label": label, "command": line.strip(),
                 "scope": "DISPLAY" if display_scope else "unconditional"}
        if display_scope:
            assert not path.exists()
            entry["result"] = "skipped: no DISPLAY"
        else:
            data = path.read_bytes()
            assert data
            text = data.decode(errors="replace")
            assert not re.search(r"^SCRIPT ERROR|^ERROR:|Parse Error", text, re.M), label
            entry.update(result="reached; nonempty original log; no engine-error signature",
                         log=path.relative_to(frozen).as_posix(), bytes=len(data), sha256=sha(data),
                         summaries=[line for line in text.splitlines() if re.search(r"checks[=:]|checks[,;]|checks,|failures|passed|PASS|RESULT|TESTS:", line)][-5:])
        commands.append(entry)
    assert len([c for c in commands if c["scope"] == "unconditional"]) == 52
    assert len([c for c in commands if c["scope"] == "DISPLAY"]) == 5

    fixtures = []
    for name in ("scripts/test_reload_contact.py",
                 "docs/reports/media/art-v9/hands/logs/clip_contact.csv",
                 "docs/reports/media/art-v9/hands/logs/clip_contact.glb.sha256",
                 "game/assets/weapons/relay_ar/relay_ar_arms.glb"):
        data = (frozen / name).read_bytes()
        assert data == git("show", f"{head}:{name}")
        fixtures.append({"path": name, "bytes": len(data), "sha256": sha(data), "matches_git_head": True})
    stamp = (frozen / "docs/reports/media/art-v9/hands/logs/clip_contact.glb.sha256").read_text().split()[0]
    assert stamp == fixtures[-1]["sha256"]
    assert "RELOAD_CONTACT_TEST checks=24 failures=0" in full
    tracked_runtime_inventory = []
    for row in git("ls-tree", "-r", head, "--", "backend", "server").decode().splitlines():
        metadata, name = row.split("\t", 1)
        if metadata.split()[1] != "blob":
            continue
        data = (frozen / name).read_bytes()
        assert data == git("show", f"{head}:{name}"), name
        tracked_runtime_inventory.append({"path": name, "bytes": len(data), "sha256": sha(data)})

    lifecycle = {}
    for scenario in ("silent", "idle", "reject"):
        for role in ("server", "client"):
            path = log_dir / "connection-lifecycle" / f"{scenario}-{role}.log"
            text = path.read_text()
            assert not re.search(r"^SCRIPT ERROR|^ERROR:|Parse Error", text, re.M)
            last = text.strip().splitlines()[-1]
            value = json.loads(last.split(" ", 1)[1])
            assert value["ok"] is True
            if role == "server":
                assert value["peer_entries"] == 0
            else:
                assert value["scenario"] == scenario
                assert value["admitted"] == (scenario == "idle")
            lifecycle[f"{scenario}-{role}"] = value

    failed = args.repository / "docs/reports/gauntlet/combined-validation-a23e349/attempt-1"
    inventory = json.loads((failed / "MANIFEST.json").read_text())
    old_archive = (failed / "raw-logs.tar.gz").read_bytes()
    assert sha(old_archive) == (failed / "archive-sha256.txt").read_text().split()[0]
    with tarfile.open(failed / "raw-logs.tar.gz") as archive:
        files = [m for m in archive.getmembers() if m.isfile()]
        assert len(files) == len(inventory) == 57
        for record in inventory:
            data = archive.extractfile(record["path"]).read()
            assert len(data) == record["bytes"] and sha(data) == record["sha256"]
        old_exit = archive.extractfile("builds/combined-validation/exit.txt").read().decode().strip()
        assert old_exit == "1"
        old_log = archive.extractfile("builds/combined-validation/validate.log").read().decode()
        assert "clip_contact.glb.sha256 is missing" in old_log and "FileNotFoundError" in old_log

    smoke_match = re.search(r"^NETWORK_LOG_DIR=(.+)$", full, re.M)
    assert smoke_match
    smoke_dir = Path(smoke_match[1])
    original_files = [(p, p.relative_to(frozen).as_posix()) for p in sorted(run.iterdir()) if p.is_file()]
    original_files += [(p, p.relative_to(frozen).as_posix()) for p in sorted(log_dir.glob("*.log"))]
    original_files += [(p, p.relative_to(frozen).as_posix()) for p in sorted((log_dir / "connection-lifecycle").glob("*.log"))]
    original_files += [(p, "network-smoke/" + p.name) for p in sorted(smoke_dir.glob("*.log"))]
    raw_inventory = []
    with tarfile.open(out / "raw-logs.tar.gz", "w:gz") as archive:
        for path, name in original_files:
            data = path.read_bytes()
            archive.add(path, arcname=name)
            raw_inventory.append({"path": name, "bytes": len(data), "sha256": sha(data)})
    (out / "MANIFEST.json").write_text(json.dumps(raw_inventory, indent=2) + "\n")
    (out / "archive-sha256.txt").write_text(sha((out / "raw-logs.tar.gz").read_bytes()) + "  raw-logs.tar.gz\n")

    compared = git("rev-parse", args.comparison_ref).decode().strip()
    trees = {name: {"validated": git("rev-parse", f"{head}:{name}").decode().strip(),
                    "comparison": git("rev-parse", f"{compared}:{name}").decode().strip()}
             for name in ("game", "backend", "server", "scripts", ".github")}
    result = {"validated_source": before, "matching_before_after": before == after,
              "exit": exit_code, "validate_sh_sha256": sha(script_bytes),
              "validation_directory": str(log_dir), "commands": commands,
              "display_skips": [c["label"] for c in commands if c["scope"] == "DISPLAY"],
              "python_unittest_summaries": re.findall(r"^Ran \d+ tests? in .+$|^OK(?: \(skipped=\d+\))?$", full, re.M),
              "catalog_serializer_check": re.search(r"^backend_world.json matches the backend.+$", full, re.M)[0],
              "fixtures": fixtures,
              "backend_server_actual_files_matching_git": tracked_runtime_inventory,
              "connection_lifecycle_actual_last_observations": lifecycle,
              "failed_attempt": {"source": "a23e3492bf59b370f6fb1411f585ae1de0431787", "exit": 1,
                                 "archive_files": 57, "all_manifest_hashes_match": True, "sha256": sha(old_archive)},
              "comparison_commit": compared, "compared_tree_ids": trees,
              "code_changes_after_validated_source": git("diff", "--name-status", f"{head}..{compared}", "--", "game", "scripts", "backend", "server", ".github").decode().splitlines(),
              "raw_inventory_files": len(raw_inventory)}
    (out / "audit.json").write_text(json.dumps(result, indent=2) + "\n")
    for name in ("source-before.json", "source-after.json", "exit.txt"):
        (out / name).write_bytes((run / name).read_bytes())
    print(json.dumps({"source": head, "exit": exit_code, "required_godot_logs": 52,
                      "DISPLAY_skips": 5, "raw_files": len(raw_inventory), "output": str(out)}, indent=2))


if __name__ == "__main__":
    main()
