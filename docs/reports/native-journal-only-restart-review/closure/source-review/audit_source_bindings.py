"""Independent read-only source/record audit. Never imports or runs target code."""
import ast
from collections import Counter
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parent
REPO = Path(r"C:\Users\blith\OneDrive\Documents\Default Project\sightbreak")
CONTROLLER = Path(r"C:\Users\blith\AppData\Local\Temp\opencode\journal-review-e8f9e5706e73e619\CONTROLLER")
BLIND = Path(r"C:\Users\blith\AppData\Local\Temp\opencode\independent-journal-critic-7fbb839fd97341e1aa44aa5f82d59883")
PACKET = BLIND / "packet"
EVIDENCE = "e6fc11b2c103bb45551dd065bb9131851d072d50"
PUBLICATION = "0e536d94621453adba5469303908536c6e58d952"
HARNESS = "7be70f73ec6a065849d902e7075d2b76e78bdd21"
CHERRY = "9e4fd4f6e1567fbc923d145982301e54afe3d0cc"
OLD_HARNESS = "31438cbcea6ef08a131ae312c65b94f7e3e882c3"
PREFIX = "docs/reports/native-journal-only-restart-evidence/r2/"
PIN = "4ef6ffc75a2ef410a55d576a273626c625582053aba5dc910c1e0bc3dbf19c86"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def git(*args, data=None):
    return subprocess.check_output(["git", "-C", str(REPO), *args], input=data)


def gtext(*args):
    return git(*args).decode().strip()


def load(path):
    return json.loads(path.read_bytes())


def objects(rev, *paths):
    result = {}
    for entry in git("ls-tree", "-rz", rev, "--", *paths).split(b"\0"):
        if entry:
            metadata, path = entry.split(b"\t", 1)
            mode, kind, oid = metadata.decode().split()
            assert kind == "blob"
            result[path.decode()] = oid
    names = sorted(result)
    batch = git("cat-file", "--batch", data="".join(result[n] + "\n" for n in names).encode())
    offset, raw = 0, {}
    for name in names:
        end = batch.index(b"\n", offset)
        oid, kind, length = batch[offset:end].decode().split()
        assert oid == result[name] and kind == "blob"
        size = int(length)
        raw[name] = batch[end + 1:end + 1 + size]
        offset = end + size + 2
    assert offset == len(batch)
    return result, raw


def one(rows, **fields):
    found = [r for r in rows if all(r.get(k) == v for k, v in fields.items())]
    assert len(found) == 1, fields
    return found[0]


mapping_bytes = (CONTROLLER / "mapping.json").read_bytes()
assert sha(mapping_bytes) == PIN
mapping = json.loads(mapping_bytes)
assert mapping["evidence_commit"] == EVIDENCE
before_originals = {name: sha((BLIND / name).read_bytes()) for name in ["VERDICT.md", "independent-audit.json"]}
assert before_originals == {
    "VERDICT.md": "ce31d12d3def7e7b312ce1a44e30fc654290085796b3b0a5c2bd561e59c904af",
    "independent-audit.json": "873b727b69b44eb2dd6d9116eb13d34b86e20b268c50783cb291f617ed957f39",
}
oids, raw_evidence = objects(EVIDENCE, "docs/reports/native-journal-only-restart-evidence", "scripts/validate_native_transaction_restart.py", "scripts/native_transaction_restart_probe.gd")
pub_oids, _ = objects(PUBLICATION, "docs/reports/native-journal-only-restart-evidence", "scripts/validate_native_transaction_restart.py", "scripts/native_transaction_restart_probe.gd")
bound_paths = set()


def original(binding):
    path = binding["path"]
    assert binding["commit"] == EVIDENCE
    data = raw_evidence[path]
    assert oids[path] == binding["git_blob"] == pub_oids[path]
    assert sha(data) == binding["sha256"] and len(data) == binding["bytes"]
    assert (REPO / path).read_bytes() == data
    bound_paths.add(path)
    return data


