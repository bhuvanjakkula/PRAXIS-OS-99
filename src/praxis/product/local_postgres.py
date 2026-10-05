"""Windows per-user PostgreSQL lifecycle; state stays outside the synced project."""
import argparse
import json
import os
from pathlib import Path
import secrets
import subprocess
from urllib.parse import quote
from zipfile import ZipFile


def root():
    if os.name != 'nt':
        raise RuntimeError('This launcher is for Windows; use compose.yaml elsewhere')
    return Path(os.environ['LOCALAPPDATA']) / 'PRAXIS-OS' / 'postgresql'


def run(args, **kwargs):
    return subprocess.run([str(arg) for arg in args], check=True,
                          creationflags=subprocess.CREATE_NO_WINDOW, **kwargs)


def config():
    return json.loads((root() / 'connection.secret').read_text(encoding='utf-8'))


def database_url(settings, database='praxis'):
    return (f"postgresql+psycopg://praxis:{quote(settings['app_password'], safe='')}"
            f"@127.0.0.1:{settings['port']}/{database}")


def start():
    base = root()
    control = base / 'pgsql/bin/pg_ctl.exe'
    status = subprocess.run([str(control), '-D', str(base / 'data'), 'status'],
                            capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
    if status.returncode == 0:
        return
    if status.returncode != 3:
        raise RuntimeError('PostgreSQL status could not be checked; run setup first')
    run([control, '-D', base / 'data', '-l', base / 'postgresql.log', '-w', 'start'])


def setup(archive):
    import psycopg
    from psycopg import sql
    from praxis.product.storage import ProductStore
    base = root()
    base.mkdir(parents=True, exist_ok=True)
    sid = run(['powershell', '-NoProfile', '-Command',
               '[System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value'],
              capture_output=True, text=True).stdout.strip()
    # Windows chmod does not restrict read access. Protect the whole state directory.
    run(['icacls', base, '/inheritance:r', '/grant:r',
         f'*{sid}:(OI)(CI)F', '*S-1-5-18:(OI)(CI)F'], capture_output=True)
    binary = base / 'pgsql/bin/postgres.exe'
    if not (base / 'server-extracted').exists():
        with ZipFile(archive) as bundle:
            for entry in bundle.infolist():
                parts = Path(entry.filename).parts
                if len(parts) < 2 or parts[0] != 'pgsql' or parts[1] not in {'bin', 'lib', 'share'}:
                    continue
                target = (base / entry.filename).resolve()
                if not target.is_relative_to(base.resolve()):
                    raise ValueError('Unsafe archive path')
                bundle.extract(entry, base)
        (base / 'server-extracted').write_text('PostgreSQL 16 server files extracted\n', encoding='utf-8')
    version = run([binary, '--version'], capture_output=True, text=True).stdout.strip()
    if not version.startswith('postgres (PostgreSQL) 16.'):
        raise RuntimeError('Expected PostgreSQL 16 binaries')
    secret = base / 'connection.secret'
    if not secret.exists():
        if (base / 'data').exists():
            raise RuntimeError('Existing data has no configuration; refusing to reinitialize')
        with secret.open('x', encoding='utf-8') as handle:
            json.dump({'port':55432, 'admin_password':secrets.token_urlsafe(36),
                       'app_password':secrets.token_urlsafe(36),
                       'signing_key':secrets.token_urlsafe(48), 'tenant':'praxis-local'}, handle)
    settings = config()
    if not (base / 'data/PG_VERSION').exists():
        password_file = base / 'initialization.secret'
        try:
            password_file.write_text(settings['admin_password'], encoding='utf-8')
            run([base / 'pgsql/bin/initdb.exe', '-D', base / 'data', '-U', 'praxis_admin',
                 '--pwfile', password_file, '--auth=scram-sha-256', '--encoding=UTF8', '--locale=C'])
        finally:
            password_file.unlink(missing_ok=True)
    (base / 'data/praxis.conf').write_text(
        f"listen_addresses = '127.0.0.1'\nport = {settings['port']}\npassword_encryption = 'scram-sha-256'\n",
        encoding='utf-8')
    server_config = base / 'data/postgresql.conf'
    if "include = 'praxis.conf'" not in server_config.read_text(encoding='utf-8'):
        with server_config.open('a', encoding='utf-8') as handle:
            handle.write("\n# PRAXIS local instance\ninclude = 'praxis.conf'\n")
    start()
    with psycopg.connect(host='127.0.0.1', port=settings['port'], user='praxis_admin',
                         password=settings['admin_password'], dbname='postgres', autocommit=True) as connection:
        if not connection.execute("SELECT 1 FROM pg_roles WHERE rolname = 'praxis'").fetchone():
            connection.execute(sql.SQL('CREATE ROLE praxis LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD {}')
                               .format(sql.Literal(settings['app_password'])))
        if not connection.execute("SELECT 1 FROM pg_database WHERE datname = 'praxis'").fetchone():
            connection.execute('CREATE DATABASE praxis OWNER praxis')
        connection.execute('REVOKE CONNECT ON DATABASE praxis FROM PUBLIC')
    store = ProductStore(database_url(settings))
    try:
        store.migrate()
        assert store.ready()
    finally:
        store.engine.dispose()
    print(f'{version}; PRAXIS schema installed on 127.0.0.1:{settings["port"]}')
    print(f'Data and private configuration: {base}')


def issue_token(settings):
    from praxis.product.security import Credentials
    output = root() / 'operator.token'
    output.write_text(Credentials(secret=settings['signing_key']).issue(
        'local-operator', settings['tenant'], ['admin'], 86400), encoding='utf-8')
    print(f'Login token (valid 24 hours): {output}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    install = commands.add_parser('setup')
    install.add_argument('--archive', type=Path, required=True)
    for command in ('start', 'serve', 'token', 'status'):
        commands.add_parser(command)
    args = parser.parse_args()
    if args.command == 'setup':
        setup(args.archive)
        return
    if args.command == 'start':
        start()
        return
    settings = config()
    if args.command == 'token':
        issue_token(settings)
    elif args.command == 'status':
        from praxis.product.storage import ProductStore
        store = ProductStore(database_url(settings))
        try:
            print(json.dumps(store.database_status(settings['tenant']), indent=2))
        finally:
            store.engine.dispose()
    elif args.command == 'serve':
        import uvicorn
        start()
        os.environ['PRAXIS_DATABASE_URL'] = database_url(settings)
        os.environ['PRAXIS_SIGNING_KEY'] = settings['signing_key']
        issue_token(settings)
        print('Open http://127.0.0.1:8766/ and paste the token into the sign-in dialog.')
        uvicorn.run('praxis.product.api:application', factory=True, host='127.0.0.1', port=8766)


if __name__ == '__main__':
    main()
