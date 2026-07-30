import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

base_dir = Path(__file__).resolve().parent
load_dotenv(base_dir / '.env')
load_dotenv()

DB_URL = os.getenv('SUPABASE_DATABASE_URL') or os.getenv('DATABASE_URL')

SCHEMA_PATH = Path(__file__).resolve().parent.parent / 'supabase' / 'schema.sql'


def apply_schema_migration():
    if not DB_URL:
        print('No SUPABASE_DATABASE_URL or DATABASE_URL found in environment. Skipping schema migration.')
        return

    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f'Schema file not found at {SCHEMA_PATH}')

    with SCHEMA_PATH.open('r', encoding='utf-8') as schema_file:
        sql = schema_file.read().strip()

    if not sql:
        raise ValueError('Schema file is empty.')

    print('Applying schema migration from:', SCHEMA_PATH)

    conn = psycopg2.connect(DB_URL)
    try:
        with conn:
            with conn.cursor() as cursor:
                statements = [stmt.strip() for stmt in sql.split(';') if stmt.strip()]
                for statement in statements:
                    cursor.execute(statement)
        print('Schema migration completed successfully.')
    finally:
        conn.close()


if __name__ == '__main__':
    try:
        apply_schema_migration()
    except Exception as exc:
        raise SystemExit(f'Schema migration failed: {exc}')
