"""Explicit, repeatable initial migration. Never run schema changes at API startup."""
from pathlib import Path
from sqlalchemy import text
from app import engine, Base
if __name__ == '__main__':
    Base.metadata.create_all(engine)
    with engine.begin() as connection:
        for migration in sorted((Path(__file__).parent / 'migrations').glob('*.sql')):
            connection.exec_driver_sql(migration.read_text())
    print('PostgreSQL schema migrated to version 4')
