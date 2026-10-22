#!/usr/bin/env python3
"""Independent behavior and log audit of native protocol/handshake raw logs."""
import argparse
import hashlib
import json
import re
from pathlib import Path


def content(path):
    return path.read_text(errors='replace')


def summary(log, prefix):
    match = re.search('^'+prefix+r' (\{.*\})$', log, re.M)
    return json.loads(match.group(1)) if match else {}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--protocol', type=Path, required=True)
    parser.add_argument('--network', type=Path, required=True)
    parser.add_argument('--handshake', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    report = {'protocol': [], 'handshake': [], 'network': {}, 'raw_log_audit': []}
    combos = [('release', 'release'), ('current', 'current'), ('release', 'current'), ('current', 'release'),
              ('future', 'current'), ('current', 'future'), ('previous', 'current'), ('current', 'previous')]
    for client, server in combos:
        name = f'client-{client}.server-{server}'
        client_log = content(args.protocol/(name+'.client.log'))
        server_log = content(args.protocol/(name+'.server.log'))
        data = summary(client_log, 'PROTOCOL_CLIENT')
        failure_times = [float(v) for v in re.findall(r'^PROTOCOL_STATE ([0-9.]+) failed$', client_log, re.M)]
        notices = data.get('notices', [])
        admitted = server_log.count('joined Relay Yard')
        if client == server:
            passed = data.get('joined') is True and data.get('final_state') == 'connected' and admitted >= 1
        elif (client, server) == ('release', 'current'):
            drops = [float(v) for v in re.findall(r'^PROTOCOL_NOTICE ([0-9.]+) Server disconnected', client_log, re.M)]
            first = re.search(r'^PROTOCOL_NOTICE ([0-9.]+) ', client_log, re.M)
            origin = float(first.group(1)) if first else 0
            passed = not data.get('joined') and admitted == 0 and bool(drops) and drops[0]-origin <= 6.5 and 'PROTOCOL_TIMEOUT' in server_log
        elif (client, server) == ('current', 'release'):
            passed = data.get('final_state') == 'failed' and admitted == 0 and bool(failure_times) and failure_times[0] <= 6.5 and any('No version handshake' in n for n in notices)
        else:
            passed = data.get('final_state') == 'failed' and admitted == 0 and bool(failure_times) and failure_times[0] <= 2 and any('Version mismatch' in n for n in notices) and 'PROTOCOL_REJECTED' in server_log
        report['protocol'].append({'combo': client+':'+server, 'passed': bool(passed), 'client_summary': data, 'first_failure_seconds': failure_times[0] if failure_times else None, 'server_admissions': admitted})
    network_logs = {name: content(args.network/name) for name in ['server.log', 'client-a.log', 'client-b.log']}
    clients = [network_logs[name] for name in ['client-a.log', 'client-b.log']]
    report['network'] = {'both_clients_pass': all('NETWORK_CLIENT_PASS' in log for log in clients),
                         'privacy_dictionary_count': sum(int(v) for log in clients for v in re.findall(r'NETWORK_PRIVACY dictionaries=(\d+)', log)),
                         'no_logged_errors': all('ERROR:' not in log and 'SCRIPT ERROR' not in log for log in network_logs.values()),
                         'cleanup_log': content(args.network/'cleanup.log')}
    if args.handshake:
        for name in ['spam', 'fractional', 'huge', 'bad_then_good', 'good_then_bad']:
            client_log = content(args.handshake/f'attack-{name}.client.log')
            server_log = content(args.handshake/f'attack-{name}.server.log')
            data = summary(client_log, 'HANDSHAKE_ATTACK')
            if name == 'good_then_bad':
                passed = data.get('admitted') is True and 'PROTOCOL_REJECTED' not in server_log
            else:
                passed = bool(data) and data.get('admitted') is False and data.get('replies') == 1 and 0 < data.get('dropped_after', 0) < 1.5 and server_log.count('PROTOCOL_REJECTED') == 1
            report['handshake'].append({'case': name, 'passed': passed, 'raw_summary': data})
        for name in ['hang_up', 'reject_then_hang_up', 'accepted_text']:
            log = content(args.handshake/f'hostile-{name}.client.log')
            data = summary(log, 'PROTOCOL_CLIENT')
            notices = re.findall(r'^PROTOCOL_NOTICE [0-9.]+ (.*)$', log, re.M)
            wanted = 'Version mismatch' if name == 'accepted_text' else 'closed the connection during the version check'
            passed = bool(notices) and wanted in notices[-1] and 'older SIGHTBREAK release' not in notices[-1] and data.get('joined') is False
            report['handshake'].append({'case': name, 'passed': passed, 'last_notice': notices[-1] if notices else None, 'client_summary': data})
    for directory in [args.network, args.protocol, *([args.handshake] if args.handshake else [])]:
        for path in sorted(directory.glob('*.log')):
            log = content(path)
            errors = [line for line in log.splitlines() if line.startswith(('ERROR:', 'SCRIPT ERROR:'))]
            report['raw_log_audit'].append({'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'errors': errors,
                                            'resource_leak': 'ObjectDB instances leaked' in log or 'Leaked instance' in log})
    args.out.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'protocol_passed': sum(r['passed'] for r in report['protocol']), 'handshake_passed': sum(r['passed'] for r in report['handshake']),
                      'network': report['network'], 'logged_errors': sum(len(r['errors']) for r in report['raw_log_audit']), 'resource_leaks': sum(r['resource_leak'] for r in report['raw_log_audit'])}, indent=2))


if __name__ == '__main__':
    main()
