import os
import sys
from pathlib import Path

# Add project root to sys.path so 'app', 'scripts', and 'data' resolve cleanly on Vercel
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Export the ASGI FastAPI application for Vercel Serverless Function runtime
from app.main import app
