"""CPU4 Git/file-only initialization and exact source-union evidence."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

OWN = Path(__file__).resolve().parents[5]
REPORT = Path(__file__).resolve().parent
TARGET = '329d3ff56e686fccdefa04151667ecb7841c3d64'
BASE = 'b6f25804cddc3e48faeec613a2daa7f392fb1990'
HANDOFF = '64afaa4132c1f1e1c1376f5269b46ff9918aa9a6'
DEPTH = Path('/workspace/reviews/objective-perception-codec-exact-depth1-20261024')
ALTERNATE = '/workspace/sightbreak/.git/objects'
BUILDER = Path('/workspace/sightbreak-fov-exact-binary-input')
PREFIX = Path('docs/reports/gauntlet/fov-exact-binary-input-20261024')


def git(*args, cwd=OWN, check=True):
    return subprocess.run(['git', *args], cwd=cwd, capture_output=True, check=check)


def tree(commit):
    result = {}
    for raw in git('ls-tree', '-rz', commit).stdout.split(b'\0'):
        if not raw:
            continue
        header, path = raw.split(b'\t', 1)
        path = path.decode()
        if path.startswith('docs/'):
            continue
        mode, kind, oid = header.decode().split()
        result[path] = dict(mode=mode, kind=kind, oid=oid)
    return result


def verify(view, expected):
    physical, omitted = [], []
    for path, item in sorted(expected.items()):
        file = view/path
        if not file.exists():
            omitted.append(path)
            continue
        actual = file.read_bytes()
        wanted = git('cat-file', 'blob', item['oid']).stdout
        assert actual == wanted, (view, path, 'bytes')
        assert bool(file.stat().st_mode & 0o111) == (item['mode'] == '100755'), (view, path, 'mode')
        physical.append(dict(path=path, bytes=len(actual), sha256=hashlib.sha256(actual).hexdigest(), **item))
    return dict(materialized=len(physical), omitted=omitted, physical=physical,
                all_materialized_blobs_and_modes_equal=True)


def main():
    assert os.sched_getaffinity(0) == {4}
    expected, base = tree(TARGET), tree(BASE)
    changed = {p: dict(base=base.get(p), target=expected.get(p)) for p in sorted(set(base)|set(expected))
               if base.get(p) != expected.get(p)}
    assert len(expected) == 523 and len(changed) == 8
    assert not git('diff', '--name-only', TARGET, 'HEAD', '--', '.', ':(exclude)docs').stdout
    assert not git('diff', '--name-only', TARGET, HANDOFF, '--', '.', ':(exclude)docs').stdout
    # Only a new, absent, owned view can be initialized. It shares objects and
    # intentionally has one reachable commit; no historical Git is a test oracle.
    assert not DEPTH.exists(), 'never replace/reinitialize an existing view'
    DEPTH.mkdir()
    git('init', '-q', cwd=DEPTH)
    (DEPTH/'.git/objects/info/alternates').write_text(ALTERNATE+'\n')
    (DEPTH/'.git/shallow').write_text(TARGET+'\n')
    git('update-ref', 'refs/heads/critic-codec-exact-source', TARGET, cwd=DEPTH)
    git('symbolic-ref', 'HEAD', 'refs/heads/critic-codec-exact-source', cwd=DEPTH)
    git('config', 'core.sparseCheckout', 'true', cwd=DEPTH)
    sparse = Path(git('rev-parse', '--git-path', 'info/sparse-checkout').stdout.decode().strip()).read_text()
    (DEPTH/'.git/info/sparse-checkout').write_text(sparse)
    git('reset', '--hard', '-q', TARGET, cwd=DEPTH)
    proof=[]
    for args in [('rev-parse','HEAD'),('rev-list','--count','HEAD'),('rev-parse','--verify','HEAD^'),('status','--porcelain=v1')]:
        value=git(*args,cwd=DEPTH,check=False)
        proof.append(dict(command=['git',*args],exit=value.returncode,stdout=value.stdout.decode(),stderr=value.stderr.decode()))
    assert proof[0]['stdout'].strip()==TARGET and proof[1]['stdout'].strip()=='1'
    assert proof[2]['exit']==128 and proof[3]['stdout']==''
    builder_dir=BUILDER/PREFIX
    shutil.copytree(builder_dir,REPORT/'builder-handoff')
    for file in sorted(builder_dir.rglob('*')):
        if file.is_file():
            rel=(PREFIX/file.relative_to(builder_dir)).as_posix()
            assert git('show',HANDOFF+':'+rel).stdout==file.read_bytes(),rel
    result=dict(base=BASE,target=TARGET,handoff=HANDOFF,full_non_doc_union=len(set(base)|set(expected)),
                target_non_doc=len(expected),changed=changed,protected=len(set(base)&set(expected))-4,
                views={str(v):verify(v,expected) for v in (OWN,DEPTH)},
                initialized_depth_view=str(DEPTH),depth_proof=proof,
                index_count=len(git('ls-files','-z',cwd=DEPTH).stdout.split(b'\0'))-1,
                shared_alternate=ALTERNATE,self_contained=False)
    (REPORT/'SOURCE_UNION_AND_DEPTH.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(target=TARGET,union=result['full_non_doc_union'],changed=len(changed),
                         protected=result['protected'],materialized={p:v['materialized'] for p,v in result['views'].items()},
                         depth_index=result['index_count'])))


if __name__ == '__main__':
    main()
