#!/usr/bin/env python3
"""Synthetic match fixture -> actual Godot HTTP bridge -> isolated PostgreSQL settlement.
Run after `.venv/bin/python backend/bridge_fixture.py --serve` in another terminal.
No normal gameplay bypass exists: fixture mutations occur only in the test script.
"""
from pathlib import Path
import json
import os
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    fixture_path = ROOT / '.local/bridge-fixture.json'
    fixture = json.loads(fixture_path.read_text())
    env = os.environ.copy()
    env['SIGHTBREAK_SERVER_KEY'] = fixture['server_key']
    from sqlalchemy import create_engine, text
    from sqlalchemy.engine import make_url
    assert make_url(fixture['database_url']).database == 'sightbreak_bridge_test', 'Only the isolated bridge fixture database is allowed'
    engine = create_engine(fixture['database_url'])
    # This harness only reads DB records. The backend commits all fixture rewards.
    with tempfile.TemporaryDirectory() as directory:
        report_path = Path(directory) / 'result.json'
        command = [str(ROOT / 'scripts/godot.sh'), '--headless', '--script', 'res://tests/reward_bridge_test.gd', '--', '--fixture=' + str(fixture_path), '--result=' + str(report_path)]
        result = subprocess.run(command, cwd=ROOT, env=env, text=True, capture_output=True, timeout=45)
        print(result.stdout, end='')
        if result.returncode or 'ERROR:' in result.stderr:
            print(result.stderr)
            raise RuntimeError('Native reward adapter failed')
        report = json.loads(report_path.read_text())
        with engine.connect() as database:
            for reward in report['rewards']:
                wallet = database.execute(text('SELECT credits, xp FROM players WHERE id = :id'), {'id': reward['player_id']}).one()
                assert wallet.credits == reward['credits'] and wallet.xp == reward['xp'], 'Wallet differs from single committed reward'
                ledger_count = database.execute(text('SELECT count(*) FROM ledger WHERE player_id = :id AND reference = :match'), {'id': reward['player_id'], 'match': report['match_id']}).scalar_one()
                assert ledger_count == 1, 'Replay created another ledger grant'
            rewards = database.execute(text('SELECT count(*) FROM rewards WHERE id LIKE :prefix'), {'prefix': report['match_id'] + ':%'}).scalar_one()
            assert rewards == 10, 'Expected exactly ten persistent match records'
        print('REWARD_BRIDGE_DB_PASS 10 exact wallets; 10 ledger grants; 10 match records; replay minted nothing')
    engine.dispose()


if __name__ == '__main__':
    main()
