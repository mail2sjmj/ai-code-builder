"""Code generation endpoint — SSE streaming."""

import logging

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.dependencies import deps_session_store, deps_settings
from app.config.settings import Settings
from app.schemas.codegen import CodeFixRequest, CodeGenRequest
from app.services.codegen_service import stream_code_fix, stream_code_generation
from app.session.session_store import SessionStore
from app.utils.streaming import sse_event_generator

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Code Generation"])


@router.post(
    "/codegen/generate",
    summary="Generate Python transformation code from a refined prompt",
    description="Streams generated Python code via Server-Sent Events.",
)
async def generate_code(
    body: CodeGenRequest,
    settings: Settings = Depends(deps_settings),
    session_store: SessionStore = Depends(deps_session_store),
) -> StreamingResponse:
    stream = stream_code_generation(
        session_id=body.session_id,
        refined_prompt=body.refined_prompt,
        session_store=session_store,
        settings=settings,
    )
    return StreamingResponse(
        sse_event_generator(stream),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.post(
    "/codegen/fix",
    summary="Auto-fix broken Python code using the execution error",
    description="Streams a corrected version of the code via Server-Sent Events.",
)
async def fix_code(
    body: CodeFixRequest,
    settings: Settings = Depends(deps_settings),
    session_store: SessionStore = Depends(deps_session_store),
) -> StreamingResponse:
    stream = stream_code_fix(
        session_id=body.session_id,
        broken_code=body.broken_code,
        error_message=body.error_message,
        session_store=session_store,
        settings=settings,
    )
    return StreamingResponse(
        sse_event_generator(stream),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
