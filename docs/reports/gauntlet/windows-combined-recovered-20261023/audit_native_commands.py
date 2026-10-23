"""Check actual Windows source-suite argv, producer records and strict outputs."""
import argparse
import hashlib
import json
from pathlib import Path, PureWindowsPath
import re

SUITES = ['actor', 'match', 'authority_order', 'state_privacy', 'movement_prediction',
          'peer_lifecycle', 'input_mode', 'menu_focus', 'offline_diagnostics',
          'hud_objective_hint', 'activity_provenance', 'bot_squad_symmetry',
          'bot_dry_weapon','transaction_journal', 'gunplay_rules']
EXPECTED = [73, 75, 178, 55, 725, 16, 462, 30, 60, 1535, 32, 2722, 590, 41, 2840]
READ = lambda p: json.loads(p.read_text())
NORMAL = lambda p: str(p).replace('\\', '/').rstrip('/').lower()


def audit(root):
    base = root / 'evidence/regressions'
    isolation = READ(base / 'isolation.json')
    results = READ(base / 'results.json')
    checks, rows, competing = {}, [], []
    checks['actual_fifteen_order'] = [r['suite'] for r in results] == SUITES
    checks['original_limits_and_pinned_engine'] = (isolation['suite_timeout_seconds'] == 120
        and isolation['probe_timeout_seconds'] == 30
        and isolation['engine'] == '4.7.2.stable.official.ed1daf0bf')
    checks['native_import_clean'] = (isolation['import']['exit'] == 0
        and isolation['import']['clean_log'] is True and isolation['import']['wall_seconds'] < 120)
    for item in results:
        suite = item['suite']
        expected = (['--headless', '--audio-driver', 'Dummy', '--script', 'res://tests/gunplay_rules_probe.gd']
                    if suite == 'gunplay_rules' else ['--headless', '--audio-driver', 'Dummy', '--script', 'res://tests/bot_dry_weapon_test.gd'] if suite == 'bot_dry_weapon' else ['--headless', '--script', 'res://tests/' + suite + '_test.gd'])
        command = item['command']
        prefix = suite + ':'
        checks[prefix + 'exact_actual_argv'] = command[1] == '--path' and command[3:] == expected
        checks[prefix + 'one_private_project_and_binary'] = command[:3] == isolation['import']['command'][:3]
        checks[prefix + 'original_suite_limit'] = 0 < item['wall_seconds'] < 120
        log = (base / (suite + '.log')).read_text()
        summaries = re.findall(r'checks=(\d+) failures=(\d+)|(?<!\d)(\d+) checks, (\d+) failures|(?<!\d)(\d+)/(\d+) passed', log)
        counts = []
        for row in summaries:
            a,b,c,d,e,f = row
            counts.append((int(a),int(b)) if a else (int(c),int(d)) if c else (int(f),int(f)-int(e)))
        if suite == 'gunplay_rules':
            native = [json.loads(line.removeprefix('GUNPLAY_RULES ')) for line in log.splitlines() if line.startswith('GUNPLAY_RULES ')]
            counts = [(r['checks'], len(r['failures'])) for r in native]
        checks[prefix + 'single_expected_native_summary'] = counts == [(EXPECTED[SUITES.index(suite)], 0)]
        if suite == 'bot_dry_weapon':
            native = [json.loads(line.removeprefix('BOT_DRY_WEAPON_RESULT ')) for line in log.splitlines() if line.startswith('BOT_DRY_WEAPON_RESULT ')]
            counts = [(r['checks'], r['failures']) for r in native]
        if suite == 'transaction_journal':
            children = [json.loads(line.removeprefix('COMPETING_PROCESS ')) for line in log.splitlines() if line.startswith('COMPETING_PROCESS ')]
            for child in children:
                for stream in child:
                    competing.extend(json.loads(line.removeprefix('OWNER_BLOCKED ')) for line in stream.splitlines() if line.startswith('OWNER_BLOCKED '))
            checks[prefix + 'actual_competing_child'] = (len(children) == len(competing) == 1
                and competing[0]['unchanged'] is True and competing[0]['pid'] > 0
                and all(competing[0][key] == 22 for key in ('claim','clear','stage')))
        producers = []
        for stage in ('before', 'after'):
            receipt = item[stage]
            name = PureWindowsPath(receipt['producer_receipt']).name
            original = READ(base / name)
            checks[prefix + stage + '_original_native_producer_matches'] = original == {k:v for k,v in receipt.items() if k not in ('producer_receipt','run')}
            run = receipt['run']
            checks[prefix + stage + '_clean_native_probe_original_limit'] = run['exit'] == 0 and run['clean_log'] is True and 0 < run['wall_seconds'] < 30
            checks[prefix + stage + '_exact_native_probe_target'] = (run['command'][:3] == command[:3]
                and run['command'][3:5] == ['--headless','--script']
                and run['command'][-2:] == ['--','--receipt=' + receipt['producer_receipt']]
                and NORMAL(receipt['project_path']) == NORMAL(command[2]))
            checks[prefix + stage + '_windows_private_namespace'] = (receipt['os'] == 'Windows'
                and receipt['uses_custom_user_dir'] is True
                and receipt['custom_user_dir'] == isolation['namespace'] + '/' + suite
                and NORMAL(receipt['user_data_dir']) == NORMAL(receipt['data_dir'] + '/' + receipt['custom_user_dir']))
            producers.append(name)
        rows.append({'suite':suite,'native_checks':counts,'command':command,'wall_seconds':item['wall_seconds'],
                     'producer_records':producers,'raw_log_sha256':hashlib.sha256((base/(suite+'.log')).read_bytes()).hexdigest()})
    checks['distinct_31_native_producers_including_bootstrap'] = len(list(base.glob('producer-*.json'))) == 31
    checks['finalization_and_owned_cleanup'] = (isolation['passed'] is True and isolation['failure'] is None
        and isolation['finalization_failures'] == [] and isolation['temporary_project_removed'] is True
        and len(isolation['cleanup']) == 1 and all(r['removed'] is True and NORMAL(r['user_namespace']).endswith('/'+isolation['namespace'].lower()) for r in isolation['cleanup']))
    return {'checks':checks,'all_checks_passed':all(checks.values()),'actual_suite_records':rows,
            'journal_competing_process_receipts':competing,
            'native_assertion_total':sum(EXPECTED) if all(checks.values()) else None,
            'scope':'Actual source-suite and producer file audit. Exported OS input and fixtures are separate evidence; no local engine/OCR.'}


if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    result=audit(a.root);a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'all_checks_passed':result['all_checks_passed'],'native_assertion_total':result['native_assertion_total'],
                      'failed_checks':[k for k,v in result['checks'].items() if not v]}))
