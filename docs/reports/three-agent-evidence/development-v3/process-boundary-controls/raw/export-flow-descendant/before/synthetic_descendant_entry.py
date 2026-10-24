"""Synthetic token-bound worker with a failing CPython descendant, no native work."""
from pathlib import Path
import argparse
import json
import os
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE / "source/scripts"), r"C:\Users\blith\AppData\Local\Temp\opencode\sightbreak-v3\scripts"]
import export_flow


def main(supervised=False):
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout", type=float, required=True)
    args = parser.parse_args()
    out = export_flow.prepare_flow_output(args.output, supervised)
    case = out.parent
    body = ("from pathlib import Path; import json,os,time; "
            f"Path({str(case / 'child-started.json')!r}).write_text(json.dumps({{'pid':os.getpid()}})); "
            "time.sleep(1.5); print('ERROR: token-bound worker left failing descendant',flush=True); "
            f"Path({str(case / 'child-finished.txt')!r}).write_text('finished'); raise SystemExit(7)")
    child = subprocess.Popen([sys.executable, "-B", "-c", body])
    while not (case / "child-started.json").exists():
        time.sleep(.005)
    print("SYNTHETIC worker validated owning token:", bool(os.environ.get(export_flow.TOKEN_ENV)), flush=True)
    (out / "results.json").write_text(json.dumps({"passed": True, "synthetic_control_not_native_evidence": True}))


if __name__ == "__main__":
    raise SystemExit(export_flow.entry(main, __file__))
