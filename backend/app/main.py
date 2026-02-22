"""
FastAPI application factory.
Configures middleware, routers, lifecycle events, and exception handlers.
"""

import asyncio
import json
import logging
import logging.config
import sys
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.api.v1.router import router as v1_router
from app.config.settings import get_settings
from app.session.session_store import get_session_store

# ── Logging Setup ─────────────────────────────────────────────────────────────

def _configure_logging(app_env: str) -> None:
    if app_env == "production":
        # JSON structured logging in production
        fmt = '{"time":"%(asctime)s","level":"%(levelname)s","module":"%(name)s","msg":"%(message)s"}'
    else:
        fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

    logging.basicConfig(
        level=logging.DEBUG if app_env == "development" else logging.INFO,
        format=fmt,
        stream=sys.stdout,
    )


logger = logging.getLogger(__name__)


# ── Startup validation ────────────────────────────────────────────────────────

def _validate_startup(settings) -> None:  # type: ignore[no-untyped-def]
    errors = []
    if not settings.ANTHROPIC_API_KEY:
        errors.append("ANTHROPIC_API_KEY is not set.")
    temp_dir = Path(settings.TEMP_DIR)
    try:
        temp_dir.mkdir(parents=True, exist_ok=True)
        test_file = temp_dir / ".write_test"
        test_file.touch()
        test_file.unlink()
    except Exception as exc:
        errors.append(f"TEMP_DIR '{settings.TEMP_DIR}' is not writable: {exc}")
    if errors:
        for err in errors:
            logger.critical("Startup validation failed: %s", err)
        sys.exit(1)


# ── Session cleanup background task ──────────────────────────────────────────

async def _session_cleanup_loop(settings, session_store) -> None:  # type: ignore[no-untyped-def]
    interval = 15 * 60  # every 15 minutes
    while True:
        await asyncio.sleep(interval)
        removed = await session_store.cleanup_expired_sessions(settings.SESSION_TTL_SECONDS)
        if removed:
            logger.info("Session GC: removed %d expired session(s)", removed)


# ── Application factory ───────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[no-untyped-def]
    settings = get_settings()
    _configure_logging(settings.APP_ENV)
    _validate_startup(settings)
    session_store = get_session_store()
    cleanup_task = asyncio.create_task(_session_cleanup_loop(settings, session_store))
    logger.info(
        "AI Code Builder started: version=%s env=%s model=%s",
        settings.APP_VERSION,
        settings.APP_ENV,
        settings.ANTHROPIC_MODEL,
    )
    try:
        yield
    finally:
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            pass
        logger.info("AI Code Builder shutting down.")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="AI Code Builder API",
        version=settings.APP_VERSION,
        description="AI-Powered Python code generation and execution platform.",
        docs_url=None if settings.is_production else "/docs",
        redoc_url=None if settings.is_production else "/redoc",
        lifespan=lifespan,
    )

    # ── CORS ─────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Security headers ─────────────────────────────────────────────────────
    @app.middleware("http")
    async def security_headers(request: Request, call_next):  # type: ignore[no-untyped-def]
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        return response

    # ── Request timing ───────────────────────────────────────────────────────
    @app.middleware("http")
    async def timing_middleware(request: Request, call_next):  # type: ignore[no-untyped-def]
        start = time.monotonic()
        response = await call_next(request)
        duration_ms = int((time.monotonic() - start) * 1000)
        response.headers["X-Response-Time"] = f"{duration_ms}ms"
        logger.debug("%s %s → %d (%dms)", request.method, request.url.path, response.status_code, duration_ms)
        return response

    # ── Exception handlers ───────────────────────────────────────────────────
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):  # type: ignore[no-untyped-def]
        detail = exc.detail
        if isinstance(detail, dict):
            body = detail
        else:
            body = {"error_code": "HTTP_ERROR", "message": str(detail)}
        return JSONResponse(status_code=exc.status_code, content=body)

    @app.exception_handler(ValidationError)
    async def validation_exception_handler(request: Request, exc: ValidationError):  # type: ignore[no-untyped-def]
        return JSONResponse(
            status_code=422,
            content={
                "error_code": "VALIDATION_ERROR",
                "message": "Request validation failed.",
                "fields": exc.errors(),
            },
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):  # type: ignore[no-untyped-def]
        logger.exception("Unhandled exception on %s %s: %s", request.method, request.url.path, exc)
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred." if settings.is_production else str(exc),
            },
        )

    # ── Routers ───────────────────────────────────────────────────────────────
    app.include_router(v1_router, prefix=settings.API_PREFIX)

    # ── Health ────────────────────────────────────────────────────────────────
    @app.get("/health", tags=["Health"])
    async def health() -> dict:
        return {
            "status": "ok",
            "version": settings.APP_VERSION,
            "env": settings.APP_ENV,
        }

    return app


app = create_app()
