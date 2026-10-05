import sys
from pathlib import Path

# Add project root and src to python path for Vercel
root = Path(__file__).resolve().parent.parent
src_dir = root / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from praxis.api import app
