#!/usr/bin/env python3
"""Read original aggregate provenance and independently inspect scoped terminal state."""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import traceback


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main(args):
    frozen, run, out = args.frozen.resolve(), args.run.resolve(), args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    report = {"mode": "Independent original-receipt/source and live read-only cleanup audit", "checks": 0, "failures": []}

    def check(value, label):
        report["checks"] += 1
        if not value:
            report["failures"].append(label)

    def read(name):
        return json.loads((run / name).read_text())

    def git(*parts):
        return subprocess.check_output(["git", "-C", str(frozen), *parts])

    try:
        before, after = read("source-before.json"), read("source-after.json")
        command, result = read("command.json"), read("result.json")
        engine, preflight, cleanup = read("engine.json"), read("preflight-resources.json"), read("cleanup.json")
        observed, launch_inputs = read("observed-processes.json"), read("tracked-inputs.json")
        outer = read("outer-live.json")
        independent_outer = json.loads(Path(__file__).with_name("independent-outer-live.json").read_text())
        check(before == after == result.get("source_after", before), "before/after source receipts exactly equal")
        check(before["source_commit"] == args.expected_source and not before["source_dirty"] and not before["source_game_dirty"], "receipts identify exact clean freeze")
        check(git("rev-parse", "HEAD").decode().strip() == args.expected_source and not git("status", "--porcelain", "--untracked-files=all"), "actual whole frozen checkout remains exact and clean")
        check(before["source_game_tree"] == git("rev-parse", "HEAD:game").decode().strip(), "actual frozen game tree agrees with receipt")
        content, validation = hashlib.sha256(), hashlib.sha256()
        for p in sorted((frozen / "game").rglob("*")):
            relative = p.relative_to(frozen / "game")
            if p.is_file() and ".godot" not in relative.parts and "tests" not in relative.parts:
                content.update(relative.as_posix().encode() + b"\0" + p.read_bytes() + b"\0")
        for directory in ("scripts", ".github", "game/tests"):
            for p in sorted((frozen / directory).rglob("*")):
                if p.is_file() and not any(part in ("__pycache__", ".godot") for part in p.parts) and p.suffix != ".pyc":
                    validation.update(p.relative_to(frozen).as_posix().encode() + b"\0" + p.read_bytes() + b"\0")
        check(content.hexdigest() == before["source_content_sha256"], "independent actual shipping content digest agrees")
        check(validation.hexdigest() == before["source_validation_sha256"], "independent actual validation digest agrees")
        pre_run = json.loads(Path(__file__).with_name("pre-run-source-review.json").read_text())
        expected_inputs = {r["path"]: r["sha256"] for r in pre_run["inventory"]}
        check(launch_inputs == expected_inputs, "all actual launch input names/hashes equal independent pre-run inventory")
        for name, digest in launch_inputs.items():
            check(sha((frozen / name).read_bytes()) == digest, "retained actual launch input unchanged: " + name)
        runner = frozen / "docs/reports/gauntlet/aggregate-recovered-20261023/run_aggregate.py"
        check((run / "runner.py").read_bytes() == runner.read_bytes() == git("show", args.expected_source + ":docs/reports/gauntlet/aggregate-recovered-20261023/run_aggregate.py"), "actual archived runner equals frozen committed bytes")
        check(command["runner_sha256"] == pre_run["runner_sha256"] == sha(runner.read_bytes()), "runner hash equals independent pre-run binding")
        check(command["command"] == ["./scripts/validate.sh"] and command["cwd"] == str(frozen), "actual unmodified maintained argv/cwd without backend branch")
        check(command["timeout_seconds"] == 1200 and command["pid"] == command["pgid"], "original aggregate whole bound and new process group identity")
        check(all(result.get(k) == v for k, v in command.items()), "result matches every original launch field")
        check(result["exit_code"] == 0 and result["passed"] is True and result["source_unchanged"] is True and result["failure"] is None and not result.get("forced_group_cleanup"), "original aggregate normal zero exit without supervisor error/forced group cleanup")
        started, completed = dt.datetime.fromisoformat(result["started_utc"]), dt.datetime.fromisoformat(result["completed_utc"])
        check(started < completed and 0 < result["seconds"] < 1200 and abs((completed - started).total_seconds() - result["seconds"]) < 1.0, "actual bounded elapsed and ordered UTC completion receipts")
        check(outer["aggregate_pid"] == command["pid"] and outer["outer_pid"] == independent_outer["pid"] and outer["outer_start_ticks"] == independent_outer["start_ticks"] and outer["outer_pgid"] == independent_outer["pgid"] and outer["outer_sid"] == independent_outer["sid"] and outer["outer_argv_sha256"] == independent_outer["argv_sha256"], "coordinator outer identity matches independent live PID/start/argv/group/session observation")
        check(independent_outer["argv"] == ["python3", "docs/reports/gauntlet/aggregate-recovered-20261023/run_aggregate.py", str(frozen), args.expected_source, str(run)] and independent_outer["cwd"] == str(frozen), "independently observed actual supervisor argv/cwd")
        check(started < dt.datetime.fromisoformat(outer["observed_utc"]) < dt.datetime.fromisoformat(independent_outer["observed_utc"]) < completed, "both live outer identity observations occur during this actual aggregate")
        environment = command["environment"]
        check(environment["DISPLAY"] is None and environment["GODOT_BIN"] is None and environment["SIGHTBREAK_TEST_TIMEOUT"] is None, "no rendering, engine or 540-second stage-timeout override")
        check(environment["SIGHTBREAK_TOOLS_DIR"] == "/workspace/tools" and environment["SIGHTBREAK_STATE_DIR"] == str(frozen / ".local/aggregate-state") and environment["SIGHTBREAK_BACKEND_PYTHON"] == "/workspace/sightbreak/.venv/bin/python", "actual declared private state and backend interpreter selectors")
        check(engine["path"] == "/workspace/tools/godot-4.7.2/Godot_v4.7.2-stable_linux.x86_64" and engine["sha256"] == pre_run["engine_sha256"] == sha(Path(engine["path"]).read_bytes()), "actual engine before/after equals independently pinned pre-run bytes")
        check(preflight["processes"] == preflight["listeners"] == [], "original preflight records no checkout engine/fixed listeners")
        check(cleanup["remaining"] == cleanup["listeners"] == [], "original supervisor terminal session/checkout/fixed-port scan empty")
        check(cleanup["scope"] == "original session and Godot argv bound to frozen checkout; not arbitrary escaped descendants", "supervisor cleanup scope states its actual boundary")
        check(bool(observed) and len({(r["pid"], r["start_ticks"]) for r in observed}) == len(observed), "original sampled PID/start identities unique and retained")

        logs = Path(re.findall(r"^Validation completed\. Logs: (.+)$", (run / "aggregate.log").read_text(), re.M)[0])
        log_paths = list(logs.rglob("*.log"))
        smoke = Path(re.findall(r"^NETWORK_LOG_DIR=(.+)$", (run / "aggregate.log").read_text(), re.M)[0])
        log_paths += list(smoke.glob("*.log"))
        ready_ports = {int(p) for path in log_paths for p in re.findall(r"SIGHTBREAK_SERVER_READY port=(\d+)", path.read_text())}
        fixed_ports = {27991, 29900, 29901, 29902, 33540, 33541, 33542, 33543}
        ports = fixed_ports | ready_ports
        owned = {(r["pid"], r["start_ticks"]) for r in observed}
        owned.add((independent_outer["pid"], independent_outer["start_ticks"]))
        found, reused, session_members = [], [], []
        for path in Path("/proc").iterdir():
            if not path.name.isdigit():
                continue
            try:
                stat = (path / "stat").read_text()
                values = stat[stat.rindex(")") + 2:].split()
                pid, pgid, sid, ticks = int(path.name), int(values[2]), int(values[3]), int(values[19])
                comm = (path / "comm").read_text().strip()
                argv = (path / "cmdline").read_bytes()
                row = {"pid": pid, "ppid": int(values[1]), "pgid": pgid, "sid": sid, "start_ticks": ticks, "state": values[0], "comm": comm, "argv_sha256": sha(argv)}
                if sid in {command["pid"], independent_outer["sid"]} or pgid in {command["pgid"], independent_outer["pgid"]}:
                    session_members.append(row)
                if (pid, ticks) in owned or pid == command["pid"] or comm.lower().startswith("godot") and os.fsencode(str(frozen)) in argv:
                    found.append(row)
                elif pid in {r[0] for r in owned}:
                    reused.append(row)
            except (OSError, ValueError, IndexError):
                pass
        sockets = []
        for family in ("tcp", "tcp6", "udp", "udp6"):
            for line in Path("/proc/net", family).read_text().splitlines()[1:]:
                c = line.split()
                port = int(c[1].split(":")[1], 16)
                if port in ports and (family.startswith("udp") or c[3] == "0A"):
                    sockets.append({"family": family, "port": port, "state": c[3], "inode": c[9]})
        observation = {"observed_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "session_or_group_members": session_members,
                       "matching_observed_identity_or_checkout_engine": found, "reused_pids_with_different_start": reused,
                       "matching_bound_sockets": sockets, "checked_ports": sorted(ports), "original_ready_ports": sorted(ready_ports),
                       "aggregate_pid": command["pid"], "aggregate_pgid": command["pgid"], "observed_identities": len(owned),
                       "outer_pid": independent_outer["pid"], "outer_pgid": independent_outer["pgid"],
                       "scope": "Read-only actual original inner/outer session/group, sampled PID/start, checkout-bound Godot and fixed/ready-port scan. No signal sent. No arbitrary escaped-descendant coverage claim."}
        check(not session_members and not found and not sockets, "independent actual scoped process/listener observation empty")
        (out / "process-after.json").write_text(json.dumps(observation, indent=2) + "\n")
        report.update(source=before, command=command, result=result, engine=engine, preflight=preflight,
                      cleanup=cleanup, observed_processes=observed, current_observation=observation,
                      outer_live=outer, independent_outer_live=independent_outer,
                      launch_input_count=len(launch_inputs), independent_content_sha256=content.hexdigest(),
                      independent_validation_sha256=validation.hexdigest(),
                      outer_exit_scope="The parent's actual run_aggregate.py tool/session exit is reviewed separately; result.json records the inner aggregate exit.")
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
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--expected-source", required=True)
    parser.add_argument("--output", type=Path, required=True)
    raise SystemExit(main(parser.parse_args()))
