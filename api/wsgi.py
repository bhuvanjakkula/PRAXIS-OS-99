from fastapi import FastAPI
import os
import sys
from pathlib import Path

# Add project root and src to python path for Vercel
root = Path(__file__).resolve().parent.parent
src_dir = root / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

# On Vercel, writeable directory is /tmp
if os.environ.get("VERCEL") and not os.environ.get("PRAXIS_DB"):
    os.environ["PRAXIS_DB"] = "/tmp/praxis.db"

import praxis.api as _praxis_api

app: FastAPI = _praxis_api.app
