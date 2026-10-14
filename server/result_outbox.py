#!/usr/bin/env python3
"""Local server-only result recovery; no listening socket or secret persistence.

Godot flushes/renames immutable result files. This worker imports them into SQLite
FULL/WAL before removing source files, then retries exact payloads over verified
HTTPS (or exact loopback HTTP). Backend idempotency remains the award authority.
"""
import argparse
from contextlib import closing
import fcntl
import hashlib
import http.client
import json
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import signal
import sqlite3
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from uuid import UUID

MAX_BYTES = 16384
MAX_RESPONSE = 65536
RETENTION = 7 * 86400
MAX_PENDING_AGE = 86400


def canonical(payload):
    if not isinstance(payload, dict) or set(payload) != {'match_id', 'mode', 'started_at', 'ended_at', 'participants'}:
        raise ValueError('Invalid result fields')
    if not isinstance(payload['match_id'], str) or any(not isinstance(payload[k], str) or len(payload[k]) > 64 for k in ('started_at', 'ended_at')):
        raise ValueError('Invalid identity/timestamps')
    identity = str(UUID(payload['match_id']))
    if identity != payload['match_id'] or payload['mode'] != 'ranked_5v5' or not isinstance(payload['participants'], list) or len(payload['participants']) != 10:
        raise ValueError('Invalid result identity/mode/roster')
    for player in payload['participants']:
        if not isinstance(player, dict) or set(player) != {'player_id', 'won', 'active_seconds', 'objective_contributions', 'abandoned'}:
            raise ValueError('Unexpected participant fields')
        if not isinstance(player['player_id'], str) or str(UUID(player['player_id'])) != player['player_id']:
            raise ValueError('Invalid participant identity')
        if type(player['won']) is not bool or type(player['abandoned']) is not bool or type(player['active_seconds']) is not int or type(player['objective_contributions']) is not int:
            raise ValueError('Invalid participant types')
    encoded = json.dumps(payload, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    if len(encoded) > MAX_BYTES:
        raise ValueError('Oversized result')
    return identity, encoded, hashlib.sha256(encoded).hexdigest()


def sync_directory(path):
    descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try: os.fsync(descriptor)
    finally: os.close(descriptor)


class Outbox:
    def __init__(self, path, max_records=2048):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.max_records = max_records
        with closing(self.connect()) as db, db:
            db.execute('PRAGMA journal_mode=WAL')
            db.execute('''CREATE TABLE IF NOT EXISTS results (
                id TEXT PRIMARY KEY, payload BLOB NOT NULL, fingerprint TEXT NOT NULL,
                state TEXT NOT NULL CHECK(state IN ('pending','committed','dead')),
                created REAL NOT NULL, updated REAL NOT NULL, attempts INTEGER NOT NULL DEFAULT 0,
                next_attempt REAL NOT NULL DEFAULT 0, status INTEGER NOT NULL DEFAULT 0,
                response BLOB)''')
        os.chmod(self.path, 0o600)
        sync_directory(self.path.parent)

    def connect(self):
        db = sqlite3.connect(self.path, timeout=5)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA synchronous=FULL')
        db.execute('PRAGMA busy_timeout=5000')
        return db

    def enqueue(self, payload, now=None):
        now = time.time() if now is None else now
        identity, encoded, fingerprint = canonical(payload)
        with closing(self.connect()) as db, db:
            db.execute('BEGIN IMMEDIATE')
            old = db.execute('SELECT * FROM results WHERE id=?', (identity,)).fetchone()
            if old:
                if old['fingerprint'] != fingerprint: raise ValueError('Match identity collision')
                return old['state']
            db.execute("DELETE FROM results WHERE state IN ('committed','dead') AND updated<?", (now - RETENTION,))
            if db.execute('SELECT count(*) FROM results').fetchone()[0] >= self.max_records:
                raise OverflowError('Outbox capacity reached; keep source spool')
            db.execute('INSERT INTO results(id,payload,fingerprint,state,created,updated) VALUES(?,?,?,\'pending\',?,?)', (identity, encoded, fingerprint, now, now))
        return 'pending'

    def import_spool(self, directory, now=None):
        now = time.time() if now is None else now
        imported = 0
        # Bounded scan; full source files remain untouched if durable import fails.
        for path in sorted(Path(directory).iterdir())[:512]:
            if path.is_symlink() or not path.is_file() or path.suffix not in ('.json', '.tmp', '.invalid'):
                continue
            try:
                age = now - path.stat().st_mtime
            except FileNotFoundError:
                continue # Producer atomically renamed a temporary file.
            if path.suffix == '.invalid':
                if age > MAX_PENDING_AGE:
                    try: path.unlink()
                    except FileNotFoundError: continue
                    sync_directory(path.parent)
                continue
            if path.suffix == '.tmp' and age < 10:
                continue
            try:
                with path.open('rb') as source: raw = source.read(MAX_BYTES + 1)
                if len(raw) > MAX_BYTES: raise ValueError('Oversized spool record')
                payload = json.loads(raw)
                if not isinstance(payload, dict): raise ValueError('Invalid spool object')
                if not path.name.startswith(str(payload.get('match_id', '')) + '.'):
                    raise ValueError('Spool identity mismatch')
                self.enqueue(payload, now)
                path.unlink()
                sync_directory(path.parent)
                imported += 1
            except FileNotFoundError:
                continue # Source changed between directory scan and open.
            except OverflowError:
                break
            except (ValueError, TypeError, KeyError, RecursionError):
                # Malformed/partial writes never mint rewards. Retain for diagnosis,
                # then expire after one day; pending valid results are never pruned here.
                try:
                    if age > MAX_PENDING_AGE:
                        path.unlink()
                    else:
                        path.rename(path.with_suffix(path.suffix + '.invalid'))
                except FileNotFoundError:
                    continue # Producer completed a previously partial write.
                sync_directory(path.parent)
                logging.getLogger('outbox').warning('OUTBOX_INVALID_SPOOL record=%s', path.name)
        return imported

    def deliver_one(self, transport, now=None):
        now = time.time() if now is None else now
        with closing(self.connect()) as db:
            row = db.execute("SELECT * FROM results WHERE state='pending' AND next_attempt<=? ORDER BY created,id LIMIT 1", (now,)).fetchone()
        if row is None: return False
        status, response = transport(bytes(row['payload']))
        valid_response = False
        if 200 <= status < 300:
            try:
                data = json.loads(response)
                valid_response = data.get('match_id') == row['id'] and isinstance(data.get('rewards'), list) and len(data['rewards']) == 10
            except (ValueError, TypeError, AttributeError, RecursionError): pass
        state = 'committed' if valid_response else 'pending'
        if not valid_response and ((300 <= status < 500 and status not in (408, 429)) or now - row['created'] >= MAX_PENDING_AGE):
            state = 'dead'
        attempts = row['attempts'] + 1
        with closing(self.connect()) as db, db:
            db.execute('UPDATE results SET state=?,updated=?,attempts=?,next_attempt=?,status=?,response=? WHERE id=?',
                       (state, now, attempts, now + min(60, 2 ** min(attempts, 6)), status, response[:MAX_RESPONSE] if valid_response else None, row['id']))
        logging.getLogger('outbox').info('OUTBOX_DELIVERY match=%s state=%s status=%s attempts=%s', row['id'], state, status, attempts)
        return True

    def maintenance(self, now=None):
        now = time.time() if now is None else now
        with closing(self.connect()) as db:
            with db:
                db.execute("DELETE FROM results WHERE state IN ('committed','dead') AND updated<?", (now - RETENTION,))
            db.execute('PRAGMA wal_checkpoint(PASSIVE)')


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *_args, **_kwargs): return None


