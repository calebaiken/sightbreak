"""Read-only Git-object collector for this post-freeze review, never a runtime."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess

OUT = Path(__file__).resolve().parent
REPO = Path(r"C:\Users\blith\AppData\Local\Temp\opencode\sightbreak-v3")
GIT = json.loads((OUT / "auditraw" / "00-initial.json").read_text(encoding="utf-8"))["git_executable"]
ENV = dict(os.environ, GIT_OPTIONAL_LOCKS="0", GIT_TERMINAL_PROMPT="0", GIT_NO_REPLACE_OBJECTS="1")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def git(args, save=None, allowed_exits=(0,)):
    assert args[0] in ("cat-file", "ls-tree", "rev-parse", "diff-tree", "diff"), args
    assert "--ext-diff" not in args and "--textconv" not in args
    indices = [int(p.name.split(".")[0]) for p in (OUT / "auditraw").glob("[0-9][0-9][0-9].command.json")]
    index = max(indices, default=0) + 1
    argv = [GIT, "--no-pager", "--no-optional-locks", "-C", str(REPO), *args]
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    result = subprocess.run(argv, env=ENV, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    stem = f"{index:03d}"
    (OUT / "auditraw" / f"{stem}.stdout.bin").write_bytes(result.stdout)
    (OUT / "auditraw" / f"{stem}.stderr.bin").write_bytes(result.stderr)
    (OUT / "auditraw" / f"{stem}.exit.txt").write_text(str(result.returncode) + "\n", encoding="ascii")
    record = {"number": index, "argv": argv, "started_utc": started, "completed_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "exit_code": result.returncode, "stdout_bytes": len(result.stdout), "stdout_sha256": sha(result.stdout), "stderr_bytes": len(result.stderr), "stderr_sha256": sha(result.stderr), "saved_object": save}
    (OUT / "auditraw" / f"{stem}.command.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    if save is not None and result.returncode == 0:
        target = OUT / "objects" / save
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(result.stdout)
    assert result.returncode in allowed_exits, {**record, "stderr": result.stderr.decode("utf-8", errors="replace")}
    return result.stdout


def write_json(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
