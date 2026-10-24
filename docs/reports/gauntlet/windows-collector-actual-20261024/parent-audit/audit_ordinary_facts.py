#!/usr/bin/env python3
"""Reconstruct original ordinary/delayed authority effects; no native execution."""
import argparse
import hashlib
import json
from pathlib import Path
import re


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def audit(base):
    result, actions = read(base / 'results.json'), read(base / 'actions.json')
    commands = read(base / 'commands.json')
    telemetry = read(base / 'authority-telemetry.json')['samples']
    server = (base / 'server.log').read_text(encoding='utf-8', errors='replace')
    client = (base / 'client.log').read_text(encoding='utf-8', errors='replace')
    summaries = [json.loads(line.split('EXPORT_UI_AUTHORITY ', 1)[1]) for line in server.splitlines() if line.startswith('EXPORT_UI_AUTHORITY ')]
    shots = [dict(actor=int(match[1]), shots=int(match[2]), ammo=int(match[3])) for match in re.finditer(r'^EXPORT_UI_SHOT actor=(\d+) shots=(\d+) ammo=(\d+)', server, re.M)]
    summary_path = base / 'authority.json'
    summary = read(summary_path) if summary_path.is_file() else None
    actor_id = summary.get('joined_id') if summary else next((row['joined_id'] for row in reversed(telemetry) if row.get('joined_id', 0) > 0), None)
    own = [row for row in telemetry if row.get('joined_id') == actor_id and 'ammo' in row]
    reload_states = [row for row in own if row.get('reload_remaining', 0) > 0]
    complete = [row for row in own if row.get('reload_remaining') == 0 and row.get('ammo') == 30 and row.get('reserve', 90) < 90]
    fire_edges = [row for row in actions if row.get('event') == 'button_after']
    reload_edges = [row for row in actions if row.get('event') == 'key_after' and row.get('key') == 'r']
    expected_flag = base.name == 'native-input'
    command_rows = {row['name']: row for row in commands}
    server_command, client_command = [command_rows.get(name, {}).get('command', []) for name in ('server', 'client')]
    observations = {name: sum(line.startswith('SIGHTBREAK_INPUT_OBSERVATION ') for line in text.splitlines()) for name, text in [('client', client), ('server', server)]}
    checks = {
        'exact_source': result.get('authority_source', {}).get('source_commit') == 'c32415148db1f110bbc7eadfca3793d4693429ff',
        'source_clean': result.get('authority_source', {}).get('source_dirty') is False and result.get('authority_source', {}).get('source_game_dirty') is False,
        'keyboard_native_reload_command': 'EXPORT_UI_RELOAD_COMMAND actor=' in server and '--automatic-reload' not in server_command,
        'actual_fire_effects': bool(shots) and [row['shots'] for row in shots] == list(range(1, len(shots) + 1)) and all(row['actor'] == actor_id for row in shots),
        'authority_joined_ack_and_depletion': bool(own) and max(row.get('ack', 0) for row in own) > 10 and min(row.get('ammo', 30) for row in own) < 30,
        'reload_start_countdown_and_completion': bool(reload_states) and bool(complete) and 'EXPORT_UI_RELOAD_STARTED trigger=native_client_input' in server and 'EXPORT_UI_RELOAD_COMPLETED ammo=30' in server,
        'summary_fields_recomputed': bool(summary) and summary.get('joined_id', 0) > 0 and summary.get('shots') == len(shots) and summary.get('lowest_ammo') == 30 - len(shots) and summary.get('largest_ack', 0) > 10 and summary.get('reload_seen') is True and summary.get('reload_completed') is True and summary.get('reload_command_seen') is True and summary.get('reload_trigger') == 'native client input',
        'final_ammo_conservation': bool(complete) and complete[-1]['ammo'] == 30 and complete[-1]['reserve'] == 90 - len(shots),
        'source_authority_summary_consistent': bool(summary) and bool(summaries) and summaries[-1] == summary and result.get('authority') == summary,
        'protocol6_prediction_default_false': bool(summary) and summary.get('protocol') == 6 and summary.get('prediction_default') is False,
        'original_one_fire_down_up_native_state': len(fire_edges) == 2 and [row.get('down') for row in fire_edges] == [True, False] and all(row.get('native_state', {}).get('lmb_down') is row['down'] for row in fire_edges),
        'native_R_down_up_state': len(reload_edges) == 2 and [row.get('down') for row in reload_edges] == [True, False] and all(row.get('native_state', {}).get('keys_down', {}).get('r') is row['down'] for row in reload_edges),
        'normal_exit_receipts': result.get('client_exit') == result.get('server_exit') == 0 and len(commands) == 2 and all(row.get('exit_code') == 0 for row in commands) and result.get('cleanup_errors') == [],
        'collector_flag_only_ordinary': ('--native-input-observation' in server_command) is expected_flag and ('--native-input-observation' in client_command) is expected_flag,
        'client_flag_after_user_delimiter': not expected_flag or '--' in client_command and client_command.index('--') < client_command.index('--native-input-observation'),
        'collector_actual_role_logs_or_absence': all(value > 0 for value in observations.values()) if expected_flag else all(value == 0 for value in observations.values()),
    }
    return dict(scenario=base.name, checks=checks, all_effect_checks_passed=all(checks.values()),
                original_result_passed=result.get('passed'), original_error=result.get('error'),
                elapsed_including_cleanup=result.get('elapsed_seconds'), raw_shot_rows=shots,
                authority_summary=summary, authority_summary_records=len(summaries),
                telemetry_samples=len(telemetry), own_actor_samples=len(own),
                positive_reload_samples=reload_states, final_reload_samples=complete,
                actual_fire_edges=fire_edges, actual_reload_edges=reload_edges,
                actual_commands=commands, observation_line_counts=observations,
                hashes={name: hashlib.sha256((base / name).read_bytes()).hexdigest() for name in ('results.json', 'actions.json', 'commands.json', 'authority-telemetry.json', 'server.log', 'client.log')},
                limits=['Telemetry retains only its final128 samples; preceding effects need the full native log.',
                        'OS call/state brackets and authority effects do not measure physical latency or bind an image to an exact authority tick.',
                        'Original source checks owned job accounting and remaining deadline before success; that final accounting query is not a separate serialized raw witness.',
                        'Elapsed includes separate failure/teardown work and is reported separately from original acceptance-budget enforcement.'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('receipts', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    rows = [audit(args.receipts / 'evidence' / name) for name in ('native-input', 'reload-release-first', 'reload-legacy-delayed')]
    args.output.write_text(json.dumps(dict(source='c32415148db1f110bbc7eadfca3793d4693429ff', run_id=40080238905, scenarios=rows), indent=2) + '\n')
    print(json.dumps([dict(scenario=row['scenario'], all_effect_checks_passed=row['all_effect_checks_passed'], failed=[key for key, value in row['checks'].items() if not value], shots=len(row['raw_shot_rows'])) for row in rows]))
