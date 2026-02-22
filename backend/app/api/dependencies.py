"""FastAPI dependency providers."""

from app.config.settings import Settings, get_settings
from app.session.session_store import SessionStore, get_session_store


def deps_settings() -> Settings:
    return get_settings()


def deps_session_store() -> SessionStore:
    return get_session_store()
