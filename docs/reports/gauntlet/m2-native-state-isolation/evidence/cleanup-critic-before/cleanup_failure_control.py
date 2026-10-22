#!/usr/bin/env python3
"""Review-only fault injection; never modifies candidate implementation."""
import json
from pathlib import Path
import shutil
import sys

ROOT = Path('/workspace/reviews/m2-isolation-critic')
sys.path.insert(0, str(ROOT / 'source/scripts'))
from run_native_regressions import NativeSceneSuites

real_rmtree = shutil.rmtree
owned_namespace = None
failure = None
try:
    with NativeSceneSuites(ROOT / 'cleanup-failure') as runner:
        runner.run('peer_lifecycle')  # Actual native success before cleanup fails.
        owned_namespace = next(iter(runner.user_roots))

        def blocked_namespace(path, *args, **kwargs):
            if Path(path) == owned_namespace:
                raise PermissionError('Independent review injected namespace cleanup failure')
            return real_rmtree(path, *args, **kwargs)

        shutil.rmtree = blocked_namespace
except PermissionError as error:
    failure = {'type': type(error).__name__, 'message': str(error)}
finally:
    shutil.rmtree = real_rmtree

receipt = json.loads((ROOT / 'cleanup-failure/isolation.json').read_text())
observed = {'control': 'Real native successful peer_lifecycle suite then review-only cleanup fault',
            'raised': failure, 'isolation_passed': receipt['passed'],
            'isolation_failure': receipt['failure'], 'cleanup': receipt['cleanup'],
            'owned_namespace_remained': owned_namespace.exists(),
            'temporary_project_removed': receipt['temporary_project_removed']}
assert failure and observed['owned_namespace_remained']
assert receipt['passed'] is True and receipt['failure'] is None and receipt['cleanup'] == []
# Clean up only this control's owned namespace after retaining its false receipt.
assert owned_namespace.name == runner.namespace
assert owned_namespace.is_relative_to(ROOT / 'state/cleanup-failure/data')
real_rmtree(owned_namespace)
observed['review_cleanup_removed_namespace'] = not owned_namespace.exists()
(ROOT / 'cleanup-failure-observed.json').write_text(json.dumps(observed, indent=2) + '\n')
print(json.dumps(observed, indent=2))
