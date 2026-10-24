"""Read-only final byte, mode, AST, index, and archived-manifest audit."""
import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path

REPORT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('registered_view_proof', REPORT/'prepare_views.py')
views = importlib.util.module_from_spec(spec)
spec.loader.exec_module(views)


def dump(node):
    return ast.dump(node, include_attributes=False)


def nodes(raw):
    return {n.name:n for n in ast.parse(raw).body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}


def manifest_check(path, base=None):
    value = json.loads(path.read_text())
    entries = value['files'] if 'files' in value else value
    entries = entries if isinstance(entries, list) else [dict(path=p, **v) for p,v in entries.items()]
    base = base or path.parent
    total = 0
    for entry in entries:
        raw = (base/entry['path']).read_bytes()
        assert len(raw) == entry['bytes'], (path, entry['path'], 'bytes')
        assert hashlib.sha256(raw).hexdigest() == entry['sha256'], (path, entry['path'], 'hash')
        total += len(raw)
    return dict(path=str(path), members=len(entries), bytes=total, all_bytes_hashes_equal=True)


def main():
    assert os.sched_getaffinity(0) == {4}
    expected = views.tree(views.SOURCE)
    materialized = {str(v): views.verify(v, expected) for v in (views.OWN, views.DEPTH, views.BUILDER)}
    assert [v['materialized'] for v in materialized.values()] == [354,354,516]
    assert all(len(v['omitted']) in (0,162) for v in materialized.values())
    assert not views.git('diff','--name-only',views.SOURCE,'HEAD','--','.',':(exclude)docs').stdout
    assert not views.git('diff','--name-only',views.SOURCE,views.HANDOFF,'--','.',':(exclude)docs').stdout
    depth = []
    for args in [('rev-parse','HEAD'),('rev-list','--count','HEAD'),('rev-parse','--verify','HEAD^'),('status','--porcelain=v1')]:
        result=views.git(*args,cwd=views.DEPTH,check=False)
        depth.append(dict(command=['git',*args], exit=result.returncode, stdout=result.stdout.decode(), stderr=result.stderr.decode()))
    assert depth[0]['stdout'].strip()==views.SOURCE and depth[1]['stdout'].strip()=='1'
    assert depth[2]['exit']==128 and not depth[3]['stdout']
    assert len(views.git('ls-files','-z',cwd=views.DEPTH).stdout.split(b'\0'))-1 == 16262
    old = (REPORT/'frozen-control-source/windows_shutdown_study.py').read_bytes()
    new = (views.OWN/'scripts/windows_shutdown_study.py').read_bytes()
    old_nodes,new_nodes=nodes(old),nodes(new)
    protected=['require','write','WindowsOwner','driver_arguments','typed_leak_rows','embedded_pck_identity','runtime_identity','main']
    assert all(dump(old_nodes[name])==dump(new_nodes[name]) for name in protected)
    old_test=(REPORT/'frozen-control-source/test_windows_shutdown_study.py').read_bytes()
    new_test=(views.OWN/'scripts/test_windows_shutdown_study.py').read_bytes()
    tests=lambda raw:{c.name+'.'+n.name:dump(n) for c in ast.parse(raw).body if isinstance(c,ast.ClassDef) for n in c.body if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')}
    assert tests(old_test)==tests(new_test) and len(tests(new_test))==28
    assert dump(nodes(old_test)['Owner'])==dump(nodes(new_test)['Owner'])
    assertions=sum(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr.startswith('assert') for n in ast.walk(ast.parse(new_test)))
    assert assertions==113
    proposal=nodes((REPORT.parent/'phase-a-construction-verdict/OLD28_HELPER_PROPOSAL_V3.py').read_bytes())['run_generated']
    helper=next(n for n in nodes(new_test)['StudyTests'].body if isinstance(n,ast.FunctionDef) and n.name=='run_generated')
    assert dump(helper)==dump(proposal)
    fixture=(views.OWN/'scripts/shutdown_evidence_fixtures.py').read_bytes()
    assert fixture==(REPORT.parent/'phase-a-construction-verdict/shutdown_evidence_fixtures-e902.py').read_bytes()
    manifests=[]
    for phase in ('phase-a-fixture-adjudication','phase-a-v3','phase-a-construction-verdict'):
        manifests.append(manifest_check(REPORT.parent/phase/'MANIFEST.json'))
    manifests.append(manifest_check(REPORT.parent/'ARCHIVED_AVAILABILITY_MANIFEST.json', REPORT.parent))
    manifests.append(manifest_check(REPORT/'INTERIM_MANIFEST.json'))
    assert manifests[-1]['members']==849 and manifests[-1]['bytes']==205366615
    handoff=manifest_check(REPORT/'builder-handoff/MANIFEST.json')
    assert handoff['members']==97
    # Every copied handoff member, including its manifest, is its exact tracked blob.
    copied=0
    for file in (REPORT/'builder-handoff').rglob('*'):
        if not file.is_file(): continue
        rel=file.relative_to(REPORT/'builder-handoff').as_posix()
        assert file.read_bytes()==views.git('show',views.HANDOFF+':'+views.PREFIX+rel).stdout
        copied+=1
    binding=[]
    for label in ('frozen-own','frozen-depth'):
        summary=json.loads((REPORT/'builder-handoff'/label/'SUMMARY.json').read_text())
        row=next(r for r in summary['results'] if r['name']=='binding')
        raw=(REPORT/'builder-handoff'/label/'binding.stderr').read_text()
        assert row['exit']==0 and 'Ran 11 tests' in raw and raw.rstrip().endswith('OK')
        binding.append(dict(view=label, original_exit=0, original_methods=11, repeated=False))
    result=dict(source=views.SOURCE, handoff=views.HANDOFF,
                non_doc_paths=516, changed_or_added=5, protected=511,
                views={k:dict(materialized=v['materialized'], omitted=len(v['omitted']),bytes_modes_equal=v['all_materialized_bytes_modes_equal']) for k,v in materialized.items()},
                depth=depth, depth_index_count=16262, shared_objects=views.ALTERNATE, self_contained=False,
                protected_study_AST=protected, old28_methods_and_113_assertions_and_Owner_AST_unchanged=True,
                run_generated_exact_adjudicated_V3_AST=True, fixture_exact_e902_bytes=True,
                preserved_manifests=manifests, builder_manifest=handoff, builder_tracked_files_equal=copied,
                separate_binding_originals=binding, candidate_tests_rerun_in_this_audit=0,
                native_or_API_or_real_process_trials=0)
    (REPORT/'FINAL_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
