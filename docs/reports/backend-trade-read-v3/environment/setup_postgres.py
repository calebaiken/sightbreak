"""One-off portable loopback PostgreSQL setup for the isolated trade-read audit."""
from pathlib import Path
import hashlib
import json
import socket
import subprocess
import urllib.request
import zipfile

root = Path(__file__).resolve().parent
url = 'https://get.enterprisedb.com/postgresql/postgresql-17.11-5-windows-x64-binaries.zip'
archive = root / 'postgresql-17.11-5-windows-x64-binaries.zip'
if not archive.exists():
    with urllib.request.urlopen(url, timeout=120) as response, archive.open('wb') as output:
        while block := response.read(1024 * 1024):
            output.write(block)
digest = hashlib.file_digest(archive.open('rb'), 'sha256').hexdigest()
with zipfile.ZipFile(archive) as package:
    for member in package.infolist():
        if member.filename.startswith(('pgsql/bin/', 'pgsql/lib/', 'pgsql/share/')):
            package.extract(member, root)
binary = root / 'pgsql/bin'
data = root / 'data'
password = root / 'local-password.txt'
password.write_text('sightbreak_local_only\n')
port = 55439
with socket.socket() as probe:
    probe.bind(('127.0.0.1', port))

commands = []
def run(args):
    result = subprocess.run([str(x) for x in args], text=True, capture_output=True, timeout=120)
    commands.append({'command': [str(x) for x in args], 'exit': result.returncode,
                     'stdout': result.stdout, 'stderr': result.stderr})
    (root / 'postgres-setup.json').write_text(json.dumps({'url': url, 'sha256': digest, 'port': port, 'commands': commands}, indent=2))
    print(result.stdout, result.stderr, flush=True)
    result.check_returncode()

run([binary / 'postgres.exe', '--version'])
if not data.exists():
    run([binary / 'initdb.exe', '-D', data, '-U', 'sightbreak', '--pwfile', password,
         '--auth=scram-sha-256', '--encoding=UTF8', '--locale=C'])
run([binary / 'pg_ctl.exe', '-D', data, '-l', root / 'postgres.log', '-o',
     f'-h 127.0.0.1 -p {port} -c max_connections=30 -c shared_buffers=32MB', '-w', 'start'])
