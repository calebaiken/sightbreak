#!/usr/bin/env python3
"""Verify regular leaf replacements and a shared-parent link introduced after init."""
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
from run_native_regressions import NativeSceneSuites

output = Path(__file__).parent / 'additional'
results = {}
with NativeSceneSuites(output) as runner:
    normal = runner.run('hud_objective_hint')
    data = Path(normal['before']['data_dir'])
    parent = data / 'SIGHTBREAK_QA'
    controls = {
        'regular-leaf-replacement': '''var held := fixture_user_dir + ".held"
DirAccess.rename_absolute(fixture_user_dir, held)
var file := FileAccess.open(fixture_user_dir, FileAccess.WRITE)
file.store_string("Foreign replacement leaf must remain unchanged")
file.close()
finish(0)''',
        'parent-linked-after-init': '''var parent := fixture_user_dir.get_base_dir()
DirAccess.rename_absolute(parent, parent + ".held")
DirAccess.make_dir_recursive_absolute(parent + ".target")
var file := FileAccess.open((parent + ".target").path_join("protected.txt"), FileAccess.WRITE)
file.store_string("Protected linked parent target must remain unchanged")
file.close()
var out: Array = []
assert(OS.execute("ln", ["-s", parent + ".target", parent], out) == 0)
finish(1)''',
    }
    for label, body in controls.items():
        script = runner.output / (label + '.gd')
        script.write_text('extends "res://tests/hud_objective_hint_test.gd"\nfunc run() -> void:\n' + '\n'.join('    ' + line for line in body.splitlines()) + '\n')
        run = runner.execute(label, ['--headless', '--script', str(script)], 120)
        raw = Path(run['log']).read_text()
        receipt = json.loads(re.search(r'^HUD_OBJECTIVE_HINT_TEST_CLEANUP (.*)$', raw, re.M).group(1))
        inner = Path(receipt['native_user_dir'])
        assert receipt['original_user_dir_restored'] and not receipt['removed'] and receipt['owned']
        assert not run['clean_log'] and receipt['exit'] == run['exit']
        observation = {}
        if label == 'regular-leaf-replacement':
            held = Path(str(inner) + '.held')
            assert run['exit'] == 2 and inner.is_file() and inner.read_text() == 'Foreign replacement leaf must remain unchanged'
            assert (held / 'hud-fixture-owner.txt').read_text() == receipt['owner']
            observation.update(path_is_regular_file=True, foreign_file_bytes=inner.read_text(), held_marker_bytes=(held / 'hud-fixture-owner.txt').read_text())
            inner.unlink()
            (held / 'hud-fixture-owner.txt').unlink()
            held.rmdir()
        else:
            held = Path(str(parent) + '.held')
            target = Path(str(parent) + '.target')
            held_leaf = held / inner.name
            assert run['exit'] == 1 and receipt['original_exit'] == 1 and 'linked shared namespace' in receipt['reason']
            assert parent.is_symlink() and (target / 'protected.txt').read_text() == 'Protected linked parent target must remain unchanged'
            assert (held_leaf / 'hud-fixture-owner.txt').read_text() == receipt['owner']
            observation.update(parent_is_symlink=True, target_entries=sorted(p.name for p in target.iterdir()), protected_target_bytes=(target / 'protected.txt').read_text(), held_marker_bytes=(held_leaf / 'hud-fixture-owner.txt').read_text())
            parent.unlink()
            (target / 'protected.txt').unlink()
            target.rmdir()
            (held_leaf / 'hud-fixture-owner.txt').unlink()
            held_leaf.rmdir()
            held.rename(parent)
        results[label] = {'native':run, 'cleanup':receipt, 'observed_before_control_teardown':observation, 'owned_control_teardown_complete':True}

assert runner.report['passed'] and runner.report['source_resources_unchanged'] and runner.report['copied_resources_unchanged']
results['outer_runner_passed'] = True
(output / 'additional-results.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results,indent=2))
