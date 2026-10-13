#!/usr/bin/env python3
"""Native UI -> real HTTP -> disposable PostgreSQL ownership/ledger regression.

Run using .venv/bin/python after backend/dev-db.sh. Fictional balances are seeded
only in a uniquely named disposable *_test database. No value enters the dev DB.
"""
from pathlib import Path
import json
import os
import secrets
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request

import psycopg
from psycopg import sql

ROOT = Path(__file__).resolve().parents[1]
DATABASE = "sightbreak_native_" + secrets.token_hex(5) + "_test"
CONNECT = dict(host="127.0.0.1", port=55432, user="sightbreak", password="sightbreak_local_only")


def main():
    assert DATABASE.startswith("sightbreak_native_") and DATABASE.endswith("_test")
    with psycopg.connect(**CONNECT, dbname="postgres", autocommit=True) as connection:
        connection.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(DATABASE)))
    service = None
    try:
        os.environ["DATABASE_URL"] = "postgresql+psycopg://sightbreak:sightbreak_local_only@127.0.0.1:55432/" + DATABASE
        sys.path[:0] = [str(ROOT / "backend"), str(ROOT / "backend/tests")]
        from app import Base, engine
        from test_economy import player, item
        Base.metadata.create_all(engine)
        with engine.begin() as connection:
            for migration in sorted((ROOT / "backend/migrations").glob("*.sql")):
                connection.exec_driver_sql(migration.read_text())
        a, ha = player(2000)
        b, hb = player(2000)
        fixture = dict(a=a, b=b, token_a=ha["Authorization"][7:], token_b=hb["Authorization"][7:],
                       case=item(a, "obsidian_case"), key=item(a, "key"), skin=item(a, "obsidian_rare"))
        # Let the OS select an unused loopback port. Startup health verifies the
        # resulting API before any request with fixture credentials is sent.
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            port = listener.getsockname()[1]
        fixture["api_url"] = "http://127.0.0.1:" + str(port)
        with tempfile.TemporaryDirectory(prefix="sightbreak-native-qa-") as folder, tempfile.TemporaryFile(mode="w+") as log:
            fixture_path = Path(folder) / "fixture.json"
            fixture_path.write_text(json.dumps(fixture))
            fixture_path.chmod(0o600)
            environment = os.environ.copy()
            environment["SIGHTBREAK_NATIVE_FIXTURE"] = str(fixture_path)
            environment["SIGHTBREAK_STATE_DIR"] = str(Path(folder) / "state")
            service = subprocess.Popen([sys.executable, "-m", "uvicorn", "app:app", "--app-dir", str(ROOT / "backend"),
                                        "--host", "127.0.0.1", "--port", str(port)], cwd=ROOT, env=environment, stdout=log, stderr=log)
            for _ in range(100):
                if service.poll() is not None:
                    raise RuntimeError("Isolated native QA API exited")
                try:
                    with urllib.request.urlopen(fixture["api_url"] + "/health", timeout=0.5) as response:
                        if json.load(response)["status"] == "ok":
                            break
                except OSError:
                    time.sleep(0.1)
            else:
                raise RuntimeError("Isolated native QA API did not become healthy")
            result = subprocess.run([str(ROOT / "scripts/godot.sh"), "--headless", "--script", "res://tests/native_economy_test.gd"],
                                    cwd=ROOT, env=environment, text=True, capture_output=True, timeout=90)
            print(result.stdout, end="")
            print(result.stderr, end="", file=sys.stderr)
            if result.returncode or "ERROR:" in result.stderr or "14/14 passed" not in result.stdout:
                raise RuntimeError("Native economy regression failed")
            service.terminate()
            service.wait(timeout=10)
            service = None
        engine.dispose()
    finally:
        if service is not None:
            service.terminate()
            service.wait(timeout=10)
        with psycopg.connect(**CONNECT, dbname="postgres", autocommit=True) as connection:
            connection.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(DATABASE)))


if __name__ == "__main__":
    main()
