"""One-time CPU4 Git/file source proof. Never starts a producer or process model."""
import hashlib
import json
import os
from pathlib import Path
import subprocess

OWN=Path('/workspace/reviews/fov-owned-ancestry-r3-independent-20261024')
REPORT=Path(__file__).resolve().parent
BASE='329d3ff56e686fccdefa04151667ecb7841c3d64'
SOURCE='8cc38cdcd7dfff37056782149e513c08037e4e77'
HANDOFF='9807106cb79033cd00b69c1411c3808488c372bb'
BUILDER=Path('/workspace/sightbreak-fov-owned-ancestry-r3')
PREFIX='docs/reports/gauntlet/fov-owned-ancestry-r3-20261024/'
DEPTH=Path('/workspace/reviews/fov-owned-ancestry-r3-exact-depth1-20261024')
ALTERNATE='/workspace/sightbreak/.git/objects'


def git(*args,cwd=OWN,check=True):
    return subprocess.run(['git',*args],cwd=cwd,capture_output=True,check=check)


def tree(commit):
    result={}
    for raw in git('ls-tree','-rz',commit).stdout.split(b'\0'):
        if not raw:continue
        header,path=raw.split(b'\t',1);path=path.decode()
        if path.startswith('docs/'):continue
        mode,kind,oid=header.decode().split();result[path]=dict(mode=mode,kind=kind,oid=oid)
    return result


def verify(root,expected):
    physical=[];omitted=[]
    for path,info in sorted(expected.items()):
        file=root/path
        if not file.exists():omitted.append(path);continue
        raw=file.read_bytes();assert raw==git('cat-file','blob',info['oid']).stdout,(root,path,'bytes')
        assert bool(file.stat().st_mode & 0o111)==(info['mode']=='100755'),(root,path,'mode')
        physical.append(dict(path=path,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),**info))
    return dict(materialized=len(physical),physical=physical,omitted=omitted,all_materialized_bytes_modes_equal=True)


def main():
    assert os.sched_getaffinity(0)=={4}
    old,target=tree(BASE),tree(SOURCE)
    changes={p:dict(base=old.get(p),target=target.get(p)) for p in sorted(set(old)|set(target)) if old.get(p)!=target.get(p)}
    assert len(target)==525 and len(changes)==5
    assert not git('diff','--name-only',SOURCE,'HEAD','--','.',':(exclude)docs').stdout
    assert not git('diff','--name-only',SOURCE,HANDOFF,'--','.',':(exclude)docs').stdout
    assert not DEPTH.exists();DEPTH.mkdir()
    git('init','-q',cwd=DEPTH)
    (DEPTH/'.git/objects/info/alternates').write_text(ALTERNATE+'\n')
    (DEPTH/'.git/shallow').write_text(SOURCE+'\n')
    git('update-ref','refs/heads/critic-fov-ancestry-exact',SOURCE,cwd=DEPTH)
    git('symbolic-ref','HEAD','refs/heads/critic-fov-ancestry-exact',cwd=DEPTH)
    git('config','core.sparseCheckout','true',cwd=DEPTH)
    sparse=Path(git('rev-parse','--git-path','info/sparse-checkout').stdout.decode().strip()).read_text()
    (DEPTH/'.git/info/sparse-checkout').write_text(sparse)
    git('reset','--hard','-q',SOURCE,cwd=DEPTH)
    proof=[]
    for args in [('rev-parse','HEAD'),('rev-list','--count','HEAD'),('rev-parse','--verify','HEAD^'),('status','--porcelain=v1')]:
        value=git(*args,cwd=DEPTH,check=False);proof.append(dict(command=['git',*args],exit=value.returncode,stdout=value.stdout.decode(),stderr=value.stderr.decode()))
    assert proof[0]['stdout'].strip()==SOURCE and proof[1]['stdout'].strip()=='1' and proof[2]['exit']==128 and not proof[3]['stdout']
    dest=REPORT/'builder-handoff';dest.mkdir()
    for name in git('ls-tree','-r','--name-only',HANDOFF,'--',PREFIX).stdout.decode().splitlines():
        raw=git('show',HANDOFF+':'+name).stdout
        file=dest/name[len(PREFIX):];file.parent.mkdir(parents=True,exist_ok=True);file.write_bytes(raw)
        assert (BUILDER/name).read_bytes()==raw,name
    base_dir=REPORT/'frozen-control-source';base_dir.mkdir()
    for name in ['scripts/acquire_fov_math_reference.py','scripts/test_fov_math_reference.py','scripts/fixtures/fov_binary_protected_segments.json']:
        (base_dir/Path(name).name).write_bytes(git('show',BASE+':'+name).stdout)
    prior=Path('/workspace/reviews/objective-perception-math-independent-20261024/docs/reports/gauntlet/objective-perception-math-independent-20261024/process-source-r2/independent_controls.py')
    (base_dir/'literal_old_independent_controls.py').write_bytes(prior.read_bytes())
    result=dict(base=BASE,target=SOURCE,handoff=HANDOFF,non_doc_union=len(set(old)|set(target)),changed=changes,
                protected=len(set(old)&set(target))-3,views={str(v):verify(v,target) for v in [OWN,DEPTH,BUILDER]},
                depth_proof=proof,index_count=len(git('ls-files','-z',cwd=DEPTH).stdout.split(b'\0'))-1,
                shared_alternate=ALTERNATE,self_contained=False)
    (REPORT/'SOURCE_UNION_AND_DEPTH.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(union=result['non_doc_union'],changes=len(changes),protected=result['protected'],
                         views={p:v['materialized'] for p,v in result['views'].items()},depth_index=result['index_count'])))


if __name__=='__main__':main()
