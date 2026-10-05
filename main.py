import os
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
src_dir = root / 'src'
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

# Ensure writable sqlite path in serverless environment
if os.environ.get('VERCEL') and not os.environ.get('PRAXIS_DB'):
    os.environ['PRAXIS_DB'] = '/tmp/praxis.db'

from praxis.api import app
