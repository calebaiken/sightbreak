"""Static CI routing checks only; does not run Actions or Apple tooling."""
import json
from pathlib import Path
import subprocess
import yaml

root = Path('/workspace/reviews/ios-compile-critic/source571e8c7')
out = Path(__file__).resolve().parent
workflow = yaml.safe_load((root/'.github/workflows/desktop-alpha.yml').read_text())
steps = workflow['jobs']['native']['steps']
compile_step = next(s for s in steps if s.get('name') == 'Unsigned generic-device iOS compiler and linker qualification (ARM macOS)')
control_step = next(s for s in steps if s.get('name') == 'iOS compile qualification controls (ARM macOS)')
assert compile_step['if'] == control_step['if'] == "always() && steps.export.outcome == 'success' && matrix.os == 'macos-15'"
diagnostic = next(s for s in steps if s.get('name') == 'Intel macOS render feature attribution after the unchanged startup gate')
assert steps.index(compile_step) > steps.index(diagnostic)
assert compile_step['timeout-minutes'] == 17
assert '--builds builds/ios-device-export --derived-data builds/ios-device-derived' in compile_step['run']
assert 'builds/desktop-playability/ios-compile' in compile_step['run']
packer = next(s for s in steps if s.get('name') == 'Package bounded raw QA receipts')
assert '--source builds/desktop-playability --output builds/qa-receipts/qa-receipts.zip' in packer['run']
changes = subprocess.check_output(['git','diff','--numstat','3968f47..HEAD','--','.github/workflows/desktop-alpha.yml'],cwd=root,text=True).strip()
assert changes.startswith('7\t0\t'), changes
result = {'yaml_parse':True,'ios_conditions':compile_step['if'],'step_timeout_minutes':17,
          'diagnostic_order_preserved':True,'native_payload_paths_outside_qa':True,
          'existing_workflow_changes':changes,
          'reviewed_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),
          'source_status_after':subprocess.check_output(['git','status','--porcelain'],cwd=root,text=True)}
(out/'workflow-static-review.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
