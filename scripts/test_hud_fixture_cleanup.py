#!/usr/bin/env python3
"""Native HUD fixture cleanup and protected-state controls."""
import argparse
import hashlib
import json
from pathlib import Path
import re

from run_native_regressions import NativeSceneSuites


PROFILE = b'{"fixture":"original-player-profile-must-not-change"}\n'
PROTECTED = 'Protected fixture save must remain unchanged'
FOREIGN_OWNER = 'Changed ownership marker must remain unchanged'
HIDDEN = 'Hidden protected fixture file must remain unchanged'


def cleanup_receipt(run, before):
    text = Path(run['log']).read_text(encoding='utf-8')
    match = re.search(r'^HUD_OBJECTIVE_HINT_TEST_CLEANUP (.*)$', text, re.M)
    assert match, text
    receipt = json.loads(match.group(1))
    inner = Path(receipt['native_user_dir'])
    assert inner.resolve() == (Path(before['data_dir']) / receipt['owner']).resolve()
    assert inner.parent.name == 'SIGHTBREAK_QA' and inner.name.startswith('hud-objective-hint-')
    assert receipt['owned'] and receipt['original_user_dir_restored']
    assert receipt['exit'] == run['exit']
    return receipt, inner


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    results = {}
    with NativeSceneSuites(args.output) as runner:
        success = runner.run('hud_objective_hint')
        receipt, inner = cleanup_receipt(success, success['before'])
        assert success['exit'] == 0 and success['clean_log']
        assert receipt['removed'] and not inner.exists() and not receipt['reason']
        assert 'checks=33 failures=0' in Path(success['log']).read_text(encoding='utf-8')
        results['success'] = {'native': success, 'cleanup': receipt, 'inner_directory_absent': True}

        # This is the unique runner-owned startup user directory, representing
        # an existing caller profile. No ordinary application directory is edited.
        before = success['after']
        profile = Path(before['user_data_dir']) / 'offline_training.json'
        assert not profile.exists()
        profile.write_bytes(PROFILE)
        existing = runner.execute('caller-profile-success', ['--headless', '--script', 'res://tests/hud_objective_hint_test.gd'], 120)
        receipt, inner = cleanup_receipt(existing, before)
        assert existing['exit'] == 0 and existing['clean_log']
        assert receipt['removed'] and not inner.exists() and not receipt['reason']
        assert 'checks=33 failures=0' in Path(existing['log']).read_text(encoding='utf-8')
        assert profile.read_bytes() == PROFILE
        results['existing_caller_profile_success'] = {'native': existing, 'cleanup': receipt, 'inner_directory_absent': True}
        early = runner.execute('early-source-failure', ['--headless', '--script', 'res://tests/hud_objective_hint_test.gd',
                               '--', '--baseline-source=res://tests/intentional_missing_hud_source.gd'], 120)
        receipt, inner = cleanup_receipt(early, before)
        assert early['exit'] == 2 and not early['clean_log']
        assert receipt['original_exit'] == 2 and receipt['removed'] and not inner.exists()
        assert profile.read_bytes() == PROFILE
        results['early_source_failure'] = {'native': early, 'cleanup': receipt, 'inner_directory_absent': True}

        controls = {
            'protected-profile': ('var file := FileAccess.open("user://offline_training.json", FileAccess.WRITE)\n    file.store_string(' + json.dumps(PROTECTED) + ')\n    file.close()\n    await super.run()',
                                  {'hud-fixture-owner.txt': None, 'offline_training.json': PROTECTED}),
            'changed-owner': ('var file := FileAccess.open("user://hud-fixture-owner.txt", FileAccess.WRITE)\n    file.store_string(' + json.dumps(FOREIGN_OWNER) + ')\n    file.close()\n    finish(0)',
                              {'hud-fixture-owner.txt': FOREIGN_OWNER}),
            'hidden-protected-file': ('var file := FileAccess.open("user://.protected", FileAccess.WRITE)\n    file.store_string(' + json.dumps(HIDDEN) + ')\n    file.close()\n    finish(0)',
                                      {'hud-fixture-owner.txt': None, '.protected': HIDDEN}),
        }
        for label, (body, expected_files) in controls.items():
            script = runner.output / (label + '.gd')
            script.write_text('extends "res://tests/hud_objective_hint_test.gd"\nfunc run() -> void:\n    ' + body + '\n', encoding='utf-8')
            run = runner.execute(label, ['--headless', '--script', str(script)], 120)
            receipt, inner = cleanup_receipt(run, before)
            try:
                assert run['exit'] == 2 and not run['clean_log']
                assert not receipt['removed'] and inner.is_dir()
                assert 'Refusing HUD cleanup' in receipt['reason']
                assert sorted(path.name for path in inner.iterdir()) == sorted(expected_files)
                observed = {}
                for name, value in expected_files.items():
                    contents = (inner / name).read_text(encoding='utf-8')
                    assert contents == (receipt['owner'] if value is None else value)
                    observed[name] = contents
                assert profile.read_bytes() == PROFILE
                results[label] = {'native': run, 'cleanup': receipt, 'protected_files_preserved': observed}
            finally:
                # Only this control's known files, in its verified unique leaf.
                # Later teardown never changes the retained refused-cleanup result.
                for name in expected_files:
                    (inner / name).unlink()
                inner.rmdir()
            results[label]['control_teardown_removed_fixture'] = not inner.exists()
        assert profile.read_bytes() == PROFILE
        results['caller_profile_unchanged_sha256'] = hashlib.sha256(PROFILE).hexdigest()
    assert runner.report['passed'] and runner.report['source_resources_unchanged']
    assert runner.report['temporary_project_removed'] and all(item['removed'] for item in runner.report['cleanup'])
    results.update(control_assertions_passed=True, outer_cleanup_passed=True)
    (runner.output / 'hud-cleanup-controls.json').write_text(json.dumps(results, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
