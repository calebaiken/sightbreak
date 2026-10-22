#!/usr/bin/env python3
"""Independent Linux native edge controls; source game resources stay frozen."""
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
from run_native_regressions import NativeSceneSuites

output = Path(__file__).parent / 'edges'
results = {}

def run_control(runner, label, body):
    script = runner.output / (label + '.gd')
    script.write_text('extends "res://tests/hud_objective_hint_test.gd"\nfunc run() -> void:\n' + '\n'.join('    ' + line for line in body.splitlines()) + '\n')
    run = runner.execute(label, ['--headless', '--script', str(script)], 120)
    raw = Path(run['log']).read_text()
    receipt = json.loads(re.search(r'^HUD_OBJECTIVE_HINT_TEST_CLEANUP (.*)$', raw, re.M).group(1))
    inner = Path(receipt['native_user_dir'])
    observation = {'path_exists': inner.exists(), 'path_is_symlink': inner.is_symlink(), 'path_lexists': inner.exists() or inner.is_symlink()}
    results[label] = {'native': run, 'cleanup': receipt, 'observation': observation}
    assert receipt['original_user_dir_restored'] and receipt['exit'] == run['exit']
    return receipt, inner

with NativeSceneSuites(output) as runner:
    normal = runner.run('hud_objective_hint')
    before = normal['before']
    data = Path(before['data_dir'])
    parent = data / 'SIGHTBREAK_QA'
    caller = Path(before['user_data_dir']) / 'offline_training.json'
    sentinel = b'Independent caller profile must remain unchanged\n'
    caller.write_bytes(sentinel)

    receipt, inner = run_control(runner, 'assertion-failure', 'check(false, "Independent forced assertion failure")\nfinish(1)')
    assert receipt['original_exit'] == 1 and receipt['exit'] == 1 and receipt['removed'] and not inner.exists()

    receipt, inner = run_control(runner, 'marker-symlink', 'var marker := fixture_user_dir.path_join("hud-fixture-owner.txt")\nvar target := fixture_user_dir + ".marker-target"\nDirAccess.rename_absolute(marker, target)\nvar out: Array = []\nassert(OS.execute("ln", ["-s", target, marker], out) == 0)\nfinish(0)')
    target = Path(str(inner) + '.marker-target')
    assert receipt['exit'] == 2 and not receipt['removed'] and (inner / 'hud-fixture-owner.txt').is_symlink()
    assert target.read_text() == receipt['owner']
    results['marker-symlink']['target_unchanged'] = True
    (inner / 'hud-fixture-owner.txt').unlink()
    inner.rmdir()
    target.unlink()

    receipt, inner = run_control(runner, 'leaf-symlink', 'var held := fixture_user_dir + ".held"\nDirAccess.rename_absolute(fixture_user_dir, held)\nvar out: Array = []\nassert(OS.execute("ln", ["-s", held, fixture_user_dir], out) == 0)\nfinish(0)')
    held = Path(str(inner) + '.held')
    assert receipt['exit'] == 2 and not receipt['removed'] and inner.is_symlink()
    assert (held / 'hud-fixture-owner.txt').read_text() == receipt['owner']
    inner.unlink()
    (held / 'hud-fixture-owner.txt').unlink()
    held.rmdir()

    receipt, inner = run_control(runner, 'dangling-leaf-symlink', 'var held := fixture_user_dir + ".held"\nDirAccess.rename_absolute(fixture_user_dir, held)\nvar out: Array = []\nassert(OS.execute("ln", ["-s", fixture_user_dir + ".absent", fixture_user_dir], out) == 0)\nfinish(0)')
    held = Path(str(inner) + '.held')
    assert receipt['exit'] == 2 and inner.is_symlink() and not inner.exists()
    assert (held / 'hud-fixture-owner.txt').read_text() == receipt['owner']
    results['dangling-leaf-symlink']['receipt_matches_path_removal'] = not receipt['removed']
    inner.unlink()
    (held / 'hud-fixture-owner.txt').unlink()
    held.rmdir()

    receipt, inner = run_control(runner, 'unwritable-leaf', 'var out: Array = []\nassert(OS.execute("chmod", ["500", fixture_user_dir], out) == 0)\nfinish(1)')
    inner.chmod(0o700)
    assert receipt['exit'] == 1 and receipt['original_exit'] == 1 and not receipt['removed']
    assert (inner / 'hud-fixture-owner.txt').read_text() == receipt['owner']
    assert 'Cannot remove private HUD fixture ownership marker' in receipt['reason']
    (inner / 'hud-fixture-owner.txt').unlink()
    inner.rmdir()

    # The shared parent is an existing link before the candidate starts.
    assert parent.is_dir() and not any(parent.iterdir())
    parent.rmdir()
    target = runner.output / 'linked-parent-target'
    target.mkdir()
    protected = target / 'protected.txt'
    protected.write_bytes(sentinel)
    parent.symlink_to(target, target_is_directory=True)
    receipt, inner = run_control(runner, 'linked-shared-parent', 'finish(0)')
    assert protected.read_bytes() == sentinel
    results['linked-shared-parent']['parent_symlink_preserved'] = parent.is_symlink()
    results['linked-shared-parent']['target_entries_after'] = sorted(p.name for p in target.iterdir())
    results['linked-shared-parent']['linked_path_refused'] = receipt['exit'] != 0 and 'Refusing' in receipt['reason']
    parent.unlink()
    protected.unlink()
    target.rmdir()
    assert caller.read_bytes() == sentinel
    results['caller_profile_unchanged'] = True

assert runner.report['passed'] and runner.report['source_resources_unchanged'] and runner.report['copied_resources_unchanged']
results['runner_finalization'] = runner.report
(output / 'edge-results.json').write_text(json.dumps(results, indent=2) + '\n')
print(json.dumps({label: value.get('cleanup', value) for label, value in results.items() if label != 'runner_finalization'}, indent=2))
