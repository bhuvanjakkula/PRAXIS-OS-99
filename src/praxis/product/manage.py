"""Operator-only migrations, credential issuance, OpenAPI export and demo seed."""
import argparse
import json
import os
from pathlib import Path
from uuid import UUID, uuid5, NAMESPACE_URL
from praxis.product.storage import ProductStore
from praxis.product.security import Credentials, Principal


def main():
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("migrate")
    issue = commands.add_parser("issue-token")
    issue.add_argument("--subject", required=True); issue.add_argument("--tenant", required=True)
    issue.add_argument("--roles", required=True); issue.add_argument("--output", type=Path, required=True)
    issue.add_argument("--lifetime", type=int, default=3600)
    seed = commands.add_parser("seed"); seed.add_argument("--tenant", required=True)
    export = commands.add_parser("openapi"); export.add_argument("--output", type=Path, required=True)
    sync = commands.add_parser('sync-file', help='Import a normalized export into one tenant atomically')
    sync.add_argument('--tenant', required=True)
    sync.add_argument('--source-id', type=UUID, required=True)
    sync.add_argument('--path', type=Path, required=True)
    args = parser.parse_args()
    if args.command == "issue-token":
        token = Credentials().issue(args.subject, args.tenant, args.roles.split(","), args.lifetime)
        with args.output.open("x", encoding="utf-8") as f: f.write(token)
        try: args.output.chmod(0o600)
        except OSError: pass
        print("Credential written to the specified file; expires after", args.lifetime, "seconds")
        return
    store = ProductStore(os.environ["PRAXIS_DATABASE_URL"])
    if args.command == "migrate": store.migrate(); print("Schema version 1 installed"); return
    if args.command == 'sync-file':
        from praxis.product.enterprise import SyncBatch, synchronize
        if args.path.stat().st_size > 3_000_000:
            parser.error('Export file exceeds 3 MB')
        batch = SyncBatch.model_validate_json(args.path.read_text(encoding='utf-8'))
        principal = Principal('import-operator', args.tenant, frozenset({'admin'}))
        print(json.dumps(synchronize(store, principal, args.source_id, batch), indent=2))
        return
    if args.command == "openapi":
        from praxis.product.api import create_app
        args.output.write_text(json.dumps(create_app(store).openapi(), indent=2), encoding="utf-8")
        return
    principal = Principal("seed-operator", args.tenant, frozenset({"admin"}))
    org = str(uuid5(NAMESPACE_URL, f"praxis-demo:{args.tenant}:organization"))
    for label, kind, owner, attributes in [
        ("Demo Organization", "organization", None, {"demo":True}),
        ("Finance", "team", org, {"objective":"Preserve runway"}),
        ("Technology", "team", org, {"objective":"Reduce technical debt"}),
        ("Legal", "team", org, {"objective":"Review compliance exposure"}),
        ("Cash", "money", org, {"balance":1000000,"currency":"INR","demo":True}),
    ]:
        identifier = org if owner is None else str(uuid5(NAMESPACE_URL, f"praxis-demo:{args.tenant}:{label}"))
        if store.history(args.tenant,"institution",identifier): continue
        store.put(principal,"institution",identifier,{"id":identifier,"name":label,"kind":kind,"owner_id":owner,"attributes":attributes,"version":1})
    print("Demo institutional entities seeded without external connections")


if __name__ == "__main__": main()
