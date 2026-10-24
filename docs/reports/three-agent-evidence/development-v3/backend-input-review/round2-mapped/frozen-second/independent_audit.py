"""Offline second-round artifact audit; inputs are packet and prior verdict only.

The packet verifier is run in an isolated approved CPython child process after
its full manifest and source have been reviewed. Its output is retained, but no
provided verifier function is imported or reused by the independent audit below.
Outputs are written only beside this script, never into either input directory.
"""
from __future__ import annotations

import collections
import datetime
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
import statistics
import subprocess
import sys


ROOT = Path(r"C:\Users\blith\AppData\Local\Temp\opencode\blind-trade-retention-r2-527acf0980f8\packet")
OUT = Path(__file__).resolve().parent
PRIOR = Path(r"C:\Users\blith\AppData\Local\Temp\opencode\sol-backend-blind-verdict-20261019T194014Z\NEUTRAL_VERDICT.md")
MANIFEST_SHA = "dd07a3bfd69e09e27c43257be3a719d001c5d8446a9338746460829887c86d64"
PRIOR_SHA = "f76906b5b3ee735d65eedef6bf23998d274a614778fb9e76c196ba39957bfdfa"
LABELS = ("M", "V")
CASES = [(0, 0), (1, 0), (1, 2), (10, 1), (40, 1), (40, 20), (501, 0)]
TABLES = {"players", "sessions", "ledger", "items", "operations", "audit", "listings", "trades", "rewards", "rate_buckets", "game_tickets", "loadouts"}
EMPTY_TABLES = {"audit", "game_tickets", "ledger", "listings", "loadouts", "operations", "rate_buckets", "rewards"}
TRADE_KEYS = {"id", "a", "b", "revision", "offers", "confirmations", "state", "names", "offer_items"}
ITEM_KEYS = {"id", "definition_id", "rarity", "pattern_seed", "wear", "variant", "acquired_at", "name", "collection", "kind", "reserved", "trade_eligible", "marketplace_eligible"}
ITEM_COLUMNS = "items.id, items.owner_id, items.definition_id, items.rarity, items.pattern_seed, items.wear, items.variant, items.reservation, items.consumed, items.acquired_at"
BASE_SQL = [
    "SELECT sessions.token_hash, sessions.player_id, sessions.expires_at \nFROM sessions \nWHERE sessions.token_hash = %(pk_1)s::VARCHAR",
    "SELECT players.id, players.username, players.display_name, players.password_hash, players.credits, players.xp, players.active, players.last_trade \nFROM players \nWHERE players.id = %(pk_1)s::VARCHAR",
    "SELECT trades.id, trades.a, trades.b, trades.revision, trades.offers, trades.confirmations, trades.state \nFROM trades \nWHERE trades.a = %(a_1)s::VARCHAR OR trades.b = %(b_1)s::VARCHAR",
]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def no_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def bad_constant(value):
    raise ValueError(f"Non-finite JSON constant: {value}")


def parse(data):
    return json.loads(data, object_pairs_hook=no_duplicate_keys, parse_constant=bad_constant)


def write_json(name, value):
    (OUT / name).write_bytes(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True, allow_nan=False).encode("utf-8") + b"\n")


def safe_path(root, name):
    require(isinstance(name, str) and "\\" not in name and ":" not in name, f"Non-relative artifact path: {name!r}")
    parts = PurePosixPath(name)
    require(not parts.is_absolute() and ".." not in parts.parts and parts.as_posix() == name, f"Unsafe artifact path: {name!r}")
    path = (root / name).resolve()
    require(path.is_relative_to(root.resolve()), f"Artifact escapes input: {name}")
    return path


def chunks(count):
    result = []
    while count:
        take = min(count, 500)
        result.append(take)
        count -= take
    return result


def in_sql(table, count):
    columns = ITEM_COLUMNS if table == "items" else "players.id, players.display_name"
    placeholders = ", ".join(f"%(id_1_{i})s::VARCHAR" for i in range(1, count + 1))
    return f"SELECT {columns} \nFROM {table} \nWHERE {table}.id IN ({placeholders})"


