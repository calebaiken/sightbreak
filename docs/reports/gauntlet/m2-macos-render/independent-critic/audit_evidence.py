#!/usr/bin/env python3
from pathlib import Path
from PIL import Image
import json,sys,subprocess,tempfile,numpy as np,zipfile
repo=Path('/workspace/sightbreak-macos-render');review=Path('/workspace/reviews/macos-diagnostic-critic')
sys.path.insert(0,str(repo/'scripts'))
from diagnose_macos_render import draw_trace,prepare_fixture
from diagnose_macos_startup import digest
from native_log import failed
from build_manifest import source
before=source()
with tempfile.TemporaryDirectory(prefix='critic-render-fixture-') as tmp:
    fixture=prepare_fixture(Path(tmp)); manifest=json.loads((Path(tmp)/'fixture-source.json').read_text())
    mismatches=[e['path'] for e in manifest['copied_shipping_files'] if digest(repo/e['path'])!=e['sha256'] or (e['path'] not in ('game/project.godot','game/export_presets.cfg') and digest(fixture/Path(e['path']).relative_to('game'))!=e['sha256'])]
    tracked=subprocess.check_output(['git','ls-files','-z','--','game'],cwd=repo).decode().split('\0')
    expected={p for p in tracked if p and '.godot' not in Path(p).parts and 'tests' not in Path(p).parts}
    record={'source_before':before,'source_after':source(),'preserved':before==source(),'copied_count':len(manifest['copied_shipping_files']),'expected_count':len(expected),'path_sets_equal':expected=={e['path'] for e in manifest['copied_shipping_files']},'byte_mismatches':mismatches}
    (review/'raw/fresh-fixture-source.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (review/'raw/preservation.json').write_text(json.dumps(record,indent=2)+'\n')
    assert record['preserved'] and record['path_sets_equal'] and not mismatches
saved=review/'linux-controls/attempt-4'; results=[];full=Image.open(saved/'full.png').convert('RGB')
for entry in json.loads((saved/'linux-results.json').read_text())['results']:
    case=entry['case'];log=(saved/(case+'.log')).read_text();trace,complete=draw_trace(log,case)
    image=Image.open(saved/(case+'.png'));image.verify();comparison=Image.open(saved/(case+'.png')).convert('RGB')
    a=np.array(full);b=np.array(comparison);rects=[(0,0,1280,72),(36,295,460,581),(502,368,1200,508),(36,660,200,690)];roi=[]
    for x1,y1,x2,y2 in rects:
        delta=np.abs(a[y1:y2,x1:x2].astype(int)-b[y1:y2,x1:x2].astype(int))
        roi.append({'box':[x1,y1,x2,y2],'different_pixels':int(np.any(delta,axis=2).sum()),'max_channel_delta':int(delta.max())})
    item={'case':case,'trace_complete':complete,'trace_matches_saved_json':trace==entry['draw_trace'],'clean_log':not failed(log),'capture_size':comparison.size,'capture_sha256':digest(saved/(case+'.png')),'constructed_lines':[line for line in log.splitlines() if 'phase=constructed' in line],'draws':sorted({f['draws'] for f in trace}),'primitives':sorted({f['primitives'] for f in trace}),'frame_1_msec':trace[0]['msec'],'frame_15_msec':trace[-1]['msec'],'ui_comparison':roi}
    results.append(item);assert complete and trace==entry['draw_trace'] and not failed(log) and comparison.size==(1280,720)
(review/'raw/saved-evidence-audit.json').write_text(json.dumps(results,indent=2)+'\n')
original=repo/'docs/reports/gauntlet/m2-macos-render/intel-original-artifact-12398461742.zip'
attachment=Path('/workspace/attachments/a85df036-caeb-45f0-91f7-ef4d8fb0712e/github-actions-artifact-12398461742.zip')
assert digest(original)==digest(attachment)=='c3179d25d87cce7030bc3d9c9700990094d799eb8610df221e38a8e321b5b8a5'
print(json.dumps({'preservation':record,'saved_controls':[{k:v for k,v in e.items() if k!='ui_comparison'} for e in results],'original_artifact_sha256':digest(original)},indent=2))
