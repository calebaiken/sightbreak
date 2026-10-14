#!/usr/bin/env python3
"""Real Godot processes through seeded loopback UDP impairment proxies.

--rtt-ms is added round-trip delay (half each direction), not cellular evidence.
Logs UDP payload bytes actually forwarded; ENet and IP overhead aren't guessed.
No privileged network configuration or public server is used.
"""
import argparse
import bisect
import heapq
import json
import math
import os
import platform
from pathlib import Path
import random
import selectors
import socket
import statistics
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]


def percentile(values, fraction):
    return sorted(values)[min(len(values) - 1, int((len(values) - 1) * fraction))] if values else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rtt-ms', type=float, default=0)
    parser.add_argument('--jitter-ms', type=float, default=0)
    parser.add_argument('--loss', type=float, default=0)
    parser.add_argument('--reorder', type=float, default=0)
    parser.add_argument('--clients', type=int, default=2, choices=range(2, 11))
    parser.add_argument('--seconds', type=float, default=14)
    parser.add_argument('--seed', type=int, default=7301)
    parser.add_argument('--port', type=int, default=29400)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--no-prediction', action='store_true')
    parser.add_argument('--render-client', type=int, default=-1, help='One native rendered client index; -1 keeps all headless (requires DISPLAY)')
    parser.add_argument('--blackout-at', type=float, default=-1, help='Seconds after clients launch; -1 disables')
    parser.add_argument('--blackout-seconds', type=float, default=0)
    parser.add_argument('--reconnect-at', type=float, default=-1, help='Explicitly close each connected client and exercise its resume token at this elapsed time')
    args = parser.parse_args()
    if args.render_client < -1 or args.render_client >= args.clients:
        parser.error('render-client must identify a launched client or be -1')
    if not (0 <= args.blackout_seconds <= 60 and -1 <= args.blackout_at <= args.seconds and -1 <= args.reconnect_at <= args.seconds and 0 <= args.loss < 1 and 0 <= args.reorder <= 1 and args.rtt_ms >= 0 and args.jitter_ms >= 0 and 5 <= args.seconds <= 600):
        parser.error('invalid impairment bounds')
    args.out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(args.seed)
    selector = selectors.DefaultSelector()
    routes, sockets, queue, processes, logs = [], [], [], [], []
    traffic = {'up': {'received_packets': 0, 'forwarded_packets': 0, 'dropped_packets': 0, 'udp_payload_bytes': 0, 'max_datagram_bytes': 0, 'datagrams_over_1200': 0},
               'down': {'received_packets': 0, 'forwarded_packets': 0, 'dropped_packets': 0, 'udp_payload_bytes': 0, 'max_datagram_bytes': 0, 'datagrams_over_1200': 0}}
    samples = {}
    resource_timeline = []
    last_resource_sample = 0.0
    source = {'commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
              'dirty': bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True).strip()),
              'platform': platform.platform(), 'python': platform.python_version()}

    def blackout(now):
        return args.blackout_at >= 0 and args.blackout_at <= now - start < args.blackout_at + args.blackout_seconds
    serial = 0

    def launch(role, name, port, seconds):
        log = (args.out / (name + '.log')).open('w')
        logs.append(log)
        display = ['--audio-driver', 'Dummy'] if name == 'client-' + str(args.render_client) else ['--headless']
        cmd = [str(ROOT / 'scripts/godot.sh'), *display, '--max-fps', '60', '--script', 'res://tests/network_simulation_probe.gd', '--',
               '--role=' + role, '--port=' + str(port), '--seconds=' + str(seconds), '--output=' + str((args.out / (name + '.json')).resolve())]
        if args.no_prediction:
            cmd.append('--no-prediction')
        if args.reconnect_at >= 0 and role == 'client':
            cmd.append('--reconnect-at=' + str(args.reconnect_at))
        process = subprocess.Popen(cmd, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
        processes.append((name, process))
        samples[name] = {'rss_peak_kib': 0, 'cpu_seconds': 0.0}
        return process

    try:
        server = launch('server', 'server', args.port, args.seconds + 3)
        for _ in range(200):
            if 'SIGHTBREAK_SERVER_READY' in (args.out / 'server.log').read_text():
                break
            if server.poll() is not None:
                raise RuntimeError('server startup failed')
            time.sleep(.05)
        else:
            raise RuntimeError('server readiness timed out')
        for index in range(args.clients):
            downstream = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            downstream.bind(('127.0.0.1', args.port + 1 + index))
            upstream = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            upstream.bind(('127.0.0.1', 0))
            route = {'client': None, 'upstream': upstream, 'downstream': downstream,
                     'traffic': {direction: dict(values) for direction, values in traffic.items()}}
            routes.append(route)
            for sock, direction in [(downstream, 'up'), (upstream, 'down')]:
                sock.setblocking(False)
                selector.register(sock, selectors.EVENT_READ, (route, direction))
                sockets.append(sock)
            launch('client', 'client-' + str(index), args.port + index + 1, args.seconds)
        start = time.monotonic()
        deadline = start + args.seconds + 15
        while any(p.poll() is None for _, p in processes) and time.monotonic() < deadline:
            now = time.monotonic()
            while queue and queue[0][0] <= now:
                _, _, sock, destination, packet, direction, route = heapq.heappop(queue)
                if blackout(now):
                    traffic[direction]['dropped_packets'] += 1
                    route['traffic'][direction]['dropped_packets'] += 1
                    continue
                if destination is not None:
                    traffic[direction]['max_datagram_bytes'] = max(traffic[direction]['max_datagram_bytes'], len(packet))
                    traffic[direction]['datagrams_over_1200'] += int(len(packet) > 1200)
                    sock.sendto(packet, destination)
                    traffic[direction]['forwarded_packets'] += 1
                    traffic[direction]['udp_payload_bytes'] += len(packet)
                    per_client = route['traffic'][direction]
                    per_client['max_datagram_bytes'] = max(per_client['max_datagram_bytes'], len(packet))
                    per_client['datagrams_over_1200'] += int(len(packet) > 1200)
                    per_client['forwarded_packets'] += 1
                    per_client['udp_payload_bytes'] += len(packet)
            for key, _ in selector.select(.003):
                route, direction = key.data
                packet, address = key.fileobj.recvfrom(65536)
                traffic[direction]['received_packets'] += 1
                route['traffic'][direction]['received_packets'] += 1
                if direction == 'up':
                    route['client'] = address
                if blackout(now) or rng.random() < args.loss:
                    traffic[direction]['dropped_packets'] += 1
                    route['traffic'][direction]['dropped_packets'] += 1
                    continue
                delay = max(0, args.rtt_ms / 2 + rng.uniform(-args.jitter_ms, args.jitter_ms)) / 1000
                if rng.random() < args.reorder:
                    delay += .04
                sock = route['upstream'] if direction == 'up' else route['downstream']
                destination = ('127.0.0.1', args.port) if direction == 'up' else route['client']
                serial += 1
                heapq.heappush(queue, (now + delay, serial, sock, destination, packet, direction, route))
            for name, process in processes:
                try:
                    status = Path(f'/proc/{process.pid}/status').read_text()
                    rss = next(int(line.split()[1]) for line in status.splitlines() if line.startswith('VmRSS:'))
                    stat = Path(f'/proc/{process.pid}/stat').read_text().rsplit(')', 1)[1].split()
                    cpu = (int(stat[11]) + int(stat[12])) / os.sysconf('SC_CLK_TCK')
                    samples[name]['rss_peak_kib'] = max(samples[name]['rss_peak_kib'], rss)
                    samples[name]['rss_current_kib'] = rss
                    samples[name]['cpu_seconds'] = max(samples[name]['cpu_seconds'], cpu)
                except (OSError, StopIteration):
                    pass
            if now - last_resource_sample >= 1:
                resource_timeline.append({'seconds': now-start, 'peak_samples': {name: dict(row) for name, row in samples.items()}})
                last_resource_sample = now
        failures = [name for name, process in processes if process.poll() != 0]
        for name, _ in processes:
            text = (args.out / (name + '.log')).read_text()
            if 'SCRIPT ERROR' in text or 'ERROR:' in text:
                failures.append(name + ': logged error')
        server_report = json.loads((args.out / 'server.json').read_text()) if (args.out / 'server.json').exists() else {}
        trajectories = {}
        for pose in server_report.get('poses', []):
            trajectories.setdefault(pose['id'], []).append(pose)
        errors, gaps, rendered_steps, prediction_errors = [], [], [], []
        corrections, hard_corrections = 0, 0
        first_movement = []
        final_client_states = []
        for index in range(args.clients):
            path = args.out / f'client-{index}.json'
            if not path.exists():
                failures.append('client-' + str(index) + ': missing report')
                continue
            data = json.loads(path.read_text())
            first_movement.append(data.get("first_movement_seconds"))
            final_client_states.append({"client": index, "state": data.get("state"), "last_snapshot_age_seconds": data.get("last_snapshot_age_seconds"),
                                        "accepted_snapshots": data.get('accepted_snapshots'), "last_accepted_age_seconds": data.get('last_accepted_age_seconds'),
                                        "last_accepted_tick": data.get('last_accepted_tick'), "reconnect_passed": data.get('reconnect_passed')})
            prediction_errors.extend(data.get('prediction_errors_m', []))
            corrections += data.get('corrections', 0)
            hard_corrections += data.get('hard_corrections', 0)
            gaps.extend(data['accepted_tick_gaps'])
            previous = {}
            for pose in data['poses']:
                trajectory = trajectories.get(pose['id'], [])
                offset = bisect.bisect_left([p['t'] for p in trajectory], pose['t'])
                if offset < 1 or offset >= len(trajectory):
                    continue
                a, b = trajectory[offset - 1], trajectory[offset]
                weight = (pose['t'] - a['t']) / max(1e-9, b['t'] - a['t'])
                errors.append(math.sqrt(sum((pose[axis] - (a[axis] + (b[axis] - a[axis]) * weight)) ** 2 for axis in ['x', 'y', 'z'])))
                if pose['id'] in previous:
                    rendered_steps.append(math.dist([pose[a] for a in ['x', 'y', 'z']], previous[pose['id']]))
                previous[pose['id']] = [pose[a] for a in ['x', 'y', 'z']]
        ticks = server_report.get('tick_usec', [])
        intervals = server_report.get('tick_intervals_usec', [])
        report = {'conditions': {k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()},
                  'scope': 'loopback real Godot processes; added RTT simulation; no device/cellular claim',
                  'source': source,
                  'traffic_window_seconds': time.monotonic() - start,
                  'failures': failures, 'traffic': traffic, 'processes': samples,
                  'per_client_traffic': [route['traffic'] for route in routes], 'resource_peak_timeline': resource_timeline,
                  'skipped_commands': server_report.get('skipped_commands', 0),
                  'tick_usec_p50': percentile(ticks, .5), 'tick_usec_p95': percentile(ticks, .95), 'tick_usec_max': max(ticks, default=0),
                  'tick_interval_usec_p50': percentile(intervals, .5), 'tick_interval_usec_p95': percentile(intervals, .95), 'tick_interval_usec_max': max(intervals, default=0),
                  'received_tick_gap_median': statistics.median(gaps) if gaps else None,
                  'render_position_error_p50_m': percentile(errors, .5), 'render_position_error_p95_m': percentile(errors, .95),
                  'prediction_error_at_ack_p50_m': percentile(prediction_errors, .5), 'prediction_error_at_ack_p95_m': percentile(prediction_errors, .95),
                  'first_movement_seconds': first_movement, 'final_client_states': final_client_states,
                  'corrections': corrections, 'hard_corrections': hard_corrections,
                  'render_step_p95_m': percentile(rendered_steps, .95), 'render_samples_compared': len(errors)}
        (args.out / 'summary.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report, indent=2))
        return 1 if failures else 0
    finally:
        for _, process in processes:
            if process.poll() is None:
                process.terminate()
        for _, process in processes:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        for log in logs:
            log.close()
        selector.close()
        for sock in sockets:
            sock.close()


if __name__ == '__main__':
    raise SystemExit(main())
