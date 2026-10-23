#!/usr/bin/env python3
from pathlib import Path
import sys,json,yaml
repo=Path('/workspace/sightbreak-macos-render'); review=Path('/workspace/reviews/macos-diagnostic-critic')
sys.path.insert(0,str(repo/'scripts'))
from verify_builds import packed_paths,no_test_harnesses,integrated_resources
from diagnose_macos_startup import digest
fixture=repo/'builds/macos-render-linux-control/attempt-4'
expected=json.loads((fixture/'local-fixture-final-sha256.json').read_text())
assert all(digest(fixture/p)==h for p,h in expected.items())
manifest=json.loads((fixture/'fixture-source.json').read_text())
assert digest(repo/'scripts/diagnostics/render_feature_probe.gd')==expected['render-project/render_probe.gd']==manifest['diagnostic_overrides']['render_probe.gd']
mismatches=[e['path'] for e in manifest['copied_shipping_files'] if digest(repo/e['path'])!=e['sha256'] or (e['path'] not in ('game/project.godot','game/export_presets.cfg') and digest(fixture/'render-project'/Path(e['path']).relative_to('game'))!=e['sha256'])]
assert not mismatches
paths=packed_paths(fixture/'render-probe.x86_64',embedded=True)
no_test_harnesses(paths);integrated_resources(paths)
assert 'render_probe.gdc' in paths and 'render_probe.tscn.remap' in paths
record={'binary':str(fixture/'render-probe.x86_64'),'sha256':digest(fixture/'render-probe.x86_64'),'expected_hashes':expected,'all_saved_fixture_hashes_match':True,'preserved_resource_byte_mismatches':mismatches,'packed_resource_count':len(paths),'packed_paths':paths,'shipping_integrated_resources_present':True,'test_harnesses_absent':True}
(review/'raw/exported-fixture-audit.json').write_text(json.dumps(record,indent=2)+'\n')
wf=yaml.load((repo/'.github/workflows/macos-render-diagnostic.yml').read_text(),Loader=yaml.BaseLoader)
assert set(wf['on'])=={'workflow_dispatch'} and wf['permissions']=={'contents':'read'} and wf['jobs']['intel-render']['runs-on']=='macos-15-intel'
steps=wf['jobs']['intel-render']['steps']
assert all(len(s['uses'].split('@')[1])==40 for s in steps if 'uses' in s)
assert next(i for i,s in enumerate(steps) if s.get('id')=='export')<next(i for i,s in enumerate(steps) if 'verify_builds.py' in s.get('run',''))<next(i for i,s in enumerate(steps) if 'diagnose_macos_render.py' in s.get('run',''))
summary={'fixture':{k:v for k,v in record.items() if k not in ['packed_paths','expected_hashes']},'workflow':{'trigger':list(wf['on']),'permissions':wf['permissions'],'runner':wf['jobs']['intel-render']['runs-on'],'actions':[s['uses'] for s in steps if 'uses' in s]}}
(review/'raw/fixture-workflow-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
