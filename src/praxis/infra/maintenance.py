"""SQLite inspection and non-destructive, consistent backup/restore operations."""
from contextlib import closing
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import sqlite3


def read_only(path):
    source = Path(path).resolve(strict=True)
    return sqlite3.connect(source.as_uri() + '?mode=ro', uri=True)


def inspect_database(path):
    with closing(read_only(path)) as connection:
        integrity = [row[0] for row in connection.execute('PRAGMA quick_check')]
        names = [row[0] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
        counts = {name: connection.execute('SELECT COUNT(*) FROM "'+name.replace('"','""')+'"').fetchone()[0]
                  for name in names}
        foreign_keys = len(connection.execute('PRAGMA foreign_key_check').fetchall())
    return {'backend':'sqlite', 'sql_version':sqlite3.sqlite_version,
            'status':'ok' if integrity == ['ok'] and not foreign_keys else 'needs_attention',
            'integrity':integrity, 'foreign_key_violations':foreign_keys,
            'table_rows':counts, 'file_bytes':Path(path).stat().st_size}


def snapshot(source, destination):
    """Create a SQLite snapshot into a NEW file. Never replace an existing database."""
    source = Path(source).resolve(strict=True)
    destination = Path(destination).resolve()
    if source == destination:
        raise ValueError('Snapshot destination must differ from source')
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation also refuses existing databases, symlinks and accidental overwrites.
    with destination.open('xb'):
        pass
    with closing(read_only(source)) as origin, closing(sqlite3.connect(destination)) as target:
        origin.backup(target)
    report = inspect_database(destination)
    if report['status'] != 'ok':
        raise ValueError('Snapshot failed integrity validation; preserve it for inspection')
    digest = sha256(destination.read_bytes()).hexdigest()
    return {**report, 'file':destination.name, 'sha256':digest,
            'created_at':datetime.now(timezone.utc).isoformat()}
