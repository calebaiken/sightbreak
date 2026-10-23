"""Recompute source identity from frozen Git objects without native execution."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
SOURCE='3b97a0043fc415c2408ed774f38710ac022cfd72'
SHA=lambda raw:hashlib.sha256(raw).hexdigest()
def git(*args):
    return subprocess.check_output(['git', *args], cwd=CHECKOUT)

def source_identity():
    paths = git('ls-tree','-rz','--name-only',SOURCE).decode().split('\0')[:-1]
    shipping = hashlib.sha256()
    validation = hashlib.sha256()
    inventory = []
    groups = [[p for p in paths if p.startswith('game/') and 'tests' not in Path(p).parts and '.godot' not in Path(p).parts]]
    groups += [[p for p in paths if p.startswith(directory+'/')] for directory in ('scripts','.github','game/tests')]
    for index,group in enumerate(groups):
        for path in sorted(group):
            if any(p in ('__pycache__','.godot') for p in Path(path).parts) or path.endswith('.pyc'):
                continue
            raw = git('show',SOURCE+':'+path)
            name = path.removeprefix('game/') if index == 0 else path
            (shipping if index == 0 else validation).update(name.encode()+b'\0'+raw+b'\0')
            inventory.append({'scope':'shipping' if index == 0 else 'validation','path':path,'bytes':len(raw),'sha256':SHA(raw)})
    return {'source_commit':SOURCE,'source_game_tree':git('rev-parse',SOURCE+':game').decode().strip(),
            'source_content_sha256':shipping.hexdigest(),'source_validation_sha256':validation.hexdigest(),
            'method':'Independent framed SHA256 of sorted tracked Git-object bytes, with shipping tests excluded and validation directories in declared order',
            'files':inventory}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('checkout',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();CHECKOUT=args.checkout
    args.output.write_text(json.dumps(source_identity(),indent=2)+'\n')
