#!/usr/bin/env python3
"""Run the production focus assertions in a fresh ordinary exported stock match.

This separate probe omits purchases, second-round setup and settings restart.
It never implies full offline-journey acceptance. The focus block is copied
verbatim at runtime from the production controller; all its budgets are retained.
"""
import hashlib
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'scripts'))
path = ROOT / 'scripts/verify_offline_export.py'
original = path.read_text()
spawn = "        capture('02-offline-spawn')\n"
focus_start = '        focus_start = observed('
focus_end = '        ui.request_close()\n        reopened.wait(timeout=min(20, remaining()))'
cleanup = '    except (Exception, SystemExit) as error:\n'
assert all(original.count(marker) == 1 for marker in (spawn, focus_start, focus_end, cleanup))
focus = original[original.index(focus_start):original.index(focus_end)]
setup = original[:original.index(spawn) + len(spawn)]
setup += "        loaded = initial_offline\n"
finish = '''        result['native_focus_recovery']['scope'] = 'fresh first stock match; settings restart not run'
        ui.request_close()
        client.wait(timeout=min(20, remaining()))
        initial_exit = client.returncode
        if initial_exit or failed((out / 'client.log').read_text(encoding='utf-8', errors='replace')):
            raise RuntimeError('Focus-only export did not shut down cleanly')
        validate_record(args.target, before)
        if before != source():
            raise RuntimeError('Source changed during focus-only validation')
        audit_clients()
        remaining()
        result.update(passed=True, native_focus_only=True, clean_exit=True,
                      full_offline_journey='UNVERIFIED', settings_restart='NOT_RUN',
                      focus_only_driver=FOCUS_ONLY_RECEIPT)
'''
transformed = setup + focus + finish + original[original.index(cleanup):]
receipt = {'driver_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
           'production_controller_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
           'verbatim_focus_block_sha256': hashlib.sha256(focus.encode()).hexdigest(),
           'executed_controller_sha256': hashlib.sha256(transformed.encode()).hexdigest(),
           'scope': 'first ordinary stock match, exact production focus block, no injected state or changed physics'}
namespace = {'__name__': '__main__', '__file__': str(path), 'FOCUS_ONLY_RECEIPT': receipt}
exec(compile(transformed, '<production controller with focus-only entry>', 'exec'), namespace)
