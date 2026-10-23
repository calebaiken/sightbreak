#!/usr/bin/env python3
"""Native regression and save-safety controls for the isolated source-suite runner.

Requires a test account/environment without an existing canonical SIGHTBREAK save.
Existing saves are rejected before any fixture is written. Never changes HOME.
"""
import argparse
import hashlib
import json
from pathlib import Path

from run_native_regressions import NativeSceneSuites


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    checks = {'passed': False}
    canonical_profile = None
    owns_profile = False
    with NativeSceneSuites(args.output) as runner:
        try:
            # Reproduce the real producer's shared-state failure on an unchanged
            # copy of the source project config before exercising the candidate.
            (runner.project / 'project.godot').write_bytes(runner.original_config.encode('utf-8'))
            path_receipt = runner.output / 'canonical-producer.json'
            probe = runner.execute('canonical-producer', ['--headless', '--script', str(runner.driver),
                                   '--', '--receipt=' + str(path_receipt)], 30)
            assert probe['exit'] == 0 and probe['clean_log']
            canonical = json.loads(path_receipt.read_text(encoding='utf-8'))
            canonical_profile = Path(canonical['user_data_dir']) / 'offline_training.json'
            if canonical['profile_exists'] or canonical_profile.exists():
                raise RuntimeError('Existing canonical player save rejected; choose a fresh test state')
            owns_profile = True
            first = runner.execute('baseline-input_mode', ['--headless', '--script', 'res://tests/input_mode_test.gd'], 120)
            assert first['exit'] == 0 and first['clean_log']
            assert canonical_profile.is_file(), 'Actual input-mode producer did not create its canonical save'
            produced = canonical_profile.read_bytes()
            second = runner.execute('baseline-menu_focus', ['--headless', '--script', 'res://tests/menu_focus_test.gd'], 120)
            assert second['exit'] == 2 and not second['clean_log']
            assert 'Use a fresh isolated state directory' in Path(second['log']).read_text(encoding='utf-8')
            assert canonical_profile.read_bytes() == produced
            checks['baseline'] = {'input_mode': first, 'menu_focus': second,
                                  'produced_save_sha256': hashlib.sha256(produced).hexdigest()}
            (runner.output / 'baseline-produced-profile.json').write_bytes(produced)

            canonical_profile.unlink()  # Only the profile this test just produced.
            sentinel = b'{"fixture":"canonical-player-save-must-not-change"}\n'
            canonical_profile.write_bytes(sentinel)
            negative = runner.execute('canonical-sentinel-guard', ['--headless', '--script', 'res://tests/menu_focus_test.gd'], 120)
            assert negative['exit'] == 2 and canonical_profile.read_bytes() == sentinel
            checks['source_fresh_save_guard'] = negative

            # Exercise actual native startup with CRLF config bytes too. This is
            # a line-ending control, not a claim of Windows execution.
            original_config = runner.original_config
            runner.original_config = original_config.replace('\r\n', '\n').replace('\n', '\r\n')
            receipts = [runner.run(suite) for suite in ('input_mode', 'menu_focus', 'offline_diagnostics')]
            private_config = (runner.project / 'project.godot').read_bytes()
            assert b'\r\n' in private_config and b'\r\r\n' not in private_config
            assert private_config.replace(b'\r\n', b'').find(b'\n') == -1
            checks['native_startup_with_crlf_config'] = True
            runner.original_config = original_config
            paths = [receipt['before']['user_data_dir'] for receipt in receipts]
            assert len(set(paths)) == 3
            assert all(not receipt['before']['profile_exists'] and not receipt['before']['diagnostics_exist'] for receipt in receipts)
            assert all(receipt['before']['user_data_dir'] == receipt['after']['user_data_dir'] for receipt in receipts)
            assert all(str(Path(canonical['user_data_dir']).resolve()) != path for path in paths)
            assert canonical_profile.read_bytes() == sentinel
            checks['canonical_sentinel_preserved_sha256'] = hashlib.sha256(sentinel).hexdigest()
            checks['distinct_native_suite_paths'] = paths

            # A stale suite identity must fail before executing or deleting its save.
            prepared = runner.prepare('hud_objective_hint')
            stale = Path(prepared['user_data_dir']) / 'offline_training.json'
            stale.write_bytes(sentinel)
            try:
                runner.run('hud_objective_hint')
            except RuntimeError as error:
                assert 'Refusing existing suite state' in str(error), str(error)
                assert stale.read_bytes() == sentinel
                assert not (runner.output / 'hud_objective_hint.log').exists()
                checks['existing_isolated_save_rejected'] = str(error)
            else:
                raise AssertionError('Existing isolated save was overwritten or admitted')
        finally:
            if owns_profile:
                canonical_profile.unlink(missing_ok=True)
            (runner.output / 'save-safety.json').write_text(json.dumps(checks, indent=2) + '\n', encoding='utf-8')
    assert runner.report['source_resources_unchanged'] and runner.report['copied_resources_unchanged']
    assert runner.report['temporary_project_removed'] and all(item['removed'] for item in runner.report['cleanup'])
    checks.update(passed=True, source_resources_unchanged=True, copied_resources_unchanged=True,
                  temporary_project_removed=True, user_namespaces_removed=True)
    (runner.output / 'save-safety.json').write_text(json.dumps(checks, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(checks, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
