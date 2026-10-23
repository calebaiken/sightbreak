#!/usr/bin/env python3
"""Run the production settings/resume transaction in a first ordinary match.

The separate probe omits weapon purchases, second-round setup and restart. It
executes the settings block verbatim with the stock sidearm and preserves every
transaction guard/budget. It never implies full offline-journey acceptance.
"""
import hashlib
import os
from pathlib import Path
import sys

ROOT = (Path(os.environ['SIGHTBREAK_PROBE_ROOT']) if 'SIGHTBREAK_PROBE_ROOT' in os.environ else Path(__file__).resolve().parents[4]).resolve()
sys.path.insert(0, str(ROOT / 'scripts'))
path = ROOT / 'scripts/verify_offline_export.py'
original = path.read_text()
spawn = "        capture('02-offline-spawn')\n"
settings_start = "        capture('07-field-menu')\n"
settings_end = "        ui.request_close()\n        client.wait(timeout=min(20, remaining()))"
cleanup = '    except (Exception, SystemExit) as error:\n'
assert all(original.count(marker) == 1 for marker in (spawn, settings_start, settings_end, cleanup))
transaction = original[original.index(settings_start):original.index(settings_end)]
setup = original[:original.index(spawn) + len(spawn)]
setup += '''        observed(lambda state: state.get('phase') == 'live'
                 and state.get('local_actor', {}).get('alive') is True
                 and state.get('ui', {}).get('focused') is True
                 and state.get('ui', {}).get('paused') is False,
                 60, 'First ordinary stock match reaches living active settings probe', initial_offline['wall_msec'])
        capture('boundary-before-settings')
        boundary_hud = read_hud('boundary-before-settings', resume_after=False)
        settings_pause = result['hud_analysis_pauses'][-1]['after_analysis']
'''
finish = '''        ui.request_close()
        client.wait(timeout=min(20, remaining()))
        initial_exit = client.returncode
        if initial_exit or failed((out / 'client.log').read_text(encoding='utf-8', errors='replace')):
            raise RuntimeError('Settings-only export did not shut down cleanly')
        validate_record(args.target, before)
        if before != source():
            raise RuntimeError('Source changed during settings-only validation')
        audit_clients()
        remaining()
        result.update(passed=True, native_settings_only=True, clean_exit=True,
                      full_offline_journey='UNVERIFIED', settings_restart='NOT_RUN',
                      boundary_hud=boundary_hud, resumed_hud=resumed_hud,
                      settings_only_driver=SETTINGS_ONLY_RECEIPT)
'''
transformed = setup + transaction + finish + original[original.index(cleanup):]
receipt = {'driver_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
           'production_controller_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
           'verbatim_settings_block_sha256': hashlib.sha256(transaction.encode()).hexdigest(),
           'executed_controller_sha256': hashlib.sha256(transformed.encode()).hexdigest(),
           'scope': 'first ordinary stock match, exact production settings block with stock sidearm, no injected state or changed physics'}
namespace = {'__name__': '__main__', '__file__': str(path), 'SETTINGS_ONLY_RECEIPT': receipt}
exec(compile(transformed, '<production controller with settings-only entry>', 'exec'), namespace)
