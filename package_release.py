"""Bundle source, original Git history, docs and build artifacts; exclude local state."""
from hashlib import sha256
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile
import argparse

root = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, default=root.parent / 'PRAXIS-OS-WINDOWS-READY.zip')
parser.add_argument('--dist-dir', type=Path, default=root / 'dist', help='Directory containing the current wheel and source archive')
args = parser.parse_args()
output = args.output.resolve()
dist_dir = args.dist_dir.resolve()
excluded = {".venv", ".pytest_cache", "__pycache__", ".test-tmp", "build", "node_modules", "test-results", "playwright-report", "backups"}
with ZipFile(output, "w", ZIP_DEFLATED) as archive:
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if any(part in excluded or part.endswith(".egg-info") for part in relative.parts):
            continue
        if not path.is_file() or path.suffix in {".pyc", ".db", ".log"}:
            continue
        if (path.name.startswith(".env") and path.name != ".env.example") or path.suffix in {".token", ".secret", ".pem", ".key"} or path.name.endswith((".db-shm", ".db-wal")):
            continue
        if relative.parts[0] == "dist":
            continue
        archive.write(path, Path("praxis-os") / relative)
    for path in sorted(dist_dir.glob('praxis_os-0.9.0*')):
        if path.is_file() and path.name.endswith(('.whl', '.tar.gz')):
            archive.write(path, Path('praxis-os/dist') / path.name)
with ZipFile(output) as archive:
    assert archive.testzip() is None
digest = sha256(output.read_bytes()).hexdigest()
output.with_suffix(".zip.sha256").write_text(f"{digest}  {output.name}\n", encoding="utf-8")
print(f"Verified ZIP: {output} ({output.stat().st_size:,} bytes)")
