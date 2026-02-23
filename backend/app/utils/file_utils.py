"""
File system utilities with path-traversal protection.
"""

import logging
import re
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)

_SAFE_FILENAME_RE = re.compile(r"[^a-zA-Z0-9._\-]")


def safe_filename(name: str) -> str:
    """Strip directory components and restrict characters in a filename."""
    base = Path(name).name  # strip any directory prefix
    sanitized = _SAFE_FILENAME_RE.sub("_", base)
    return sanitized or "upload"


def safe_path_join(base_dir: str, *parts: str) -> Path:
    """
    Join path parts and assert the result stays under base_dir.
    Raises ValueError on path traversal attempts.
    """
    base = Path(base_dir).resolve()
    target = (base / Path(*parts)).resolve()
    if not target.is_relative_to(base):
        raise ValueError(
            f"Path traversal detected: '{target}' escapes base '{base}'"
        )
    return target


def get_session_dir(base_temp_dir: str, session_id: str) -> Path:
    """Return the session-specific directory path (not guaranteed to exist)."""
    return safe_path_join(base_temp_dir, session_id)


def cleanup_session_files(base_temp_dir: str, session_id: str) -> None:
    """Remove all files associated with a session. Silently ignores missing dirs."""
    session_dir = get_session_dir(base_temp_dir, session_id)
    if session_dir.exists():
        shutil.rmtree(session_dir, ignore_errors=True)
        logger.info("Cleaned up session directory: %s", session_dir)
