"""Restore only the already-recorded dedicated portable cluster; retain all diagnostics."""
from pathlib import Path
import json
import subprocess
import time
import psycopg

base = Path("C:/Users/blith/AppData/Local/Temp/opencode/sightbreak-backend-trade-env")
out = Path(__file__).resolve().parent / "native-journal-only-resume"
out.mkdir(exist_ok=False)
(out / "restore-controller.py").write_bytes(Path(__file__).read_bytes())
command = [str(base / "pgsql/bin/pg_ctl.exe"), "-D", str(base / "data"),
           "-l", str(out / "postgres.log"), "-o",
           "-h 127.0.0.1 -p 55439 -c max_connections=30 -c shared_buffers=32MB",
           "-t", "30", "-w", "start"]
record = dict(command=command, started_wall_ns=time.time_ns(),
              preceding_pg_ctl_status="no server running (retained tool result after session restart)",
              existing_postmaster_pid=(base / "data/postmaster.pid").read_text(),
              existing_postmaster_opts=(base / "data/postmaster.opts").read_text())

def save():
    (out / "restoration.json").write_text(json.dumps(record, indent=2, default=str) + "\n", encoding="utf-8")

save()
try:
    with (out / "pg_ctl.stdout.txt").open("wb") as stdout, (out / "pg_ctl.stderr.txt").open("wb") as stderr:
        process = subprocess.Popen(command, stdout=stdout, stderr=stderr, stdin=subprocess.DEVNULL)
        record["controller_pid"] = process.pid
        save()
        record["returncode"] = process.wait(timeout=40)
    if record["returncode"]:
        raise RuntimeError("Recorded-cluster restoration failed; inspect retained logs")
    with psycopg.connect(host="127.0.0.1", port=55439, user="sightbreak", password="sightbreak_local_only",
                         dbname="postgres", connect_timeout=5) as db:
        record["health"] = db.execute("SELECT version(), inet_server_port(), pg_backend_pid(), "
                                     "current_setting('data_directory'), pg_postmaster_start_time()").fetchone()
        record["failed_attempt_database_absent"] = db.execute(
            "SELECT NOT EXISTS (SELECT 1 FROM pg_database WHERE datname=%s)",
            ("sightbreak_receipt_dc2c4fa65cf1f39b_test",)).fetchone()[0]
except Exception as error:
    record["error"] = f"{type(error).__name__}: {error}"
    raise
finally:
    record["finished_wall_ns"] = time.time_ns()
    save()
    print(json.dumps(record, indent=2, default=str), flush=True)
