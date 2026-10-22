#!/usr/bin/env python3
"""Run the actual base fixture and observe its post-run owned orphan."""
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, '/workspace/reviews/hud-fixture-cleanup-baseline/scripts')
from run_native_regressions import NativeSceneSuites

output = Path(__file__).parent / 'baseline'
with NativeSceneSuites(output) as runner:
    native = runner.run('hud_objective_hint')
raw = Path(native['log']).read_text()
match = re.search(r'^HUD_OBJECTIVE_HINT_TEST_STATE native_user_dir=(.*?) original_user_dir=(.*?) owner=(.*?)$', raw, re.M)
assert match and 'checks=33 failures=0' in raw and native['exit'] == 0
inner, original, owner = match.groups()
inner = Path(inner)
marker = inner / 'hud-fixture-owner.txt'
assert inner.resolve() == (Path(native['before']['data_dir']) / owner).resolve()
assert marker.read_text() == owner and sorted(p.name for p in inner.iterdir()) == ['hud-fixture-owner.txt']
assert runner.report['passed'] and runner.report['source_resources_unchanged'] and runner.report['copied_resources_unchanged']
assert all(item['removed'] for item in runner.report['cleanup']) and runner.report['temporary_project_removed']
observed = {'source_commit':'60db9ff884ad6989c6bfd87cf2fe3405505a9997', 'native':native, 'outer_runner_passed':runner.report['passed'], 'inner_orphan_after_outer_cleanup':str(inner), 'marker_bytes':marker.read_text()}
marker.unlink()
inner.rmdir()
observed['owned_orphan_control_teardown_removed'] = not inner.exists()
(output / 'orphan-observed.json').write_text(json.dumps(observed, indent=2) + '\n')
print(json.dumps(observed, indent=2))
