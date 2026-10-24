"""Freeze only this explicitly authorized external verdict directory."""
import datetime
import hashlib
import json
from pathlib import Path
import stat
import sys


ROOT = Path(__file__).resolve().parent
NAMES = {
    "NEUTRAL_RETENTION_VERDICT.md", "per_workload_judgments.json", "input_hashes.json",
    "packet_verifier.stdout.json", "packet_verifier.stderr.txt", "packet_verifier_execution.json",
    "independent_audit.py", "freeze_artifacts.py",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    require(sys.version_info[:3] == (3, 13, 15) and sys.flags.isolated and sys.flags.no_site and sys.flags.dont_write_bytecode and not sys.flags.optimize, "Use approved CPython 3.13.15 -I -S -B, no -O")
    require(not (ROOT / "FROZEN.json").exists() and not (ROOT / "SHA256SUMS.txt").exists(), "Already frozen: preserve and use a separate addendum")
    require({p.name for p in ROOT.iterdir()} == NAMES, "Unexpected or missing external payload")
    inputs = json.loads((ROOT / "input_hashes.json").read_bytes())
    assessment = json.loads((ROOT / "per_workload_judgments.json").read_bytes())
    packet = Path(inputs["packet_root"])
    for entry in inputs["packet_input_files"]:
        data = (packet / entry["path"]).read_bytes()
        require(len(data) == entry["bytes"] and digest(data) == entry["sha256"], f"Packet changed before freeze: {entry['path']}")
    require({p.relative_to(packet).as_posix() for p in packet.rglob("*") if p.is_file()} == {entry["path"] for entry in inputs["packet_input_files"]}, "Packet inventory changed")
    prior = inputs["first_round_verdict"]
    require(digest(Path(prior["path"]).read_bytes()) == prior["sha256"] == "f76906b5b3ee735d65eedef6bf23998d274a614778fb9e76c196ba39957bfdfa", "First verdict changed")
    require(inputs["packet_manifest_sha256_actual"] == inputs["packet_manifest_sha256_expected"] == "dd07a3bfd69e09e27c43257be3a719d001c5d8446a9338746460829887c86d64", "Wrong input anchor")
    totals = assessment["totals"]
    require([totals[k] for k in ("workload_records", "received_responses", "timed_samples", "full_table_snapshots", "aggregate_states_reconstructed")] == [14, 168, 140, 336, 28], "Wrong assessment totals")
    execution = json.loads((ROOT / "packet_verifier_execution.json").read_bytes())
    require(execution["exit_code"] == 0 and execution["stderr_bytes"] == 0, "Verifier execution did not pass cleanly")
    for stream, filename in (("stdout", "packet_verifier.stdout.json"), ("stderr", "packet_verifier.stderr.txt")):
        data = (ROOT / filename).read_bytes()
        require(digest(data) == execution[f"{stream}_sha256"] and len(data) == execution[f"{stream}_bytes"], "Raw verifier stream changed")
    decision = assessment["decision"]
    require(decision["preferred_label"] == "V" and decision["narrow_verdict"] == "ACCEPT WITH QUALIFICATIONS", "Decision mismatch")
    artifacts = []
    for name in sorted(NAMES):
        data = (ROOT / name).read_bytes()
        artifacts.append({"path": name, "bytes": len(data), "sha256": digest(data)})
    frozen = {
        "schema": "neutral-retention-r2-pre-mapping-freeze-v1",
        "frozen_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "packet_root": str(packet), "packet_manifest_sha256": inputs["packet_manifest_sha256_actual"],
        "preserved_first_verdict": prior, "first_verdict_rechecked_unchanged": True,
        "blind_status": "Anonymous M/V only; identity key/source/repository/owner reports not inspected; no source or cross-round assignment asserted",
        "blinding_limit": assessment["blinding_limit"], "decision": decision,
        "verified_totals": totals, "r1_gap_resolution": assessment["r1_gap_resolution"],
        "artifacts": artifacts, "windows_read_only_attribute_requested": True,
        "immutability_limit": "Hash-frozen and best-effort local read-only files, not WORM storage, trusted timestamp, or third-party capture attestation",
        "preservation_rule": "Preserve both verdicts unchanged. Any mapping/source binding or changed judgment belongs in a separate post-unblinding addendum citing freeze hashes.",
    }
    (ROOT / "FROZEN.json").write_bytes(json.dumps(frozen, indent=2, sort_keys=True, ensure_ascii=True, allow_nan=False).encode("utf-8") + b"\n")
    covered = NAMES | {"FROZEN.json"}
    manifest = "".join(f"{digest((ROOT / name).read_bytes())}  {name}\n" for name in sorted(covered)).encode("utf-8")
    (ROOT / "SHA256SUMS.txt").write_bytes(manifest)
    for line in manifest.decode("utf-8").splitlines():
        expected, name = line.split("  ", 1)
        require(digest((ROOT / name).read_bytes()) == expected, f"Frozen hash mismatch: {name}")
    for name in sorted(covered | {"SHA256SUMS.txt"}):
        (ROOT / name).chmod(stat.S_IREAD)
    require(all((ROOT / name).stat().st_file_attributes & stat.FILE_ATTRIBUTE_READONLY for name in covered | {"SHA256SUMS.txt"}), "Read-only attribute was not applied")
    print(json.dumps({
        "directory": str(ROOT), "frozen_utc": frozen["frozen_utc"], "all_frozen_hashes_verified": True,
        "covered_files": len(covered), "all_external_files_read_only": True,
        "external_manifest_sha256": digest((ROOT / "SHA256SUMS.txt").read_bytes()),
        "artifact_hashes": {name: digest((ROOT / name).read_bytes()) for name in sorted(covered)},
        "first_verdict_unchanged_sha256": prior["sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()
