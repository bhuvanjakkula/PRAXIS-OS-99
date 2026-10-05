"""Offline, backup-first migration of local SQLite record integrity."""
import argparse
import json
import sqlite3
from pathlib import Path
from praxis.security.integrity import configured_integrity, FIELD

TABLES=('claims','evidence_events','graph_nodes','graph_edges','quant_models','scenarios','model_runs','decision_revisions','studio_records','local_lab_records')

def scope(table,row):
    if table=='decision_revisions':return dict(tenant='local',decision_id=row['decision_id'],version=row['version'],kind='decision_revision')
    if table=='studio_records':return dict(tenant='local',decision_id=row['decision_id'],id=row['id'],version=row['version'],kind=row['kind'])
    if table=='local_lab_records':return dict(tenant='local',kind=row['kind'],id=row['id'],version=row['version'])
    return dict(tenant='local',table=table,id=row['id'],version=row['version'] if table=='quant_models' else 1)

def migrate(path,backup,protector):
    if protector is None or protector.allow_legacy:raise ValueError('Strict signing key required')
    if not Path(path).is_file():raise ValueError('Existing database required')
    if Path(backup).exists():raise ValueError('Backup destination already exists')
    with sqlite3.connect(path) as c:
        c.row_factory=sqlite3.Row
        # The application and workers must be stopped before this offline command.
        with sqlite3.connect(backup) as destination:c.backup(destination)
        c.execute('BEGIN IMMEDIATE')
        names={r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        count=0
        for table in TABLES:
            if table not in names:continue
            for row in c.execute(f'SELECT rowid AS migration_rowid,* FROM {table}').fetchall():
                payload=json.loads(row['payload']);bound=scope(table,row)
                if FIELD in payload:protector.open(payload,bound)
                else:
                    signed=protector.seal(payload,bound)
                    c.execute(f'UPDATE {table} SET payload=? WHERE rowid=?',(json.dumps(signed),row['migration_rowid']))
                    count+=1
            for row in c.execute(f'SELECT * FROM {table}'):protector.open(json.loads(row['payload']),scope(table,row))
        return count

def main():
    p=argparse.ArgumentParser(description='Stop Praxis and workers before migration. Signatures attest to the imported snapshot, not historical authorship.')
    p.add_argument('database');p.add_argument('--backup',required=True)
    args=p.parse_args();print(json.dumps({'migrated':migrate(args.database,args.backup,configured_integrity()),'verified':True}))

if __name__=='__main__':main()
