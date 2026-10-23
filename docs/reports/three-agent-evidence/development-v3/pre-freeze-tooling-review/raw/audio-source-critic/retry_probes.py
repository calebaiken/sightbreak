"""Retain the initial critic-fixture path failure; rerun in a new fixture directory."""
import hashlib
import json
import os
from pathlib import Path

import audit

env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", TEMP=str(audit.EVIDENCE / "scratch"),
           TMP=str(audit.EVIDENCE / "scratch"),
           NEGATIVE_AUDIO_TEST_OUT=str(audit.EVIDENCE / "independent-probe-fixtures-retry"),
           AUDIO_CRITIC_PROBE_LABEL="independent-probes-retry")
code = audit.run_receipted("independent-probes-retry", [str(audit.EXACT_PYTHON), "-B",
    str(audit.EVIDENCE / "audit.py"), "--probes"], env=env)
before = json.loads((audit.EVIDENCE / "source-hashes-before.json").read_text(encoding="utf-8"))
after = [{"path": row["path"], "bytes": (audit.REPO / row["path"]).stat().st_size,
          "sha256": hashlib.sha256((audit.REPO / row["path"]).read_bytes()).hexdigest()} for row in before["files"]]
audit.write_json(audit.EVIDENCE / "source-hashes-after-retry.json", {
    "files": after, "unchanged": after == before["files"], "native_executed": False})
audit.write_json(audit.EVIDENCE / "audit-retry.result.json", {
    "independent_probe_retry_exit": code, "reviewed_source_unchanged": after == before["files"],
    "native_executed": False,
    "initial_failure": "Critic-only nested unittest class id contained <locals>, invalid in Windows directory names. Initial raw failure preserved, no product finding.",
    "critic_script_sha256": hashlib.sha256((audit.EVIDENCE / "audit.py").read_bytes()).hexdigest(),
})
raise SystemExit(code)
