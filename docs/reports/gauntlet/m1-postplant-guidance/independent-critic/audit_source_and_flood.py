#!/usr/bin/env python3
"""Independently reparse retained engine logs and compare frozen Git source."""
import collections
import hashlib
import json
import pathlib
import re
import subprocess
import sys

repo = pathlib.Path(sys.argv[1])
out = pathlib.Path(__file__).parent
logs = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else out
baseline, candidate = '93ec98b', '3c4d921'


def blob(ref, path):
    return subprocess.check_output(['git', 'show', ref + ':' + path], cwd=repo)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def funcs(raw):
    text = raw.decode()
    matches = list(re.finditer(r'^func (\w+)\(', text, re.M))
    result = {}
    for i, match in enumerate(matches):
        lines = text[match.start():matches[i + 1].start() if i + 1 < len(matches) else len(text)].splitlines()
        # Top-level documentation and RPC annotations belong to the next method.
        while lines and (not lines[-1] or lines[-1].startswith(('#', '@rpc'))):
            lines.pop()
        result[match.group(1)] = ('\n'.join(lines) + '\n').encode()
    return result


summary = {
    'baseline': subprocess.check_output(['git', 'rev-parse', baseline], cwd=repo, text=True).strip(),
    'candidate': subprocess.check_output(['git', 'rev-parse', candidate], cwd=repo, text=True).strip(),
    'scope': 'Independent replay of actual builder engine outputs and frozen source; no new game execution',
}
rows = {}
for side in ('baseline', 'candidate'):
    path = logs / f'{side}.log'
    raw = path.read_bytes()
    lines = raw.decode().splitlines()
    samples = [json.loads(line.split(' ', 1)[1]) for line in lines if line.startswith('HUD_PRIORITY_SAMPLE ')]
    benches = [json.loads(line.split(' ', 1)[1]) for line in lines if line.startswith('HUD_PRIORITY_BENCHMARK ')]
    clean = [json.loads(line.split(' ', 1)[1]) for line in lines if line.startswith('HUD_OBJECTIVE_HINT_TEST_CLEANUP ')]
    assert len(samples) == 1458 and len(benches) == 2 and len(clean) == 1
    groups = collections.defaultdict(list)
    for row in samples:
        groups[(row['touch'], row['connection'], row['role'])].append(row)
        assert row['game_tick'] == 0
        assert row['correct'] == (row['actual'] == row['expected'])
        assert row['until'] == row['ui_elapsed'] + 5
    assert len(groups) == 18
    for key, samples_in_group in groups.items():
        assert [row['sample'] for row in samples_in_group] == list(range(81))
        assert [row['ui_elapsed'] for row in samples_in_group] == [2000 + i * .25 for i in range(81)]
        assert key[1] in ('offline', 'hosting', 'connected')
    wrong = sum(not row['correct'] for row in samples)
    assert wrong == (1458 if side == 'baseline' else 0)
    assert all(bench['samples'] == 729 and bench['wrong_frames'] == (729 if side == 'baseline' else 0) for bench in benches)
    assert clean[0]['removed'] and clean[0]['original_user_dir_restored'] and not clean[0]['reason']
    assert not pathlib.Path(clean[0]['native_user_dir']).exists()
    match = re.findall(r'HUD_OBJECTIVE_HINT_TEST source=(.*?) scope=frozen_source_ui checks=(\d+) failures=(\d+)', raw.decode())
    assert len(match) == 1 and int(match[0][1]) == 1535
    rows[side] = {
        'path': str(path), 'bytes': len(raw), 'sha256': sha(raw), 'summary': match[0],
        'flood_samples': len(samples), 'wrong_frames': wrong,
        'groups': [dict(touch=key[0], state=key[1], role=key[2], samples=len(value),
                        wrong=sum(not item['correct'] for item in value)) for key, value in sorted(groups.items())],
        'cleanup': clean[0],
    }
summary['engine_log_audit'] = rows
base_main, cand_main = (blob(ref, 'game/scripts/main.gd') for ref in (baseline, candidate))
bf, cf = funcs(base_main), funcs(cand_main)
assert bf.keys() == cf.keys()
changed = [name for name in bf if bf[name] != cf[name]]
assert changed == ['_process'], changed
summary['main_functions'] = {
    'total': len(bf), 'changed': changed, 'all_other_functions_byte_identical': True,
    'preserved': {name: dict(bytes=len(cf[name]), sha256=sha(cf[name])) for name in
                  ['sync_hud_input_mode', '_refit_kill_feed_rows', '_fit_kill_feed_frame', '_fit_status_line', 'objective_hint', 'show_notification']},
}
base_match, cand_match = (blob(ref, 'game/scripts/gameplay/match.gd') for ref in (baseline, candidate))
bf, cf = funcs(base_match), funcs(cand_match)
changed = [name for name in bf if bf[name] != cf[name]]
added = sorted(cf.keys() - bf.keys())
assert changed == ['_host', '_connect_client', '_fail_connection', '_retry_resume', '_server_disconnected', '_welcome_rpc'], changed
assert added == ['_notify_connection_status']
assert re.findall(rb'^@rpc\(.*?\)\nfunc .*?\n', base_match, re.M) == re.findall(rb'^@rpc\(.*?\)\nfunc .*?\n', cand_match, re.M)
summary['match_functions'] = {
    'baseline_total': len(bf), 'candidate_total': len(cf), 'changed': changed, 'added': added,
    'rpc_annotations_and_signatures_byte_identical': True,
    'preserved': {name: dict(bytes=len(cf[name]), sha256=sha(cf[name])) for name in
                  ['_snapshot', '_snapshot_rpc', '_apply_snapshot', '_authority_tick', '_input_rpc', '_client_tick', '_close_retired_client']},
}
baseline_files = [repo / '.local/postplant-priority/baseline-main.gd',
                  repo / 'docs/reports/gauntlet/m1-postplant-guidance/round-1/baseline-main.gd.source']
baseline_file = next(path for path in baseline_files if path.exists())
assert baseline_file.read_bytes() == base_main
summary['baseline_main_blob_exact'] = True
summary['baseline_main_sha256'] = sha(base_main)
commands = json.loads((logs / 'flood-commands.json').read_text())
for command in commands:
    assert command['sha256'] == rows[command['label']]['sha256']
    assert command['exit_code'] == (1 if command['label'] == 'baseline' else 0)
summary['builder_command_receipts_match'] = True
(out / 'source-and-flood-audit.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps(dict(baseline_wrong=rows['baseline']['wrong_frames'], candidate_wrong=rows['candidate']['wrong_frames'],
                      baseline_total_failures=rows['baseline']['summary'][2], candidate_total_failures=rows['candidate']['summary'][2],
                      main_changed=summary['main_functions']['changed'], match_changed=changed), indent=2))
