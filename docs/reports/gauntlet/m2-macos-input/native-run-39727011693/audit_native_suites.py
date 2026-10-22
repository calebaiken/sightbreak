"""Read-only recomputation from transferred native CI raw receipt artifacts.

This never launches Godot or supplies replacement evidence for missing PNGs.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re

SOURCE = 'e7718ee42fd67a65bcb83061c868b34bd9a2c3d2'
RULES = {'buy_seconds':15, 'round_seconds':100, 'device_seconds':35,
         'plant_seconds':3, 'defuse_seconds':5, 'win_score':7}
SUITES = ['actor','match','authority_order','state_privacy','movement_prediction',
          'peer_lifecycle','input_mode','menu_focus','offline_diagnostics','hud_objective_hint']
read = lambda path: json.loads(path.read_text(encoding='utf-8'))
lines = lambda path: [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line]
digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
clean = lambda text: re.search(r'^(?:SCRIPT ERROR|ERROR:)|Parse Error|ObjectDB.*leaked|Leaked instance', text, re.M) is None

def identity(receipt):
    source = receipt.get('source', receipt.get('authority_source', {}))
    return (source.get('source_commit') == SOURCE and source.get('source_dirty') is False
            and source.get('source_game_dirty') is False)

def exits(receipt):
    return (receipt.get('cleanup_errors') == [] and bool(receipt.get('commands'))
            and all(command.get('exit_code') == 0 for command in receipt['commands']))

def index_check(root):
    index = read(root/'qa-receipts-index.json')
    failures = []
    for entry in index['files']:
        path = root/entry['archive_path']
        if not path.is_file() or path.stat().st_size != entry['bytes'] or digest(path) != entry['sha256']:
            failures.append(entry['path'])
    expected = {entry['archive_path'] for entry in index['files']}
    actual = {path.relative_to(root).as_posix() for path in (root/'evidence').rglob('*') if path.is_file()}
    return {'files':len(expected),'all_sizes_and_hashes_match':not failures,
            'complete_selected_file_set':actual==expected,'failures':failures}

def regressions(base):
    isolation = read(base/'regressions/isolation.json')
    results = read(base/'regressions/results.json')
    before = [item['before'] for item in results]
    after = [item['after'] for item in results]
    retained_produced=[]
    missing_produced=[]
    mismatched_produced=[]
    native_summaries={}
    hud_log=(base/'regressions/hud_objective_hint.log').read_text(errors='replace')
    hud_cleanup=[json.loads(line.split('HUD_OBJECTIVE_HINT_TEST_CLEANUP ',1)[1])
                 for line in hud_log.splitlines() if line.startswith('HUD_OBJECTIVE_HINT_TEST_CLEANUP ')]
    for item in results:
        suite=item['suite']
        native_summaries[suite]=[line for line in (base/'regressions'/(suite+'.log')).read_text(errors='replace').splitlines()
                                 if re.search(r'checks=\d+.*failures=\d+|\d+ checks, \d+ failures|\d+/\d+ passed',line)]
        for name,expected in item['produced_files_sha256'].items():
            path=base/'regressions'/(suite+'-userdata')/name
            if path.is_file():
                retained_produced.append(suite+'/'+name)
                if digest(path)!=expected:mismatched_produced.append(suite+'/'+name)
            else:
                missing_produced.append(suite+'/'+name)
    checks = {
        'ten_exact_maintained_suites':[item['suite'] for item in results] == SUITES,
        'all_native_exits_clean':all(item['exit']==0 and item['clean_log'] for item in results),
        'native_logs_clean':all(clean((base/'regressions'/(item['suite']+'.log')).read_text(errors='replace')) for item in results),
        'every_suite_has_native_assertion_summary':all(native_summaries.values()),
        'fresh_before_state':all(not item['profile_exists'] and not item['diagnostics_exist'] for item in before),
        'distinct_native_producer_paths':len({item['user_data_dir'] for item in before})==len(SUITES),
        'before_after_same_native_path':all(a['user_data_dir']==b['user_data_dir'] and a['custom_user_dir']==b['custom_user_dir'] for a,b in zip(before,after)),
        'native_custom_identity_selected':all(item['uses_custom_user_dir'] and item['custom_user_dir']==isolation['namespace']+'/'+suite for suite,item in zip(SUITES,before)),
        'native_path_matches_namespace':all(item['user_data_dir'].replace('\\','/').endswith('/'+item['custom_user_dir']) for item in before),
        'original_resources_unchanged':isolation['source_resources_unchanged'],
        'copied_resources_unchanged':isolation['copied_resources_unchanged'],
        'owned_cleanup_complete':isolation['temporary_project_removed'] and bool(isolation['cleanup']) and all(item['removed'] for item in isolation['cleanup']),
        'no_finalization_failure':isolation['failure'] is None and isolation['finalization_failures']==[],
        'isolation_pass_receipt':isolation['passed'],
        'retained_produced_files_match_hashes':not mismatched_produced,
        'separate_HUD_fixture_cleanup_attested':len(hud_cleanup)==1 and hud_cleanup[0]['owned'] is True and hud_cleanup[0]['removed'] is True and hud_cleanup[0]['original_user_dir_restored'] is True and hud_cleanup[0]['reason']=='' and hud_cleanup[0]['original_exit']==0 and hud_cleanup[0]['exit']==0,
    }
    return {'checks':checks,'all_checks_passed':all(checks.values()),
            'native_test_summaries':native_summaries,
            'retained_produced_files_verified':retained_produced,
            'produced_files_not_in_selected_receipts':missing_produced,
            'HUD_fixture_cleanup_native_receipts':hud_cleanup,
            'suites':[
        {'suite':item['suite'],'exit':item['exit'],'wall_seconds':item['wall_seconds'],
         'produced_files':item['produced_files_sha256'],'native_user_dir':item['before']['user_data_dir']}
        for item in results]}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description='Read-only transferred native source-suite audit')
    parser.add_argument('root',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    result=regressions(args.root/'evidence')
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'all_checks_passed':result['all_checks_passed']}))
