import os
import sys
from pathlib import Path
from fastapi import FastAPI

root = Path(__file__).resolve().parent.parent
src_dir = root / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

if os.environ.get("VERCEL") and not os.environ.get("PRAXIS_DB"):
    os.environ["PRAXIS_DB"] = "/tmp/praxis.db"

import praxis.api as _praxis_api

app = FastAPI(
    title="PRAXIS OS",
    routes=_praxis_api.app.routes,
    middleware=_praxis_api.app.user_middleware,
    exception_handlers=_praxis_api.app.exception_handlers,
)
