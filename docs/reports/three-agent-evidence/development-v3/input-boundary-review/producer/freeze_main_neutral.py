"""Freeze the main-author component assessment without opening source identity."""
import datetime
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent
paths = [root / "MAIN_NEUTRAL_COMPONENT_VERDICT.md",
         root / "attempt-r3" / "neutral" / "RESULTS.json"]
record = {
    "frozen_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "private_mapping_opened": False,
    "assessment": "Main-author neutral component assessment, not independent QA",
    "files": [{"path": str(path.relative_to(root)), "bytes": path.stat().st_size,
               "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
              for path in paths],
}
with (root / "MAIN_NEUTRAL_FREEZE.json").open("x", encoding="utf-8") as stream:
    json.dump(record, stream, indent=2)
    stream.write("\n")
print(json.dumps(record, indent=2))
