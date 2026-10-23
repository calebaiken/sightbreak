#!/usr/bin/env python3
"""Local HTTP fault injection tests retry identity and redirect refusal, no economy grants."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json
import os
import secrets
import subprocess
import threading

ROOT = Path(__file__).resolve().parents[1]


def check_mode(mode):
    calls = []
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            body = self.rfile.read(int(self.headers['Content-Length']))
            calls.append((self.path, body))
            if mode == 'redirect':
                self.send_response(302)
                self.send_header('Location', f'http://127.0.0.1:{self.server.server_port}/must-not-follow')
                self.send_header('Content-Length', '0')
                self.end_headers()
            elif len(calls) < 3:
                body = b'{"detail":"temporary fixture outage"}'
                self.send_response(503)
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            else:
                body = json.dumps({'match_id': 'fixed-test-id'}).encode()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
        def log_message(self, *_args):
            pass
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    env = os.environ.copy()
    env['SIGHTBREAK_SERVER_KEY'] = secrets.token_urlsafe(48)
    try:
        result = subprocess.run([str(ROOT / 'scripts/godot.sh'), '--headless', '--script', 'res://tests/bridge_transport_test.gd', '--', f'--api=http://127.0.0.1:{server.server_port}', '--expect=' + mode], cwd=ROOT, env=env, text=True, capture_output=True, timeout=15)
        print(result.stdout, end='')
        if result.returncode or 'ERROR:' in result.stderr:
            print(result.stderr)
            raise RuntimeError('Bridge transport test failed')
        assert len(calls) == (3 if mode == 'retry' else 1)
        assert len({body for _, body in calls}) == 1, 'Retry changed idempotent payload'
        assert all(path == '/server/matches' for path, _ in calls), 'Privileged redirect was followed'
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


if __name__ == '__main__':
    check_mode('retry')
    check_mode('redirect')
    print('BRIDGE_TRANSPORT_TEST: three bounded identical retries; redirect refused without forwarding')
