"""Exercise the actual launcher and worker, with an isolated game-process stub."""
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[2]

class SupervisionTests(unittest.TestCase):
    def test_worker_death_stops_and_reaps_game(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'scripts').mkdir(); (root / 'server').mkdir()
            for name in ('scripts/serve-account-match.sh', 'server/result_outbox.py'):
                shutil.copy(ROOT / name, root / name)
            stub = root / 'scripts/godot.sh'
            stub.write_text('#!/bin/sh\nexec python3 -c \'import os,pathlib,time; pathlib.Path(os.environ["GAME_PID_FILE"]).write_text(str(os.getpid())); time.sleep(60)\'\n')
            stub.chmod(0o700)
            env = os.environ.copy()
            env.update(SIGHTBREAK_SERVER_KEY='fictional-test-key-' + 'x' * 32, SIGHTBREAK_ECONOMY_URL='http://127.0.0.1:8185', GAME_PID_FILE=str(root / 'game.pid'))
            for key in ('SIGHTBREAK_RESULT_SPOOL', 'SIGHTBREAK_RESULT_DB', 'SIGHTBREAK_RESULT_LOG'): env.pop(key, None)
            startup = root / '.local/server-results/startup.log'
            startup.parent.mkdir(parents=True)
            startup.write_text('OUTBOX_READY\n') # Restart must not trust old readiness.
            with (root / 'launcher.log').open('w') as log:
                process = subprocess.Popen(['bash', str(root / 'scripts/serve-account-match.sh')], env=env, stdout=log, stderr=subprocess.STDOUT)
                try:
                    deadline = time.monotonic() + 8
                    while not (root / 'game.pid').exists() and time.monotonic() < deadline and process.poll() is None: time.sleep(.05)
                    self.assertTrue((root / 'game.pid').exists(), (root / 'launcher.log').read_text())
                    game = int((root / 'game.pid').read_text())
                    self.assertIsNone(process.poll(), (root / 'launcher.log').read_text())
                    children = subprocess.check_output(['ps', '-o', 'pid=', '--ppid', str(process.pid)], text=True).split()
                    workers = [int(pid) for pid in children if b'result_outbox.py' in Path(f'/proc/{pid}/cmdline').read_bytes()]
                    self.assertEqual(len(workers), 1)
                    os.kill(workers[0], signal.SIGKILL)
                    self.assertEqual(process.wait(timeout=5), 1)
                    self.assertFalse(Path(f'/proc/{game}').exists(), 'game child must be reaped, including zombies')
                    self.assertIn('shutting down account match server', (root / 'launcher.log').read_text())
                finally:
                    if process.poll() is None: process.terminate(); process.wait(timeout=12)
