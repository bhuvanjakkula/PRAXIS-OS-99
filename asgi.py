from fastapi import FastAPI
import os
import sys
import shutil
from pathlib import Path

# Add project root and src to python path for Vercel
root = Path(__file__).resolve().parent
if root.name in (src, app, api):
    root = root.parent
src_dir = root / src
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

# On Vercel, writeable directory is /tmp
if os.environ.get(VERCEL):
    db_path = /tmp/praxis.db
    if not os.environ.get(PRAXIS_DB):
        os.environ[PRAXIS_DB] = db_path
    if not os.path.exists(db_path):
        source_db = root / praxis.db
        if source_db.exists():
            try:
                shutil.copyfile(source_db, db_path)
            except Exception:
                pass

import praxis.api as _praxis_api

app: FastAPI = _praxis_api.app
