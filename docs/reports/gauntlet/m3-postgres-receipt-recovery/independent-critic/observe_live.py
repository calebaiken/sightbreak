"""Bounded independent selected-field live SQL observation; root releases runtime."""
import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from uuid import uuid4


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("marker", type=Path)
    parser.add_argument("--source", required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True, mode=0o700)
    marker = json.loads(args.marker.read_text())
    phase, run = marker["phase"], marker["run"]
    assert phase in ("pre_original", "post_final_refresh")
    assert re.fullmatch(r"sightbreak-pg-receipt-[a-f0-9]{12}", run)
    assert re.fullmatch(r"[a-f0-9]{64}", marker["container_id"])
    assert marker["database"] == "sb_receipt_" + run.rsplit("-", 1)[1] + "_test"
    assert marker["role"] == "sb_receipt" and marker["source_commit"] == args.source
    assert marker["label_key"] == "io.sightbreak.receipt-run" and marker["label_value"] == run
    env = dict(os.environ)
    for key in ("DOCKER_HOST", "DOCKER_CONTEXT", "DOCKER_TLS", "DOCKER_TLS_VERIFY", "DOCKER_CERT_PATH"):
        env.pop(key, None)
    records = []
    def command(label, argv):
        start = dict(requested_monotonic_ns=time.monotonic_ns(), requested_wall_ns=time.time_ns())
        result = subprocess.run(argv, env=env, cwd=args.candidate, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
        row = dict(label=label, argv=argv, **start, completed_monotonic_ns=time.monotonic_ns(), completed_wall_ns=time.time_ns(),
                   exit=result.returncode, stdout=result.stdout, stderr=result.stderr)
        records.append(row)
        (args.out / (phase + "-commands.json")).write_text(json.dumps(records, indent=2) + "\n")
        assert result.returncode == 0, label + " failed; retained selected command output"
        return result.stdout, row
    source, _ = command("source", ["git", "rev-parse", "HEAD"])
    status, _ = command("clean-source", ["git", "status", "--porcelain", "--untracked-files=all"])
    assert source.strip() == args.source and not status
    sys.path.insert(0, str(args.candidate / "scripts"))
    from postgres_receipt_oracle import BUSINESS_SQL, verify_market, verify_market_fixture, verify_sql_witness
    sql_path = Path(marker["sql_file"])
    assert sql_path.resolve() == (args.marker.parent / "read-only-business.sql").resolve()
    assert sql_path.read_text() == BUSINESS_SQL + ";\n"
    docker = ["docker", "--host=unix:///var/run/docker.sock"]
    command("managed-daemon", docker + ["info", "--format", "{{json .ServerVersion}}\n{{json .OSType}}\n{{json .DockerRootDir}}"])
    raw, _ = command("container", docker + ["inspect", "--format", "{{json .Id}}\n{{json .Name}}\n{{json .Image}}\n{{json .Config.Labels}}\n{{json .NetworkSettings.Ports}}\n{{json .State.Pid}}\n{{json .Mounts}}", marker["container_id"]])
    container = dict(zip(("id", "name", "image", "labels", "ports", "pid", "mounts"), [json.loads(v) for v in raw.splitlines()]))
    assert container["id"] == marker["container_id"] and container["name"] == "/" + run
    assert container["labels"][marker["label_key"]] == run and container["labels"]["io.sightbreak.owner"] == "client_result_recovery_builder"
    mounts = container["mounts"]
    assert len(mounts) == 1 and mounts[0]["Name"] == run + "-data" and mounts[0]["Type"] == "volume"
    assert mounts[0]["Destination"] == "/var/lib/postgresql/data" and mounts[0]["RW"] is True
    ports = container["ports"]["5432/tcp"]
    assert len(ports) == 1 and ports[0]["HostIp"] == "127.0.0.1" and ports[0]["HostPort"] != "55432"
    raw, _ = command("volume", docker + ["volume", "inspect", "--format", "{{json .Name}}\n{{json .Labels}}", run + "-data"])
    name, labels = [json.loads(v) for v in raw.splitlines()]
    assert name == run + "-data" and labels[marker["label_key"]] == run and labels["io.sightbreak.owner"] == "client_result_recovery_builder"
    image = "postgres:17@sha256:2d2b8998d31037bf721cfdf764d76ba74171b4fab3431b7f72c27c56ddbdf9e3"
    raw, _ = command("pinned-image", docker + ["image", "inspect", "--format", "{{json .Id}}\n{{json .RepoDigests}}", image])
    image_id, digests = [json.loads(v) for v in raw.splitlines()]
    assert container["image"] == image_id and "postgres@sha256:" + image.rsplit("sha256:", 1)[1] in digests
    query = "SELECT jsonb_build_object('read_only',current_setting('transaction_read_only'),'snapshot',(" + BUSINESS_SQL + "))"
    raw, clocks = command("read-only-business-sql", docker + ["exec", "-e", "PGOPTIONS=-c default_transaction_read_only=on -c statement_timeout=5000", marker["container_id"],
                         "psql", "-h", "/var/run/postgresql", "-X", "-qAt", "--set=ON_ERROR_STOP=1", "-U", marker["role"], "-d", marker["database"], "-c", query])
    parsed = json.loads(raw)
    assert parsed["read_only"] == "on"
    snapshot = dict(parsed["snapshot"], phase=phase, query_id="independent:" + run + ":" + phase + ":" + uuid4().hex,
                    **{k: clocks[k] for k in ("requested_monotonic_ns", "requested_wall_ns", "completed_monotonic_ns", "completed_wall_ns")})
    verify_sql_witness(snapshot, phase, marker["event"])
    fixture_out = args.marker.parent.parent
    identity = json.loads((fixture_out / "identity-before-migration.json").read_text())
    assert snapshot["database"] == marker["database"] and snapshot["role"] == marker["role"]
    assert snapshot["system_identifier"] == marker["system_identifier"] == identity["system_identifier"]
    assert datetime.fromisoformat(snapshot["postmaster_started"]) == datetime.fromisoformat(identity["postmaster_started"])
    spec = json.loads((fixture_out / "business-spec.json").read_text())
    if phase == "pre_original":
        verify_market_fixture(snapshot, spec)
    else:
        before = json.loads((args.out / "pre_original-witness.json").read_text())["snapshot"]
        events = [json.loads(line) for line in (fixture_out / "timeline.jsonl").read_text().splitlines()]
        original = next(e["response"] for e in events if e["phase"] == "market_1_backend_200")
        refreshed = next(e for e in events if e["phase"] == "final_recovery_response_and_refresh_complete")
        verify_sql_witness(snapshot, phase, refreshed)
        verify_market(before, snapshot, spec, original)
    witness = dict(source=args.source, marker=marker, container=container, sql_sha256=hashlib.sha256(BUSINESS_SQL.encode()).hexdigest(), snapshot=snapshot)
    (args.out / (phase + "-witness.json")).write_text(json.dumps(witness, indent=2) + "\n")
    release = Path(marker["release_marker"])
    assert release.resolve() == (args.marker.parent / (phase + ".release.json")).resolve()
    release.write_text(json.dumps(dict(run=run, phase=phase, status="observed")) + "\n")
    print(json.dumps(dict(phase=phase, run=run, status="observed", query_id=snapshot["query_id"], out=str(args.out))), flush=True)


if __name__ == "__main__":
    main()
