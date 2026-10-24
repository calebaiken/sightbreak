#!/usr/bin/env python3
"""Full native EconomyUI -> real HTTP response-contract comparison.

Uses a committed game archive and an explicitly inventoried import cache. The
HTTP fixture supplies complete backend-serialized item examples and controlled
response corruptions. It is not a PostgreSQL/economy or crash-durability test.
Run this identical frozen harness against the held and proposed revisions.
"""
from __future__ import annotations

import argparse
import base64
import copy
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import threading
import time
import uuid
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = Path(__file__).resolve().parent
OWNER = "10000000-0000-4000-8000-000000000001"


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def inventory(root, exclude_cache=False):
    return {p.relative_to(root).as_posix(): digest(p) for p in sorted(root.rglob("*"))
            if p.is_file() and (not exclude_cache or ".godot" not in p.relative_to(root).parts)}


def journal(path):
    path = Path(path)
    raw = path.read_bytes() if path.is_file() else b""
    return {"exists": path.is_file(), "bytes": len(raw), "base64": base64.b64encode(raw).decode()}


def cases(world):
    """Mutations target the existing backend contract, independently of UI helpers."""
    items = world["inventory"]["items"]
    key = copy.deepcopy(next(i for i in items if i["kind"] == "key"))
    case = copy.deepcopy(next(i for i in items if i["kind"] == "case"))
    reward = copy.deepcopy(next(i for i in items if i["definition_id"] == "obsidian_common"))
    listing = copy.deepcopy(world["market"]["listings"][0])
    purchase = copy.deepcopy(listing["item"])
    for item in (key, case, reward, purchase):
        item.update(reserved=False, trade_eligible=True, marketplace_eligible=True)
    # Minted case reward identity differs from the case and key consumed by this call.
    reward["id"] = "d0000000-0000-4000-8000-000000000001"
    templates = {
        "store_key": ("/store/buy", {"definition_id": key["definition_id"]}, {"item": key, "credits": 1600}),
        "store_case": ("/store/buy", {"definition_id": case["definition_id"]}, {"item": case, "credits": 1600}),
        "case": ("/cases/open", {"case_id": case["id"], "key_id": key["id"]},
                 {"item": reward, "roll": 123, "table_version": "1"}),
        "market": ("/market/" + listing["id"] + "/buy", {"expected_price": 400},
                   {"item": purchase, "credits": 1600, "fee": 12}),
    }
    result = []

    def add(name, route="store_key", valid=False, transform=None, context=True, payload_change=None):
        path, payload, response = copy.deepcopy(templates[route])
        if transform:
            transform(response)
        if payload_change:
            payload_change(payload)
        result.append(dict(name=name, path=path, payload=payload, response=response, valid=valid,
                           inventory=copy.deepcopy(items) if context else [],
                           listings=[copy.deepcopy(listing)] if context else [],
                           account={**world["account"], "credits": 999999},
                           catalog=copy.deepcopy(world["catalog"])))

    for route in templates:
        add("complete_" + route, route, True)
    add("historical_case_without_inventory", "case", True,
        lambda r: r.update(table_version="historical-version"), context=False)
    add("historical_market_without_listing", "market", True, context=False)
    add("legacy_price_omitted", "market", True, payload_change=lambda p: p.pop("expected_price"))
    add("legacy_price_null", "market", True, payload_change=lambda p: p.update(expected_price=None))
    add("price_one_zero_fee", "market", True, lambda r: r.update(fee=0),
        payload_change=lambda p: p.update(expected_price=1))
    add("additional_response_fields", valid=True, transform=lambda r: r.update(future_field="allowed"))
    add("additional_item_fields", valid=True, transform=lambda r: r["item"].update(future_field="allowed"))
    add("valid_leap_date", valid=True, transform=lambda r: r["item"].update(acquired_at="2024-02-29T23:59:59Z"))
    add("sol_partial_market", "market", transform=lambda r: r.update(item={"id": "unrelated"}, credits=0, fee=0))
    add("sol_partial_case", "case", transform=lambda r: r.update(item={"id": "partial"}, roll=0, table_version="anything"))
    for field in key:
        add("missing_item_" + field, transform=lambda r, f=field: r["item"].pop(f))
        add("null_item_" + field, transform=lambda r, f=field: r["item"].update({f: None}))
    for field, value in [
        ("id", "partial"), ("id", "g0000000-0000-4000-8000-000000000001"),
        ("definition_id", "x" * 101), ("rarity", "x" * 25), ("variant", "x" * 25),
        ("name", "  "), ("collection", ""), ("kind", "anything"),
        ("pattern_seed", -1), ("pattern_seed", 2147483648), ("pattern_seed", 1.5), ("pattern_seed", True),
        ("wear", -0.01), ("wear", 1.01), ("wear", "0.1"), ("wear", True),
        ("reserved", True), ("reserved", 0), ("trade_eligible", False), ("marketplace_eligible", False),
        ("acquired_at", "2026-02-30T08:00:00+00:00"), ("acquired_at", "2026-01-01T00:00:00+25:00"),
        ("acquired_at", "yesterday"),
    ]:
        add("invalid_" + field + "_" + str(len(result)), transform=lambda r, f=field, v=value: r["item"].update({f: v}))
    add("item_array", transform=lambda r: r.update(item=[]))
    add("missing_item", transform=lambda r: r.pop("item"))
    add("wrong_store_definition", transform=lambda r: r.update(item=copy.deepcopy(case)))
    add("case_reuses_case_id", "case", transform=lambda r: r["item"].update(id=case["id"]))
    add("case_reuses_key_id", "case", transform=lambda r: r["item"].update(id=key["id"]))
    add("case_wrong_kind", "case", transform=lambda r: r.update(item=copy.deepcopy(key)))
    add("case_wrong_collection", "case", transform=lambda r: r["item"].update(collection="Blacksite"))
    add("case_wrong_definition", "case", transform=lambda r: r["item"].update(definition_id="obsidian_rare"))
    add("market_wrong_known_item", "market", transform=lambda r: r["item"].update(id=reward["id"]))
    add("market_fee_exceeds_consent", "market", transform=lambda r: r.update(fee=401))
    for route, field in [("store_key", "credits"), ("market", "credits"), ("market", "fee"), ("case", "roll")]:
        add(route + "_missing_" + field, route, transform=lambda r, f=field: r.pop(f))
        for label, value in [("null", None), ("negative", -1), ("fraction", 0.5), ("boolean", True), ("text", "0")]:
            add(route + "_" + field + "_" + label, route, transform=lambda r, f=field, v=value: r.update({f: v}))
    add("case_roll_above_limit", "case", transform=lambda r: r.update(roll=10000))
    for label, value in [("blank", "  "), ("null", None), ("number", 1)]:
        add("case_table_version_" + label, "case", transform=lambda r, v=value: r.update(table_version=v))
    add("case_missing_table_version", "case", transform=lambda r: r.pop("table_version"))
    expanded = []
    for row in result:
        for mode in ("initial", "recovery"):
            item = copy.deepcopy(row)
            item["id"] = row["name"] + "__" + mode
            item["mode"] = mode
            item["payload"]["idempotency_key"] = str(uuid.uuid5(uuid.NAMESPACE_URL, item["id"]))
            expanded.append(item)
    return expanded


