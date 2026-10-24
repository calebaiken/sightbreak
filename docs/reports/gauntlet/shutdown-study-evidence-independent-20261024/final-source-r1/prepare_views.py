"""One-time source/index/baseline evidence; no candidate module execution."""
import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess

OWN=Path('/workspace/reviews/shutdown-study-evidence-independent-20261024')
REPORT=Path(__file__).resolve().parent
BASE='1add0f828b26b86b9bc2ec9e02c4208e31bb2e5a'
SOURCE='0f478a078277fdb0d711837bef67cf14262d9d8f'
HANDOFF='99a864a8e1ab05d25ba0f0db92552326377e2a00'
BUILDER=Path('/workspace/sightbreak-windows-shutdown-evidence-completeness-frozen')
PREFIX='docs/reports/gauntlet/windows-shutdown-evidence-completeness-20261024/'
DEPTH=Path('/workspace/reviews/shutdown-study-evidence-independent-depth1-20261024')
ALTERNATE='/workspace/sightbreak/.git/objects'
LEGACY='8ee93ac725d519c9f6d7f1ffbb3f7c9ee960baf8'


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
    assert len(target)==516 and len(changes)==5
    assert not git('diff','--name-only',SOURCE,'HEAD','--','.',':(exclude)docs').stdout
    assert not git('diff','--name-only',SOURCE,HANDOFF,'--','.',':(exclude)docs').stdout
    # The new pure checker explicitly reads this exact tracked GDScript as data.
    # Restore only that dependency, never a bulk game/asset tree.
    git('restore','--source='+SOURCE,'--worktree','--ignore-skip-worktree-bits','--','game/scripts/profile.gd')
    assert not DEPTH.exists();DEPTH.mkdir()
    git('init','-q',cwd=DEPTH);(DEPTH/'.git/objects/info/alternates').write_text(ALTERNATE+'\n')
    (DEPTH/'.git/shallow').write_text(SOURCE+'\n')
    git('update-ref','refs/heads/critic-shutdown-evidence-exact',SOURCE,cwd=DEPTH)
    git('symbolic-ref','HEAD','refs/heads/critic-shutdown-evidence-exact',cwd=DEPTH)
    git('config','core.sparseCheckout','true',cwd=DEPTH)
    sparse=Path(git('rev-parse','--git-path','info/sparse-checkout').stdout.decode().strip()).read_text()
    (DEPTH/'.git/info/sparse-checkout').write_text(sparse+'\n/game/scripts/profile.gd\n')
    git('reset','--hard','-q',SOURCE,cwd=DEPTH)
    proof=[]
    for args in [('rev-parse','HEAD'),('rev-list','--count','HEAD'),('rev-parse','--verify','HEAD^'),('status','--porcelain=v1')]:
        value=git(*args,cwd=DEPTH,check=False);proof.append(dict(command=['git',*args],exit=value.returncode,stdout=value.stdout.decode(),stderr=value.stderr.decode()))
    assert proof[0]['stdout'].strip()==SOURCE and proof[1]['stdout'].strip()=='1' and proof[2]['exit']==128 and not proof[3]['stdout']
    dest=REPORT/'builder-handoff';dest.mkdir()
    for name in git('ls-tree','-r','--name-only',HANDOFF,'--',PREFIX).stdout.decode().splitlines():
        file=dest/name[len(PREFIX):];file.parent.mkdir(parents=True,exist_ok=True);file.write_bytes(git('show',HANDOFF+':'+name).stdout)
    control=REPORT/'frozen-control-source';control.mkdir()
    for name in ['scripts/windows_shutdown_study.py','scripts/test_windows_shutdown_study.py','scripts/verify_offline_export.py','scripts/shutdown_study_retention.py']:
        (control/Path(name).name).write_bytes(git('show',BASE+':'+name).stdout)
    legacy=git('show',LEGACY+':scripts/verify_offline_export.py').stdout
    (control/'verify_offline_export-8ee93ac7.py').write_bytes(legacy)
    current=git('show',SOURCE+':scripts/test_windows_shutdown_study.py').stdout
    original=(control/'test_windows_shutdown_study.py').read_bytes()
    def methods(raw):
        return {c.name+'.'+n.name:ast.dump(n,include_attributes=False) for c in ast.parse(raw).body if isinstance(c,ast.ClassDef) for n in c.body if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')}
    assert methods(current)==methods(original) and len(methods(current))==28
    assertions=sum(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr.startswith('assert') for n in ast.walk(ast.parse(current)))
    assert assertions==113
    owner=lambda raw:ast.dump(next(n for n in ast.parse(raw).body if isinstance(n,ast.ClassDef) and n.name=='Owner'),include_attributes=False)
    assert owner(current)==owner(original)
    protected_binding=[p for p in old if 'binding' in p or p=='scripts/shutdown_study_retention.py']
    assert all(old[p]==target[p] for p in protected_binding)
    result=dict(base=BASE,target=SOURCE,handoff=HANDOFF,non_doc_union=len(set(old)|set(target)),changed=changes,protected=len(set(old)&set(target))-2,
                views={str(v):verify(v,target) for v in [OWN,DEPTH,BUILDER]},depth_proof=proof,index_count=len(git('ls-files','-z',cwd=DEPTH).stdout.split(b'\0'))-1,
                shared_alternate=ALTERNATE,self_contained=False,old_methods=28,old_assertions=113,old_methods_and_Owner_AST_exact=True,
                legacy_baseline=dict(commit=LEGACY,path='scripts/verify_offline_export.py',bytes=len(legacy),sha256=hashlib.sha256(legacy).hexdigest(),test_runtime_git_dependency=False),
                unchanged_binding_paths=protected_binding,setup_lookup_note='MODEL.md source-read lookup failed; actual handoff names MODEL_AND_COVERAGE.md, read successfully. No check skipped.')
    (REPORT/'SOURCE_UNION_AND_DEPTH.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(union=result['non_doc_union'],changes=len(changes),protected=result['protected'],views={p:v['materialized'] for p,v in result['views'].items()},depth_index=result['index_count'],old28_AST_exact=True)))


if __name__=='__main__':main()