def http_transport(origin, key):
    parsed = urllib.parse.urlsplit(origin)
    if parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username or parsed.password or parsed.path not in ('', '/') or parsed.query or parsed.fragment:
        raise ValueError('Invalid backend origin')
    if parsed.scheme != 'https' and parsed.hostname not in ('127.0.0.1', 'localhost'):
        raise ValueError('Plaintext backend must be exact loopback')
    if parsed.port is not None and not 1 <= parsed.port <= 65535: raise ValueError('Invalid backend port')
    if len(key) < 32: raise ValueError('Server credential missing')
    opener = urllib.request.build_opener(NoRedirect(), urllib.request.HTTPSHandler(context=ssl.create_default_context()))
    def send(payload):
        request = urllib.request.Request(origin.rstrip('/') + '/server/matches', payload, {'Content-Type': 'application/json', 'X-Server-Key': key})
        try:
            with opener.open(request, timeout=10) as response:
                body = response.read(MAX_RESPONSE + 1)
                return (response.status, body) if len(body) <= MAX_RESPONSE else (0, b'')
        except urllib.error.HTTPError as error:
            status = error.code
            error.close()
            return status, b''
        except (urllib.error.URLError, TimeoutError, OSError, http.client.HTTPException):
            return 0, b''
    return send


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', type=Path, required=True)
    parser.add_argument('--spool', type=Path, required=True)
    parser.add_argument('--backend', default='http://127.0.0.1:8080')
    parser.add_argument('--once', action='store_true')
    parser.add_argument('--log', type=Path, help='Rotate delivery metadata at1MiB with3 backups')
    args = parser.parse_args()
    os.umask(0o077)
    handler = RotatingFileHandler(args.log, maxBytes=1048576, backupCount=3) if args.log else logging.StreamHandler()
    logging.basicConfig(level=logging.INFO, handlers=[handler], format='%(message)s')
    args.database.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    args.spool.mkdir(parents=True, exist_ok=True, mode=0o700)
    lock = os.open(str(args.database) + '.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    outbox = Outbox(args.database)
    send = http_transport(args.backend, os.environ.get('SIGHTBREAK_SERVER_KEY', ''))
    stopping = False
    def stop(_signum, _frame):
        nonlocal stopping
        stopping = True
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    print('OUTBOX_READY', flush=True)
    while not stopping:
        outbox.import_spool(args.spool)
        outbox.deliver_one(send)
        outbox.maintenance()
        if args.once: break
        time.sleep(.25)
    os.close(lock)

if __name__ == '__main__': main()