def run(args):
    args.out.mkdir(parents=True, exist_ok=False)
    revision = git(args.source, "rev-parse", args.revision)
    project = args.out / "source"
    project.mkdir()
    archive = args.out / "game.zip"
    subprocess.run(["git", "-C", str(args.source), "archive", "--format=zip", "--output=" + str(archive), revision, "game"], check=True)
    with zipfile.ZipFile(archive) as zipped:
        zipped.extractall(project)
    source_before = inventory(project, True)
    write(args.out / "source-before.json", source_before)
    cache_before = inventory(args.cache)
    shutil.copytree(args.cache, project / "game/.godot")
    assert inventory(project / "game/.godot") == cache_before
    write(args.out / "cache.json", cache_before)
    probe = args.out / "receipt_response_probe.gd"
    shutil.copyfile(HERE / probe.name, probe)
    shutil.copyfile(Path(__file__), args.out / Path(__file__).name)
    fixture = args.source / "game/tests/fixtures/backend_world.json"
    world = json.loads(fixture.read_text(encoding="utf-8"))["world"]
    entries = cases(world)
    if args.limit:
        entries = entries[:args.limit]
    for entry in entries:
        directory = args.out / "cases" / entry["id"]
        directory.mkdir(parents=True)
        entry.update(journal=str(directory / "journal.json"), output=str(directory / "native.json"))
    write(args.out / "cases.json", entries)
    by_key = {e["payload"]["idempotency_key"]: e for e in entries}
    calls = []
    counts = {}
    lock = threading.Lock()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def do_GET(self):
            value = {"/me": world["account"], "/inventory": world["inventory"],
                     "/catalog": world["catalog"], "/loadout": {"slots": {}}}.get(self.path, {})
            self.respond(200, value)

        def do_POST(self):
            raw = self.rfile.read(int(self.headers.get("Content-Length", "0")))
            body = json.loads(raw)
            entry = by_key[body["idempotency_key"]]
            with lock:
                number = counts.get(entry["id"], 0) + 1
                counts[entry["id"]] = number
            status = 500 if entry["mode"] == "recovery" and number == 1 else 200
            value = {"detail": "Injected unknown prior result"} if status == 500 else entry["response"]
            row = dict(case=entry["id"], number=number, path=self.path, body=body, raw=raw.decode(),
                       status=status, response=value, staged=journal(entry["journal"]), time_ns=time.time_ns())
            with lock:
                calls.append(row)
                with (args.out / "http.jsonl").open("a", encoding="utf-8") as file:
                    file.write(json.dumps(row) + "\n")
            self.respond(status, value)

        def respond(self, status, value):
            raw = json.dumps(value).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    native_cases = [{k: v for k, v in e.items() if k not in {"response", "valid", "name"}} for e in entries]
    config = args.out / "config.json"
    write(config, {"url": "http://127.0.0.1:" + str(server.server_port), "owner": OWNER, "cases": native_cases})
    env = os.environ.copy()
    env["SIGHTBREAK_RESPONSE_FIXTURE"] = str(config)
    command = [str(args.godot), "--headless", "--path", str(project / "game"), "--script", str(probe)]
    identity = dict(revision=revision, game_tree=git(args.source, "rev-parse", revision + ":game"),
                    workspace_status=git(args.source, "status", "--porcelain"), platform=platform.platform(),
                    harness_sha256=digest(__file__), probe_sha256=digest(probe), fixture_sha256=digest(fixture),
                    executable_sha256=digest(args.godot), command=command, source_archive_sha256=digest(archive))
    write(args.out / "identity.json", identity)
    try:
        with (args.out / "native.stdout.txt").open("wb") as stdout, (args.out / "native.stderr.txt").open("wb") as stderr:
            completed = subprocess.run(command, env=env, stdout=stdout, stderr=stderr, timeout=240)
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
        write(args.out / "source-after.json", inventory(project, True))
    stdout = (args.out / "native.stdout.txt").read_text(encoding="utf-8")
    stderr = (args.out / "native.stderr.txt").read_text(encoding="utf-8")
    observations = {row["id"]: row for row in [json.loads(line.removeprefix("RESPONSE_OBSERVATION "))
                    for line in stdout.splitlines() if line.startswith("RESPONSE_OBSERVATION ")]}
    rows = []
    for entry in entries:
        found = observations.get(entry["id"], {})
        requests = [r for r in calls if r["case"] == entry["id"]]
        structural = bool(found) and len(requests) == (2 if entry["mode"] == "recovery" else 1)
        structural = structural and all(r["path"] == entry["path"] and r["body"] == entry["payload"] and r["staged"]["exists"] for r in requests)
        if found:
            structural = structural and json.loads(Path(entry["output"]).read_text()) == found and journal(entry["journal"]) == found["after"]
            if entry["mode"] == "recovery":
                structural = structural and found["seed_result"].get("_uncertain") is True and found["before"] == requests[-1]["staged"]
        state = bool(found) and not found["busy"] and not found["storage_error"]
        if entry["valid"]:
            state = state and found["result"] == entry["response"] and not found["pending"] and not found["after"]["exists"] and not found["retry_visible"]
        else:
            state = state and found["result"].get("_uncertain") is True and found["result"].get("_outcome") == "unknown"
            state = state and found["pending"].get("payload") == entry["payload"] and found["retry_visible"] and found["after"] == requests[-1]["staged"]
        rows.append(dict(id=entry["id"], positive=entry["valid"], capture_pass=bool(structural), contract_pass=bool(state)))
    summary = dict(identity=identity, cases=len(rows), capture_pass=all(r["capture_pass"] for r in rows),
                   contract_passes=sum(r["contract_pass"] for r in rows), rows=rows, exit=completed.returncode,
                   source_unchanged=inventory(project, True) == source_before,
                   engine_errors=any(word in stdout + stderr for word in ["SCRIPT ERROR", "ERROR:", "ObjectDB instances leaked", "resources still in use"]))
    write(args.out / "summary.json", summary)
    print(json.dumps({k: v for k, v in summary.items() if k not in {"rows", "identity"}}, indent=2))
    assert completed.returncode == 0 and summary["capture_pass"] and summary["source_unchanged"] and not summary["engine_errors"]
    return 0 if summary["contract_passes"] == summary["cases"] else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path.cwd())
    parser.add_argument("--revision", required=True)
    parser.add_argument("--godot", type=Path, required=True)
    parser.add_argument("--cache", type=Path, default=Path("game/.godot"))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=0, help="Preflight only; accepted comparison uses all cases")
    args = parser.parse_args()
    for name in ("source", "godot", "cache", "out"):
        setattr(args, name, getattr(args, name).resolve())
    raise SystemExit(run(args))
