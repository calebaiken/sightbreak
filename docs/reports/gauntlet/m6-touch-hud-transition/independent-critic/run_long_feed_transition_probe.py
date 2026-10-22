#!/usr/bin/env python3
"""Independent source-only adversarial probe using maintained native isolation."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / "scripts"))
from run_native_regressions import NativeSceneSuites, inventory

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
probe = Path(__file__).with_name("long_feed_transition_probe.gd")
try:
    with NativeSceneSuites(args.output) as runner:
        runner.report["source_commit"] = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        runner.report["probe_sha256"] = hashlib.sha256(probe.read_bytes()).hexdigest()
        runner.report["scope"] = "Independent headless long-name feed geometry; no native rendering, export or physical-input acceptance"
        runner.configure("long_feed_transition")
        before = runner.probe("before-long-feed-transition")
        if before["profile_exists"] or before["diagnostics_exist"]:
            raise RuntimeError("Fresh isolated state required")
        receipt = runner.execute("long-feed-transition", ["--headless", "--script", str(probe), "--", "--receipt=" + str(runner.output / "geometry.json")], 120)
        receipt.update(before=before, after=runner.probe("after-long-feed-transition"))
        receipt["produced_files_sha256"] = inventory(Path(receipt["after"]["user_data_dir"]))
        runner.receipts.append(receipt)
        (runner.output / "results.json").write_text(json.dumps(runner.receipts, indent=2) + "\n")
        if receipt["exit"] or not receipt["clean_log"]:
            raise RuntimeError("Independent long-feed transition probe failed; raw output retained")
except RuntimeError as error:
    print(str(error), file=sys.stderr)
    sys.exit(1)
