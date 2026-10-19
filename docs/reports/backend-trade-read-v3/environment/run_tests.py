from pathlib import Path
import hashlib
import json
import os
import secrets
import subprocess
import sys
import time
import psycopg
from psycopg import sql

source = Path(sys.argv[1]).resolve()
out = Path(sys.argv[2]).resolve()
out.mkdir(parents=True, exist_ok=False)
tests = sys.argv[3:] or ['backend/tests/test_economy.py']
database = 'sightbreak_trade_tests_' + secrets.token_hex(6) + '_test'
admin = 'postgresql://sightbreak:sightbreak_local_only@127.0.0.1:55439/postgres'
with psycopg.connect(admin, autocommit=True) as db:
    version = db.execute('SELECT version()').fetchone()[0]
    db.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(database)))
env = os.environ.copy()
env.update(DATABASE_URL='postgresql+psycopg://sightbreak:sightbreak_local_only@127.0.0.1:55439/' + database,
           PYTHONPATH=os.pathsep.join([str(source/'backend'), str(source/'backend/tests')]),
           PYTHONDONTWRITEBYTECODE='1', SIGHTBREAK_SERVER_ID='local-relay')
env.pop('SIGHTBREAK_SERVER_KEY', None)
command = [sys.executable, '-B', '-m', 'pytest', '-p', 'no:cacheprovider', '--import-mode=importlib', *tests, '-q']
record = {'command': command, 'source': str(source),
          'commit': subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip(),
          'backend_tree': subprocess.check_output(['git','rev-parse','HEAD:backend'],cwd=source,text=True).strip(),
          'backend_status': subprocess.check_output(['git','status','--porcelain','--','backend'],cwd=source,text=True).strip(),
          'python': sys.version, 'postgresql': version, 'database': database}
try:
    start=time.monotonic()
    with (out/'pytest.log').open('w') as log:
        result=subprocess.run(command,cwd=source,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=300)
    record.update(exit=result.returncode,seconds=time.monotonic()-start)
    print((out/'pytest.log').read_text(),flush=True)
finally:
    with psycopg.connect(admin, autocommit=True) as db:
        db.execute(sql.SQL('DROP DATABASE {} WITH (FORCE)').format(sql.Identifier(database)))
    record['database_dropped']=True
    (out/'run.json').write_text(json.dumps(record,indent=2)+'\n')
sys.exit(result.returncode)
