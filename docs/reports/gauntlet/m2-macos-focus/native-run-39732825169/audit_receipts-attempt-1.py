"""Read-only native artifact audit; never invokes the implementation or engine."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess

SOURCE = 'b09cfe1b661ec153f2bd57d45e695cc70e9717b0'
IDENTITY = ('source_commit', 'source_game_tree', 'source_content_sha256', 'source_validation_sha256')
read = lambda path: json.loads(path.read_text(encoding='utf-8'))
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
clean = lambda text: re.search(r'^(?:SCRIPT ERROR|ERROR:)|Parse Error|ObjectDB.*leaked|Leaked instance', text, re.M) is None


def index_check(root):
    index = read(root / 'qa-receipts-index.json')
    failures = []
    for item in index['files']:
        path = root / item['archive_path']
        if not path.is_file() or path.stat().st_size != item['bytes'] or sha(path) != item['sha256']:
            failures.append(item['path'])
    actual = {p.relative_to(root).as_posix() for p in (root / 'evidence').rglob('*') if p.is_file()}
    expected = {item['archive_path'] for item in index['files']}
    return {'indexed_files': len(expected), 'size_or_hash_failures': failures, 'file_set_complete': actual == expected}


def regressions(base, checkout):
    raw = subprocess.check_output(['git', 'show', SOURCE + ':scripts/run_native_regressions.py'], cwd=checkout).decode()
    expected = next(ast.literal_eval(n.value) for n in ast.parse(raw).body
                    if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'SUITES' for t in n.targets))
    results = read(base / 'regressions/results.json')
    isolation = read(base / 'regressions/isolation.json')
    resource_failures = []
    for name, expected_hash in isolation['source_resources_sha256'].items():
        raw = subprocess.check_output(['git', 'show', SOURCE + ':game/' + name], cwd=checkout)
        if hashlib.sha256(raw).hexdigest() != expected_hash:
            resource_failures.append(name)
    produced_checked, produced_missing, produced_failures = [], [], []
    producer_failures = []
    details = []
    for item in results:
        for stage in ('before', 'after'):
            embedded = item[stage]
            original = read(base / 'regressions' / Path(embedded['producer_receipt']).name)
            if any(embedded.get(key) != value for key, value in original.items()):
                producer_failures.append(item['suite'] + '/' + stage)
        for name, expected_hash in item['produced_files_sha256'].items():
            path = base / 'regressions' / (item['suite'] + '-userdata') / name
            if path.is_file():
                produced_checked.append(item['suite'] + '/' + name)
                if sha(path) != expected_hash:
                    produced_failures.append(item['suite'] + '/' + name)
            else:
                produced_missing.append(item['suite'] + '/' + name)
        text = (base / 'regressions' / (item['suite'] + '.log')).read_text(errors='replace')
        summaries = [line for line in text.splitlines()
                     if re.search(r'checks=\d+.*failures=\d+|\d+ checks, \d+ failures|\d+/\d+ passed', line)]
        counts = []
        for line in summaries:
            pair = re.search(r'checks=(\d+).*failures=(\d+)', line) or re.search(r'(\d+) checks, (\d+) failures', line)
            if pair:
                counts.append({'checks': int(pair[1]), 'failures': int(pair[2])})
            else:
                pair = re.search(r'(\d+)/(\d+) passed', line)
                counts.append({'checks': int(pair[2]), 'failures': int(pair[2]) - int(pair[1])})
        details.append({'suite': item['suite'], 'exit': item['exit'], 'clean_log_receipt': item['clean_log'],
                        'clean_log_recomputed': clean(text), 'summaries': summaries, 'counts': counts,
                        'before_profile_absent': not item['before']['profile_exists'],
                        'before_diagnostics_absent': not item['before']['diagnostics_exist'],
                        'native_user_dir': item['before']['user_data_dir'],
                        'before_after_same_user_dir': item['before']['user_data_dir'] == item['after']['user_data_dir']})
    hud_text = (base / 'regressions/hud_objective_hint.log').read_text()
    hud_cleanup = [json.loads(line.split('HUD_OBJECTIVE_HINT_TEST_CLEANUP ', 1)[1])
                   for line in hud_text.splitlines() if line.startswith('HUD_OBJECTIVE_HINT_TEST_CLEANUP ')]
    return {'expected_suites_from_frozen_source': expected,
            'resource_hashes_checked': len(isolation['source_resources_sha256']),
            'resource_hash_failures': resource_failures,
            'standalone_producer_receipts_checked': 2 * len(results),
            'standalone_producer_receipt_failures': producer_failures,
            'produced_files_checked': produced_checked,
            'produced_files_missing': produced_missing,
            'produced_file_hash_failures': produced_failures,
            'HUD_fixture_cleanup': hud_cleanup,
            'exact_suite_order_matches': [item['suite'] for item in results] == list(expected),
            'all_have_one_summary': all(len(item['counts']) == 1 for item in details),
            'assertion_total': sum(c['checks'] for item in details for c in item['counts']),
            'assertion_failures': sum(c['failures'] for item in details for c in item['counts']),
            'suites': details, 'isolation': isolation}


def menu_audit(base, expected):
    preflight_path = base / 'macos-input-preflight/results.json'
    preflight = read(preflight_path)
    menu = read(base / 'macos-menu-input/results.json')
    same = lambda obj: {key: obj.get(key) for key in IDENTITY} == {key: expected[key] for key in IDENTITY}
    actions_path = base / 'macos-menu-input/actions.json'
    actions = read(actions_path) if actions_path.exists() else []
    paths = {item['path']: item for item in expected['files']}
    helper = menu.get('capture_helper', {})
    return {
        'preflight_source_matches_git_objects': same(preflight.get('source', {})),
        'preflight_artifact_source_matches_git_objects': same(preflight.get('artifact_source', {})),
        'menu_source_matches_git_objects': same(menu.get('source', {})),
        'menu_artifact_source_matches_git_objects': same(menu.get('artifact_source', {})),
        'menu_binds_exact_preflight_file': menu.get('preflight_sha256') == sha(preflight_path),
        'helper_source_expected_sha256': paths['scripts/macos_window_capture.swift']['sha256'],
        'helper_identity_receipt': helper,
        'helper_source_matches_git_objects': helper.get('source_sha256') == paths['scripts/macos_window_capture.swift']['sha256'],
        'preflight': preflight, 'menu': menu,
        'action_count': len(actions),
        'post_attempts': [item for item in actions if item['event'] == 'cg_event_post_attempt'],
        'observed_controls': [item for item in actions if item['event'] == 'native_control_observed'],
        'confirmed_screens': [item for item in actions if item['event'] == 'screen_confirmed'],
        'actions': actions,
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('receipts', type=Path)
    parser.add_argument('--checkout', type=Path, required=True)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = {'receipt_index': index_check(args.receipts),
              'regressions': regressions(args.receipts / 'evidence', args.checkout),
              'menu': menu_audit(args.receipts / 'evidence', read(args.source))}
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'index': result['receipt_index'],
                      'suite_count': len(result['regressions']['suites']),
                      'assertion_total': result['regressions']['assertion_total'],
                      'assertion_failures': result['regressions']['assertion_failures'],
                      'menu_status': result['menu']['menu']['status']}))
