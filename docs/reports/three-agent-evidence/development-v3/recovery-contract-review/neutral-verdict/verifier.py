"""Offline outcome-only verifier. Reads only the fixed NEUTRAL packet; no runtime replay.
All observations are consistency checks on retained unsigned captures, not release gates.
Usage: the explicitly approved Python 3.13.15 -I -B verifier.py
"""
import collections
import copy
import datetime
import hashlib
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(r"C:\Users\blith\AppData\Local\Temp\opencode\sol-recovery-review-20261022T205225Z\NEUTRAL")
PIN = "746561c7caf5a57d53fcf52fca2d018cca4b044218ac6fa4190362eea7502021"
TABLES = {"audit", "items", "ledger", "listings", "loadouts", "operations", "players", "rewards", "trades"}
SNAMES = ["01-before", "02-committed-before-kill", "03-after-kill", "04-after-recovery", "05-after-second-restart"]

def sha(b):
    return hashlib.sha256(b).hexdigest()

def utc_ns(n):
    return datetime.datetime.fromtimestamp(n / 1e9, datetime.timezone.utc).isoformat()

def time_ns(s):
    dt = datetime.datetime.fromisoformat(s)
    epoch = datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc)
    d = dt.astimezone(datetime.timezone.utc) - epoch
    return (d.days * 86400 + d.seconds) * 1000000000 + d.microseconds * 1000

def native(text):
    return [json.loads(l.split("NATIVE_RECEIPT_EVENT ", 1)[1]) for l in text.splitlines() if "NATIVE_RECEIPT_EVENT " in l]

def one(seq):
    assert len(seq) == 1, ("expected one record", len(seq))
    return seq[0]

