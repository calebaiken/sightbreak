#!/usr/bin/env python3
"""Verify absence of exact fake-run processes, container and selected ports."""
from datetime import datetime, timezone
import json
from pathlib import Path
import socket
import subprocess
import sys

run, observations, output = (Path(arg).resolve() for arg in sys.argv[1:4])
report = json.loads((run / 'report.json').read_text())
observer = json.loads((observations / 'observer-report.json').read_text())
assert report['status'] in ('passed', 'failed') and observer['status'] == 'finished'
pids = [p['pid'] for p in report['process_exits']] + observer['psql_pids']
processes = [dict(pid=pid, proc_exists=(Path('/proc') / str(pid)).exists()) for pid in pids]
assert not any(p['proc_exists'] for p in processes), 'An owned child PID remains present'
container = report['container']
assert container == observer['container'] and container.startswith('sightbreak-account-match-')
inspection = subprocess.run(['docker', '--host=unix:///var/run/docker.sock', 'inspect', '--format', '{{.Id}}', container],
                            capture_output=True, text=True)
assert inspection.returncode != 0 and 'No such object' in inspection.stderr
tcp = []
for label, port in (('api', report['api_port']), ('postgres', report['postgres_port'])):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(.5)
        code = sock.connect_ex(('127.0.0.1', port))
    tcp.append(dict(name=label, port=port, connect_errno=code))
    assert code != 0, label + ' listener remains open'
udp = []
for family, address in ((socket.AF_INET, '0.0.0.0'), (socket.AF_INET6, '::')):
    with socket.socket(family, socket.SOCK_DGRAM) as sock:
        sock.bind((address, report['game_port']))
    udp.append(dict(family='ipv4' if family == socket.AF_INET else 'ipv6',
                    port=report['game_port'], wildcard_bind_available=True))
result = dict(status='passed', at_utc=datetime.now(timezone.utc).isoformat(), processes=processes,
              container=container, exact_container_absent=True, tcp=tcp, udp=udp,
              observer_psql_children_reaped=observer['all_psql_children_reaped'])
output.write_text(json.dumps(result, indent=2) + '\n')
print('Independent owned cleanup passed:', len(processes), 'child PIDs, exact container, API/PostgreSQL/game ports')
