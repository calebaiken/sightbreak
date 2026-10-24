#!/usr/bin/env python3
"""Build exact-commit source-only shallow fixture without remote/filter dependence."""
from pathlib import Path
import json
import subprocess
import sys
source = Path(sys.argv[1]).resolve()
fixture = Path(sys.argv[2]).resolve()
candidate = "c91d9b98a293ef8605d99ae6e83402d3af983519"
def git(*args, cwd=source, input=None):
    return subprocess.run(["git", *args], cwd=cwd, input=input,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
git("init", "--initial-branch=fixture", str(fixture))
paths = git("ls-tree", "-r", "--name-only", candidate, "scripts", "game/scripts",
            "game/tests", "docs/reports/gauntlet/m5-objective-observability").stdout.decode().splitlines()
objects = git("rev-list", "--objects", "--filter=blob:none", "--no-object-names",
              "--max-count=1", candidate).stdout.decode().splitlines()
objects += [git("rev-parse", candidate + ":" + path).stdout.decode().strip() for path in paths]
objects = sorted(set(objects))
pack = git("pack-objects", "--stdout", "--threads=1", input=("\n".join(objects)+"\n").encode()).stdout
index = git("index-pack", "--stdin", cwd=fixture, input=pack).stdout.decode().strip()
(fixture / ".git/shallow").write_text(candidate + "\n")
git("update-ref", "refs/heads/fixture", candidate, cwd=fixture)
git("config", "core.sparseCheckout", "true", cwd=fixture)
(fixture / ".git/info/sparse-checkout").write_text("\n".join("/"+path for path in paths)+"\n")
git("read-tree", "-mu", "HEAD", cwd=fixture)
print(json.dumps({"fixture":str(fixture), "head":git("rev-parse","HEAD",cwd=fixture).stdout.decode().strip(),
 "shallow":git("rev-parse","--is-shallow-repository",cwd=fixture).stdout.decode().strip(),
 "commit_count":git("rev-list","--count","HEAD",cwd=fixture).stdout.decode().strip(),
 "remotes":git("remote","-v",cwd=fixture).stdout.decode(),
 "status":git("status","--short",cwd=fixture).stdout.decode(),
 "hydrated_paths":len(paths), "copied_objects":len(objects), "pack_bytes":len(pack),
 "index_pack":index}, indent=2))