categories, occurrences = Counter(), Counter()
unchanged = transformed = stages = 0
for row in mapping["files"]:
    packet = (PACKET / row["packet_path"]).read_bytes()
    assert sha(packet) == row["packet_sha256"]
    if "original" not in row:
        assert row["generated"]
        for binding in row["original_inputs"]:
            original(binding)
        continue
    data = original(row["original"])
    initially = data
    label = row["packet_path"].split("/")[0]
    allowed_substitutions = set()
    for category, value, replacement in mapping["labels"][label]["aliases"]:
        for spelling in {value, value.replace("\\", "/"), value.replace("/", "\\")}:
            allowed_substitutions.add((category, spelling, replacement))
            allowed_substitutions.add((category, json.dumps(spelling)[1:-1], replacement))
    for change in row["transformations"]:
        assert (change["category"], change["original_text"], change["replacement_text"]) in allowed_substitutions
        old, new = change["original_text"].encode(), change["replacement_text"].encode()
        assert data.count(old) == change["occurrences"]
        data = data.replace(old, new)
        categories[change["category"]] += 1
        occurrences[change["category"]] += change["occurrences"]
    assert data == packet
    assert row["byte_identical"] == (initially == packet)
    if initially == packet:
        unchanged += 1
    else:
        transformed += 1
    if re.match(r"0[1-5]-", Path(row["packet_path"]).name):
        assert initially == packet
        stages += 1
assert (unchanged, transformed, stages) == (26, 24, 10)
for row in mapping["withheld"]:
    assert row["byte_identical"]
    assert (CONTROLLER / row["controller_path"]).read_bytes() == original(row["original"])

zip_path = Path(mapping["packet"]["zip_path"])
zip_bytes = zip_path.read_bytes()
assert sha(zip_bytes) == mapping["packet"]["zip_sha256"]
zip_blob = hashlib.sha1(b"blob " + str(len(zip_bytes)).encode() + b"\0" + zip_bytes).hexdigest()
assert zip_blob == mapping["packet"]["git_blob"] == gtext("rev-parse", PUBLICATION + ":docs/reports/native-journal-only-restart-review/" + zip_path.name)
assert git("cat-file", "blob", zip_blob) == zip_bytes

source_names = ["validate_native_transaction_restart.py", "native_transaction_restart_probe.gd"]
harness_hashes = {}
for name in source_names:
    blob = git("show", HARNESS + ":scripts/" + name)
    assert blob == git("show", CHERRY + ":scripts/" + name) == git("show", PUBLICATION + ":scripts/" + name)
    assert blob == (CONTROLLER / "source-context/baseline-701" / name).read_bytes() == (CONTROLLER / "source-context/candidate-7b6f379" / name).read_bytes()
    harness_hashes[name] = sha(blob)

