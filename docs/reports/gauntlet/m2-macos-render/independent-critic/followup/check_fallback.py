#!/usr/bin/env python3
"""Review fallback workflow and nested raw-artifact fidelity without a renderer."""
import sys,json,hashlib,subprocess,tempfile,zipfile
from pathlib import Path
import yaml
repo=Path('/workspace/reviews/macos-diagnostic-evidence-worktree')
review=Path('/workspace/reviews/macos-diagnostic-critic/followup')
sys.path.insert(0,str(repo/'scripts'))
from package_qa_receipts import package
before=subprocess.check_output(['git','show','b9826d4:.github/workflows/desktop-alpha.yml'],cwd=repo,text=True)
after=subprocess.check_output(['git','show','3bfc29b:.github/workflows/desktop-alpha.yml'],cwd=repo,text=True)
a=yaml.load(before,Loader=yaml.BaseLoader);b=yaml.load(after,Loader=yaml.BaseLoader)
steps=b['jobs']['native']['steps']
features=[s for s in steps if 'diagnose_macos_render.py' in s.get('run','')]
assert len(features)==1
feature=features[0]
assert feature['if']=="always() && steps.export.outcome == 'success' && matrix.os == 'macos-15-intel'"
assert feature['run']=='python scripts/diagnose_macos_render.py --output builds/desktop-playability/macos-diagnostics/render-features'
position=steps.index(feature)
assert 'diagnose_macos_startup.py' in steps[position-1]['run']
assert any('verify_builds.py' in s.get('run','') and '--graphical' in s['run'] for s in steps[:position])
steps.remove(feature)
assert a==b # Every other condition, command, artifact setting and job cap identical.
assert b['jobs']['native']['timeout-minutes']=='60'
original=Path('/workspace/sightbreak-macos-render')
for name in ['scripts/diagnose_macos_render.py','scripts/diagnostics/render_feature_probe.gd','scripts/diagnose_macos_startup.py','scripts/verify_builds.py']:
    assert (repo/name).read_bytes()==(original/name).read_bytes(),name
with tempfile.TemporaryDirectory(prefix='critic-nested-qa-') as tmp:
    tmp=Path(tmp);source=tmp/'qa'; source.mkdir()
    expected={
      'macos-diagnostics/render-features/results.json':b'{"scope":"fixture only"}\n',
      'macos-diagnostics/render-features/full.log':b'RENDER_DIAG phase=drawn frame=1 case=full msec=1 draws=135.0 primitives=43330.0\n',
      'macos-diagnostics/render-features/full-15s.sample.txt':b'Native sample fixture\n',
      'macos-diagnostics/render-features/full-90s.sample.txt':b'Later native sample fixture\n',
      'macos-diagnostics/render-features/fixture-source.json':b'{"copy":"fixture"}\n',
      'macos-diagnostics/render-features/render-import.log':b'Import fixture\n',
      'macos/source.json':b'{"source_commit":"3bfc29b"}\n',
      'verification/results.json':b'{"shipping_gate":"failed fixture"}\n',
    }
    excluded=['macos-diagnostics/render-features/full.png','macos-diagnostics/render-features/RenderDiagnostic.app/Contents/metadata.json','macos-diagnostics/render-features/render-project/.godot/cache.json']
    for name,data in {**expected,**{n:b'Excluded fixture' for n in excluded}}.items():
        path=source/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    result=package(source,tmp/'receipts.zip')
    with zipfile.ZipFile(tmp/'receipts.zip') as archive:
        index=json.loads(archive.read('qa-receipts-index.json'))
        assert {r['path'] for r in index['files']}==set(expected)
        for row in index['files']:
            assert archive.read(row['archive_path'])==expected[row['path']]
            assert row['sha256']==hashlib.sha256(expected[row['path']]).hexdigest()
    assert all((source/n).is_file() for n in excluded)
    package_summary={'included':list(expected),'excluded_from_small_archive':excluded,'report':result,'byte_fidelity':True,'original_excluded_files_preserved':True}
summary={'source_commit':'3bfc29b90360cdbfdaf4bbdebd424b8d804600a7','workflow_delta_only_feature_step':True,'step':feature,'same_reviewed_runner_bytes':True,'job_cap_minutes':60,'nested_packaging':package_summary,'scope':'Fallback dispatch correctness only; no native Mac run or product fix established'}
(review/'raw-results.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
