"""
Root ASGI entry for Vercel and other hosts that expect app.py at the repo root.
The real FastAPI app lives in backend.app.
"""
from backend.app import app

__all__ = ["app"]
