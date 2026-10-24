"""Read-only review runner; no native engine, export, or campaign is invoked."""
from pathlib import Path
import os
import subprocess
import sys

ROOT = Path(r"C:\Users\blith\AppData\Local\Temp\opencode\sightbreak-v3")
OUT = Path(__file__).resolve().parent
temp = OUT / "unit-temp"
temp.mkdir(exist_ok=True)
env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", TEMP=str(temp), TMP=str(temp))
command = [sys.executable, "-B", "-m", "unittest", "-v",
           "test_build_manifest", "test_validate_matrix", "test_offline_hud", "test_export_ui"]
completed = subprocess.run(command, cwd=ROOT / "scripts", env=env, capture_output=True)
(OUT / "allowed-unittests.stdout.txt").write_bytes(completed.stdout)
(OUT / "allowed-unittests.stderr.txt").write_bytes(completed.stderr)
(OUT / "allowed-unittests.exit.txt").write_text(str(completed.returncode) + "\n")
print(completed.stdout.decode(errors="replace"))
print(completed.stderr.decode(errors="replace"))
raise SystemExit(completed.returncode)
