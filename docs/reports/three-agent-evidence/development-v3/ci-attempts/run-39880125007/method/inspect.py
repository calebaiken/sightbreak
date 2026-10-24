"""Offline receipt audit; never import or execute project code or artifact payloads."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import zipfile

REPO = Path(r"C:\Users\blith\AppData\Local\Temp\opencode\sightbreak-v3")
EVIDENCE = Path(r"C:\Users\blith\AppData\Local\Temp\opencode\sightbreak-v3-evidence\ci-39880125007")
OUT = Path(__file__).parent
FROZEN = "2a026e61cabee3c66334066d45e92eb3ec6c2641"
PACKET = "docs/reports/three-agent-evidence/development-v3/ci-attempts/run-39880125007/"
ENV = dict(os.environ, GIT_OPTIONAL_LOCKS="0", PYTHONDONTWRITEBYTECODE="1")

def sha(data):
    return hashlib.sha256(data).hexdigest()

def git(*args):
    return subprocess.check_output(["git", "-c", "core.fsmonitor=false", *args], cwd=REPO, env=ENV)

def write(path, data):
    p = OUT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("xb") as f:
        f.write(data)

def dump(path, data):
    write(path, (json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode())

def snapshot(label):
    status = git("status", "--porcelain=v2", "--branch", "--untracked-files=all")
    write(label + "-status.txt", status)
    names = git("ls-files", "-z", "--cached", "--others", "--exclude-standard").split(b"\0")
    files = {}
    for item in names:
        name = item.decode("utf-8", "surrogateescape")
        if not name or name.startswith(PACKET):
            continue
        p = REPO / name
        if p.is_file():
            files[name] = {"bytes": p.stat().st_size, "sha256": sha(p.read_bytes())}
        else:
            files[name] = {"missing": True}
    index = Path(git("rev-parse", "--git-path", "index").decode().strip())
    if not index.is_absolute():
        index = REPO / index
    dump(label + "-snapshot.json", {
        "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "head": git("rev-parse", "HEAD").decode().strip(),
        "refs": git("show-ref").decode(),
        "index_sha256": sha(index.read_bytes()),
        "status_sha256": sha(status), "files_excluding_authorized_packet": files,
    })

def main():
    snapshot("before")
    ancestors = []
    for parent in [REPO, *REPO.parents]:
        p = parent / "AGENTS.md"
        if p.is_file():
            ancestors.append({"path": str(p), "text": p.read_text(encoding="utf-8")})
    dump("ancestor-instructions.json", ancestors)
    print("ANCESTOR INSTRUCTIONS", json.dumps(ancestors))
    tree = git("ls-tree", "-r", "--full-tree", FROZEN).decode()
    write("frozen-ls-tree.txt", tree.encode())
    print("FROZEN SCRIPTS")
    for line in tree.splitlines():
        name = line.split("\t", 1)[1]
        if name.startswith(("scripts/", ".github/workflows/")):
            print(name)
    sources = []
    for line in tree.splitlines():
        meta, name = line.split("\t", 1)
        if name.startswith(("scripts/", ".github/workflows/")) and name.endswith((".py", ".sh", ".yml", ".yaml")):
            data = git("show", FROZEN + ":" + name)
            write("frozen/" + name, data)
            sources.append({"path": name, "git_object": meta.split()[2], "sha256": sha(data), "bytes": len(data)})
    dump("frozen-selected-source-manifest.json", sources)
    inventory = {}
    for p in sorted(EVIDENCE.glob("*.zip")):
        with zipfile.ZipFile(p) as z:
            entries = [{"name": i.filename, "bytes": i.file_size, "compressed": i.compress_size,
                        "crc32": f"{i.CRC:08x}", "mode": oct(i.external_attr >> 16),
                        "create_system": i.create_system} for i in z.infolist()]
            inventory[p.name] = entries
            print("ARCHIVE", p.name, "members", len(entries), "uncompressed", sum(i["bytes"] for i in entries))
            if "12470965068" in p.name or "12470681259" in p.name or p.name == "run-logs.zip":
                for i in entries:
                    print(i["bytes"], i["name"])
            else:
                print("MATRIX TOP LOGS")
                for i in entries:
                    if i["name"].count("/") <= 3 or "nested-resource" in i["name"]:
                        print(i["bytes"], i["name"])
    dump("archive-inventory.json", inventory)

if __name__ == "__main__":
    main()
