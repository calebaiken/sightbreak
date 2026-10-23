#!/usr/bin/env python3
"""Package unchanged raw evidence with a complete index and bounded Git parts."""
import hashlib
import json
from pathlib import Path
import tarfile

RAW = Path(__file__).resolve().parent
REPORT = Path("/workspace/sightbreak-touch-contrast-recovered/docs/reports/gauntlet/m6-touch-contrast-recovered/native-r4b-r3")
ARCHIVE = RAW.with_suffix(".tar.xz")


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    end = json.loads((RAW / "lane-end.json").read_text())
    assert isinstance(end["acquisition_complete"], bool), end
    assert end["display_socket_absent"] and end["display_lock_absent"]
    assert all(x["proc_path_absent"] for x in end["owned_cleanup"])
    assert not ARCHIVE.exists()
    REPORT.mkdir(parents=True, exist_ok=False)
    paths = sorted(p for p in RAW.rglob("*") if p.is_file())
    entries = [{"path": str(p.relative_to(RAW)), "bytes": p.stat().st_size, "sha256": sha(p)} for p in paths]
    manifest = {"raw_root": str(RAW), "files": entries, "file_count": len(entries),
                "raw_bytes": sum(x["bytes"] for x in entries),
                "png_count": sum(x["path"].endswith(".png") for x in entries),
                "source_freeze": "108d1cdc6cf471daa7390298c234bb1c087ae865",
                "acquisition_complete": end["acquisition_complete"], "acquisition_error": end["error"]}
    index = REPORT / "payload-manifest.json"
    index.write_text(json.dumps(manifest, indent=2) + "\n")
    print("INDEX", len(entries), manifest["raw_bytes"], "PNG", manifest["png_count"], flush=True)
    with tarfile.open(ARCHIVE, "w:xz", preset=6) as bundle:
        bundle.add(index, arcname="payload-manifest.json", recursive=False)
        for n, entry in enumerate(entries):
            bundle.add(RAW / entry["path"], arcname="raw/" + entry["path"], recursive=False)
            if n and n % 500 == 0:
                print("ARCHIVED", n, flush=True)
    parts = []
    with ARCHIVE.open("rb") as stream:
        number = 0
        while chunk := stream.read(24 * 1024 * 1024):
            path = REPORT / ("evidence.tar.xz.part-%03d" % number)
            path.write_bytes(chunk)
            parts.append({"path": path.name, "bytes": len(chunk), "sha256": sha(path)})
            number += 1
    receipt = {"archive_local_path": str(ARCHIVE), "archive_bytes": ARCHIVE.stat().st_size,
               "archive_sha256": sha(ARCHIVE), "parts": parts, "payload_manifest_sha256": sha(index),
               "members": len(entries) + 1, "file_count": len(entries), "raw_bytes": manifest["raw_bytes"],
               "png_count": manifest["png_count"], "all_raw_files_retained": True}
    (REPORT / "ARCHIVE.json").write_text(json.dumps(receipt, indent=2) + "\n")
    # Re-read every archive member rather than trusting tar creation alone.
    expected = {"raw/" + e["path"]: e for e in entries}
    expected["payload-manifest.json"] = {"bytes": index.stat().st_size, "sha256": sha(index)}
    seen = set()
    with tarfile.open(ARCHIVE, "r:xz") as bundle:
        for member in bundle:
            assert member.name in expected and member.name not in seen
            assert member.isfile() and member.size == expected[member.name]["bytes"]
            data = bundle.extractfile(member)
            digest = hashlib.sha256()
            for chunk in iter(lambda: data.read(1024 * 1024), b""):
                digest.update(chunk)
            assert digest.hexdigest() == expected[member.name]["sha256"], member.name
            seen.add(member.name)
    assert seen == set(expected)
    print("VERIFIED", json.dumps(receipt), flush=True)


if __name__ == "__main__":
    main()
