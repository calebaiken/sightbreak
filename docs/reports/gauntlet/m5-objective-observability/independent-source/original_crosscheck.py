#!/usr/bin/env python3
"""Check retained historical bytes and five gameplay identities without an engine."""
from pathlib import Path
import hashlib
import io
import json
import subprocess
import sys
import zipfile
root = Path(sys.argv[1]).resolve()
report = root / "docs/reports/gauntlet/m5-objective-observability"
identity = json.loads((report / "benchmark-identity.json").read_text())
base = identity["base_commit"]
original = "05277154c6b8c92b80fd7c25e8365de9efdc4fae"
def show(rev, path):
    return subprocess.check_output(["git", "show", f"{rev}:{path}"], cwd=root)
def digest(data):
    return hashlib.sha256(data).hexdigest()
source = {}
for path, expected in identity["source"].items():
    baseline, historical = show(base, path), show(original, path)
    source[path] = {"manifest_sha256": expected, "base_actual_sha256": digest(baseline),
                    "original_0527715_sha256": digest(historical),
                    "manifest_matches_base": digest(baseline) == expected,
                    "original_equals_base": baseline == historical}
archive = show(base, identity["archive_git_path"])
with zipfile.ZipFile(io.BytesIO(archive)) as z:
    raw = z.read(identity["member"])
lines = raw.splitlines(keepends=True)
rows = [json.loads(line) for line in lines]
selected = b"".join(line for line,row in zip(lines, rows)
                    if row["event_index"] in identity["selected_event_indices"])
print(json.dumps({"source": source, "archive_sha256": digest(archive),
 "archive_sha256_matches": digest(archive) == identity["archive_sha256"],
 "member_sha256": digest(raw), "member_sha256_matches": digest(raw) == identity["member_sha256"],
 "member_rows": len(rows), "selected_bytes_match": selected == (report / "original-timeout-slice.jsonl").read_bytes(),
 "has_planted_state_rows": any(row.get("objective_state") == "planted" for row in rows)}, indent=2))
