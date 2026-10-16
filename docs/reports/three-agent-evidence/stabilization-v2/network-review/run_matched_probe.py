"""Read-only frozen-source nested protocol-client reproduction on reserved ports."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parent
GODOT = Path('/workspace/tools/godot-4.7.2/Godot_v4.7.2-stable_linux.x86_64')
PROJECT = ROOT / 'frozen/game'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', default='original-1')
    parser.add_argument('--port', type=int, default=36071)
    parser.add_argument('--seconds', type=float, default=15)
    parser.add_argument('--probe', default=str(PROJECT / 'tests/protocol_client_probe.gd'))
    parser.add_argument('--audio-driver', default='Dummy')
    parser.add_argument('--client-arg', action='append', default=[])
    args = parser.parse_args()
    assert 36000 <= args.port <= 36999
    out = ROOT / args.name
    out.mkdir(exist_ok=True)
    probe_bytes = Path(args.probe).read_bytes()
    if Path(args.probe).resolve() != (PROJECT / 'tests/protocol_client_probe.gd').resolve():
        copied_probe = out / 'probe.gd'
        copied_probe.write_bytes(probe_bytes)
        args.probe = str(copied_probe)
    def env(role):
        state = out / ('state-' + role)
        state.mkdir(exist_ok=True)
        return {**os.environ, 'XDG_DATA_HOME': str(state), 'XDG_CONFIG_HOME': str(state), 'XDG_CACHE_HOME': str(state)}
    base = [str(GODOT), '--headless', '--verbose', '--audio-driver', args.audio_driver, '--path', str(PROJECT)]
    server_cmd = base + ['--', '--server', f'--port={args.port}']
    client_cmd = base + ['--script', args.probe, '--', f'--port={args.port}', f'--seconds={args.seconds}', '--name=Read-only review'] + args.client_arg
    manifest = {'source_sha': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT / 'frozen', text=True).strip(),
                'probe_sha256': hashlib.sha256(probe_bytes).hexdigest(),
                'server': server_cmd, 'client': client_cmd}
    server_file = (out / 'server.log').open('w')
    server = subprocess.Popen(server_cmd, env=env('server'), stdout=server_file, stderr=subprocess.STDOUT)
    try:
        for _ in range(150):
            if 'SIGHTBREAK_SERVER_READY' in (out / 'server.log').read_text(errors='replace'):
                break
            if server.poll() is not None:
                raise RuntimeError('Server exited before readiness')
            time.sleep(.1)
        else:
            raise RuntimeError('Server readiness timed out')
        with (out / 'client.log').open('w') as client_file:
            client = subprocess.run(client_cmd, env=env('client'), stdout=client_file, stderr=subprocess.STDOUT, timeout=args.seconds + 45)
            manifest['client_exit'] = client.returncode
        client_log = (out / 'client.log').read_text(errors='replace')
        manifest['leaks'] = [line for line in client_log.splitlines() if 'Leaked instance:' in line or 'ObjectDB instances' in line]
        manifest['summaries'] = [line for line in client_log.splitlines() if line.startswith('PROTOCOL_CLIENT ')]
    finally:
        server.terminate()
        try:
            server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.kill(); server.wait(timeout=5)
        server_file.close()
        (out / 'run.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    main()