def verify():
    assert sys.version_info[:3] == (3, 13, 15), sys.version
    assert pathlib.Path(sys.executable).resolve() == pathlib.Path(r"C:\Users\blith\AppData\Local\Temp\opencode\sightbreak-tools\python\cpython-3.13.15-windows-x86_64-none\python.exe").resolve()
    manifest_raw = (ROOT / "manifest.json").read_bytes()
    assert sha(manifest_raw) == PIN, "manifest pin mismatch"
    m = json.loads(manifest_raw)
    files = {}
    hashes = []
    checks = []
    def ck(name, condition, detail=None, target=checks):
        row = {"check": name, "consistent": bool(condition)}
        if detail is not None:
            row["detail"] = detail
        target.append(row)
        return bool(condition)
    names = set()
    for entry in m["files"]:
        rel = pathlib.PurePosixPath(entry["path"])
        assert not rel.is_absolute() and ".." not in rel.parts and ":" not in str(rel)
        assert str(rel).casefold() not in names, "duplicate manifest path"
        names.add(str(rel).casefold())
        p = ROOT.joinpath(*rel.parts)
        assert p.resolve().is_relative_to(ROOT.resolve())
        for ancestor in [p, *p.parents]:
            if not ancestor.is_relative_to(ROOT):
                break
            assert not ancestor.is_symlink() and not ancestor.is_junction(), "linked input rejected"
        b = p.read_bytes()
        h = sha(b)
        ck("payload_hash_and_length:" + str(rel), h == entry["sha256"] and len(b) == entry["bytes"])
        if h != entry["sha256"] or len(b) != entry["bytes"]:
            raise ValueError("payload hash mismatch: " + str(rel))
        files[str(rel)] = b
        hashes.append({"path": str(rel), "bytes": len(b), "sha256": h})
        if "records" in entry:
            ck("jsonl_record_count:" + str(rel), len(b.decode("utf-8").splitlines()) == entry["records"])
    actual = {p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*") if p.is_file()}
    ck("exact_file_inventory", actual == set(files) | {"manifest.json"})
    ck("manifest_counts", len(files) == m["file_count_excluding_this_manifest"] == 178)
    hashes.append({"path": "manifest.json", "bytes": len(manifest_raw), "sha256": PIN})
    def raw(rel):
        return files[rel]
    def text(rel):
        return raw(rel).decode("utf-8", errors="replace")
    def obj(rel):
        return json.loads(raw(rel))
    def events(rel):
        return [json.loads(l) for l in text(rel).splitlines()]
    cases = []
    samples = sorted({k.split("/")[1] for k in files if k.startswith("samples/")})
    for sample in samples:
        service = text("samples/" + sample + "/service-console.txt")
        for trial in ["trial-1", "trial-2", "trial-3"]:
            base = "samples/" + sample + "/" + trial + "/"
            s = obj(base + "scenario.json")
            ev = events(base + "timeline.jsonl")
            snaps = [obj(base + n + ".json") for n in SNAMES]
            econ = [sn["economic_state"] for sn in snaps]
            before, committed = econ[:2]
            local = []
            def test(name, cond, detail=None):
                return ck(name, cond, detail, target=local)
            def pick(event, **kw):
                return [(i, e) for i, e in enumerate(ev) if e["event"] == event and all(e.get(k) == v for k, v in kw.items())]
            buyer, seller, item_id, listing, path, payload = [s[k] for k in ["owner", "seller", "item", "listing", "path", "payload"]]
            price = payload["expected_price"]
            fee = 3 * price // 100
            key = payload["idempotency_key"]
            opid = buyer + ":buy:" + listing + ":" + key
            test("integer_price_and_fresh_fixture_identity", type(price) is int and buyer != seller and path == "/market/" + listing + "/buy")
            test("wall_and_monotonic_event_order", all(a["wall_ns"] <= b["wall_ns"] and a["monotonic_ns"] <= b["monotonic_ns"] for a, b in zip(ev, ev[1:])))
            test("single_harness_pid_in_case", len({e["harness_pid"] for e in ev}) == 1)
            order = {}
            for i, name in enumerate(SNAMES):
                idx, e = one(pick("postgresql_snapshot", name=name))
                order[name] = idx
                meta = snaps[i]["postgresql"]
                test("snapshot_state_sha:" + name, sha(json.dumps(econ[i], sort_keys=True).encode()) == e["state_sha256"])
                test("snapshot_connection_and_database:" + name, meta["pg_backend_pid"] == e["connection_pid"] and meta["current_database"] == e["database"])
                test("snapshot_clock_precedes_capture_event:" + name, time_ns(meta["clock_timestamp"]) <= e["wall_ns"])
                test("nine_economic_tables:" + name, set(econ[i]) == TABLES)
                for table, rows in econ[i].items():
                    test("unique_row_ids:" + name + ":" + table, len({r["id"] for r in rows}) == len(rows))
            test("same_database_endpoint_in_all_snapshots", len({(sn["postgresql"]["current_database"], sn["postgresql"]["inet_server_port"], sn["postgresql"]["version"]) for sn in snaps}) == 1)
            test("independent_snapshot_backend_ids", len({sn["postgresql"]["pg_backend_pid"] for sn in snaps}) == 5)
            req_i, req = one(pick("proxy_request", phase="send", path=path))
            rsp_i, rsp = one(pick("proxy_upstream_response", phase="send", path=path))
            hold_i, hold = one(pick("response_held_before_any_client_headers"))
            kr_i, kr = one(pick("kill_requested"))
            kf_i, kf = one(pick("native_finished", phase="killed-client"))
            kc_i, kc = one(pick("kill_confirmed"))
            discard_i, discard = one(pick("held_response_discarded"))
            test("request_raw_json_and_integer_price", req["method"] == "POST" and req["body"] == payload and json.loads(req["raw_utf8"]) == payload and type(json.loads(req["raw_utf8"])["expected_price"]) is int)
            test("upstream_success_raw_json", rsp["status"] == 200 and json.loads(rsp["raw_utf8"]) == rsp["response"])
            test("observed_commit_before_kill_order", order[SNAMES[0]] < req_i < rsp_i < hold_i < order[SNAMES[1]] < kr_i < kf_i < kc_i < order[SNAMES[2]] < discard_i)
            test("db_visible_commit_clock_before_kill", time_ns(snaps[1]["postgresql"]["clock_timestamp"]) < kr["wall_ns"])
            test("zero_initial_response_delivery_attestation", hold["sent_bytes"] == kr["client_response_bytes"] == discard["sent_bytes"] == 0 and kr["upstream_committed"] is True and not pick("proxy_response_delivered", phase="send", path=path))
            test("kill_matches_initial_native_pid", kr["pid"] == kc["pid"] == kf["pid"] and kf["returncode"] == kc["returncode"] == 1)
            native_by = {phase: native(text(base + phase + ".stdout.txt")) for phase in ["killed-client", "recovery", "second-restart"]}
            lifecycle = []
            tokens = []
            for phase, console, end_snapshot in [("send", "killed-client", 1), ("recovery", "recovery", 3), ("second-restart", "second-restart", 4)]:
                start_i, start = one(pick("native_started", phase=phase))
                end_i, end = one(pick("native_finished", phase=console))
                rows = native_by[console]
                auth = one([e for e in rows if e["event"] == "authenticated"])
                ui = one([e for e in rows if e["event"] == "ui_ready"])
                token = auth["token_sha256"]
                tokens.append(token)
                logins = [e for _, e in pick("proxy_request", phase=phase, path="/auth/login")]
                login_response = one([e for _, e in pick("proxy_upstream_response", phase=phase, path="/auth/login")])
                session = one([r for r in snaps[end_snapshot]["sessions"] if r["token_hash"] == token])
                requests = [e for _, e in pick("proxy_request", phase=phase) if e["path"] != "/auth/login"]
                test("process_pid_and_recorded_slot:" + phase, start["pid"] == end["pid"] and all(r["pid"] == start["pid"] for r in rows) and start["other_native_pids"] == [])
                test("native_events_within_process:" + phase, all(start["wall_ns"] / 1e9 <= r["unix_seconds"] <= end["wall_ns"] / 1e9 for r in rows))
                test("authenticated_account_and_session_owner:" + phase, len(logins) == 1 and logins[0]["body"]["username"] == s["username"] and login_response["status"] == 200 and login_response["response"]["player_id"] == auth["owner"] == session["player_id"] == buyer and auth["ok"] is True)
                test("authenticated_token_hash_binding:" + phase, all(e["token_sha256"] == token for e in requests))
                test("session_expiry_matches_login:" + phase, time_ns(session["expires_at"]) == time_ns(login_response["response"]["expires_at"]))
                me = [e for _, e in pick("proxy_upstream_response", phase=phase, path="/me")]
                test("http_me_owner_and_balance:" + phase, bool(me) and all(e["status"] == 200 and e["response"]["player_id"] == buyer and e["response"]["credits"] == (price + 1600 if phase == "send" else 1600) for e in me))
                inventory = [e for _, e in pick("proxy_upstream_response", phase=phase, path="/inventory")]
                test("http_inventory_unique_item:" + phase, bool(inventory) and all(e["response"]["items"] == ([] if phase == "send" else [rsp["response"]["item"]]) for e in inventory))
                test("stderr_empty:" + phase, raw(base + console + ".stderr.txt") == b"")
                lifecycle.append({"phase": phase, "pid": start["pid"], "returncode": end["returncode"], "start_index": start_i, "end_index": end_i, "start_wall_ns": start["wall_ns"], "end_wall_ns": end["wall_ns"], "token_sha256": token, "pending_at_ui_ready": ui.get("pending", {})})
                if phase != "send":
                    done = one([e for e in rows if e["event"] == "completed"])
                    test("native_completion_and_exit:" + phase, end["returncode"] == 0 and done["mode"] == "retry" and done["account"]["player_id"] == buyer and done["account"]["credits"] == 1600 and done["inventory"] == [rsp["response"]["item"]] and done["pending_after"] == {})
                else:
                    perform = one([e for e in rows if e["event"] == "perform_entered"])
                    test("original_native_request_and_no_completion", perform["payload"] == payload and perform["path"] == path and perform["expected_price_is_int"] is True and not [e for e in rows if e["event"] == "completed"])
            test("three_fresh_nonoverlapping_processes", len({r["pid"] for r in lifecycle}) == 3 and lifecycle[0]["end_index"] < lifecycle[1]["start_index"] and lifecycle[1]["end_index"] < lifecycle[2]["start_index"])
            test("three_fresh_session_hashes", len(set(tokens)) == 3)
            for i, expected_token in [(1, tokens[0]), (2, None), (3, tokens[1]), (4, tokens[2])]:
                old = {r["token_hash"]: r for r in snaps[i-1]["sessions"]}
                new = {r["token_hash"]: r for r in snaps[i]["sessions"]}
                added = set(new) - set(old)
                test("isolated_session_delta:" + SNAMES[i], set(old).issubset(new) and all(new[k] == v for k, v in old.items()) and added == ({expected_token} if expected_token else set()))
            diff = {}
            for table in sorted(TABLES):
                a = {r["id"]: r for r in before[table]}
                b = {r["id"]: r for r in committed[table]}
                diff[table] = {"added": [r for k, r in b.items() if k not in a], "removed": [r for k, r in a.items() if k not in b], "changed": [{"before": a[k], "after": r} for k, r in b.items() if k in a and a[k] != r]}
            expected = copy.deepcopy(before)
            bp = one([r for r in expected["players"] if r["id"] == buyer])
            sp = one([r for r in expected["players"] if r["id"] == seller])
            buyer_before, seller_before = bp["credits"], sp["credits"]
            test("fixture_owner_username_and_balances", bp["username"] == s["username"] and bp["active"] is True and sp["active"] is True and buyer_before == price + 1600 and seller_before == 2000)
            bp["credits"] -= price
            sp["credits"] += price - fee
            it = one([r for r in expected["items"] if r["id"] == item_id])
            test("unique_original_item_and_reservation", it["owner_id"] == seller and it["reservation"] == "market:" + listing and it["consumed"] is False)
            it["owner_id"], it["reservation"] = buyer, None
            li = one([r for r in expected["listings"] if r["id"] == listing])
            test("original_listing_identity_price_and_state", li == {"buyer_id": None, "id": listing, "item_id": item_id, "price": price, "seller_id": seller, "state": "active"})
            li["buyer_id"], li["state"] = buyer, "sold"
            ledger = diff["ledger"]["added"]
            purchase = one([r for r in ledger if r["reason"] == "market_purchase"])
            sale = one([r for r in ledger if r["reason"] == "market_sale"])
            test("exact_new_purchase_and_sale_rows", len(ledger) == 2 and {k: v for k, v in purchase.items() if k not in ("id", "created_at")} == {"amount": -price, "balance_after": 1600, "player_id": buyer, "reason": "market_purchase", "reference": listing} and {k: v for k, v in sale.items() if k not in ("id", "created_at")} == {"amount": price-fee, "balance_after": seller_before+price-fee, "player_id": seller, "reason": "market_sale", "reference": listing})
            audit = one(diff["audit"]["added"])
            test("single_settlement_actor_and_details", audit["action"] == "market_settled" and audit["actor"] == buyer and audit["details"] == {"fee": fee, "from_player": seller, "item_id": item_id, "listing_id": listing, "to_player": buyer})
            op = one(diff["operations"]["added"])
            bodyhash = sha(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode())
            test("original_operation_receipt_and_request_hash", op["id"] == opid and op["request_hash"] == bodyhash == sha(req["raw_utf8"].encode()) and op["response"] == rsp["response"])
            response_item = rsp["response"]["item"]
            test("receipt_matches_unique_database_item_and_fee", response_item["id"] == it["id"] and response_item["definition_id"] == it["definition_id"] and response_item["pattern_seed"] == it["pattern_seed"] and round(response_item["wear"] * 10000) == it["wear"] and response_item["reserved"] is False and rsp["response"]["credits"] == 1600 and rsp["response"]["fee"] == fee)
            for table in ["audit", "ledger", "operations"]:
                expected[table] += diff[table]["added"]
            test("only_expected_economic_row_changes", all(sorted(expected[t], key=lambda r: r["id"]) == sorted(committed[t], key=lambda r: r["id"]) for t in TABLES))
            test("fee_conservation_player_and_ledger_sums", sum(r["credits"] for r in committed["players"]) - sum(r["credits"] for r in before["players"]) == -fee and sum(r["amount"] for r in ledger) == -fee)
            test("economic_state_stable_after_kill_recovery_third", all(e == committed for e in econ[2:]))
            test("economic_state_changes_at_original_commit", before != committed)
            journals = {n: obj(base + "journal-" + n + ".json") for n in ["before-kill", "after-kill", "after-recovery", "after-second-restart"]}
            test("journal_stable_across_initial_kill", journals["before-kill"] == journals["after-kill"])
            rec = one([e for e in native_by["recovery"] if e["event"] == "completed"])
            third = one([e for e in native_by["second-restart"] if e["event"] == "completed"])
            retry_requests = [e for _, e in pick("proxy_request", phase="recovery", path=path)]
            retry_responses = [e for _, e in pick("proxy_upstream_response", phase="recovery", path=path)]
            posts_by_phase = {phase: [e["path"] for _, e in pick("proxy_request", phase=phase) if e["method"] == "POST" and e["path"] != "/auth/login"] for phase in ["send", "recovery", "second-restart"]}
            test("third_process_no_economic_post_or_pending_result", posts_by_phase["second-restart"] == [] and third["pending_on_start"] == third["pending_after"] == third["result"] == {})
            durable = journals["after-kill"]["exists"]
            raw_response_same = None
            if durable:
                j = journals["after-kill"]
                tx = j["record"]["transaction"]
                for n in ["before-kill", "after-kill"]:
                    rb = raw(base + "journal-" + n + ".raw.json")
                    test("verbatim_journal_binding:" + n, sha(rb) == journals[n]["sha256"] and len(rb) == journals[n]["bytes"] and json.loads(rb) == journals[n]["record"])
                    lowered = rb.lower()
                    test("journal_structural_no_credentials:" + n, not any(k in lowered for k in [b'"password"', b'"token"', b'"authorization"']))
                test("durable_original_receipt_owner_server_body", j["record"]["schema"] == 1 and tx["method"] == 2 and tx["owner"] == buyer and tx["server"] == s["url"] and tx["path"] == path and tx["payload"] == payload)
                retry = one(retry_requests)
                replay = one(retry_responses)
                test("retry_exact_original_raw_body_method_path", retry["raw_utf8"] == req["raw_utf8"] and retry["body"] == req["body"] and retry["method"] == req["method"] and type(json.loads(retry["raw_utf8"])["expected_price"]) is int)
                test("replay_success_semantically_identical_receipt", replay["status"] == 200 and replay["response"] == rsp["response"] == op["response"] and json.loads(replay["raw_utf8"]) == rsp["response"])
                test("retry_response_delivered", len(pick("proxy_response_delivered", phase="recovery", path=path)) == 1)
                test("native_recovery_uses_original_pending_receipt", rec["pending_on_start"] == tx == lifecycle[1]["pending_at_ui_ready"] and rec["result"] == rsp["response"])
                test("no_unexpected_economic_posts", posts_by_phase == {"send": [path], "recovery": [path], "second-restart": []})
                raw_response_same = rsp["raw_utf8"] == replay["raw_utf8"]
                outcome = "original_receipt_recovered_in_fresh_process; third_process_noop"
            else:
                test("recorded_missing_journal_and_no_receipt_retry", all(j["exists"] is False and j["record"] is None and j["bytes"] == 0 and j["sha256"] == sha(b"") for j in journals.values()) and retry_requests == retry_responses == [] and rec["pending_on_start"] == rec["result"] == {} and lifecycle[1]["pending_at_ui_ready"] == {})
                test("no_unexpected_economic_posts", posts_by_phase == {"send": [path], "recovery": [], "second-restart": []})
                outcome = "original_receipt_recovery_failed_in_retained_scenario; account_inventory_refreshed_only"
            for n in ["after-recovery", "after-second-restart"]:
                test("journal_absent_after_completion:" + n, journals[n]["exists"] is False and journals[n]["record"] is None and journals[n]["bytes"] == 0)
            expected_calls = 2 if durable else 1
            test("service_console_corroborates_measured_buy_count", service.count('"POST ' + path + ' HTTP/1.1" 200 OK') == expected_calls)
            cases.append({"case": sample + "/" + trial, "sample": sample, "trial": trial, "price": price, "fee_observed": fee, "seller_net": price-fee, "buyer_before": buyer_before, "buyer_after": 1600, "seller_before": seller_before, "seller_after": seller_before+price-fee, "identities": {k: s[k] for k in ["owner", "seller", "item", "listing", "path", "url", "username"]}, "idempotency_key": key, "operation_id": opid, "request_hash": bodyhash, "initial_raw_request_sha256": sha(req["raw_utf8"].encode()), "initial_response": rsp["response"], "capture_start_utc": utc_ns(ev[0]["wall_ns"]), "capture_end_utc": utc_ns(ev[-1]["wall_ns"]), "timeline_record_count": len(ev), "snapshot_economic_sha256": [sha(json.dumps(e, sort_keys=True).encode()) for e in econ], "snapshot_metadata": [sn["postgresql"] for sn in snaps], "commit_before_kill_margin_ns": kr["wall_ns"] - ev[order[SNAMES[1]]]["wall_ns"], "ordering_indexes": {**order, "request": req_i, "upstream_success": rsp_i, "held": hold_i, "kill_requested": kr_i, "killed_exit": kf_i, "kill_confirmed": kc_i, "held_discarded": discard_i}, "lifecycle": lifecycle, "journals": journals, "economic_delta": diff, "economic_state_stable": all(e == committed for e in econ[2:]), "durable_original_receipt": durable, "same_receipt_retry_count": len(retry_requests), "initial_vs_replay_raw_response_identical": raw_response_same, "outcome": outcome, "checks": local, "inconsistent_checks": [r for r in local if not r["consistent"]]})
    retained = []
    for attempt in sorted({k.split("/")[1] for k in files if k.startswith("retained-attempts/attempt-")}):
        prefix = "retained-attempts/" + attempt + "/"
        names_in = sorted(k for k in files if k.startswith(prefix))
        row = {"attempt": attempt, "files": names_in, "status": None, "diagnostic_excerpts": [], "aborted_cases": []}
        for name in names_in:
            if name.endswith("recorded-status.json"):
                row["status"] = obj(name)
            if name.endswith((".txt", ".log")):
                counts = collections.Counter(l for l in text(name).splitlines() if re.search(r"error|exception|failed|failure|exit|20 minutes|preflight|no database|occupied|before draining|after communicate|authoritative_pass|must come|no server|ready to accept", l, re.I))
                row["diagnostic_excerpts"].append({"file": name, "empty": len(raw(name)) == 0, "matched_lines": [{"line": l, "count": n} for l,n in counts.items()]})
            if name.endswith("/timeline.jsonl"):
                ev = events(name)
                ab = name.rsplit("/",1)[0] + "/"
                state = obj(ab + "01-before.json")
                capture = one([e for e in ev if e["event"] == "postgresql_snapshot"])
                local = []
                ck("aborted_initial_snapshot_hash", sha(json.dumps(state["economic_state"], sort_keys=True).encode()) == capture["state_sha256"], target=local)
                ck("aborted_no_observed_proxy_request", not any(e["event"].startswith("proxy_") for e in ev), target=local)
                ck("aborted_native_exit_one", one([e for e in ev if e["event"] == "native_finished"])["returncode"] == 1, target=local)
                row["aborted_cases"].append({"scenario": obj(ab+"scenario.json"), "timeline": ev, "economic_table_counts": {k:len(v) for k,v in state["economic_state"].items()}, "checks": local, "limitation": "Only before snapshot; no after snapshot, HTTP buy, commit barrier, recovery, or successful measurement retained. Exit 1 is aborted attempt, not completed recovery."})
        retained.append(row)
    controls = []
    for control in sorted({k.split("/")[1] for k in files if k.startswith("ancillary-controls/")}):
        prefix = "ancillary-controls/" + control + "/"
        observed = obj(prefix+"recorded-outcome.json")
        ev = events(prefix+"timeline.jsonl")
        stdout, stderr = text(prefix+"native-economy.stdout.txt"), text(prefix+"native-economy.stderr.txt")
        end = one([e for e in ev if e["event"] == "native_finished"])
        controls.append({"control":control, "recorded":observed, "timeline":ev, "stdout":stdout, "stderr":stderr, "checks":[{"check":"tally_and_exit_agree_in_records", "consistent": observed["returncode"] == end["returncode"] and observed["tally"] in stdout}], "judgment":"unmatched altered condition; no replacement of original failure" if observed["calibrated"] else "retained ancillary failure; not a between-sample comparator"})
    return {"schema":1, "generated_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(), "python_executable":sys.executable, "python_version":sys.version, "input_root":str(ROOT), "manifest_sha256":PIN, "payload_count":len(files), "payload_total_bytes":sum(len(v) for v in files.values()), "input_hashes":sorted(hashes,key=lambda r:r["path"]), "packet_checks":checks, "cases":cases, "retained_attempts":retained, "database_resume_record":obj("retained-attempts/database-resume-record.json"), "ancillary_controls":controls, "limits":"Retained unsigned capture consistency only. No new native/DB/network execution; no source or key read; no release approval. Numeric equality in native console allows integral floats; raw HTTP request integer types checked separately. Sent-byte/commit/PID attestation is not independent wire/OS proof. Local pending message is not a screenshot or uncertainty-indicator proof."}

if __name__ == "__main__":
    print(json.dumps(verify(), sort_keys=True, indent=2, ensure_ascii=True))
