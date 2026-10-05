"""Local server launcher, available from source and installed wheels."""
import argparse
import os
from pathlib import Path


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run PRAXIS OS locally")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--db", type=Path, help="SQLite database path")
    sub = parser.add_subparsers(dest="command")
    ingest = sub.add_parser("ingest", help="Persist a local text document as unverified candidates")
    ingest.add_argument("path", type=Path)
    ingest.add_argument("--source-id", required=True, help="Stable local source label")
    ingest.add_argument("--domain", choices=["business", "finance", "technology", "law", "legal", "document", "research"], default="document")
    ingest.add_argument("--jurisdiction")
    ingest.add_argument("--valid-from")
    ingest.add_argument("--valid-to")
    retrieve = sub.add_parser("retrieve", help="Search the persisted source documents")
    retrieve.add_argument("query")
    retrieve.add_argument("--as-of")
    retrieve.add_argument("--known-at")
    retrieve.add_argument("--jurisdiction")
    retrieve.add_argument("--limit", type=int, default=8)
    sub.add_parser('database-check', help='Inspect SQL integrity and table counts without changing data')
    backup = sub.add_parser('backup', help='Create an integrity-checked SQLite snapshot into a new file')
    backup.add_argument('--output', type=Path, required=True)
    restore = sub.add_parser('restore', help='Restore a snapshot to a NEW database, never overwrite the current one')
    restore.add_argument('--input', type=Path, required=True)
    restore.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    if not 1 <= args.port <= 65535:
        parser.error("port must be between 1 and 65535")
    default_data = Path(os.environ.get("LOCALAPPDATA", Path.home() / ".local" / "share")) / "PRAXIS-OS"
    database = args.db or Path(os.environ.get("PRAXIS_DB", str(default_data / "praxis.db")))
    database = database.expanduser().resolve()
    if args.command not in {'database-check', 'backup', 'restore'}:
        database.parent.mkdir(parents=True, exist_ok=True)
    os.environ["PRAXIS_DB"] = str(database)
    if args.command:
        if args.command in {'database-check', 'backup', 'restore'}:
            import json
            from praxis.infra.maintenance import inspect_database, snapshot
            try:
                result = (inspect_database(database) if args.command == 'database-check'
                          else snapshot(args.input if args.command == 'restore' else database, args.output))
            except (ValueError, OSError) as error:
                parser.error(str(error))
            print(json.dumps(result, indent=2))
            return 0
        from praxis.grounding.cli import run
        try:
            return run(args, database)
        except (ValueError, OSError, KeyError) as error:
            parser.error(str(error))
    print(f"PRAXIS OS: http://127.0.0.1:{args.port}/", flush=True)
    print(f"Developer API: http://127.0.0.1:{args.port}/docs", flush=True)
    print(f"Database: {database}", flush=True)
    import uvicorn
    uvicorn.run("praxis.api:app", host="127.0.0.1", port=args.port,
                limit_concurrency=32,timeout_keep_alive=5,proxy_headers=False)


if __name__ == "__main__":
    raise SystemExit(main())
