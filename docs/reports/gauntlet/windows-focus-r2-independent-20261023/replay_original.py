"""Replay immutable original 77 definitions against an exact separate checkout.

The old false-acceptance assertions remain historical defect reproductions.
Corrected outcomes are evaluated separately; all observations are declared.
"""
import ast
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import types

OUT = Path(__file__).resolve().parent
OWN = OUT.parents[3]
ORIGINAL_PATH = 'docs/reports/gauntlet/windows-focus-liveness-independent-20261023/probe_fence.py'
ORIGINAL_COMMIT = '0d4f7e00fd1fdc8909a0b299c7d74f215573d3c7'


def main():
    source = Path(sys.argv[1]).resolve()
    freeze, label = sys.argv[2:4]
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=source, text=True).strip() == freeze
    assert subprocess.check_output(['git', 'status', '--porcelain'], cwd=source) == b''
    helper = source / 'scripts/native_focus_fence.py'
    helper_spec = importlib.util.spec_from_file_location('native_focus_fence', helper)
    helper_module = importlib.util.module_from_spec(helper_spec)
    sys.modules['native_focus_fence'] = helper_module
    helper_spec.loader.exec_module(helper_module)
    original = subprocess.check_output(['git', 'show', ORIGINAL_COMMIT + ':' + ORIGINAL_PATH], cwd=OWN)
    assert original == (OWN / ORIGINAL_PATH).read_bytes()
    probe = types.ModuleType('immutable_original_probe')
    probe.__file__ = str(OWN / ORIGINAL_PATH)
    exec(compile(original, 'immutable-original-probe', 'exec'), probe.__dict__)
    # Only source bindings change. The original main, all inputs and assertions
    # are compiled unchanged from the prior critic commit.
    probe.ROOT = source
    probe.CONTROLLER = ast.parse((source / 'scripts/verify_offline_export.py').read_text())
    assert probe.RAW == json.loads((source / 'scripts/fixtures/offline_focus_observations.json').read_text())
    original_failure, rows = None, None
    try:
        probe.main()
    except AssertionError as error:
        original_failure = str(error)
        frame = error.__traceback__
        while frame:
            if frame.tb_frame.f_code.co_name == 'main' and 'rows' in frame.tb_frame.f_locals:
                rows = frame.tb_frame.f_locals['rows']
            frame = frame.tb_next
    assert rows is not None and len(rows) == 77
    assert original_failure == 'dead_bad_counter_wall_msec_MISSING reproduces false acceptance'
    expected = {}
    assertions = []
    def check(name, condition):
        assert condition, name
        assertions.append(name)
    positive = {'valid_living_movement', 'bad_.time_scale_3', 'predicate_returns_after_original_deadline'}
    timeouts = {'stale_movement_then_timeout', 'missing_publication_then_timeout', 'whole_deadline_limits_wait'}
    for row in rows:
        name = row['name']
        if name in positive:
            expected[name] = 'LIVING_MOVEMENT_OBSERVED'
        elif name in timeouts:
            expected[name] = 'TimeoutError'
            check(name + ': original timeout classification', row['fresh_press']['status'] == 'RESPONSE_NOT_OBSERVED_BEFORE_ORIGINAL_DEADLINE')
            check(name + ': releases W', row['keys'] == [['w', True], ['w', False]])
        elif name == 'dispatch_failure_still_releases':
            expected[name] = 'RuntimeError'
            check(name + ': releases W', row['keys'] == [['w', True], ['w', False]])
        else:
            expected[name] = 'FocusPreconditionLost'
            context = row['context_fence']
            check(name + ': structured loss', context['status'] == 'FOCUS_PRECONDITION_LOST')
            check(name + ': rejected raw retained', 'rejected_state' in context['precondition_loss'])
            check(name + ': no success', 'moved' not in row['fresh_press'])
            if row['keys']:
                check(name + ': releases attempted W', row['keys'] == [['w', True], ['w', False]])
            if name.startswith(('non_dict_before_', 'wrong_local_input_')) and 'before' in name:
                check(name + ': exact before-key raw', context['precondition_loss']['rejected_state'] == row['fresh_press']['before_key'])
            if name.startswith('dead_bad_counter_') or name == 'changed_scope_through_actual_reader_guard':
                check(name + ': exact available poll raw', context['precondition_loss']['rejected_state'] == row['polls'][0])
                check(name + ': no later life search', len(row['polls']) == 1)
        check(name + ': corrected outcome', row['observation'] == expected[name])
    by_name = {row['name']: row for row in rows}
    for name in ('dead_bad_counter_wall_msec_MISSING', 'dead_bad_counter_wall_msec_-1', 'dead_bad_counter_wall_msec_later'):
        check(name + ': original released state remains previous valid',
              by_name[name]['context_fence']['precondition_loss']['previous_valid_state'] == probe.living(1))
    full_names = {row['name'] for row in json.loads((OWN / ORIGINAL_PATH).with_name('counterexamples.json').read_text())['cases']}
    receipt = {'source_freeze': freeze, 'scope': 'Pure declared snapshots; original 77 case inputs unchanged; actual frozen controller AST',
        'original_probe_commit': ORIGINAL_COMMIT, 'original_probe_sha256': hashlib.sha256(original).hexdigest(),
        'original_defect_reproduction_assertion_now_fails': original_failure,
        'historical_original_assertion_count': 49, 'historical_assertions_claimed_passing': False,
        'corrected_case_count': len(rows), 'independent_assertion_count': len(assertions),
        'assertions': assertions, 'all_corrected_outcomes_pass': True,
        'source_hashes': {path: hashlib.sha256((source / path).read_bytes()).hexdigest()
            for path in ('scripts/native_focus_fence.py', 'scripts/verify_offline_export.py', 'scripts/fixtures/offline_focus_observations.json')},
        'case_summaries': [{'name': row['name'], 'expected': expected[row['name']], 'observation': row['observation'],
            'exception': row['exception'], 'keys': row['keys'], 'clock': row['final_clock'],
            'context_status': row['context_fence'].get('status'),
            'reason': row['context_fence'].get('precondition_loss', {}).get('reason')} for row in rows],
        'cases': [row for row in rows if row['name'] in full_names]}
    (OUT / (label + '-original-replay.json')).write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({k:v for k,v in receipt.items() if k not in ('assertions', 'case_summaries', 'cases', 'source_hashes')}))


if __name__ == '__main__':
    main()
