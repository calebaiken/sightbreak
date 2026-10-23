#!/usr/bin/env python3
"""Materialize an initialized exact-commit source fixture without ancestry/remotes."""
import argparse
import json
from pathlib import Path
import subprocess
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--source', type=Path, required=True)
p.add_argument('--destination', type=Path, required=True)
p.add_argument('--commit', required=True)
a = p.parse_args()
source, destination = a.source.resolve(), a.destination.resolve()
if destination.exists(): raise SystemExit('Fresh nonexistent destination required')
def git(*args, cwd=source, data=None):
    return subprocess.run(['git', *args], cwd=cwd, input=data, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True).stdout
candidate = git('rev-parse', a.commit + '^{commit}').decode().strip()
git('init', '--initial-branch=fixture', str(destination))
paths = git('ls-tree', '-r', '--name-only', candidate, 'game', 'scripts', 'docs/reports/gauntlet/m5-objective-observability').decode().splitlines()
objects = git('rev-list', '--objects', '--filter=blob:none', '--no-object-names', '--max-count=1', candidate).decode().splitlines()
objects += [git('rev-parse', candidate + ':' + path).decode().strip() for path in paths]
pack = git('pack-objects', '--stdout', '--threads=1', data=('\n'.join(sorted(set(objects)))+'\n').encode())
git('index-pack', '--stdin', cwd=destination, data=pack)
(destination / '.git/shallow').write_text(candidate + '\n')
git('update-ref', 'refs/heads/fixture', candidate, cwd=destination)
git('config', 'core.sparseCheckout', 'true', cwd=destination)
(destination / '.git/info/sparse-checkout').write_text('\n'.join('/' + path for path in paths) + '\n')
git('read-tree', '-mu', 'HEAD', cwd=destination)
print(json.dumps({'head': git('rev-parse','HEAD',cwd=destination).decode().strip(), 'shallow':git('rev-parse','--is-shallow-repository',cwd=destination).decode().strip(),'reachable_commits':git('rev-list','--count','HEAD',cwd=destination).decode().strip(),'status':git('status','--short',cwd=destination).decode(),'remotes':git('remote','-v',cwd=destination).decode(),'alternates_present':(destination/'.git/objects/info/alternates').exists(),'source_paths':len(paths),'pack_bytes':len(pack),'destination':str(destination)},indent=2))