driver = (CONTROLLER / "source-context/candidate-7b6f379/validate_native_transaction_restart.py").read_text()
tree = ast.parse(driver)
constants = {}
for node in tree.body:
    if isinstance(node, ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id in {"RETRY_CONFIG_KEYS", "NATIVE_ENV_KEYS"}:
                constants[target.id] = ast.literal_eval(node.value)
expected_changed = {"docs/reports/NATIVE_JOURNAL_ONLY_RESTART_PROTOCOL.md", "scripts/native_transaction_restart_probe.gd", "scripts/validate_native_transaction_restart.py"}
for rev in [HARNESS, CHERRY]:
    assert set(gtext("diff-tree", "--no-commit-id", "--name-only", "-r", rev).splitlines()) == expected_changed
    for subtree in ["game", "backend"]:
        assert gtext("rev-parse", rev + ":" + subtree) == gtext("rev-parse", rev + "^:" + subtree)
protocol = git("show", HARNESS + ":docs/reports/NATIVE_JOURNAL_ONLY_RESTART_PROTOCOL.md")
assert protocol == git("show", CHERRY + ":docs/reports/NATIVE_JOURNAL_ONLY_RESTART_PROTOCOL.md")

launch = json.loads(raw_evidence[PREFIX + "launch.json"])
assert sha(raw_evidence[PREFIX + "launch-wrapper.py"]) == launch["wrapper_sha256"]
assert launch["file_sha256"] == harness_hashes and launch["harness_commit"] == HARNESS
audit = {
    "schema": 1,
    "decision": "PASS for scoped record-backed source/binding/dataflow; original blind outcome unchanged",
    "scope": "One price-400 case per source; no runtime tests or repository edits; original source reads only after outcome freeze",
    "mapping_sha256": PIN,
    "evidence_commit": EVIDENCE,
    "publication_commit": PUBLICATION,
    "original_frozen_artifacts_sha256": before_originals,
    "transformation_audit": {"unchanged_observations": unchanged, "transformed_observations": transformed, "unchanged_sql_stages": stages, "generated_payloads": 4, "all_replays_exact": True, "replacement_records_by_category": dict(categories), "replacement_occurrences_by_category": dict(occurrences), "controller_original_bindings_verified": len(bound_paths), "withheld_bindings_verified": len(mapping["withheld"]), "all_bound_original_blobs_equal_publication_blobs": True, "zip_git_blob": zip_blob},
    "frozen_harness": {"commit": HARNESS, "main_cherry_pick": CHERRY, "file_sha256": harness_hashes, "controller_copies_and_frozen_git_blobs_identical": True, "cherry_pick_and_publication_scripts_identical": True, "only_changed_paths_in_each_freeze_commit": sorted(expected_changed), "game_and_backend_trees_unchanged_by_each_freeze_commit": True, "prior_harness_diff_reviewed": OLD_HARNESS},
    "arms": {},
}

for label, meta in sorted(mapping["labels"].items()):
    arm = meta["original_arm"]
    summary = json.loads(original(meta["original_summary"]))
    assert summary["source"] == meta["source"] == summary["source_after"]
    assert summary["harness_checkout"] == meta["harness"] == summary["harness_after"]
    assert summary["harness_sha256"] == harness_hashes[source_names[0]] and summary["probe_sha256"] == harness_hashes[source_names[1]]
    rev = meta["source"]["measured_commit"]
    for subtree in ["game", "backend"]:
        assert gtext("rev-parse", rev + ":" + subtree) == summary["source"][subtree + "_tree"]
    assert summary["source"]["backend_tree"] == "67027b4fa17674ef067c84401af76eb1524419ac"
    assert summary["cache_source"]["game_tree"] == summary["source"]["game_tree"]
    archive = git("archive", "--format=zip", rev, "game", "backend")
    assert sha(archive) == summary["archive_sha256"]
    with zipfile.ZipFile(io.BytesIO(archive)) as zipped:
        archived = {info.filename: zipped.read(info) for info in zipped.infolist() if not info.is_dir()}
    source_manifest = json.loads(raw_evidence[PREFIX + arm + "/source-manifest.json"])
    assert {p: sha(b) for p, b in archived.items()} == source_manifest
    source_oids, source_blobs = objects(rev, "game", "backend")
    assert source_blobs.keys() == archived.keys()
    converted = 0
    for path, raw in source_blobs.items():
        if raw != archived[path]:
            assert b"\r\n" not in raw
            assert raw.replace(b"\n", b"\r\n") == archived[path]
            converted += 1

    rprefix = PREFIX + arm + "/run-1/"
    initial = json.loads(raw_evidence[rprefix + "fixture.redacted.json"])
    timeline = [json.loads(line) for line in raw_evidence[rprefix + "timeline.jsonl"].decode().splitlines()]
    phases = {}
    expected_sources = {"driver": harness_hashes[source_names[0]], "probe": harness_hashes[source_names[1]], "economy_ui": source_manifest["game/scripts/ui/economy_ui.gd"], "economy_api": source_manifest["game/scripts/ui/economy_api.gd"], "transaction_journal": source_manifest.get("game/scripts/ui/transaction_journal.gd", "")}
    for phase in ["send", "recovery", "second-restart"]:
        binding = json.loads(raw_evidence[rprefix + phase + ".launch-inputs.json"])
        config_bytes = raw_evidence[rprefix + phase + ".fixture.redacted.json"]
        config = json.loads(config_bytes)
        stdout_name = "killed-client" if phase == "send" else phase
        native = [json.loads(line.removeprefix("NATIVE_RECEIPT_EVENT ")) for line in raw_evidence[rprefix + stdout_name + ".stdout.txt"].decode().splitlines() if line.startswith("NATIVE_RECEIPT_EVENT ")]
        actual_read = one(native, event="fixture_read")
        prepared = one(timeline, event="native_inputs_prepared", phase=phase)
        started = one(timeline, event="native_started", phase=phase)
        finished = one(timeline, event="native_finished", phase=stdout_name)
        assert all(prepared[k] == v for k, v in binding.items())
        assert timeline.index(prepared) < timeline.index(started) < timeline.index(finished)
        assert actual_read["pid"] == started["pid"] == finished["pid"]
        assert {e["pid"] for e in native} == {started["pid"]}
        assert actual_read["sha256"] == binding["fixture_sha256"]
        assert actual_read["bytes"] == binding["fixture_bytes"]
        assert actual_read["keys"] == binding["keys"] == sorted(config)
        assert binding["source_file_sha256"] == expected_sources
        assert actual_read["source_file_sha256"] == {k:v for k,v in expected_sources.items() if k != "driver"}
        assert sha(config_bytes) == binding["redacted_fixture_sha256"]
        assert sha(json.dumps(binding["environment"], sort_keys=True, separators=(",", ":")).encode()) == binding["environment_sha256"]
        assert set(binding["environment"]) == constants["NATIVE_ENV_KEYS"] | {"SIGHTBREAK_RECEIPT_FIXTURE"}
        assert "DATABASE_URL" not in binding["environment"]
        assert binding["environment"]["SIGHTBREAK_RECEIPT_FIXTURE"] == binding["fixture_path"]
        command = binding["command"]
        assert len(command) == 7 and command[1:4] == ["--headless", "--verbose", "--path"] and command[5] == "--script"
        assert command[4] == binding["cwd"] == started["cwd"]
        assert command == started["command"]
        inputs = [binding["environment"], command, binding["cwd"]]
        if phase != "send":
            assert set(config) == constants["RETRY_CONFIG_KEYS"] and config["mode"] == "retry"
            assert all(config[k] == initial[k] for k in config if k != "mode")
            inputs.append(config)
        visible = json.dumps(inputs)
        forbidden = [initial[k] for k in ["path", "item", "listing", "seller"]] + [initial["payload"]["idempotency_key"], "expected_price", "idempotency_key"]
        assert all(value not in visible for value in forbidden)
        assert not re.search(r"(?<!\d)400(?!\d)", visible)
        private_path = Path(binding["fixture_path"])
        assert not private_path.exists(), "A retained private file needs separate secret-safe review"
        assert config["password"] == "[REDACTED]"
        assert binding["fixture_bytes"] - len(config_bytes) == len("receipt-oracle-") + 32 - len("[REDACTED]")
        phases[phase] = {"pid": started["pid"], "fixture_bytes": binding["fixture_bytes"], "fixture_sha256": binding["fixture_sha256"], "published_redacted_config_bytes": len(config_bytes), "prelaunch_native_hash_length_keys_source_pid_order_match": True, "redacted_file_hash_recomputed": True, "raw_environment_sha256_recomputed": binding["environment_sha256"], "full_environment_and_argv_purchase_values_absent": True, "native_sources_match_frozen_probe_and_shipping_archive": True, "private_config_retained": False}

    cache = json.loads(raw_evidence[PREFIX + arm + "/cache-manifest.json"])
    launch_arm = one(launch["arms"], label=arm)
    assert json.loads(raw_evidence[PREFIX + arm + ".command.json"]) == launch_arm["command"]
    command = launch_arm["command"]
    assert command[command.index("--revision") + 1] == rev
    assert command[command.index("--repetitions") + 1] == "1" and "--native-economy" not in command
    assert launch_arm["returncode"] == 0
    worker = int(re.search(r"Started server process \[(\d+)\]", raw_evidence[PREFIX + arm + "/service.stdout.txt"].decode())[1])
    private_root = Path(next(a[1] for a in meta["aliases"] if a[0] == "private_fixture_path")).parent
    assert not (private_root / "seeded-private.json").exists()
    assert not (private_root / "source/game").exists()
    audit["arms"][label] = {"source_commit": rev, "arm": arm, "game_tree": meta["source"]["game_tree"], "backend_tree": meta["source"]["backend_tree"], "archive_sha256_reproduced": sha(archive), "complete_source_manifest_entries_verified": len(archived), "archive_versus_git_LF_to_CRLF_only_files": converted, "other_archive_versus_git_differences": [], "relevant_archived_source_sha256": dict(expected_sources, backend_app=source_manifest["backend/app.py"]), "phases": phases, "cache_manifest_entries": len(cache), "cache_manifest_sha256": sha(raw_evidence[PREFIX + arm + "/cache-manifest.json"]), "historical_archive_and_private_directory_retained": False, "launcher_pid": launch_arm["pid"], "timeline_harness_pid": one(timeline, event="native_inputs_prepared", phase="send")["harness_pid"], "service_launcher_pid": summary["service"]["pid"], "service_log_worker_pid": worker, "pid_ancestry_independently_attested": False}

exe = Path(mapping["labels"]["Set-829261D1"]["aliases"][0][1])
audit["executable_current_file"] = {"path": str(exe), "exists": exe.is_file(), "executed": False}
if exe.is_file():
    audit["executable_current_file"]["sha256"] = sha(exe.read_bytes())
    assert audit["executable_current_file"]["sha256"] == "ab1824f85bfd8e0e4128182c000c4003a3e042245b2967848d089b2a04b22424"

audit["source_reasoning"] = {
    "probe_retry": "Frozen probe lines 17-30 read/hash the same parsed text and enforce six retry keys; lines 31-39 set only journal path before UI startup; lines 43-58 authenticate then call zero-argument _retry_pending. Purchase normalization and _perform are send-only.",
    "driver_input_boundary": "Frozen driver lines 361-394 truncate/capture the same fixture; 424-426 supply only allowlisted environment and fixed argv/cwd; 460-463 build retry_config from exactly RETRY_CONFIG_KEYS. Original transaction remains driver-side oracle context, not a retry argument. --expect-recovered is checked only in final acceptance.",
    "candidate": "UI lines 65-77 load journal; 504-527 retry requires same owner/server and fresh token, claims captured pending, and sends its path/payload/message/method. Journal lines 34-44 reread/check equality; 51-74 parse/validate/restore integer price; 76-102 stage before dispatch; 113-120 clear on successful resolution. UI 554-582 returns actual HTTP result after refresh.",
    "baseline": "UI has no journal source/property or startup load. _perform at 509-531 only creates in-memory pending after an uncertain response; _retry_pending at 495-507 returns empty on fresh startup.",
    "server_and_capture": "API lines 47-79 serializes supplied payload and returns decoded HTTP result. Proxy forwards actual bytes upstream, holds/discards only first response, and forwards retry upstream result. PostgreSQL market_buy replays matching stored Operation before settlement; independent repeatable-read snapshot uses a new connection.",
}
prior_path = REPO / "docs/reports/native-pg-restart-evidence/source-binding/source-binding-completion.json"
prior = load(prior_path)
audit["prior_source_closure_reuse"] = {"path": str(prior_path.relative_to(REPO)), "sha256": sha(prior_path.read_bytes()), "use": "Reused only as prior bound on identical shipping revisions/backend and disclosed cache/ancestry limits. New archive/input/source bindings and dataflow independently checked here; prior three-price runs are not evidence of the new run."}
audit["remaining_limits"] = [
    "Original secret-bearing fixture files and seeded-private.json are absent at their recorded paths. Redacted configs plus source explain their 37-byte password-length difference, but cannot reconstruct the private SHA256 or plaintext token digests.",
    "Complete source archives reproduce; historical copied cache payloads are not retained in these records. Each 62-entry manifest and same-game-tree identity is bound, not independent historical execution attestation.",
    "On-disk source hashes, clean-checkout/source-unchanged flags and raw traces are recorder-backed. Loaded/preloaded code, machine execution, and launcher/worker PID ancestry are not independently authenticated.",
    "journal_snapshot exists is bool(raw): its absence record alone cannot distinguish a nonexistent file from an existing zero-byte file. Baseline source has no persistent journal path and recovered result remains empty either way.",
    "Producer authoritative_pass/complete_result refer to common settlement invariants; stable_journal_at_kill can mean stable absence. The frozen outcome failure of baseline remains intact.",
    "No OS sandbox or exhaustive file-access trace. Source dataflow and supplied-input absence are accepted within the declared honest-recorder causal-control scope, without adversarial non-access claims.",
]
audit["strongest_remaining_gap"] = "Unauthenticated historical machine/cache/loaded-code execution and PID ancestry, rather than an unresolved inspected-source dataflow or transformation mismatch. This is a stated limit, not a blocker for scoped record-backed acceptance."
audit["unresolved_source_or_transformation_blockers"] = []
assert {n: sha((BLIND / n).read_bytes()) for n in before_originals} == before_originals
output = ROOT / "source-binding-audit.json"
assert not output.exists()
output.write_bytes((json.dumps(audit, indent=2, ensure_ascii=True) + "\n").encode())
print(json.dumps({"path": str(output), "bytes": output.stat().st_size, "sha256": sha(output.read_bytes()), "decision": audit["decision"], "transformation_audit": audit["transformation_audit"], "arms": {k: {x:v[x] for x in ["source_commit", "complete_source_manifest_entries_verified", "archive_versus_git_LF_to_CRLF_only_files", "launcher_pid", "timeline_harness_pid", "service_launcher_pid", "service_log_worker_pid"]} for k,v in audit["arms"].items()}}, indent=2))
