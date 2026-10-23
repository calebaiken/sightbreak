#!/usr/bin/env python3
"""Review late outer-exit and actual journal-child receipts without runtime work."""
import argparse
import datetime as dt
import json
from pathlib import Path


def main(args):
    run = args.run.resolve()
    out = args.output.resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    result = json.loads((run / "result.json").read_text())
    outer = json.loads((run / "outer-exit.json").read_text())
    live = json.loads((run / "outer-live.json").read_text())
    observed = json.loads((run / "observed-processes.json").read_text())
    failures = []
    checks = 0

    def check(value, label):
        nonlocal checks
        checks += 1
        if not value:
            failures.append(label)

    check(outer["tool_exit_code"] == 0 and outer["tool_session_id"] == live["tool_session_id"] == 28337, "original outer tool session exits zero")
    check(outer["outer_pid"] == live["outer_pid"] == 13394 and outer["outer_start_ticks"] == live["outer_start_ticks"] == 528612 and outer["source_commit"] == args.expected_source, "outer exit bound to original live identity and exact source")
    expected_tool = dict(exit_code=0, failure=None, seconds=result["seconds"], source_unchanged=True, remaining=0, listeners=0)
    check(json.loads(outer["tool_output"]) == expected_tool, "outer actual output agrees with every inner completion predicate")
    check(dt.datetime.fromisoformat(outer["observed_utc"]) >= dt.datetime.fromisoformat(result["completed_utc"]), "outer exit receipt follows inner completion")
    check(not Path("/proc", str(outer["outer_pid"])).exists(), "actual original outer PID absent")
    raw = args.journal.read_text()
    streams = [json.loads(line.split(" ", 1)[1]) for line in raw.splitlines() if line.startswith("COMPETING_PROCESS ")]
    children = [json.loads(line.split(" ", 1)[1]) for stream in streams for part in stream for line in part.splitlines() if line.startswith("OWNER_BLOCKED ")]
    check(len(children) == 1, "one actual competing journal child marker")
    if children:
        child = children[0]
        check(all(type(child[k]) is int and child[k] == 22 for k in ("claim", "clear", "stage")) and child["unchanged"] is True, "actual competing child blocks all three writes with unchanged receipt")
        samples = [row for row in observed if row["pid"] == child["pid"]]
        check(len(samples) == 1 and samples[0]["sid"] == result["pid"] and samples[0]["comm"].lower().startswith("godot"), "actual printed child bound to sampled native PID/start and original session")
        check(not Path("/proc", str(child["pid"])).exists(), "actual journal child PID absent")
    report = {"observed_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "passed": not failures,
              "checks": checks, "failures": failures, "outer_exit": outer,
              "journal_children": children, "journal_child_observed_identities": samples if children else [],
              "scope": "Pure original-receipt and actual terminal PID review; no signal sent or native work launched."}
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ("passed", "checks", "failures")}))
    return int(bool(failures))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--journal", type=Path, required=True)
    parser.add_argument("--expected-source", required=True)
    parser.add_argument("--output", type=Path, required=True)
    raise SystemExit(main(parser.parse_args()))
