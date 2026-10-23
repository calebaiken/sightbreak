#!/usr/bin/env bash
set -euo pipefail
repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"
if [[ -z "${SIGHTBREAK_SERVER_KEY:-}" ]]; then
  mkdir -p .local/secrets
  chmod 700 .local/secrets
  .venv/bin/python - <<'PY'
import os
import secrets
from pathlib import Path
path = Path('.local/secrets/server.key')
try:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
except FileExistsError:
    if path.is_symlink() or not path.is_file():
        raise SystemExit('Local server credential path is not a regular file')
    os.chmod(path, 0o600)
else:
    with os.fdopen(fd, 'w') as output:
        output.write(secrets.token_urlsafe(48))
PY
  SIGHTBREAK_SERVER_KEY="$(cat .local/secrets/server.key)"
  export SIGHTBREAK_SERVER_KEY
fi
export SIGHTBREAK_SERVER_ID="${SIGHTBREAK_SERVER_ID:-local-relay}"
exec .venv/bin/python -m uvicorn app:app --app-dir backend --host 127.0.0.1 --port "${SIGHTBREAK_API_PORT:-8080}"