def main():
    require(sys.version_info[:3] == (3, 13, 15), "Approved CPython 3.13.15 required")
    require(sys.flags.isolated == 1 and sys.flags.no_site == 1 and sys.flags.dont_write_bytecode == 1 and sys.flags.optimize == 0, "Use -I -S -B without -O")
    require(not (OUT / "FROZEN.json").exists(), "Already frozen; preserve original")
    require(sha(PRIOR.read_bytes()) == PRIOR_SHA, "First frozen verdict has changed")
    manifest = (ROOT / "SHA256SUMS.txt").read_bytes()
    require(sha(manifest) == MANIFEST_SHA, "Input manifest anchor mismatch")
    entries = {}
    source_files = []
    for line in manifest.decode("utf-8").splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        require(match is not None, "Malformed input manifest line")
        digest, name = match.groups()
        require(name not in entries, f"Duplicate manifest entry: {name}")
        path = safe_path(ROOT, name)
        data = path.read_bytes()
        require(sha(data) == digest, f"Input hash mismatch: {name}")
        entries[name] = digest
        source_files.append({"path": name, "bytes": len(data), "sha256": digest, "verified": True})
    inventory = {p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*") if p.is_file()}
    require(inventory == set(entries) | {"SHA256SUMS.txt"}, "Missing or unmanifested packet file")
    require(not any(p.is_symlink() or p.is_junction() for p in ROOT.rglob("*")), "Packet symlink/junction is not permitted")
    # Strictly parse every JSON input, not just the descriptors selected by a routine.
    json_inputs = {}
    for name in entries:
        if name.endswith(".json"):
            json_inputs[name] = parse(safe_path(ROOT, name).read_bytes())
    source_files.append({"path": "SHA256SUMS.txt", "bytes": len(manifest), "sha256": MANIFEST_SHA, "verified": True})

    command = [sys.executable, "-I", "-S", "-B", str(ROOT / "verify_packet.py")]
    started = utc()
    process = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=120, check=False)
    finished = utc()
    (OUT / "packet_verifier.stdout.json").write_bytes(process.stdout)
    (OUT / "packet_verifier.stderr.txt").write_bytes(process.stderr)
    write_json("packet_verifier_execution.json", {
        "command": command, "cwd": str(ROOT), "started_utc": started, "finished_utc": finished,
        "exit_code": process.returncode, "stdout_sha256": sha(process.stdout), "stderr_sha256": sha(process.stderr),
        "stdout_bytes": len(process.stdout), "stderr_bytes": len(process.stderr),
        "approved_python_version": sys.version, "isolated": True, "no_site": True, "bytecode_writes_disabled": True,
        "application_database_network_native_tests_executed": False,
    })
    require(process.returncode == 0, f"Packet verifier failed; retained stderr: {process.stderr.decode('utf-8', errors='replace')}")
    verifier_output = parse(process.stdout)
    require(verifier_output["packet_files_verified"] == len(entries), "Packet verifier file total differs")

    references = set()
    def load_descriptor(label, descriptor, expected_file=None, canonical_file=False):
        name = descriptor["file"]
        if expected_file is not None:
            require(name == expected_file, f"Unexpected descriptor path: {label}/{name}")
        relative = f"{label}/{name}"
        require(relative in entries, f"Unmanifested descriptor: {relative}")
        data = safe_path(ROOT / label, name).read_bytes()
        require(sha(data) == descriptor["sha256"] == entries[relative], f"Descriptor hash differs: {relative}")
        value = parse(data)
        if canonical_file:
            require(data == canonical(value), f"Noncanonical saved JSON: {relative}")
        references.add(relative)
        return value, data, relative

    records = {label: json_inputs[f"{label}/measurement.json"] for label in LABELS}
    require(canonical(records["M"]["environment"]) == canonical(records["V"]["environment"]), "Environment records differ")
    eq = json_inputs["equivalence.json"]
    require(eq["schema"] == "anonymous-retained-trade-read-equivalence-v2" and len(eq["rows"]) == 7, "Equivalence schema/count differs")
    workloads = []
    retained = {}
    totals = collections.Counter()
    observed_modes = {label: set() for label in LABELS}
    all_state_counts = collections.Counter()
    for label in LABELS:
        record = records[label]
        require(record["variant"] == label and record["schema"] == "trade-read-retained-artifacts-v2", f"Wrong record identity: {label}")
        require(record["completed"] is True and record["database_dropped"] is True, f"Completion flags: {label}")
        require([(r["trades"], r["items_per_side"]) for r in record["rows"]] == CASES, f"Wrong workloads: {label}")
        for index, row in enumerate(record["rows"]):
            ref = f"{label}/measurement.json#/rows/{index}"
            trades, items_per_side = CASES[index]
            directory = f"workloads/{index:02}-{trades}-{items_per_side}"
            require(len(row["warmups"]) == 2 and len(row["samples"]) == 10, f"Retention counts: {ref}")
            expected, expected_bytes, expected_file = load_descriptor(label, row["expected_response"], f"{directory}/expected-response.json", True)
            require(type(expected) is dict and set(expected) == {"trades"} and type(expected["trades"]) is list, f"Expected envelope: {ref}")
            require(expected_bytes == canonical({"trades": sorted(expected["trades"], key=lambda t: t["id"])}), f"Expected trade order: {ref}")
            require(row["expected_response_sha256"] == sha(expected_bytes), f"Expected digest: {ref}")
            response_audits = []
            actual_hashes = set()
            raw_hashes = set()
            response_entries = [("warmup", j, r, f"{ref}/warmups/{j}") for j, r in enumerate(row["warmups"])]
            response_entries += [("timed", j, s["response"], f"{ref}/samples/{j}/response") for j, s in enumerate(row["samples"])]
            for kind, sample_index, response, response_ref in response_entries:
                require(response["status"] == 200 and type(response["status"]) is int, f"Non-200 response: {response_ref}")
                raw_hash = response["raw"]["sha256"]
                actual_hash = response["canonical"]["sha256"]
                raw, raw_bytes, raw_file = load_descriptor(label, response["raw"], f"{directory}/responses/{raw_hash}.json")
                require(type(raw) is dict and set(raw) == {"trades"} and type(raw["trades"]) is list, f"Extra/malformed raw envelope: {response_ref}")
                actual, actual_bytes, actual_file = load_descriptor(label, response["canonical"], f"{directory}/canonical-responses/{actual_hash}.json", True)
                # Preserve all fields and every nested array; sort ONLY top-level trades.
                normalized = dict(raw)
                normalized["trades"] = sorted(raw["trades"], key=lambda trade: trade["id"])
                normalized_bytes = canonical(normalized)
                require(normalized_bytes == actual_bytes == expected_bytes, f"Complete actual/canonical/expected byte inequality: {response_ref}")
                require(response["matches_expected"] is True, f"Wrong matches_expected flag: {response_ref}")
                for trade in actual["trades"]:
                    require(type(trade) is dict and set(trade) == TRADE_KEYS, f"Public trade field set: {response_ref}")
                    require(type(trade["confirmations"]) is list, f"Confirmation array type: {response_ref}")
                    sides = {trade["a"], trade["b"]}
                    require(len(sides) == 2, f"Non-distinct fixture participants: {response_ref}")
                    for field in ("offers", "offer_items", "names"):
                        require(type(trade[field]) is dict and set(trade[field]) == sides, f"Participant-map fields: {response_ref}/{field}")
                    for side in sides:
                        require(type(trade["offers"][side]) is list and type(trade["offer_items"][side]) is list, f"Offer array types: {response_ref}")
                        for item in trade["offer_items"][side]:
                            require(type(item) is dict and set(item) == ITEM_KEYS, f"Public item field set: {response_ref}")
                actual_hashes.add(sha(normalized_bytes))
                raw_hashes.add(raw_hash)
                response_audits.append({
                    "kind": kind, "index_0based": sample_index, "source_reference": response_ref, "status": response["status"],
                    "raw_file": raw_file, "raw_sha256": sha(raw_bytes), "raw_bytes": len(raw_bytes),
                    "canonical_actual_file": actual_file, "canonical_actual_sha256": sha(actual_bytes), "canonical_actual_bytes": len(actual_bytes),
                    "raw_recanonicalization_exact_bytes_equal_saved_actual_and_expected": True,
                    "complete_envelope_and_nested_field_sets_checked": True, "nested_arrays_preserved": True,
                    "status": 200, "judgment": "PASS",
                })
                totals["received_responses"] += 1
                totals[f"{label}_received_responses"] += 1
                totals[f"{kind}_responses"] += 1
            require(row["actual_response_sha256s"] == sorted(actual_hashes), f"Actual digest set: {ref}")
            states = {}
            state_audits = {}
            for phase in ("before", "after"):
                snapshot = row[f"state_{phase}"]
                require(snapshot["representation"] == "full_rows_per_table" and set(snapshot["tables"]) == TABLES, f"State table set/representation: {ref}/{phase}")
                tables = {}
                table_audits = []
                for table in sorted(TABLES):
                    descriptor = snapshot["tables"][table]
                    require(descriptor["representation"] == "full_rows", f"Non-full table descriptor: {ref}/{phase}/{table}")
                    values, data, source = load_descriptor(label, descriptor, f"{directory}/state/{phase}/{table}.json", True)
                    require(type(values) is list and all(type(value) is dict for value in values), f"Not a complete row-object array: {source}")
                    require(type(descriptor["row_count"]) is int and descriptor["row_count"] == len(values), f"Table row count: {source}")
                    require(values == sorted(values, key=canonical), f"Unsorted canonical table rows: {source}")
                    identity_key = "token_hash" if table == "sessions" else "id"
                    require(len({value[identity_key] for value in values}) == len(values), f"Duplicate row identity: {source}")
                    if table in EMPTY_TABLES:
                        require(values == [], f"Declared always-empty table is populated: {source}")
                    if table == "players":
                        require(all(v["password_hash"] == "fixture-unusable" and v["credits"] == 0 and v["xp"] == 0 and v["active"] is True for v in values), f"Player fixture assumptions: {source}")
                    tables[table] = values
                    table_audits.append({"table": table, "source_file": source, "row_count": len(values), "bytes": len(data), "sha256": sha(data), "canonical_full_rows_and_order_verified": True, "empty": not values, "judgment": "PASS"})
                    totals["full_table_snapshots"] += 1
                    totals["snapshot_row_instances"] += len(values)
                    totals["empty_table_snapshot_files"] += int(not values)
                    all_state_counts[table] += len(values)
                aggregate_bytes = canonical(tables)
                aggregate_sha = sha(aggregate_bytes)
                require(aggregate_sha == snapshot["sha256"], f"Reconstructed aggregate hash differs: {ref}/{phase}")
                states[phase] = tables
                state_audits[phase] = {"source_reference": f"{ref}/state_{phase}", "sha256": aggregate_sha, "reconstructed_canonical_bytes": len(aggregate_bytes), "aggregate_body_reconstructed_from_all_12_tables": True, "tables": table_audits}
                totals["aggregate_states_reconstructed"] += 1
            require(canonical(states["before"]) == canonical(states["after"]), f"Full before/after net rows differ: {ref}")
            require(state_audits["before"]["sha256"] == state_audits["after"]["sha256"] and row["read_only"] is True, f"State equality metadata differs: {ref}")
            for before, after in zip(state_audits["before"]["tables"], state_audits["after"]["tables"], strict=True):
                require(before["table"] == after["table"] and before["sha256"] == after["sha256"] and before["row_count"] == after["row_count"], f"Per-table equality: {ref}")

            # Check observable participant scoping, offer order and metadata against
            # retained rows, without inventing or importing implementation contracts.
            tables = states["before"]
            viewers = [p for p in tables["players"] if p["display_name"] == "Viewer"]
            require(len(viewers) == 1, f"Fixture viewer not unique: {ref}")
            viewer = viewers[0]["id"]
            players_by_id = {p["id"]: p for p in tables["players"]}
            items_by_id = {item["id"]: item for item in tables["items"]}
            visible = {t["id"]: t for t in tables["trades"] if viewer in (t["a"], t["b"])}
            hidden = {t["id"]: t for t in tables["trades"] if viewer not in (t["a"], t["b"])}
            actual_trades = expected["trades"]  # Every received body was independently byte-equal to this body.
            require(len(actual_trades) == trades and {t["id"] for t in actual_trades} == set(visible) and len(hidden) == 1, f"Visible/hidden trade membership differs: {ref}")
            unique_item_ids, participants = set(), set()
            offered_item_instances = 0
            for trade in actual_trades:
                source_trade = visible[trade["id"]]
                require(canonical({k: trade[k] for k in source_trade}) == canonical(source_trade), f"Trade row fields/order differ: {ref}/{trade['id']}")
                participants.update((trade["a"], trade["b"]))
                for side in (trade["a"], trade["b"]):
                    require(trade["names"][side] == players_by_id[side]["display_name"], f"Participant display name differs: {ref}")
                    offered = trade["offers"][side]
                    displayed = trade["offer_items"][side]
                    require(len(offered) == items_per_side and [v["id"] for v in displayed] == offered, f"Offer/item ordering differs: {ref}")
                    require([v["pattern_seed"] for v in displayed] == list(range(items_per_side - 1, -1, -1)), f"Reversed fixture seed order differs: {ref}")
                    for item in displayed:
                        db_item = items_by_id[item["id"]]
                        for key in ("id", "definition_id", "rarity", "pattern_seed", "variant", "acquired_at"):
                            require(canonical(item[key]) == canonical(db_item[key]), f"Current stored item field differs: {ref}/{key}")
                    offered_item_instances += len(offered)
                    unique_item_ids.update(offered)
            require(len(unique_item_ids) == offered_item_instances == 2 * trades * items_per_side and set(items_by_id) == unique_item_ids, f"Unique item fixture counts differ: {ref}")
            require(len(participants) == (trades + 1 if trades else 0), f"Unique participants differ: {ref}")
            require(len(tables["players"]) == trades + 3 and len(tables["sessions"]) == 2 and len(tables["trades"]) == trades + 1, f"Full populated fixture table counts differ: {ref}")
            semantics = {
                "snapshot_inferred_viewer_is_unique": True, "authentication_request_headers_not_retained": True,
                "returned_trade_ids_exactly_viewer_participant_rows": True, "hidden_trades_retained_and_excluded": len(hidden),
                "returned_trade_fields_equal_stored_rows": True, "stored_offer_and_confirmation_order_preserved": True,
                "display_names_equal_current_snapshot_rows": True, "item_ids_definition_rarity_seed_variant_acquired_at_equal_snapshot_rows": True,
                "offer_item_arrays_match_stored_offer_id_order": True, "reversed_fixture_pattern_seed_order_checked": True,
                "unique_offered_item_ids": len(unique_item_ids), "unique_visible_participant_ids": len(participants),
                "viewer_position_counts": {"a": sum(t["a"] == viewer for t in actual_trades), "b": sum(t["b"] == viewer for t in actual_trades)},
                "visible_trade_states": dict(sorted(collections.Counter(t["state"] for t in actual_trades).items())),
                "public_trade_field_set": sorted(TRADE_KEYS), "public_item_field_set": sorted(ITEM_KEYS),
                "definition_display_name_kind_collection_eligibility_rules": "Equal to retained expectation; catalog/rule source not supplied or independently audited",
                "metadata_mutation_between_requests_tested": False,
            }

            durations = [sample["milliseconds"] for sample in row["samples"]]
            require(all(type(t) in (int, float) and math.isfinite(t) and t >= 0 for t in durations), f"Invalid timing: {ref}")
            counts = [sample["statements"] for sample in row["samples"]]
            require(all(type(n) is int and n > 0 for n in counts), f"Invalid SQL count: {ref}")
            median = statistics.median(durations)
            rank = math.ceil(len(durations) * .95)
            p95 = sorted(durations)[rank - 1]
            require(math.isclose(median, row["median_ms"], rel_tol=1e-12) and p95 == row["p95_ms"], f"Timing summaries differ: {ref}")
            require(row["query_counts"] == sorted(set(counts)) and len(set(counts)) == 1, f"Query set/stability differs: {ref}")
            item_chunks, participant_chunks = chunks(len(unique_item_ids)), chunks(len(participants))
            budget = 3 + len(item_chunks) + len(participant_chunks)
            require(row["budget"] == budget, f"Recomputed budget differs: {ref}")
            sql_shapes = row["sql_shapes"]
            batched = any(" IN (" in sql for sql in sql_shapes)
            mode = "batched_id_in" if batched else ("point_id_lookups" if trades else "no_enrichment")
            if trades:
                observed_modes[label].add(mode)
            expected_sql = list(BASE_SQL)
            if batched:
                expected_sql.extend(in_sql("items", size) for size in dict.fromkeys(item_chunks))
                expected_sql.extend(in_sql("players", size) for size in dict.fromkeys(participant_chunks))
                predicted_count = budget
            else:
                if unique_item_ids:
                    expected_sql.append(f"SELECT {ITEM_COLUMNS} \nFROM items \nWHERE items.id = %(pk_1)s::VARCHAR")
                predicted_count = 3 + trades + len(unique_item_ids)
            require(sql_shapes == expected_sql and len(set(sql_shapes)) == len(sql_shapes), f"Exact SQL shapes/placeholder sequence differ: {ref}")
            require(all(n == predicted_count for n in counts), f"SQL count/shape model differs: {ref}")
            shape_audits = []
            for j, sql in enumerate(sql_shapes):
                placeholders = re.findall(r"%\(([^)]+)\)s", sql)
                shape_audits.append({
                    "index_0based": j, "source_reference": f"{ref}/sql_shapes/{j}", "utf8_sha256": sha(sql.encode("utf-8")),
                    "utf8_bytes": len(sql.encode("utf-8")), "table": re.search(r"\nFROM (\w+)", sql).group(1),
                    "placeholder_count": len(placeholders), "first_placeholder": placeholders[0], "last_placeholder": placeholders[-1],
                    "exact_sql_template_and_placeholder_sequence_verified": True, "select_only_shape": True,
                })
            statuses = {
                "packet_integrity": "PASS", "actual_response_equivalence": "PASS", "captured_net_row_state_preservation": "PASS",
                "measured_query_efficiency_vs_common_budget": "PASS" if max(counts) <= budget else "FAIL",
                "latency_generalization": "NEEDS MORE EVIDENCE", "source_monetary_contract_safety": "NOT EVALUATED",
            }
            workload = {
                "label": label, "row_index_0based": index, "source_reference": ref, "trades": trades, "items_per_side": items_per_side,
                "judgments": statuses, "responses": response_audits, "retained_received_responses": len(response_audits),
                "distinct_raw_body_hashes": sorted(raw_hashes), "distinct_actual_canonical_body_hashes": sorted(actual_hashes),
                "expected_body_file": expected_file, "expected_body_sha256": sha(expected_bytes), "expected_body_bytes": len(expected_bytes),
                "state": state_audits, "full_before_after_arrays_and_hashes_equal": True,
                "always_empty_tables": sorted(EMPTY_TABLES), "zero_wallet_balances": True, "populated_receipt_ledger_contracts_tested": False,
                "transient_write_sequence_schema_external_concurrent_safety_proven": False,
                "observable_fixture_semantics": semantics,
                "timed_samples": [{"index_0based": j, "source_reference": f"{ref}/samples/{j}", "milliseconds": s["milliseconds"], "statements": s["statements"]} for j, s in enumerate(row["samples"])],
                "sorted_duration_samples": sorted([{"index_0based": j, "milliseconds": t} for j, t in enumerate(durations)], key=lambda item: item["milliseconds"]),
                "recorded_median_ms": row["median_ms"], "recomputed_median_ms": median,
                "recorded_p95_ms": row["p95_ms"], "recomputed_p95_ms": p95, "nearest_rank_p95_rank_1based": rank,
                "p95_sample_index_0based": durations.index(p95), "min_ms": min(durations), "max_ms": max(durations),
                "recomputed_query_counts": sorted(set(counts)), "recomputed_budget_from_actual_visible_ids": budget,
                "all_sample_arithmetic_verified": True, "sql_shape_mode": mode, "sql_shapes_last_timed_request_only": shape_audits,
                "unique_shape_count": len(shape_audits), "executed_statements_last_timed_request": counts[-1],
                "item_batch_sizes_consistent_with_counts_not_full_trace": item_chunks if batched else None,
                "participant_batch_sizes_consistent_with_counts_not_full_trace": participant_chunks if batched else None,
                "full_sql_trace_bound_parameters_and_multiplicities_retained": False,
            }
            workloads.append(workload)
            retained[label, index] = {"canonical_actual": expected_bytes, "states": states, "workload": workload}
            totals["workload_records"] += 1
            totals["timed_samples"] += len(durations)
            totals[f"{label}_timed_statement_callbacks"] += sum(counts)
            totals["sql_shape_entries"] += len(sql_shapes)

    # No label identities or cross-round assignments are inferred from these modes.
    require(all(len(modes) == 1 for modes in observed_modes.values()), "Inconsistent SQL family within a variant")
    pairs = []
    for index, pair in enumerate(eq["rows"]):
        require((pair["trades"], pair["items_per_side"]) == CASES[index] and pair["state_representation"] == "full_rows_per_table", f"Equivalence coordinates/representation differ: {index}")
        left, right = retained["M", index], retained["V", index]
        require(left["canonical_actual"] == right["canonical_actual"] and pair["actual_canonical_responses_equal"] is True, f"Actual cross-variant body differs: {index}")
        table_equality, columns_differ = {}, {}
        for table in sorted(TABLES):
            m, v = left["states"]["before"][table], right["states"]["before"][table]
            table_equality[table] = canonical(m) == canonical(v)
            if not table_equality[table]:
                key = "token_hash" if table == "sessions" else "id"
                m_by_key, v_by_key = ({r[key]: r for r in values} for values in (m, v))
                require(set(m_by_key) == set(v_by_key), f"Cross-variant row identities differ: {index}/{table}")
                differing = set()
                for identity in m_by_key:
                    a, b = m_by_key[identity], v_by_key[identity]
                    for field in a.keys() | b.keys():
                        if field not in a or field not in b or canonical(a[field]) != canonical(b[field]):
                            differing.add(field)
                columns_differ[table] = sorted(differing)
        require(pair["cross_variant_table_rows_equal"] == table_equality and pair["cross_variant_differing_columns"] == columns_differ, f"Cross-variant state metadata differs: {index}")
        require(columns_differ == {"sessions": ["expires_at"]}, f"Unexpected cross-variant state difference: {index}")
        for label in LABELS:
            row = records[label]["rows"][index]
            require(pair["actual_response_sha256s"][label] == row["actual_response_sha256s"], f"Equivalence actual hashes: {index}/{label}")
            require(pair["expected_response_sha256"][label] == row["expected_response_sha256"], f"Equivalence expected hash: {index}/{label}")
            require(pair["snapshot_rows_equal_within_run"][label] is True, f"Equivalence snapshot flag: {index}/{label}")
            require(pair["state_sha256"][label] == {phase: row[f"state_{phase}"]["sha256"] for phase in ("before", "after")}, f"Equivalence state hashes: {index}/{label}")
        m, v = left["workload"], right["workload"]
        m_count, v_count = m["recomputed_query_counts"][0], v["recomputed_query_counts"][0]
        median_change = v["recomputed_median_ms"] - m["recomputed_median_ms"]
        p95_change = v["recomputed_p95_ms"] - m["recomputed_p95_ms"]
        count_winner = "TIE" if m_count == v_count else min(LABELS, key=lambda label: retained[label, index]["workload"]["recomputed_query_counts"][0])
        for current, other in ((m, v), (v, m)):
            current["timing_vs_other_label"] = {
                "other_label": other["label"],
                "median_change_ms": current["recomputed_median_ms"] - other["recomputed_median_ms"],
                "median_change_percent": 100 * (current["recomputed_median_ms"] / other["recomputed_median_ms"] - 1),
                "p95_max_change_ms": current["recomputed_p95_ms"] - other["recomputed_p95_ms"],
                "p95_max_change_percent": 100 * (current["recomputed_p95_ms"] / other["recomputed_p95_ms"] - 1),
                "direction": "REGRESSION" if current["recomputed_median_ms"] > other["recomputed_median_ms"] else "IMPROVEMENT",
                "descriptive_not_causal": True,
            }
        pairs.append({
            "row_index_0based": index, "trades": CASES[index][0], "items_per_side": CASES[index][1],
            "equivalence_reference": f"equivalence.json#/rows/{index}",
            "M_statements_all_timed_samples": m_count, "V_statements_all_timed_samples": v_count,
            "V_fewer_statements_absolute": m_count - v_count, "V_fewer_statements_percent": 100 * (m_count - v_count) / m_count, "count_winner": count_winner,
            "M_median_ms": m["recomputed_median_ms"], "V_median_ms": v["recomputed_median_ms"],
            "V_minus_M_median_ms": median_change, "V_minus_M_median_percent": 100 * median_change / m["recomputed_median_ms"],
            "M_p95_max_ms": m["recomputed_p95_ms"], "V_p95_max_ms": v["recomputed_p95_ms"],
            "M_p95_sample_index_0based": m["p95_sample_index_0based"], "V_p95_sample_index_0based": v["p95_sample_index_0based"],
            "V_minus_M_p95_max_ms": p95_change, "V_minus_M_p95_max_percent": 100 * p95_change / m["recomputed_p95_ms"],
            "M_to_V_median_ratio_descriptive_only": m["recomputed_median_ms"] / v["recomputed_median_ms"],
            "actual_canonical_bytes_equal_all_24_responses": True, "actual_canonical_sha256": sha(left["canonical_actual"]),
            "M_before_after_aggregate_sha256": m["state"]["before"]["sha256"], "V_before_after_aggregate_sha256": v["state"]["before"]["sha256"],
            "both_captured_net_row_states_preserved": True, "cross_variant_tables_equal": table_equality, "cross_variant_differing_columns": columns_differ,
            "M_and_V_row_counts_each_phase": {table: len(left["states"]["before"][table]) for table in sorted(TABLES)},
            "raw_body_hash_sets_equal": m["distinct_raw_body_hashes"] == v["distinct_raw_body_hashes"],
        })

    require(totals["workload_records"] == 14 and totals["received_responses"] == 168 and totals["timed_samples"] == 140 and totals["full_table_snapshots"] == 336 and totals["aggregate_states_reconstructed"] == 28, "Overall audit totals differ")
    non_artifact_files = {"README.md", "METHOD.md", "REVIEW_QUESTIONS.md", "verify_packet.py", "verify_artifacts.py", "equivalence.json", "M/measurement.json", "V/measurement.json"}
    require(references | non_artifact_files == set(entries), "Unreferenced packet artifact or missing referenced body")
    require(sha(PRIOR.read_bytes()) == PRIOR_SHA, "Earlier verdict changed during audit")
    input_hashes = {
        "schema": "neutral-retention-r2-input-hashes-v1", "verified_utc": utc(), "packet_root": str(ROOT),
        "packet_manifest_sha256_expected": MANIFEST_SHA, "packet_manifest_sha256_actual": sha(manifest),
        "packet_payload_files_verified": len(entries), "packet_files_including_manifest": len(inventory),
        "strict_json_files_parsed": len(json_inputs), "all_artifact_files_referenced": True,
        "packet_input_files": source_files,
        "first_round_verdict": {"path": str(PRIOR), "sha256": PRIOR_SHA, "unchanged_before_and_after_audit": True},
        "original_implementation_source_commit_tree_routine_fixture_hashes": None,
        "original_source_provenance_status": "WITHHELD_NOT_INSPECTED; no identity/source binding until after this verdict is frozen",
    }
    summary = {
        "schema": "neutral-retention-r2-independent-assessment-v1", "audited_utc": utc(),
        "packet_manifest_sha256": MANIFEST_SHA, "python_version": sys.version,
        "reviewer_mode": "Anonymous M/V only; no key, repository, owner report, source or parent inspection",
        "blinding_limit": "Distinct query-count signatures and retained timestamps make behavior-level blinding imperfect across rounds. No label-to-source or cross-round mapping is asserted or used.",
        "first_round_verdict_unchanged": {"path": str(PRIOR), "sha256": PRIOR_SHA},
        "totals": dict(totals), "total_snapshot_rows_by_table": dict(sorted(all_state_counts.items())),
        "packet_payload_files_verified": len(entries), "packet_files_including_manifest": len(inventory),
        "strict_json_files_parsed": len(json_inputs), "distinct_referenced_artifact_files": len(references),
        "packet_verifier_exit_code": process.returncode, "packet_verifier_output": verifier_output,
        "independent_audit_reuses_packet_verifier_functions": False,
        "r1_gap_resolution": {
            "missing_received_response_bodies_and_actual_hash_proof": "CLOSED for these 168 r2 response records; no retroactive proof of original r1 captures",
            "missing_full_authoritative_snapshots_and_hashes": "CLOSED for net row equality within these 14 r2 captured intervals; no transient-write proof",
            "missing_full_sql_traces_and_bound_parameters": "OPEN",
            "source_capture_provenance_adversarial_authentication_monetary_contracts": "OPEN / NOT EVALUATED",
            "latency_production_concurrent_memory_unbounded_history": "OPEN",
        },
        "decision": {
            "narrow_verdict": "ACCEPT WITH QUALIFICATIONS", "preferred_label": "V", "confidence": "HIGH for retained body/row/hash/count consistency; not trusted-capture attestation or production generalization",
            "statuses": {
                "packet_integrity": "PASS", "actual_response_equivalence": "PASS", "captured_net_row_state_preservation": "PASS",
                "measured_query_efficiency": {"M": "FAIL", "V": "PASS"}, "latency_generalization": "NEEDS MORE EVIDENCE", "source_monetary_contract_safety": "NOT EVALUATED",
            },
            "qualification": "V has two descriptive latency regressions despite count ties; all eight monetary/history tables are empty and all balances zero; capture/source provenance remains withheld. No broad implementation acceptance.",
            "broad_gates": {name: "UNVERIFIED" for name in ("human", "device", "8.5", "production", "concurrent_load", "unbounded_history")},
        },
        "pairs": pairs, "workloads": workloads,
    }
    # Protect the declared label-specific decision with observations, not assumed intent.
    require(sum(pair["count_winner"] == "V" for pair in pairs) == 5 and sum(pair["count_winner"] == "TIE" for pair in pairs) == 2, "Declared V preference not supported by counts")
    require(all(pair["V_statements_all_timed_samples"] <= pair["M_statements_all_timed_samples"] for pair in pairs), "Undisclosed V count regression")
    require([pair["row_index_0based"] for pair in pairs if pair["V_minus_M_median_ms"] > 0] == [0, 1], "Timing regression ledger differs")
    write_json("input_hashes.json", input_hashes)
    write_json("per_workload_judgments.json", summary)
    print(json.dumps({
        "audited_utc": summary["audited_utc"], "packet_files_verified": len(entries), "strict_json_files_parsed": len(json_inputs),
        "totals": dict(totals), "pairs": pairs,
        "decision": summary["decision"], "r1_gap_resolution": summary["r1_gap_resolution"],
        "written": ["input_hashes.json", "per_workload_judgments.json", "packet_verifier.stdout.json", "packet_verifier.stderr.txt", "packet_verifier_execution.json"],
    }, indent=2))


if __name__ == "__main__":
    main()
