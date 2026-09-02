"""
frontend/settings.py
--------------------
Re-exports the central `settings` object from config.settings for use in
the Streamlit frontend.

When Streamlit runs `frontend/app.py`, it inserts the *frontend/* directory
into sys.path — not the project root. This shim adds the project root so that
`config`, `core`, and `backend` packages are always importable, then simply
re-exports `settings` so that `app.py`'s existing `from settings import settings`
continues to work without any changes to app.py.
"""
import sys
import os

# Walk up two levels: frontend/ -> project root
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from config.settings import settings  # noqa: E402  (import after sys.path fix)

__all__ = ["settings"]
